import logging
from database.db import db_transaction, get_db_connection
from utils.helpers import generate_id, get_current_timestamp
from ai.reorder_engine import ReorderEngine

logger = logging.getLogger(__name__)

def _format_inventory_row(row):
    """Formats a SQLite Row into an inventory dictionary with nested product and location details."""
    if not row:
        return None
    
    qty = row["quantity"]
    res = row["reserved_quantity"]
    dmg = row["damaged_quantity"]
    avail = row["available_quantity"] if "available_quantity" in row.keys() and row["available_quantity"] is not None else max(0, qty - res - dmg)

    return {
        "id": row["id"],
        "product_id": row["product_id"],
        "location_id": row["location_id"],
        "quantity": qty,
        "reserved_quantity": res,
        "damaged_quantity": dmg,
        "available_quantity": avail,
        "last_updated": row["last_updated"],
        "product": {
            "id": row["product_id"],
            "sku": row["product_sku"],
            "name": row["product_name"],
            "category": row["product_category"],
            "unit_price": row["product_unit_price"],
            "reorder_level": row["product_reorder_level"],
            "safety_stock": row["product_safety_stock"],
            "weight": row["product_weight"]
        },
        "location": {
            "id": row["location_id"],
            "zone": row["location_zone"],
            "aisle": row["location_aisle"],
            "rack": row["location_rack"],
            "bin": row["location_bin"],
            "status": row["location_status"]
        }
    }

BASE_INVENTORY_QUERY = """
    SELECT 
        i.id,
        i.product_id,
        i.location_id,
        i.quantity,
        i.reserved_quantity,
        i.damaged_quantity,
        (i.quantity - i.reserved_quantity - i.damaged_quantity) AS available_quantity,
        i.last_updated,
        p.sku AS product_sku,
        p.name AS product_name,
        p.category AS product_category,
        p.unit_price AS product_unit_price,
        p.reorder_level AS product_reorder_level,
        p.safety_stock AS product_safety_stock,
        p.weight AS product_weight,
        l.zone AS location_zone,
        l.aisle AS location_aisle,
        l.rack AS location_rack,
        l.bin AS location_bin,
        l.status AS location_status
    FROM inventory i
    JOIN products p ON i.product_id = p.id
    JOIN warehouse_locations l ON i.location_id = l.id
"""

class InventoryService:
    @staticmethod
    def get_all_inventory():
        """Returns all inventory records with product and location details."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"{BASE_INVENTORY_QUERY} ORDER BY p.name ASC, l.zone ASC;")
        rows = cursor.fetchall()
        conn.close()
        return [_format_inventory_row(r) for r in rows]

    @staticmethod
    def get_inventory_by_id(inventory_id):
        """Returns a single inventory record by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"{BASE_INVENTORY_QUERY} WHERE i.id = ?;", (inventory_id,))
        row = cursor.fetchone()
        conn.close()
        return _format_inventory_row(row)

    @staticmethod
    def get_low_stock_inventory():
        """Returns inventory items where available_quantity <= reorder_level."""
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"{BASE_INVENTORY_QUERY} WHERE (i.quantity - i.reserved_quantity - i.damaged_quantity) <= p.reorder_level ORDER BY available_quantity ASC;"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return [_format_inventory_row(r) for r in rows]

    @staticmethod
    def get_out_of_stock_inventory():
        """Returns inventory items where available_quantity <= 0."""
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"{BASE_INVENTORY_QUERY} WHERE (i.quantity - i.reserved_quantity - i.damaged_quantity) <= 0 ORDER BY p.name ASC;"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return [_format_inventory_row(r) for r in rows]

    @staticmethod
    def get_damaged_inventory():
        """Returns inventory items where damaged_quantity > 0."""
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"{BASE_INVENTORY_QUERY} WHERE i.damaged_quantity > 0 ORDER BY i.damaged_quantity DESC;"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return [_format_inventory_row(r) for r in rows]

    @staticmethod
    def search_inventory(query_string):
        """Searches inventory by product name, SKU, category, or location zone/aisle/bin."""
        if not query_string:
            return InventoryService.get_all_inventory()
            
        term = f"%{query_string}%"
        conn = get_db_connection()
        cursor = conn.cursor()
        query = f"""
            {BASE_INVENTORY_QUERY} 
            WHERE p.name LIKE ? 
               OR p.sku LIKE ? 
               OR p.category LIKE ? 
               OR l.zone LIKE ? 
               OR l.aisle LIKE ?
               OR l.bin LIKE ?
            ORDER BY p.name ASC;
        """
        cursor.execute(query, (term, term, term, term, term, term))
        rows = cursor.fetchall()
        conn.close()
        return [_format_inventory_row(r) for r in rows]

    @staticmethod
    def patch_inventory(inventory_id, patch_data):
        """Partially updates allowed fields on an inventory record."""
        current = InventoryService.get_inventory_by_id(inventory_id)
        if not current:
            raise ValueError(f"Inventory item '{inventory_id}' not found.")

        new_quantity = patch_data.get('quantity', current['quantity'])
        new_reserved = patch_data.get('reserved_quantity', current['reserved_quantity'])
        new_damaged = patch_data.get('damaged_quantity', current['damaged_quantity'])
        new_location = patch_data.get('location_id', current['location_id'])

        if new_quantity < 0:
            raise ValueError("Quantity cannot be negative.")
        if new_reserved < 0:
            raise ValueError("Reserved quantity cannot be negative.")
        if new_damaged < 0:
            raise ValueError("Damaged quantity cannot be negative.")
        if (new_quantity - new_reserved - new_damaged) < 0:
            raise ValueError("Physical quantity cannot be less than reserved + damaged quantity.")

        now = get_current_timestamp()

        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE inventory 
                SET location_id = ?, quantity = ?, reserved_quantity = ?, damaged_quantity = ?, last_updated = ?
                WHERE id = ?;
            """, (new_location, new_quantity, new_reserved, new_damaged, now, inventory_id))

            # Record Audit Log
            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "INVENTORY_PATCHED", "INVENTORY", inventory_id, f"Updated inventory record {inventory_id}.", now))

        return InventoryService.get_inventory_by_id(inventory_id)

    @staticmethod
    def adjust_stock(inventory_id, adjustment_quantity, reason="Stock adjustment"):
        """
        Adjusts inventory physical quantity.
        Validates quantity, prevents negative physical stock, updates last_updated, and logs audit trail.
        """
        current = InventoryService.get_inventory_by_id(inventory_id)
        if not current:
            raise ValueError(f"Inventory item '{inventory_id}' not found.")

        try:
            adj_val = int(adjustment_quantity)
        except (ValueError, TypeError):
            raise ValueError("Adjustment quantity must be an integer.")

        new_quantity = current['quantity'] + adj_val
        if new_quantity < 0:
            raise ValueError(f"Stock adjustment failed: resulting stock ({new_quantity}) cannot be negative.")

        now = get_current_timestamp()

        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE inventory
                SET quantity = ?, last_updated = ?
                WHERE id = ?;
            """, (new_quantity, now, inventory_id))

            # Audit Log
            audit_id = generate_id("AUD")
            desc = f"Adjusted stock by {adj_val:+d} units (New total: {new_quantity}). Reason: {reason}"
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "STOCK_ADJUSTMENT", "INVENTORY", inventory_id, desc, now))

        return InventoryService.get_inventory_by_id(inventory_id)

    @staticmethod
    def report_damage(inventory_id, damaged_quantity_added, reason="Damaged items reported"):
        """
        Reports damaged stock:
        Increases damaged_quantity, reduces available stock, logs an Exception, and writes an Audit Log.
        """
        current = InventoryService.get_inventory_by_id(inventory_id)
        if not current:
            raise ValueError(f"Inventory item '{inventory_id}' not found.")

        try:
            dmg_add = int(damaged_quantity_added)
        except (ValueError, TypeError):
            raise ValueError("Damaged quantity added must be a positive integer.")

        if dmg_add <= 0:
            raise ValueError("Damaged quantity added must be greater than 0.")

        new_damaged_quantity = current['damaged_quantity'] + dmg_add
        available_before = current['available_quantity']

        if dmg_add > available_before:
            raise ValueError(f"Cannot mark {dmg_add} items as damaged; only {available_before} units currently available.")

        now = get_current_timestamp()
        exception_id = generate_id("EXC")

        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE inventory
                SET damaged_quantity = ?, last_updated = ?
                WHERE id = ?;
            """, (new_damaged_quantity, now, inventory_id))

            # Create Exception Entry
            exc_desc = f"Reported {dmg_add} damaged units for inventory {inventory_id} (Product: {current['product']['name']}, SKU: {current['product']['sku']}). Reason: {reason}"
            cursor.execute("""
                INSERT INTO exceptions (id, order_id, product_id, exception_type, severity, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (exception_id, None, current['product_id'], "DAMAGED_GOODS", "HIGH", exc_desc, "OPEN", now))

            # Create Audit Log Entry
            audit_id = generate_id("AUD")
            audit_desc = f"Reported {dmg_add} damaged units for inventory {inventory_id}. Exception ID: {exception_id}."
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "DAMAGE_REPORTED", "INVENTORY", inventory_id, audit_desc, now))

        updated_item = InventoryService.get_inventory_by_id(inventory_id)
        return {
            "inventory": updated_item,
            "exception": {
                "id": exception_id,
                "exception_type": "DAMAGED_GOODS",
                "severity": "HIGH",
                "description": exc_desc,
                "created_at": now
            }
        }

    @staticmethod
    def get_reorder_recommendations():
        """
        Aggregates stock levels across all products and generates deterministic reorder recommendations.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                p.id AS product_id,
                p.sku,
                p.name,
                p.reorder_level,
                p.safety_stock,
                COALESCE(SUM(i.quantity - i.reserved_quantity - i.damaged_quantity), 0) AS total_available
            FROM products p
            LEFT JOIN inventory i ON p.id = i.product_id
            GROUP BY p.id, p.sku, p.name, p.reorder_level, p.safety_stock
            HAVING total_available <= p.reorder_level
            ORDER BY total_available ASC;
        """)
        rows = cursor.fetchall()
        conn.close()

        products_list = [
            {
                "product_id": r["product_id"],
                "sku": r["sku"],
                "name": r["name"],
                "reorder_level": r["reorder_level"],
                "safety_stock": r["safety_stock"],
                "total_available": r["total_available"]
            }
            for r in rows
        ]

        return ReorderEngine.evaluate_reorder_needs(products_list)
