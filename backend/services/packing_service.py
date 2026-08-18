import logging
from database.db import db_transaction, get_db_connection
from utils.helpers import generate_id, get_current_timestamp
from services.order_service import OrderService

logger = logging.getLogger(__name__)

class PackingService:
    @staticmethod
    def create_packing_task(order_id, assigned_to=None):
        """
        Creates a packing task for an order.
        Rule: Packing cannot start before picking is complete (Order status must be PICKED).
        """
        order = OrderService.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order '{order_id}' not found.")

        if order['status'] != 'PICKED':
            raise ValueError(f"Packing cannot start for Order '{order_id}'. Current status is '{order['status']}'. Picking must be completed first.")

        task_id = generate_id("TASK")
        now = get_current_timestamp()

        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO warehouse_tasks (id, order_id, task_type, assigned_to, status, priority, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (task_id, order['id'], "PACKING", assigned_to, "PENDING", order['priority'], now))

            cursor.execute("UPDATE orders SET status = 'PACKING' WHERE id = ?;", (order['id'],))

            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "PACKING_TASK_CREATED", "ORDER", order['id'], f"Packing task {task_id} created for order {order['order_number']}.", now))

        return PackingService.get_packing_task_by_id(task_id)

    @staticmethod
    def get_packing_task_by_id(task_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM warehouse_tasks WHERE id = ? AND task_type = 'PACKING';", (task_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def start_packing(task_id):
        task = PackingService.get_packing_task_by_id(task_id)
        if not task:
            raise ValueError(f"Packing task '{task_id}' not found.")

        if task['status'] != 'PENDING':
            raise ValueError(f"Cannot start packing task in '{task['status']}' status.")

        now = get_current_timestamp()
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE warehouse_tasks SET status = 'IN_PROGRESS', started_at = ? WHERE id = ?;", (now, task_id))

            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "PACKING_STARTED", "TASK", task_id, f"Started packing task {task_id}.", now))

        return PackingService.get_packing_task_by_id(task_id)

    @staticmethod
    def complete_packing(task_id):
        """
        Completes packing task.
        Rule: Validates picked quantities match packed quantities. Updates order items packed_quantity and sets order status to PACKED.
        """
        task = PackingService.get_packing_task_by_id(task_id)
        if not task:
            raise ValueError(f"Packing task '{task_id}' not found.")

        if task['status'] != 'IN_PROGRESS':
            raise ValueError(f"Cannot complete packing task in '{task['status']}' status. Task must be IN_PROGRESS.")

        order = OrderService.get_order_by_id(task['order_id'])
        now = get_current_timestamp()

        with db_transaction() as conn:
            cursor = conn.cursor()

            # Validate and update packed_quantity to match picked_quantity
            cursor.execute("""
                UPDATE order_items
                SET packed_quantity = picked_quantity
                WHERE order_id = ?;
            """, (order['id'],))

            cursor.execute("UPDATE warehouse_tasks SET status = 'COMPLETED', completed_at = ? WHERE id = ?;", (now, task_id))
            cursor.execute("UPDATE orders SET status = 'PACKED' WHERE id = ?;", (order['id'],))

            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "PACKING_COMPLETED", "ORDER", order['id'], f"Completed packing task {task_id} for order {order['order_number']}.", now))

        return OrderService.get_order_by_id(order['id'])
