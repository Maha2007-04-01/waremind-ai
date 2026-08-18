import logging
from database.db import db_transaction, get_db_connection
from utils.helpers import generate_id, get_current_timestamp
from services.order_service import OrderService
from ai.reorder_engine import ReorderEngine

logger = logging.getLogger(__name__)

class ExceptionService:
    @staticmethod
    def get_all_exceptions():
        """Returns list of all exceptions with linked order and product details."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, e.order_id, e.product_id, e.exception_type, e.severity, 
                   e.description, e.status, e.resolution, e.created_at, e.resolved_at,
                   p.sku AS product_sku, p.name AS product_name,
                   o.order_number
            FROM exceptions e
            LEFT JOIN products p ON e.product_id = p.id
            LEFT JOIN orders o ON e.order_id = o.id
            ORDER BY e.created_at DESC;
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_exception_by_id(exception_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT e.id, e.order_id, e.product_id, e.exception_type, e.severity, 
                   e.description, e.status, e.resolution, e.created_at, e.resolved_at,
                   p.sku AS product_sku, p.name AS product_name,
                   o.order_number
            FROM exceptions e
            LEFT JOIN products p ON e.product_id = p.id
            LEFT JOIN orders o ON e.order_id = o.id
            WHERE e.id = ?;
        """, (exception_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def resolve_exception(exception_id, resolution_action=None, details=None):
        """
        Executes automated Decision -> Resolution Engine for an Exception.
        
        Resolution Strategies:
        - MISSING_ITEM: Search alternative warehouse location for replacement stock and reallocate.
        - DAMAGED_GOODS: Allocate replacement stock from alternative location.
        - INSUFFICIENT_STOCK: Trigger reorder recommendation and proceed with partial fulfillment.
        - QUALITY_CONTROL_FAILURE: Reset order status to PACKING for repack/reinspection.
        """
        exc = ExceptionService.get_exception_by_id(exception_id)
        if not exc:
            raise ValueError(f"Exception '{exception_id}' not found.")

        if exc['status'] == 'RESOLVED':
            return exc

        exc_type = exc['exception_type']
        order_id = exc['order_id']
        product_id = exc['product_id']
        now = get_current_timestamp()

        resolution_note = ""
        action_taken = ""

        with db_transaction() as conn:
            cursor = conn.cursor()

            if exc_type in ['MISSING_ITEM', 'DAMAGED_GOODS']:
                # Search alternative warehouse location with available stock
                cursor.execute("""
                    SELECT i.id, i.location_id, (i.quantity - i.reserved_quantity - i.damaged_quantity) AS avail,
                           l.zone, l.aisle, l.bin
                    FROM inventory i
                    JOIN warehouse_locations l ON i.location_id = l.id
                    WHERE i.product_id = ? AND (i.quantity - i.reserved_quantity - i.damaged_quantity) > 0
                    ORDER BY avail DESC;
                """, (product_id,))
                alt_loc = cursor.fetchone()

                if alt_loc:
                    # Allocate 1 unit from alternative location
                    alloc_id = generate_id("ALLOC")
                    cursor.execute("""
                        INSERT INTO inventory_allocations (id, order_id, product_id, location_id, quantity, allocation_status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?);
                    """, (alloc_id, order_id, product_id, alt_loc['location_id'], 1, "ALLOCATED", now))

                    cursor.execute("""
                        UPDATE inventory
                        SET reserved_quantity = reserved_quantity + 1, last_updated = ?
                        WHERE id = ?;
                    """, (now, alt_loc['id']))

                    action_taken = "REALLOCATED_ALTERNATIVE_LOCATION"
                    resolution_note = f"Allocated replacement unit from location {alt_loc['zone']}-{alt_loc['aisle']}-{alt_loc['bin']} (Inventory ID: {alt_loc['id']})."
                else:
                    action_taken = "REORDER_TRIGGERED"
                    resolution_note = f"No alternative stock available for product '{product_id}'. Triggered emergency vendor reorder request."

            elif exc_type == 'INSUFFICIENT_STOCK':
                action_taken = "PARTIAL_FULFILLMENT_ACCEPTED"
                resolution_note = "Accepted partial stock allocation. Outstanding shortage queued for vendor reorder."

            elif exc_type == 'QUALITY_CONTROL_FAILURE':
                action_taken = "RESET_FOR_REPACK"
                resolution_note = "Reset order status to PACKING for repackaging and reinspection."
                if order_id:
                    cursor.execute("UPDATE orders SET status = 'PACKING' WHERE id = ?;", (order_id,))

            else:
                action_taken = "MANUAL_RESOLUTION"
                resolution_note = details or resolution_action or "Exception reviewed and manually resolved by operations supervisor."

            full_resolution = f"[{action_taken}] {resolution_note}"

            # Update exception status
            cursor.execute("""
                UPDATE exceptions
                SET status = 'RESOLVED', resolution = ?, resolved_at = ?
                WHERE id = ?;
            """, (full_resolution, now, exception_id))

            # Audit Log
            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "EXCEPTION_RESOLVED", "EXCEPTION", exception_id, f"Resolved exception {exception_id}: {full_resolution}", now))

        return ExceptionService.get_exception_by_id(exception_id)
