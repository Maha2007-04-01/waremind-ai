"""
Idempotent Database Seed Script for WareMind AI
Populates products, warehouse locations, inventory, orders, order items, allocations, tasks, exceptions, dispatches, and audit logs.
Contains realistic, complex decision-engine challenge scenarios (stock contention, damaged goods, SLA breach risks, split locations).
"""
import sys
import os
import sqlite3
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db import get_db_connection, init_db

def seed_database():
    print("Initializing database schema...")
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now(timezone.utc)
    
    print("Seeding Products (25 items)...")
    products = [
        ("PROD-001", "SKU-IND-001", "High-Performance Industrial Sensor", "Electronics", "Precision optical motion and proximity sensor", 149.99, 15, 10, 0.5, now.isoformat()),
        ("PROD-002", "SKU-NET-002", "Smart Logistics Hub Router", "Networking", "Industrial Grade Mesh Wi-Fi 6 Router", 299.50, 10, 5, 1.2, now.isoformat()),
        ("PROD-003", "SKU-MOB-003", "Rugged Scanner Terminal", "Hardware", "Android 12 Enterprise Barcode Scanner", 499.00, 8, 4, 0.8, now.isoformat()),
        ("PROD-004", "SKU-MTR-004", "Automated Conveyor Belt Motor", "Machinery", "3-Phase AC 480V Conveyor Drive Motor", 850.00, 5, 2, 12.5, now.isoformat()),
        ("PROD-005", "SKU-CON-005", "Barcode RFID Label Roll (1000ct)", "Consumables", "Thermal Transfer RFID Smart Labels", 24.99, 50, 25, 0.3, now.isoformat()),
        ("PROD-006", "SKU-PRT-006", "Heavy-Duty Pallet Jack Wheel", "Maintenance", "Polyurethane 8-inch Load Wheel", 45.00, 20, 10, 3.1, now.isoformat()),
        ("PROD-007", "SKU-CON-007", "Thermal Transfer Ribbon 110mm", "Consumables", "Resin Enhanced Wax Ribbon Roll", 18.50, 40, 20, 0.4, now.isoformat()),
        ("PROD-008", "SKU-PWR-008", "Li-Ion Battery Pack 24V", "Electronics", "High Capacity AGV Replacement Battery", 320.00, 12, 6, 5.4, now.isoformat()),
        ("PROD-009", "SKU-PPE-009", "High-Vis Safety Vest XL", "Safety", "Class 2 Reflective Mesh Safety Vest", 15.99, 30, 15, 0.2, now.isoformat()),
        ("PROD-010", "SKU-PPE-010", "Steel-Toe Work Boots (Size 10)", "Safety", "Waterproof Anti-Slip Work Boots", 89.95, 15, 8, 1.8, now.isoformat()),
        ("PROD-011", "SKU-PKG-011", "Stretch Wrap Roll 18-inch", "Packaging", "80 Gauge Clear Pallet Stretch Film", 29.99, 60, 30, 3.8, now.isoformat()),
        ("PROD-012", "SKU-PKG-012", "Corrugated Shipping Box (Pack 25)", "Packaging", "Double Wall 18x18x18 Box", 38.00, 50, 25, 8.0, now.isoformat()),
        ("PROD-013", "SKU-TLS-013", "Laser Distance Meter Pro", "Tools", "Bluetooth Digital Rangefinder 100m", 129.00, 10, 5, 0.6, now.isoformat()),
        ("PROD-014", "SKU-ROB-014", "Pneumatic Gripper Arm Assembly", "Robotics", "Dual-Jaw Robotic Pick End-Effector", 1250.00, 3, 1, 6.2, now.isoformat()),
        ("PROD-015", "SKU-IOT-015", "Smart Warehouse Gateway Controller", "Electronics", "Edge AI Gateway Unit", 450.00, 8, 4, 1.1, now.isoformat()),
        ("PROD-016", "SKU-PPE-016", "ESD Anti-Static Wrist Strap", "Safety", "Coiled Cord Grounding Wristband", 8.99, 25, 10, 0.1, now.isoformat()),
        ("PROD-017", "SKU-EQP-017", "Digital Weight Scale 50kg", "Hardware", "High Precision Floor & Bench Scale", 180.00, 5, 2, 4.5, now.isoformat()),
        ("PROD-018", "SKU-CAB-018", "Industrial Ethernet Cable 20m", "Networking", "Shielded CAT6A M12 Connector", 22.50, 35, 15, 0.7, now.isoformat()),
        ("PROD-019", "SKU-MNT-019", "Hydraulic Fluid Shell Tellus 20L", "Maintenance", "ISO VG 46 Premium Hydraulic Oil", 78.00, 10, 5, 18.0, now.isoformat()),
        ("PROD-020", "SKU-SGN-020", "Warehouse Location Barcode Sign Plate", "Signage", "Retro-Reflective Rack Sign", 12.00, 50, 20, 0.2, now.isoformat()),
        ("PROD-021", "SKU-SAF-021", "Emergency Stop Button Switch", "Safety", "Mushroom Head Push Button 22mm", 34.50, 15, 5, 0.3, now.isoformat()),
        ("PROD-022", "SKU-SEN-022", "Proximity Sensor NPN 12V", "Electronics", "Inductive Proximity Switch 8mm", 19.99, 25, 10, 0.15, now.isoformat()),
        ("PROD-023", "SKU-HDW-023", "Heavy-Duty Shelving Clip Set", "Hardware", "Steel Rack Safety Clip (Pack 50)", 14.50, 40, 20, 1.0, now.isoformat()),
        ("PROD-024", "SKU-AGV-024", "AGV Driving Wheel Rubber Assembly", "Robotics", "Heavy Payload Drive Wheel", 340.00, 6, 3, 4.2, now.isoformat()),
        ("PROD-025", "SKU-TLS-025", "Rechargeable Headlamp 1000Lm", "Tools", "Hands-Free LED Inspection Light", 27.99, 20, 10, 0.25, now.isoformat())
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO products (id, sku, name, category, description, unit_price, reorder_level, safety_stock, weight, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, products)

    print("Seeding Warehouse Locations (15 locations)...")
    locations = [
        ("LOC-A01-1-1", "Zone A", "Aisle 01", "Rack 1", "Bin 1", 200, "AVAILABLE"),
        ("LOC-A01-1-2", "Zone A", "Aisle 01", "Rack 1", "Bin 2", 200, "AVAILABLE"),
        ("LOC-A01-2-1", "Zone A", "Aisle 01", "Rack 2", "Bin 1", 150, "AVAILABLE"),
        ("LOC-A02-1-1", "Zone A", "Aisle 02", "Rack 1", "Bin 1", 150, "AVAILABLE"),
        ("LOC-B01-1-1", "Zone B", "Aisle 01", "Rack 1", "Bin 1", 500, "AVAILABLE"),
        ("LOC-B01-1-2", "Zone B", "Aisle 01", "Rack 1", "Bin 2", 500, "AVAILABLE"),
        ("LOC-B02-2-1", "Zone B", "Aisle 02", "Rack 2", "Bin 1", 400, "AVAILABLE"),
        ("LOC-B02-3-2", "Zone B", "Aisle 02", "Rack 3", "Bin 2", 300, "AVAILABLE"),
        ("LOC-C01-1-1", "Zone C", "Aisle 01", "Rack 1", "Bin 1", 100, "AVAILABLE"),
        ("LOC-C01-1-2", "Zone C", "Aisle 01", "Rack 1", "Bin 2", 100, "AVAILABLE"),
        ("LOC-C02-1-1", "Zone C", "Aisle 02", "Rack 1", "Bin 1", 100, "MAINTENANCE"),
        ("LOC-D01-1-1", "Zone D", "Aisle 01", "Rack 1", "Bin 1", 80, "AVAILABLE"),
        ("LOC-D01-1-2", "Zone D", "Aisle 01", "Rack 1", "Bin 2", 80, "AVAILABLE"),
        ("LOC-D02-2-1", "Zone D", "Aisle 02", "Rack 2", "Bin 1", 120, "FULL"),
        ("LOC-D02-2-2", "Zone D", "Aisle 02", "Rack 2", "Bin 2", 120, "AVAILABLE")
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO warehouse_locations (id, zone, aisle, rack, bin, capacity, status)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, locations)

    print("Seeding Inventory Records (41 records)...")
    inventory_items = [
        # Stock Contention Scenario for PROD-001 (Total available = 7 units)
        ("INV-001", "PROD-001", "LOC-A01-1-1", 7, 0, 0, now.isoformat()),
        ("INV-002", "PROD-001", "LOC-B01-1-1", 0, 0, 0, now.isoformat()),

        # Split Location Scenario for PROD-002 (6 in A01, 10 in B02)
        ("INV-003", "PROD-002", "LOC-A01-1-2", 6, 0, 0, now.isoformat()),
        ("INV-004", "PROD-002", "LOC-B02-3-2", 10, 0, 0, now.isoformat()),

        # Damaged Stock Deficit for PROD-003 (10 total, 8 damaged -> 2 available)
        ("INV-005", "PROD-003", "LOC-C01-1-1", 10, 0, 8, now.isoformat()),

        # Low Stock Item for PROD-004 (2 units total)
        ("INV-006", "PROD-004", "LOC-B01-1-2", 2, 0, 0, now.isoformat()),

        # Consumables with high stock
        ("INV-007", "PROD-005", "LOC-A02-1-1", 120, 20, 0, now.isoformat()),
        ("INV-008", "PROD-005", "LOC-B02-2-1", 200, 0, 0, now.isoformat()),

        # Maintenance wheels
        ("INV-009", "PROD-006", "LOC-A01-2-1", 25, 5, 0, now.isoformat()),
        ("INV-010", "PROD-007", "LOC-A02-1-1", 80, 10, 0, now.isoformat()),

        # Out of stock item PROD-008
        ("INV-011", "PROD-008", "LOC-C01-1-2", 0, 0, 0, now.isoformat()),

        # PPE items
        ("INV-012", "PROD-009", "LOC-A01-1-1", 45, 0, 0, now.isoformat()),
        ("INV-013", "PROD-010", "LOC-A01-2-1", 18, 2, 0, now.isoformat()),

        # Packaging items
        ("INV-014", "PROD-011", "LOC-B01-1-1", 90, 15, 0, now.isoformat()),
        ("INV-015", "PROD-012", "LOC-B01-1-2", 60, 10, 2, now.isoformat()),

        # Tools & Robotics
        ("INV-016", "PROD-013", "LOC-C01-1-1", 14, 0, 0, now.isoformat()),
        ("INV-017", "PROD-014", "LOC-C01-1-2", 1, 0, 0, now.isoformat()),
        ("INV-018", "PROD-015", "LOC-C02-1-1", 12, 0, 0, now.isoformat()),

        # Safety & Hardware
        ("INV-019", "PROD-016", "LOC-A01-1-2", 50, 0, 0, now.isoformat()),
        ("INV-020", "PROD-017", "LOC-B02-2-1", 8, 1, 0, now.isoformat()),
        ("INV-021", "PROD-018", "LOC-A02-1-1", 40, 5, 0, now.isoformat()),
        ("INV-022", "PROD-019", "LOC-D01-1-1", 15, 0, 0, now.isoformat()),
        ("INV-023", "PROD-020", "LOC-A01-1-1", 100, 0, 0, now.isoformat()),
        ("INV-024", "PROD-021", "LOC-C01-1-1", 22, 2, 0, now.isoformat()),
        ("INV-025", "PROD-022", "LOC-C01-1-2", 30, 0, 0, now.isoformat()),
        ("INV-026", "PROD-023", "LOC-A01-2-1", 65, 0, 0, now.isoformat()),
        ("INV-027", "PROD-024", "LOC-D02-2-1", 8, 2, 0, now.isoformat()),
        ("INV-028", "PROD-025", "LOC-A01-1-2", 28, 0, 1, now.isoformat()),

        # Additional location distribution
        ("INV-029", "PROD-001", "LOC-A01-2-1", 0, 0, 0, now.isoformat()),
        ("INV-030", "PROD-003", "LOC-C01-1-2", 4, 0, 0, now.isoformat()),
        ("INV-031", "PROD-005", "LOC-D01-1-2", 50, 0, 0, now.isoformat()),
        ("INV-032", "PROD-006", "LOC-B01-1-1", 10, 0, 0, now.isoformat()),
        ("INV-033", "PROD-007", "LOC-B02-3-2", 30, 0, 0, now.isoformat()),
        ("INV-034", "PROD-009", "LOC-A02-1-1", 20, 0, 0, now.isoformat()),
        ("INV-035", "PROD-010", "LOC-B01-1-2", 12, 0, 0, now.isoformat()),
        ("INV-036", "PROD-011", "LOC-D02-2-2", 40, 0, 0, now.isoformat()),
        ("INV-037", "PROD-013", "LOC-C02-1-1", 5, 0, 0, now.isoformat()),
        ("INV-038", "PROD-018", "LOC-B02-2-1", 25, 0, 0, now.isoformat()),
        ("INV-039", "PROD-021", "LOC-D01-1-2", 10, 0, 0, now.isoformat()),
        ("INV-040", "PROD-023", "LOC-B01-1-1", 35, 0, 0, now.isoformat()),
        ("INV-041", "PROD-025", "LOC-B02-3-2", 15, 0, 0, now.isoformat())
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO inventory (id, product_id, location_id, quantity, reserved_quantity, damaged_quantity, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, inventory_items)

    print("Seeding Orders (15 orders)...")
    req_urgent_1 = (now + timedelta(hours=2)).isoformat()
    req_urgent_2 = (now + timedelta(minutes=30)).isoformat()
    req_normal_1 = (now + timedelta(hours=24)).isoformat()
    req_normal_2 = (now + timedelta(hours=48)).isoformat()

    orders = [
        ("ORD-001", "ORD-2026-001", "Apex Robotics Corp", "URGENT", "PENDING", req_urgent_1, now.isoformat(), 1499.90),
        ("ORD-002", "ORD-2026-002", "Global Freight Systems", "NORMAL", "PENDING", req_normal_1, now.isoformat(), 749.95),
        ("ORD-003", "ORD-2026-003", "TechDynamics Logistics", "HIGH", "PENDING", req_normal_1, now.isoformat(), 4492.50),
        ("ORD-004", "ORD-2026-004", "NextGen Manufacturing", "URGENT", "PARTIALLY_ALLOCATED", req_urgent_1, now.isoformat(), 3850.00),
        ("ORD-005", "ORD-2026-005", "AeroSpace Supplies Inc", "URGENT", "PENDING", req_urgent_2, now.isoformat(), 2495.00),
        ("ORD-006", "ORD-2026-006", "Midwest Hardware Distributors", "NORMAL", "ALLOCATED", req_normal_2, now.isoformat(), 640.00),
        ("ORD-007", "ORD-2026-007", "FastTrack Fulfillment", "NORMAL", "PICKING", req_normal_1, now.isoformat(), 1250.00),
        ("ORD-008", "ORD-2026-008", "OmniChannel Retail", "LOW", "PACKING", req_normal_2, now.isoformat(), 890.00),
        ("ORD-009", "ORD-2026-009", "Vanguard Automation", "HIGH", "DISPATCHED", req_normal_1, now.isoformat(), 5600.00),
        ("ORD-010", "ORD-2026-010", "Precision Tools Co", "NORMAL", "COMPLETED", req_normal_2, now.isoformat(), 340.00),
        ("ORD-011", "ORD-2026-011", "Summit Assembly Solutions", "URGENT", "PENDING", req_urgent_1, now.isoformat(), 1280.00),
        ("ORD-012", "ORD-2026-012", "Beacon Safety Equipment", "LOW", "PENDING", req_normal_2, now.isoformat(), 420.00),
        ("ORD-013", "ORD-2026-013", "Enterprise Networking Inc", "NORMAL", "CANCELLED", req_normal_1, now.isoformat(), 950.00),
        ("ORD-014", "ORD-2026-014", "Industrial Machinery Supply", "HIGH", "PARTIALLY_ALLOCATED", req_normal_1, now.isoformat(), 2700.00),
        ("ORD-015", "ORD-2026-015", "Metro Courier Services", "NORMAL", "PENDING", req_normal_2, now.isoformat(), 530.00)
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO orders (id, order_number, customer_name, priority, status, required_by, created_at, total_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, orders)

    print("Seeding Order Items...")
    order_items = [
        ("ITEM-001", "ORD-001", "PROD-001", 10, 0, 0, 0),
        ("ITEM-002", "ORD-002", "PROD-001", 5, 0, 0, 0),
        ("ITEM-003", "ORD-003", "PROD-002", 15, 0, 0, 0),
        ("ITEM-004", "ORD-003", "PROD-005", 10, 0, 0, 0),
        ("ITEM-005", "ORD-004", "PROD-008", 5, 0, 0, 0),
        ("ITEM-006", "ORD-004", "PROD-003", 5, 2, 0, 0),
        ("ITEM-007", "ORD-005", "PROD-004", 2, 0, 0, 0),
        ("ITEM-008", "ORD-005", "PROD-015", 1, 0, 0, 0),
        ("ITEM-009", "ORD-006", "PROD-006", 4, 4, 0, 0),
        ("ITEM-010", "ORD-007", "PROD-007", 10, 10, 10, 0),
        ("ITEM-011", "ORD-008", "PROD-010", 2, 2, 2, 2),
        ("ITEM-012", "ORD-009", "PROD-014", 3, 3, 3, 3),
        ("ITEM-013", "ORD-010", "PROD-013", 1, 1, 1, 1),
        ("ITEM-014", "ORD-011", "PROD-021", 5, 0, 0, 0),
        ("ITEM-015", "ORD-012", "PROD-009", 10, 0, 0, 0),
        ("ITEM-016", "ORD-014", "PROD-019", 4, 2, 0, 0),
        ("ITEM-017", "ORD-015", "PROD-025", 3, 0, 0, 0)
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO order_items (id, order_id, product_id, requested_quantity, allocated_quantity, picked_quantity, packed_quantity)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, order_items)

    print("Seeding Inventory Allocations...")
    allocations = [
        ("ALLOC-001", "ORD-006", "PROD-006", "LOC-A01-2-1", 4, "ALLOCATED", now.isoformat()),
        ("ALLOC-002", "ORD-007", "PROD-007", "LOC-A02-1-1", 10, "PICKED", now.isoformat()),
        ("ALLOC-003", "ORD-008", "PROD-010", "LOC-A01-2-1", 2, "PACKED", now.isoformat()),
        ("ALLOC-004", "ORD-009", "PROD-014", "LOC-C01-1-2", 3, "PACKED", now.isoformat())
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO inventory_allocations (id, order_id, product_id, location_id, quantity, allocation_status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, allocations)

    print("Seeding Warehouse Tasks...")
    tasks = [
        ("TASK-001", "ORD-007", "PICKING", "Worker-01", "IN_PROGRESS", "NORMAL", now.isoformat(), None),
        ("TASK-002", "ORD-008", "PACKING", "Worker-02", "IN_PROGRESS", "LOW", now.isoformat(), None),
        ("TASK-003", "ORD-009", "DISPATCH", "Worker-03", "COMPLETED", "HIGH", (now - timedelta(hours=2)).isoformat(), now.isoformat()),
        ("TASK-004", "ORD-005", "PICKING", "Worker-01", "PENDING", "URGENT", None, None),
        ("TASK-005", "ORD-001", "REORDER", "System", "PENDING", "URGENT", now.isoformat(), None)
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO warehouse_tasks (id, order_id, task_type, assigned_to, status, priority, started_at, completed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
    """, tasks)

    print("Seeding Exceptions (Edge Cases)...")
    exceptions = [
        ("EXC-001", "ORD-001", "PROD-001", "INSUFFICIENT_STOCK", "CRITICAL", 
         "Urgent Order ORD-001 requires 10 units of PROD-001, but total available stock across all locations is only 7 units.", 
         "OPEN", None, now.isoformat(), None),
        
        ("EXC-002", "ORD-004", "PROD-003", "DAMAGED_GOODS", "HIGH", 
         "8 of 10 units at LOC-C01-1-1 are marked DAMAGED. Net available quantity (2) cannot meet requested 5 units.", 
         "OPEN", None, now.isoformat(), None),
        
        ("EXC-003", "ORD-005", "PROD-004", "SLA_BREACH_RISK", "CRITICAL", 
         "Urgent order ORD-005 is required within 30 minutes but task TASK-004 has not started picking.", 
         "OPEN", None, now.isoformat(), None),
        
        ("EXC-004", "ORD-004", "PROD-008", "INSUFFICIENT_STOCK", "HIGH", 
         "Product PROD-008 (Li-Ion Battery Pack 24V) is completely OUT OF STOCK (0 units total).", 
         "OPEN", None, now.isoformat(), None)
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO exceptions (id, order_id, product_id, exception_type, severity, description, status, resolution, created_at, resolved_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, exceptions)

    print("Seeding Dispatches...")
    dispatches = [
        ("DSP-001", "ORD-009", "FedEx Freight", "TRK-9876543210", "DISPATCHED", now.isoformat()),
        ("DSP-002", "ORD-010", "UPS Ground", "TRK-1234567890", "DELIVERED", (now - timedelta(days=1)).isoformat())
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO dispatches (id, order_id, carrier, tracking_number, status, dispatched_at)
        VALUES (?, ?, ?, ?, ?, ?);
    """, dispatches)

    print("Seeding Audit Logs...")
    audit_logs = [
        ("AUD-001", "INITIAL_SEED", "SYSTEM", "DATABASE", "Database populated with realistic initial warehouse seed data.", now.isoformat()),
        ("AUD-002", "EXCEPTION_RAISED", "EXCEPTION", "EXC-001", "Critical stock shortage exception raised for Order ORD-001.", now.isoformat()),
        ("AUD-003", "EXCEPTION_RAISED", "EXCEPTION", "EXC-003", "SLA breach risk alert raised for Urgent Order ORD-005.", now.isoformat())
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?);
    """, audit_logs)

    from werkzeug.security import generate_password_hash
    print("Seeding Demo Users (4 demo accounts)...")
    cursor.execute("DELETE FROM users;")
    hashed_pwd = generate_password_hash("waremind2026")
    users = [
        ("USR-MANAGER", "manager", "manager@waremind.ai", hashed_pwd, "Sarah Chen", "MANAGER", now.isoformat()),
        ("USR-ADMIN", "admin", "admin@waremind.ai", hashed_pwd, "System Admin", "ADMIN", now.isoformat()),
        ("USR-CUSTOMER", "customer", "customer@apexrobotics.com", hashed_pwd, "Apex Robotics Corp", "CUSTOMER", now.isoformat()),
        ("USR-PICKER", "picker", "picker@waremind.ai", hashed_pwd, "Marcus Vance", "OPERATOR", now.isoformat())
    ]
    cursor.executemany("""
        INSERT OR REPLACE INTO users (id, username, email, password_hash, name, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, users)


    conn.commit()
    conn.close()
    print("Database seeding completed successfully!")


if __name__ == "__main__":
    seed_database()
