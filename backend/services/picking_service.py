import logging
from database.db import db_transaction, get_db_connection
from utils.helpers import generate_id, get_current_timestamp
from services.order_service import OrderService

logger = logging.getLogger(__name__)

class PickingService:
    @staticmethod
    def create_picking_task(order_id, assigned_to=None):
        """
        Creates a picking task for an order.
        Rule: Order cannot enter picking until allocation exists (status must be ALLOCATED or PARTIALLY_ALLOCATED).
        """
        order = OrderService.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order '{order_id}' not found.")

        if order['status'] not in ['ALLOCATED', 'PARTIALLY_ALLOCATED']:
            raise ValueError(f"Order '{order_id}' cannot enter picking phase. Current status is '{order['status']}'. Allocation required first.")

        task_id = generate_id("TASK")
        now = get_current_timestamp()

        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO warehouse_tasks (id, order_id, task_type, assigned_to, status, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (task_id, order['id'], "PICKING", assigned_to, "PENDING", order['priority'], now))

            cursor.execute("UPDATE orders SET status = 'PICKING' WHERE id = ?;", (order['id'],))

            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "PICKING_TASK_CREATED", "ORDER", order['id'], f"Picking task {task_id} created for order {order['order_number']}.", now))

        return PickingService.get_picking_task_by_id(task_id)

    @staticmethod
    def get_picking_task_by_id(task_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM warehouse_tasks WHERE id = ? AND task_type = 'PICKING';", (task_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def assign_picker(task_id, worker_name):
        task = PickingService.get_picking_task_by_id(task_id)
        if not task:
            raise ValueError(f"Picking task '{task_id}' not found.")

        now = get_current_timestamp()
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE warehouse_tasks SET assigned_to = ? WHERE id = ?;", (worker_name, task_id))

            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "PICKER_ASSIGNED", "TASK", task_id, f"Assigned task {task_id} to picker '{worker_name}'.", now))

        return PickingService.get_picking_task_by_id(task_id)

    @staticmethod
    def start_picking(task_id):
        task = PickingService.get_picking_task_by_id(task_id)
        if not task:
            raise ValueError(f"Picking task '{task_id}' not found.")

        if task['status'] != 'PENDING':
            raise ValueError(f"Cannot start picking task in status '{task['status']}'.")

        now = get_current_timestamp()
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE warehouse_tasks SET status = 'IN_PROGRESS', started_at = ? WHERE id = ?;", (now, task_id))

            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "PICKING_STARTED", "TASK", task_id, f"Started picking task {task_id}.", now))

        return PickingService.get_picking_task_by_id(task_id)

    @staticmethod
    def complete_picking(task_id):
        """
        Completes picking task.
        Rule: Validates picked quantities. Updates order items picked_quantity and changes order status to PICKED.
        """
        task = PickingService.get_picking_task_by_id(task_id)
        if not task:
            raise ValueError(f"Picking task '{task_id}' not found.")

        if task['status'] != 'IN_PROGRESS':
            raise ValueError(f"Cannot complete picking task in '{task['status']}' status. Task must be IN_PROGRESS.")

        order = OrderService.get_order_by_id(task['order_id'])
        now = get_current_timestamp()

        with db_transaction() as conn:
            cursor = conn.cursor()

            # Update picked_quantity on order items to match allocated_quantity
            cursor.execute("""
                UPDATE order_items
                SET picked_quantity = allocated_quantity
                WHERE order_id = ?;
            """, (order['id'],))

            # Mark task completed
            cursor.execute("UPDATE warehouse_tasks SET status = 'COMPLETED', completed_at = ? WHERE id = ?;", (now, task_id))

            # Mark order status PICKED
            cursor.execute("UPDATE orders SET status = 'PICKED' WHERE id = ?;", (order['id'],))

            # Audit log
            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "PICKING_COMPLETED", "ORDER", order['id'], f"Completed picking task {task_id} for order {order['order_number']}.", now))

        return OrderService.get_order_by_id(order['id'])

    @staticmethod
    def report_missing_item(task_id, product_id, missing_quantity=1, reason="Item not found on bin location"):
        """Reports missing item during picking. Raises a MISSING_ITEM exception."""
        task = PickingService.get_picking_task_by_id(task_id)
        if not task:
            raise ValueError(f"Picking task '{task_id}' not found.")

        now = get_current_timestamp()
        exception_id = generate_id("EXC")

        with db_transaction() as conn:
            cursor = conn.cursor()
            exc_desc = f"Missing {missing_quantity} units of product '{product_id}' reported during picking task {task_id}. Reason: {reason}"
            cursor.execute("""
                INSERT INTO exceptions (id, order_id, product_id, exception_type, severity, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (exception_id, task['order_id'], product_id, "MISSING_ITEM", "HIGH", exc_desc, "OPEN", now))

            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "MISSING_ITEM_REPORTED", "TASK", task_id, exc_desc, now))

        return {
            "task_id": task_id,
            "exception_id": exception_id,
            "status": "MISSING_ITEM_REPORTED",
            "message": "Missing item exception created. Automated relocation search initiated."
        }

    @staticmethod
    def report_damaged_item(task_id, product_id, damaged_quantity=1, location_id=None, reason="Item damaged on shelf"):
        """Reports damaged item during picking. Increases damaged_quantity and logs exception."""
        task = PickingService.get_picking_task_by_id(task_id)
        if not task:
            raise ValueError(f"Picking task '{task_id}' not found.")

        now = get_current_timestamp()
        exception_id = generate_id("EXC")

        with db_transaction() as conn:
            cursor = conn.cursor()

            if location_id:
                cursor.execute("""
                    UPDATE inventory
                    SET damaged_quantity = damaged_quantity + ?, last_updated = ?
                    WHERE product_id = ? AND location_id = ?;
                """, (damaged_quantity, now, product_id, location_id))

            exc_desc = f"Damaged {damaged_quantity} units of product '{product_id}' reported during picking task {task_id}. Reason: {reason}"
            cursor.execute("""
                INSERT INTO exceptions (id, order_id, product_id, exception_type, severity, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (exception_id, task['order_id'], product_id, "DAMAGED_GOODS", "HIGH", exc_desc, "OPEN", now))

            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "DAMAGED_ITEM_REPORTED", "TASK", task_id, exc_desc, now))

        return {
            "task_id": task_id,
            "exception_id": exception_id,
            "status": "DAMAGED_ITEM_REPORTED",
            "message": "Damaged item exception logged. Replacement allocation initiated."
        }
