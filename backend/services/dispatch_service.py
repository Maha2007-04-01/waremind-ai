import logging
import uuid
from database.db import db_transaction, get_db_connection
from utils.helpers import generate_id, get_current_timestamp
from services.order_service import OrderService

logger = logging.getLogger(__name__)

class DispatchService:
    @staticmethod
    def create_dispatch(order_id, carrier="FedEx Freight"):
        """
        Creates dispatch manifest for an order.
        Rule: Dispatch cannot happen before quality check passes (Order status must be QC_PASSED).
        """
        order = OrderService.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order '{order_id}' not found.")

        if order['status'] != 'QC_PASSED':
            raise ValueError(f"Dispatch cannot happen for Order '{order_id}'. Current status is '{order['status']}'. Quality Check must be PASSED first.")

        dispatch_id = generate_id("DSP")
        tracking_number = f"TRK-WM-{uuid.uuid4().hex[:8].upper()}"
        now = get_current_timestamp()

        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO dispatches (id, order_id, carrier, tracking_number, status, dispatched_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (dispatch_id, order['id'], carrier, tracking_number, "PREPARING", None))

            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "DISPATCH_MANIFEST_CREATED", "ORDER", order['id'], f"Dispatch manifest {dispatch_id} created with carrier {carrier} and tracking {tracking_number}.", now))

        return DispatchService.get_dispatch_by_id(dispatch_id)

    @staticmethod
    def get_dispatch_by_id(dispatch_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dispatches WHERE id = ? OR tracking_number = ?;", (dispatch_id, dispatch_id))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def assign_carrier(dispatch_id, carrier_name):
        dispatch = DispatchService.get_dispatch_by_id(dispatch_id)
        if not dispatch:
            raise ValueError(f"Dispatch '{dispatch_id}' not found.")

        now = get_current_timestamp()
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE dispatches SET carrier = ? WHERE id = ?;", (carrier_name, dispatch['id']))

            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "CARRIER_ASSIGNED", "DISPATCH", dispatch['id'], f"Carrier '{carrier_name}' assigned to dispatch {dispatch['id']}.", now))

        return DispatchService.get_dispatch_by_id(dispatch['id'])

    @staticmethod
    def mark_dispatched(dispatch_id):
        """
        Marks dispatch as DISPATCHED and finalizes physical inventory stock deduction.
        Deducts allocated quantities from physical stock (quantity) and releases reserved_quantity.
        Updates order status to DISPATCHED.
        """
        dispatch = DispatchService.get_dispatch_by_id(dispatch_id)
        if not dispatch:
            raise ValueError(f"Dispatch '{dispatch_id}' not found.")

        if dispatch['status'] == 'DISPATCHED':
            return dispatch

        order_id = dispatch['order_id']
        now = get_current_timestamp()

        with db_transaction() as conn:
            cursor = conn.cursor()

            # Finalize Inventory: Deduct physical stock & release reserved stock
            cursor.execute("""
                SELECT location_id, product_id, quantity
                FROM inventory_allocations
                WHERE order_id = ? AND allocation_status = 'ALLOCATED';
            """, (order_id,))
            allocations = cursor.fetchall()

            for alloc in allocations:
                loc_id = alloc['location_id']
                prod_id = alloc['product_id']
                alloc_qty = alloc['quantity']

                cursor.execute("""
                    UPDATE inventory
                    SET quantity = MAX(0, quantity - ?),
                        reserved_quantity = MAX(0, reserved_quantity - ?),
                        last_updated = ?
                    WHERE location_id = ? AND product_id = ?;
                """, (alloc_qty, alloc_qty, now, loc_id, prod_id))

            # Update allocation records status
            cursor.execute("UPDATE inventory_allocations SET allocation_status = 'DISPATCHED' WHERE order_id = ?;", (order_id,))

            # Update dispatch status
            cursor.execute("UPDATE dispatches SET status = 'DISPATCHED', dispatched_at = ? WHERE id = ?;", (now, dispatch['id']))

            # Update order status
            cursor.execute("UPDATE orders SET status = 'DISPATCHED' WHERE id = ?;", (order_id,))

            # Audit Log
            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "ORDER_DISPATCHED", "ORDER", order_id, f"Order {order_id} dispatched via {dispatch['carrier']}. Tracking: {dispatch['tracking_number']}. Inventory finalized.", now))

        return DispatchService.get_dispatch_by_id(dispatch['id'])
