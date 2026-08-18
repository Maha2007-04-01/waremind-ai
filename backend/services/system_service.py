import logging
from database.db import db_transaction, check_db_connection

logger = logging.getLogger(__name__)

class SystemService:
    @staticmethod
    def get_system_status():
        """
        Fetches system status including application status, database connectivity,
        and entity counts using parameterized SQLite queries across all core tables.
        """
        db_ok, db_status_msg = check_db_connection()
        
        counts = {
            "products": 0,
            "warehouse_locations": 0,
            "inventory_records": 0,
            "orders": 0,
            "order_items": 0,
            "inventory_allocations": 0,
            "active_warehouse_tasks": 0,
            "exceptions": 0,
            "dispatches": 0,
            "audit_logs": 0
        }
        
        if db_ok:
            try:
                with db_transaction() as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("SELECT COUNT(*) FROM products;")
                    counts["products"] = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM warehouse_locations;")
                    counts["warehouse_locations"] = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM inventory;")
                    counts["inventory_records"] = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM orders;")
                    counts["orders"] = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM order_items;")
                    counts["order_items"] = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM inventory_allocations;")
                    counts["inventory_allocations"] = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM warehouse_tasks WHERE status != ?;", ("COMPLETED",))
                    counts["active_warehouse_tasks"] = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM exceptions WHERE status != ?;", ("RESOLVED",))
                    counts["exceptions"] = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM dispatches;")
                    counts["dispatches"] = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM audit_logs;")
                    counts["audit_logs"] = cursor.fetchone()[0]

            except Exception as e:
                logger.error(f"Error fetching system entity counts: {str(e)}")
                db_ok = False
                db_status_msg = f"query_error: {str(e)}"

        return {
            "application_status": "ok",
            "database_status": "connected" if db_ok else db_status_msg,
            "counts": counts
        }

    @staticmethod
    def reset_demo_data():
        """Resets and re-seeds the database with clean seed data."""
        from database.seed import seed_database
        seed_database()
        return SystemService.get_system_status()

