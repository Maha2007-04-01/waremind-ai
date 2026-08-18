"""
Product Traceability Service
Reconstructs complete operational journey for products and orders
using existing audit_logs, warehouse_tasks, inventory_allocations,
dispatches, and order data — no new tables required.
"""
import logging
from database.db import get_db_connection

logger = logging.getLogger(__name__)

TIMELINE_EVENT_ICONS = {
    "RECEIVED": "📦",
    "STORED": "🏭",
    "ALLOCATED": "🛒",
    "PICKED": "👷",
    "PACKED": "📦",
    "QC_PASSED": "✅",
    "QC_FAILED": "❌",
    "DISPATCHED": "🚚",
    "DELIVERED": "✔️",
    "EXCEPTION": "⚠️",
    "ADJUSTMENT": "🔧",
    "DAMAGE_REPORTED": "🔴",
    "REORDER": "🔄",
    "GENERAL": "📋",
}


class TraceabilityService:

    @staticmethod
    def _get_product_info(conn, product_id):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.sku, p.name, p.category, p.unit_price, p.reorder_level, p.safety_stock,
                   COALESCE(SUM(i.quantity), 0) AS total_quantity,
                   COALESCE(SUM(i.reserved_quantity), 0) AS total_reserved,
                   COALESCE(SUM(i.damaged_quantity), 0) AS total_damaged,
                   COALESCE(SUM(i.quantity - i.reserved_quantity - i.damaged_quantity), 0) AS total_available
            FROM products p
            LEFT JOIN inventory i ON i.product_id = p.id
            WHERE p.id = ?
            GROUP BY p.id;
        """, (product_id,))
        return cursor.fetchone()

    @staticmethod
    def _get_inventory_locations(conn, product_id):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT i.id, i.quantity, i.reserved_quantity, i.damaged_quantity,
                   l.zone, l.aisle, l.rack, l.bin, l.status,
                   i.last_updated
            FROM inventory i
            JOIN warehouse_locations l ON i.location_id = l.id
            WHERE i.product_id = ?
            ORDER BY l.zone, l.aisle;
        """, (product_id,))
        return cursor.fetchall()

    @staticmethod
    def _get_product_audit_events(conn, product_id):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, action, entity_type, entity_id, description, created_at
            FROM audit_logs
            WHERE entity_id = ? OR description LIKE ?
            ORDER BY created_at ASC;
        """, (product_id, f"%{product_id}%"))
        return cursor.fetchall()

    @staticmethod
    def _get_product_allocations(conn, product_id):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ia.id, ia.order_id, ia.quantity_allocated, ia.status, ia.created_at,
                   o.order_number, o.priority, o.status AS order_status,
                   o.customer_name
            FROM inventory_allocations ia
            JOIN orders o ON ia.order_id = o.id
            WHERE ia.product_id = ?
            ORDER BY ia.created_at ASC;
        """, (product_id,))
        return cursor.fetchall()

    @staticmethod
    def _get_product_tasks(conn, product_id):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT wt.id, wt.task_type, wt.status, wt.assigned_to, wt.order_id,
                   wt.started_at, wt.completed_at, wt.notes,
                   o.order_number
            FROM warehouse_tasks wt
            JOIN orders o ON wt.order_id = o.id
            JOIN order_items oi ON oi.order_id = o.id
            WHERE oi.product_id = ?
            GROUP BY wt.id
            ORDER BY COALESCE(wt.started_at, wt.completed_at) ASC;
        """, (product_id,))
        return cursor.fetchall()

    @staticmethod
    def _get_product_dispatches(conn, product_id):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.id, d.order_id, d.carrier, d.tracking_number, d.status, d.dispatched_at,
                   o.order_number
            FROM dispatches d
            JOIN orders o ON d.order_id = o.id
            JOIN order_items oi ON oi.order_id = o.id
            WHERE oi.product_id = ?
            GROUP BY d.id
            ORDER BY d.dispatched_at ASC;
        """, (product_id,))
        return cursor.fetchall()

    @classmethod
    def _build_product_timeline(cls, conn, product_id, audit_events, allocations, tasks, dispatches, locations):
        events = []

        # Storage events from inventory locations
        for loc in locations:
            events.append({
                "event_type": "STORED",
                "icon": "🏭",
                "timestamp": loc["last_updated"],
                "title": "Stored in Warehouse",
                "description": f"Stored at Zone {loc['zone']} / Aisle {loc['aisle']} / Rack {loc['rack']} / Bin {loc['bin']}",
                "location": f"Zone {loc['zone']}-{loc['aisle']}-{loc['rack']}-{loc['bin']}",
                "quantity": loc["quantity"],
                "status": loc["status"],
                "related_entity": None,
                "worker": None,
                "details": {
                    "quantity": loc["quantity"],
                    "reserved": loc["reserved_quantity"],
                    "damaged": loc["damaged_quantity"],
                    "location_status": loc["status"]
                }
            })

        # Allocation events
        for alloc in allocations:
            events.append({
                "event_type": "ALLOCATED",
                "icon": "🛒",
                "timestamp": alloc["created_at"],
                "title": f"Allocated to {alloc['order_number']}",
                "description": f"Quantity {alloc['quantity_allocated']} allocated to order {alloc['order_number']} for {alloc['customer_name']}",
                "location": None,
                "quantity": alloc["quantity_allocated"],
                "status": alloc["status"],
                "related_entity": {"type": "order", "id": alloc["order_id"], "number": alloc["order_number"]},
                "worker": None,
                "details": {
                    "order_priority": alloc["priority"],
                    "order_status": alloc["order_status"],
                    "allocation_status": alloc["status"]
                }
            })

        # Task events (picking, packing, QC)
        for task in tasks:
            ts = task["completed_at"] or task["started_at"]
            task_type = task["task_type"]
            event_type = task_type if task_type in TIMELINE_EVENT_ICONS else "GENERAL"
            icon = TIMELINE_EVENT_ICONS.get(event_type, "📋")
            title = task_type.replace("_", " ").title()
            events.append({
                "event_type": event_type,
                "icon": icon,
                "timestamp": ts,
                "title": f"{title} — {task['order_number']}",
                "description": task["notes"] or f"{title} task for order {task['order_number']}",
                "location": None,
                "quantity": None,
                "status": task["status"],
                "related_entity": {"type": "order", "id": task["order_id"], "number": task["order_number"]},
                "worker": task["assigned_to"],
                "details": {
                    "started_at": task["started_at"],
                    "completed_at": task["completed_at"],
                    "task_status": task["status"]
                }
            })

        # Dispatch events
        for d in dispatches:
            events.append({
                "event_type": "DISPATCHED",
                "icon": "🚚",
                "timestamp": d["dispatched_at"],
                "title": f"Dispatched — {d['order_number']}",
                "description": f"Dispatched via {d['carrier']}. Tracking: {d['tracking_number']}",
                "location": None,
                "quantity": None,
                "status": d["status"],
                "related_entity": {"type": "order", "id": d["order_id"], "number": d["order_number"]},
                "worker": None,
                "details": {
                    "carrier": d["carrier"],
                    "tracking_number": d["tracking_number"],
                    "dispatch_status": d["status"]
                }
            })

        # Audit log events
        for audit in audit_events:
            action = audit["action"]
            event_type = "GENERAL"
            if "DAMAGE" in action or "damage" in (audit["description"] or ""):
                event_type = "DAMAGE_REPORTED"
            elif "ADJUSTMENT" in action:
                event_type = "ADJUSTMENT"
            elif "REORDER" in action:
                event_type = "REORDER"
            icon = TIMELINE_EVENT_ICONS.get(event_type, "📋")
            events.append({
                "event_type": event_type,
                "icon": icon,
                "timestamp": audit["created_at"],
                "title": action.replace("_", " ").title(),
                "description": audit["description"] or action,
                "location": None,
                "quantity": None,
                "status": None,
                "related_entity": {"type": audit["entity_type"], "id": audit["entity_id"]},
                "worker": None,
                "details": {"audit_id": audit["id"], "action": action}
            })

        # Sort by timestamp
        events.sort(key=lambda e: e["timestamp"] or "")
        return events

    @classmethod
    def trace_product(cls, product_id):
        """Returns full traceability timeline for a product."""
        conn = get_db_connection()
        try:
            product = cls._get_product_info(conn, product_id)
            if not product:
                return None

            locations = cls._get_inventory_locations(conn, product_id)
            audit_events = cls._get_product_audit_events(conn, product_id)
            allocations = cls._get_product_allocations(conn, product_id)
            tasks = cls._get_product_tasks(conn, product_id)
            dispatches = cls._get_product_dispatches(conn, product_id)

            timeline = cls._build_product_timeline(
                conn, product_id, audit_events, allocations, tasks, dispatches, locations
            )

            current_locations = [
                {
                    "zone": loc["zone"],
                    "aisle": loc["aisle"],
                    "rack": loc["rack"],
                    "bin": loc["bin"],
                    "quantity": loc["quantity"],
                    "reserved": loc["reserved_quantity"],
                    "damaged": loc["damaged_quantity"],
                    "status": loc["status"]
                }
                for loc in locations
            ]

            return {
                "product": {
                    "id": product["id"],
                    "sku": product["sku"],
                    "name": product["name"],
                    "category": product["category"],
                    "unit_price": product["unit_price"]
                },
                "current_stock": {
                    "total": product["total_quantity"],
                    "reserved": product["total_reserved"],
                    "damaged": product["total_damaged"],
                    "available": product["total_available"]
                },
                "current_locations": current_locations,
                "timeline": timeline,
                "total_events": len(timeline)
            }
        finally:
            conn.close()

    @classmethod
    def trace_order(cls, order_id):
        """Returns full traceability timeline for an order."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.*, COUNT(oi.id) AS item_count
                FROM orders o
                LEFT JOIN order_items oi ON oi.order_id = o.id
                WHERE o.id = ?
                GROUP BY o.id;
            """, (order_id,))
            order = cursor.fetchone()
            if not order:
                return None

            # Get order items
            cursor.execute("""
                SELECT oi.*, p.sku, p.name AS product_name, p.category
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?;
            """, (order_id,))
            items = cursor.fetchall()

            # Get allocations for this order
            cursor.execute("""
                SELECT ia.*, p.sku, p.name AS product_name
                FROM inventory_allocations ia
                JOIN products p ON ia.product_id = p.id
                WHERE ia.order_id = ?
                ORDER BY ia.created_at ASC;
            """, (order_id,))
            allocations = cursor.fetchall()

            # Get tasks
            cursor.execute("""
                SELECT * FROM warehouse_tasks
                WHERE order_id = ?
                ORDER BY COALESCE(started_at, completed_at) ASC;
            """, (order_id,))
            tasks = cursor.fetchall()

            # Get dispatch
            cursor.execute("SELECT * FROM dispatches WHERE order_id = ?;", (order_id,))
            dispatches = cursor.fetchall()

            # Get audit logs for this order
            cursor.execute("""
                SELECT * FROM audit_logs
                WHERE entity_id = ? OR entity_type = 'ORDER' AND description LIKE ?
                ORDER BY created_at ASC;
            """, (order_id, f"%{order_id}%"))
            audit_events = cursor.fetchall()

            # Get exceptions for this order
            cursor.execute("""
                SELECT * FROM exceptions WHERE order_id = ?
                ORDER BY created_at ASC;
            """, (order_id,))
            exceptions = cursor.fetchall()

            timeline = []

            # Order creation
            timeline.append({
                "event_type": "ORDER_CREATED",
                "icon": "📋",
                "timestamp": order["created_at"],
                "title": f"Order Created — {order['order_number']}",
                "description": f"Order {order['order_number']} created for {order['customer_name']}. Priority: {order['priority']}",
                "quantity": None, "location": None, "worker": None,
                "status": order["status"],
                "details": {"priority": order["priority"], "total_value": order["total_value"], "required_by": order["required_by"]}
            })

            # Allocation events
            for alloc in allocations:
                timeline.append({
                    "event_type": "ALLOCATED",
                    "icon": "🛒",
                    "timestamp": alloc["created_at"],
                    "title": f"Inventory Allocated — {alloc['sku']}",
                    "description": f"{alloc['quantity_allocated']} units of {alloc['product_name']} ({alloc['sku']}) allocated",
                    "quantity": alloc["quantity_allocated"],
                    "location": None, "worker": None,
                    "status": alloc["status"],
                    "details": {"product": alloc["product_name"], "sku": alloc["sku"], "allocation_status": alloc["status"]}
                })

            # Task events
            for task in tasks:
                ts = task["started_at"] or task["completed_at"]
                task_type = task["task_type"]
                icon = TIMELINE_EVENT_ICONS.get(task_type, "📋")
                timeline.append({
                    "event_type": task_type,
                    "icon": icon,
                    "timestamp": ts,
                    "title": task_type.replace("_", " ").title(),
                    "description": task["notes"] or f"{task_type} task",
                    "quantity": None, "location": None,
                    "worker": task["assigned_to"],
                    "status": task["status"],
                    "details": {"started_at": task["started_at"], "completed_at": task["completed_at"]}
                })

            # Exception events
            for exc in exceptions:
                timeline.append({
                    "event_type": "EXCEPTION",
                    "icon": "⚠️",
                    "timestamp": exc["created_at"],
                    "title": f"Exception — {exc['exception_type']}",
                    "description": exc["description"],
                    "quantity": None, "location": None, "worker": None,
                    "status": exc["severity"],
                    "details": {"exception_type": exc["exception_type"], "severity": exc["severity"], "resolution": exc["resolution"]}
                })

            # Dispatch events
            for d in dispatches:
                timeline.append({
                    "event_type": "DISPATCHED",
                    "icon": "🚚",
                    "timestamp": d["dispatched_at"],
                    "title": "Order Dispatched",
                    "description": f"Dispatched via {d['carrier']}. Tracking: {d['tracking_number']}",
                    "quantity": None, "location": None, "worker": None,
                    "status": d["status"],
                    "details": {"carrier": d["carrier"], "tracking_number": d["tracking_number"]}
                })

            timeline.sort(key=lambda e: e["timestamp"] or "")

            return {
                "order": {
                    "id": order["id"],
                    "order_number": order["order_number"],
                    "customer_name": order["customer_name"],
                    "priority": order["priority"],
                    "status": order["status"],
                    "created_at": order["created_at"],
                    "required_by": order["required_by"],
                    "total_value": order["total_value"]
                },
                "items": [
                    {
                        "product_id": item["product_id"],
                        "sku": item["sku"],
                        "product_name": item["product_name"],
                        "requested_quantity": item["requested_quantity"],
                        "allocated_quantity": item["allocated_quantity"],
                        "picked_quantity": item["picked_quantity"],
                        "packed_quantity": item["packed_quantity"]
                    }
                    for item in items
                ],
                "timeline": timeline,
                "total_events": len(timeline)
            }
        finally:
            conn.close()

    @classmethod
    def search_products(cls, query):
        """Search products by name or SKU for traceability lookup."""
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.sku, p.name, p.category,
                       COALESCE(SUM(i.quantity - i.reserved_quantity - i.damaged_quantity), 0) AS available
                FROM products p
                LEFT JOIN inventory i ON i.product_id = p.id
                WHERE LOWER(p.name) LIKE ? OR LOWER(p.sku) LIKE ?
                GROUP BY p.id
                LIMIT 20;
            """, (f"%{query.lower()}%", f"%{query.lower()}%"))
            rows = cursor.fetchall()
            return [{"id": r["id"], "sku": r["sku"], "name": r["name"], "category": r["category"], "available": r["available"]} for r in rows]
        finally:
            conn.close()
