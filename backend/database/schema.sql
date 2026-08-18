-- WareMind AI SQLite Complete Database Schema

-- 1. Products Table
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT,
    description TEXT,
    unit_price REAL DEFAULT 0.0,
    reorder_level INTEGER DEFAULT 10,
    safety_stock INTEGER DEFAULT 5,
    weight REAL DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Warehouse Locations Table
CREATE TABLE IF NOT EXISTS warehouse_locations (
    id TEXT PRIMARY KEY,
    zone TEXT NOT NULL,
    aisle TEXT NOT NULL,
    rack TEXT NOT NULL,
    bin TEXT NOT NULL,
    capacity INTEGER DEFAULT 100,
    status TEXT DEFAULT 'AVAILABLE' -- AVAILABLE, FULL, MAINTENANCE
);

-- 3. Inventory Table
CREATE TABLE IF NOT EXISTS inventory (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL,
    location_id TEXT NOT NULL,
    quantity INTEGER DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0,
    damaged_quantity INTEGER DEFAULT 0,
    available_quantity INTEGER GENERATED ALWAYS AS (quantity - reserved_quantity - damaged_quantity) VIRTUAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY(location_id) REFERENCES warehouse_locations(id) ON DELETE CASCADE
);

-- 4. Orders Table
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    order_number TEXT UNIQUE NOT NULL,
    customer_name TEXT NOT NULL,
    priority TEXT DEFAULT 'NORMAL', -- URGENT, HIGH, NORMAL, LOW
    status TEXT DEFAULT 'PENDING',  -- PENDING, PARTIALLY_ALLOCATED, ALLOCATED, PICKING, PICKED, PACKING, PACKED, QC_PASSED, QC_FAILED, DISPATCHED, COMPLETED, CANCELLED
    required_by TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_value REAL DEFAULT 0.0
);

-- 5. Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    requested_quantity INTEGER NOT NULL,
    allocated_quantity INTEGER DEFAULT 0,
    picked_quantity INTEGER DEFAULT 0,
    packed_quantity INTEGER DEFAULT 0,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- 6. Inventory Allocations Table
CREATE TABLE IF NOT EXISTS inventory_allocations (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    location_id TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    allocation_status TEXT DEFAULT 'ALLOCATED', -- ALLOCATED, PICKED, PACKED, DISPATCHED, CANCELLED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE,
    FOREIGN KEY(location_id) REFERENCES warehouse_locations(id) ON DELETE CASCADE
);

-- 7. Warehouse Tasks Table
CREATE TABLE IF NOT EXISTS warehouse_tasks (
    id TEXT PRIMARY KEY,
    order_id TEXT,
    task_type TEXT NOT NULL, -- PICKING, PACKING, DISPATCH, REORDER, QC
    assigned_to TEXT,
    status TEXT DEFAULT 'PENDING', -- PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    priority TEXT DEFAULT 'NORMAL',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE SET NULL
);

-- 8. Exceptions Table
CREATE TABLE IF NOT EXISTS exceptions (
    id TEXT PRIMARY KEY,
    order_id TEXT,
    product_id TEXT,
    exception_type TEXT NOT NULL, -- INSUFFICIENT_STOCK, DAMAGED_GOODS, SLA_BREACH_RISK, LOCATION_BLOCKED, MISSING_ITEM, QUALITY_CONTROL_FAILURE
    severity TEXT DEFAULT 'MEDIUM', -- CRITICAL, HIGH, MEDIUM, LOW
    description TEXT,
    status TEXT DEFAULT 'OPEN', -- OPEN, IN_REVIEW, RESOLVED, IGNORED
    resolution TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE SET NULL,
    FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE SET NULL
);

-- 9. Dispatches Table
CREATE TABLE IF NOT EXISTS dispatches (
    id TEXT PRIMARY KEY,
    order_id TEXT NOT NULL,
    carrier TEXT NOT NULL,
    tracking_number TEXT UNIQUE,
    status TEXT DEFAULT 'PREPARING', -- PREPARING, DISPATCHED, DELIVERED
    dispatched_at TIMESTAMP,
    FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- 10. Audit Logs Table
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. Users Table for Authentication & Access Control
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'MANAGER', -- ADMIN, MANAGER, CUSTOMER, OPERATOR
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_inventory_location ON inventory(location_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_priority ON orders(priority);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_allocations_order ON inventory_allocations(order_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON warehouse_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_order ON warehouse_tasks(order_id);
CREATE INDEX IF NOT EXISTS idx_exceptions_status ON exceptions(status);
CREATE INDEX IF NOT EXISTS idx_exceptions_severity ON exceptions(severity);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

