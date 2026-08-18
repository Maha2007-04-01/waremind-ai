import logging
from database.db import db_transaction, get_db_connection
from utils.helpers import generate_id, get_current_timestamp
from ai.priority_engine import PriorityEngine

logger = logging.getLogger(__name__)

def _format_order_row(order_row, item_rows=None):
    if not order_row:
        return None

    order_dict = {
        "id": order_row["id"],
        "order_number": order_row["order_number"],
        "customer_name": order_row["customer_name"],
        "priority": order_row["priority"],
        "status": order_row["status"],
        "required_by": order_row["required_by"],
        "created_at": order_row["created_at"],
        "total_value": order_row["total_value"],
        "items": []
    }

    if item_rows:
        order_dict["items"] = [
            {
                "id": r["id"],
                "order_id": r["order_id"],
                "product_id": r["product_id"],
                "product_sku": r["product_sku"] if "product_sku" in r.keys() else r["product_id"],
                "product_name": r["product_name"] if "product_name" in r.keys() else "",
                "requested_quantity": r["requested_quantity"],
                "allocated_quantity": r["allocated_quantity"],
                "picked_quantity": r["picked_quantity"],
                "packed_quantity": r["packed_quantity"]
            }
            for r in item_rows
        ]

    # Calculate live transparent priority scoring
    priority_eval = PriorityEngine.calculate_priority(order_dict)
    order_dict["priority_evaluation"] = priority_eval

    return order_dict

class OrderService:
    @staticmethod
    def get_all_orders():
        """Returns all orders with line items and priority evaluations."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, order_number, customer_name, priority, status, required_by, created_at, total_value
            FROM orders
            ORDER BY created_at DESC;
        """)
        order_rows = cursor.fetchall()

        orders_list = []
        for o_row in order_rows:
            cursor.execute("""
                SELECT oi.id, oi.order_id, oi.product_id, oi.requested_quantity, 
                       oi.allocated_quantity, oi.picked_quantity, oi.packed_quantity,
                       p.sku AS product_sku, p.name AS product_name
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?;
            """, (o_row["id"],))
            i_rows = cursor.fetchall()
            orders_list.append(_format_order_row(o_row, i_rows))

        conn.close()
        return orders_list

    @staticmethod
    def get_order_by_id(order_id):
        """Returns single order by ID with line items and priority evaluation."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, order_number, customer_name, priority, status, required_by, created_at, total_value
            FROM orders
            WHERE id = ? OR order_number = ?;
        """, (order_id, order_id))
        o_row = cursor.fetchone()

        if not o_row:
            conn.close()
            return None

        cursor.execute("""
            SELECT oi.id, oi.order_id, oi.product_id, oi.requested_quantity, 
                   oi.allocated_quantity, oi.picked_quantity, oi.packed_quantity,
                   p.sku AS product_sku, p.name AS product_name
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?;
        """, (o_row["id"],))
        i_rows = cursor.fetchall()
        conn.close()

        return _format_order_row(o_row, i_rows)

    @staticmethod
    def create_order(order_data):
        """
        Creates a new order with order_items and returns the created order.
        """
        customer_name = order_data.get('customer_name')
        if not customer_name:
            raise ValueError("customer_name is required")

        items_data = order_data.get('items', [])
        if not items_data:
            raise ValueError("Order must contain at least one line item in 'items'.")

        order_id = generate_id("ORD")
        order_number = order_data.get('order_number') or f"ORD-2026-{order_id[-4:]}"
        priority = (order_data.get('priority') or 'NORMAL').upper()
        required_by = order_data.get('required_by')
        now = get_current_timestamp()

        total_value = 0.0

        with db_transaction() as conn:
            cursor = conn.cursor()
            
            # Calculate total value and prepare items
            item_records = []
            for item in items_data:
                prod_id = item.get('product_id')
                req_qty = item.get('requested_quantity', 1)
                
                if req_qty <= 0:
                    raise ValueError(f"Requested quantity for product {prod_id} must be > 0.")
                
                cursor.execute("SELECT unit_price FROM products WHERE id = ?;", (prod_id,))
                prod_row = cursor.fetchone()
                if not prod_row:
                    raise ValueError(f"Product '{prod_id}' not found.")
                
                unit_price = prod_row["unit_price"]
                total_value += (unit_price * req_qty)
                item_id = generate_id("ITEM")
                item_records.append((item_id, order_id, prod_id, req_qty, 0, 0, 0))

            # Insert order
            cursor.execute("""
                INSERT INTO orders (id, order_number, customer_name, priority, status, required_by, created_at, total_value)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (order_id, order_number, customer_name, priority, "PENDING", required_by, now, total_value))

            # Insert items
            cursor.executemany("""
                INSERT INTO order_items (id, order_id, product_id, requested_quantity, allocated_quantity, picked_quantity, packed_quantity)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, item_records)

            # Audit Log
            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "ORDER_CREATED", "ORDER", order_id, f"Order {order_number} created for {customer_name}.", now))

        return OrderService.get_order_by_id(order_id)

    @staticmethod
    def update_order_status(order_id, new_status):
        """Updates status of an order."""
        valid_statuses = ['PENDING', 'PARTIALLY_ALLOCATED', 'ALLOCATED', 'PICKING', 'PACKING', 'DISPATCHED', 'COMPLETED', 'CANCELLED']
        status_upper = new_status.upper()
        if status_upper not in valid_statuses:
            raise ValueError(f"Invalid status '{new_status}'. Allowed: {valid_statuses}")

        order = OrderService.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order '{order_id}' not found.")

        now = get_current_timestamp()

        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE orders
                SET status = ?
                WHERE id = ?;
            """, (status_upper, order['id']))

            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "ORDER_STATUS_UPDATED", "ORDER", order['id'], f"Order status changed from {order['status']} to {status_upper}.", now))

        return OrderService.get_order_by_id(order['id'])
