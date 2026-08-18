import logging
from database.db import db_transaction, get_db_connection
from utils.helpers import generate_id, get_current_timestamp
from services.order_service import OrderService
from ai.priority_engine import PriorityEngine
from ai.allocation_engine import AllocationEngine
from ai.reorder_engine import ReorderEngine

logger = logging.getLogger(__name__)

class AllocationService:
    @staticmethod
    def allocate_order(order_id):
        """
        Executes smart order inventory allocation, reserves stock, creates allocation records,
        flags shortages, creates exceptions, logs audit trails, and returns structured decision response.
        """
        order = OrderService.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order '{order_id}' not found.")

        if order['status'] in ['COMPLETED', 'CANCELLED', 'DISPATCHED']:
            raise ValueError(f"Cannot allocate order in '{order['status']}' state.")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build inventory_by_product map for requested items
        inventory_by_product = {}
        for item in order['items']:
            prod_id = item['product_id']
            cursor.execute("""
                SELECT 
                    i.id,
                    i.location_id,
                    i.quantity,
                    i.reserved_quantity,
                    i.damaged_quantity,
                    (i.quantity - i.reserved_quantity - i.damaged_quantity) AS available_quantity,
                    l.zone AS location_zone,
                    l.aisle AS location_aisle,
                    l.bin AS location_bin
                FROM inventory i
                JOIN warehouse_locations l ON i.location_id = l.id
                WHERE i.product_id = ? AND (i.quantity - i.reserved_quantity - i.damaged_quantity) > 0
                ORDER BY l.zone ASC, l.aisle ASC;
            """, (prod_id,))
            rows = cursor.fetchall()
            inventory_by_product[prod_id] = [dict(r) for r in rows]

        conn.close()

        # Evaluate Allocation via AI Engine
        eval_result = AllocationEngine.evaluate_allocation(
            order_id=order['id'],
            order_items=order['items'],
            inventory_by_product=inventory_by_product
        )

        decision = eval_result['decision']
        allocations_to_make = eval_result['allocations']
        shortages = eval_result['shortages']
        exceptions_to_create = eval_result['exceptions_to_create']
        reasoning = eval_result['reasoning']

        created_allocations = []
        created_exceptions = []
        recommendations = []
        now = get_current_timestamp()

        with db_transaction() as conn:
            cursor = conn.cursor()

            # 1. Execute Allocations & Reserve Inventory
            for alloc in allocations_to_make:
                alloc_id = generate_id("ALLOC")
                cursor.execute("""
                    INSERT INTO inventory_allocations (id, order_id, product_id, location_id, quantity, allocation_status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (alloc_id, order['id'], alloc['product_id'], alloc['location_id'], alloc['quantity'], "ALLOCATED", now))

                # Update Inventory Reserved Quantity
                cursor.execute("""
                    UPDATE inventory
                    SET reserved_quantity = reserved_quantity + ?, last_updated = ?
                    WHERE id = ?;
                """, (alloc['quantity'], now, alloc['inventory_id']))

                # Update Order Item Allocated Quantity
                cursor.execute("""
                    UPDATE order_items
                    SET allocated_quantity = allocated_quantity + ?
                    WHERE order_id = ? AND product_id = ?;
                """, (alloc['quantity'], order['id'], alloc['product_id']))

                created_allocations.append({
                    "id": alloc_id,
                    "product_id": alloc['product_id'],
                    "location_id": alloc['location_id'],
                    "quantity": alloc['quantity'],
                    "status": "ALLOCATED"
                })

            # 2. Update Order Status
            if decision == "FULL_ALLOCATION":
                new_status = "ALLOCATED"
            elif decision == "PARTIAL_ALLOCATION":
                new_status = "PARTIALLY_ALLOCATED"
            else:
                new_status = "PENDING"

            cursor.execute("UPDATE orders SET status = ? WHERE id = ?;", (new_status, order['id']))

            # 3. Create Exceptions for Shortages
            for exc in exceptions_to_create:
                exc_id = generate_id("EXC")
                cursor.execute("""
                    INSERT INTO exceptions (id, order_id, product_id, exception_type, severity, description, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (exc_id, exc['order_id'], exc['product_id'], exc['exception_type'], exc['severity'], exc['description'], "OPEN", now))

                created_exceptions.append({
                    "id": exc_id,
                    "product_id": exc['product_id'],
                    "exception_type": exc['exception_type'],
                    "severity": exc['severity'],
                    "description": exc['description']
                })

            # 4. Generate Reorder Recommendations for Shortage Products
            shortage_prod_ids = [s['product_id'] for s in shortages]
            if shortage_prod_ids:
                placeholders = ','.join(['?'] * len(shortage_prod_ids))
                cursor.execute(f"""
                    SELECT p.id AS product_id, p.sku, p.name, p.reorder_level, p.safety_stock,
                           COALESCE(SUM(i.quantity - i.reserved_quantity - i.damaged_quantity), 0) AS total_available
                    FROM products p
                    LEFT JOIN inventory i ON p.id = i.product_id
                    WHERE p.id IN ({placeholders})
                    GROUP BY p.id, p.sku, p.name, p.reorder_level, p.safety_stock;
                """, shortage_prod_ids)
                s_rows = cursor.fetchall()
                s_list = [dict(r) for r in s_rows]
                recommendations = ReorderEngine.evaluate_reorder_needs(s_list)

            # 5. Audit Log
            audit_id = generate_id("AUD")
            audit_desc = f"Allocation Engine executed decision '{decision}' for Order {order['order_number']}. Allocated {len(created_allocations)} location slots."
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "ORDER_ALLOCATED", "ORDER", order['id'], audit_desc, now))

        return {
            "decision": decision,
            "order_id": order['id'],
            "allocations": created_allocations,
            "shortages": shortages,
            "exceptions": created_exceptions,
            "recommendations": recommendations,
            "reasoning": reasoning
        }

    @staticmethod
    def get_allocation_decision_explanation(order_id):
        """
        GET /api/orders/:id/decision
        Provides comprehensive explanation of priority evaluation, allocation decisions,
        shortage details, and recommended warehouse actions.
        """
        order = OrderService.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order '{order_id}' not found.")

        priority_eval = PriorityEngine.calculate_priority(order)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query existing allocations
        cursor.execute("""
            SELECT a.id, a.product_id, p.name AS product_name, p.sku AS product_sku,
                   a.location_id, l.zone, l.aisle, l.bin, a.quantity, a.allocation_status, a.created_at
            FROM inventory_allocations a
            JOIN products p ON a.product_id = p.id
            JOIN warehouse_locations l ON a.location_id = l.id
            WHERE a.order_id = ?;
        """, (order['id'],))
        alloc_rows = cursor.fetchall()

        # Query exceptions linked to order
        cursor.execute("""
            SELECT id, product_id, exception_type, severity, description, status, created_at
            FROM exceptions
            WHERE order_id = ?;
        """, (order['id'],))
        exc_rows = cursor.fetchall()

        conn.close()

        allocations = [dict(r) for r in alloc_rows]
        exceptions = [dict(r) for r in exc_rows]

        # Calculate shortages
        shortages = []
        for item in order['items']:
            req = item['requested_quantity']
            alloc = item['allocated_quantity']
            if alloc < req:
                shortages.append({
                    "product_id": item['product_id'],
                    "product_sku": item['product_sku'],
                    "product_name": item['product_name'],
                    "requested": req,
                    "allocated": alloc,
                    "shortage": req - alloc
                })

        # Determine Recommended Warehouse Action
        if order['status'] == 'ALLOCATED':
            zones = sorted(list(set([f"Zone {a['zone']}" for a in allocations])))
            zones_str = ", ".join(zones) if zones else "Primary Picking Zone"
            warehouse_action = f"Proceed to Picking: Order fully allocated. Assigned pick path: {zones_str}."
        elif order['status'] == 'PARTIALLY_ALLOCATED':
            allocated_sum = sum([a['quantity'] for a in allocations])
            warehouse_action = f"Partial Pick & Triage: Pick available {allocated_sum} units. Trigger reorder for {len(shortages)} shortage line items."
        elif order['status'] == 'PENDING':
            warehouse_action = "Awaiting Stock Arrival: Order pending inventory replenishment or allocation retry."
        else:
            warehouse_action = f"Order status is {order['status']}. Standard fulfillment pipeline."

        return {
            "order_id": order['id'],
            "order_number": order['order_number'],
            "status": order['status'],
            "priority_evaluation": priority_eval,
            "allocations_summary": allocations,
            "shortages_summary": shortages,
            "exceptions_summary": exceptions,
            "recommended_warehouse_action": warehouse_action
        }
