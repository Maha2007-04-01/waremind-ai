import logging
from database.db import db_transaction, get_db_connection
from utils.helpers import generate_id, get_current_timestamp
from services.order_service import OrderService

logger = logging.getLogger(__name__)

class QualityCheckService:
    @staticmethod
    def perform_quality_check(order_id, result="PASS", notes="", inspector=None):
        """
        Performs Quality Control (QC) inspection for an order.
        Rule: Quality check cannot start before packing is complete (Order status must be PACKED).
        """
        order = OrderService.get_order_by_id(order_id)
        if not order:
            raise ValueError(f"Order '{order_id}' not found.")

        if order['status'] not in ['PACKED', 'QC_FAILED']:
            raise ValueError(f"Quality check cannot start for Order '{order_id}'. Current status is '{order['status']}'. Packing must be completed first.")

        result_upper = result.upper()
        if result_upper not in ['PASS', 'FAIL']:
            raise ValueError("QC result must be 'PASS' or 'FAIL'.")

        now = get_current_timestamp()

        with db_transaction() as conn:
            cursor = conn.cursor()

            if result_upper == 'PASS':
                new_status = 'QC_PASSED'
                cursor.execute("UPDATE orders SET status = ? WHERE id = ?;", (new_status, order['id']))

                audit_id = generate_id("AUD")
                desc = f"QC Passed for Order {order['order_number']} by inspector '{inspector or 'System'}'. Notes: {notes}"
                cursor.execute("""
                    INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (audit_id, "QC_PASSED", "ORDER", order['id'], desc, now))

                exception_id = None
            else:
                new_status = 'QC_FAILED'
                cursor.execute("UPDATE orders SET status = ? WHERE id = ?;", (new_status, order['id']))

                exception_id = generate_id("EXC")
                exc_desc = f"QC Failed for Order {order['order_number']}. Notes: {notes}"
                cursor.execute("""
                    INSERT INTO exceptions (id, order_id, product_id, exception_type, severity, description, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, (exception_id, order['id'], None, "QUALITY_CONTROL_FAILURE", "HIGH", exc_desc, "OPEN", now))

                audit_id = generate_id("AUD")
                cursor.execute("""
                    INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, (audit_id, "QC_FAILED", "ORDER", order['id'], exc_desc, now))

        return {
            "order_id": order['id'],
            "qc_result": result_upper,
            "status": new_status,
            "exception_id": exception_id,
            "notes": notes,
            "inspector": inspector
        }
