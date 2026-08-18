# WareMind AI — Smart Warehouse Operations & Decision Intelligence Platform

**WareMind AI** is an enterprise-grade, proactive warehouse decision intelligence and order fulfillment automation platform. Designed for modern logistics centers, WareMind AI moves beyond traditional CRUD operations by embedding autonomous rule-based decision engines and optional Gemini LLM integration to optimize stock allocations, priority queueing, picking routes, risk triage, and bottleneck resolution.

---

## 🏗️ System Architecture

```
WareMind-AI/
├── backend/                  # Python Flask REST API backend
│   ├── ai/                   # Decision Intelligence Engines
│   │   ├── allocation_engine.py   # Pick-path & inventory allocation logic
│   │   ├── priority_engine.py     # Multi-variable order priority scoring
│   │   ├── reorder_engine.py      # Dynamic safety-stock & reorder triggers
│   │   ├── bottleneck_engine.py   # Queue congestion & bottleneck detection
│   │   └── decision_engine.py     # Main orchestrator & Gemini API wrapper
│   ├── database/             # SQLite DB schema, connection, & seed runner
│   ├── models/               # Data model definitions
│   ├── routes/               # Modular Flask REST API blueprints
│   ├── services/             # Core business logic & transaction handling
│   └── utils/                # Helper utilities & API response formatters
├── frontend/                 # React 18 + Vite + Tailwind CSS frontend
│   ├── src/
│   │   ├── components/       # Reusable UI cards, tables, badges, modals
│   │   │   ├── dashboard/    # AI Operations Center, Exception Center, Zone Workload Visualizer
│   │   │   ├── layout/       # Header (with live System Health & Demo Reset), Sidebar
│   │   │   └── common/       # Badge, ConfirmModal, Toast, LoadingSpinner, EmptyState
│   │   ├── pages/            # Dashboard, Inventory, Orders, Picking, Packing, Dispatch, Alerts
│   │   └── services/         # Axios/Fetch API connector client
├── tests/                    # Pytest automated test suite (36 tests)
│   ├── test_core_decision_scenario.py  # Core Urgent vs. Normal stock decision test
│   ├── test_allocation.py              # Inventory allocation edge cases
│   ├── test_decision_engine.py         # AI Decision Engine unit tests
│   ├── test_inventory.py              # Negative stock prevention & damage reporting
│   ├── test_orders.py                 # Order status & creation tests
│   └── test_workflow.py               # End-to-end fulfillment pipeline tests
├── README.md                 # Project documentation & demo guide
└── run.py                    # Flask server entry runner
```

---

## ✨ Key Features

1. **AI Operations Center**: Real-time actionable decision cards with severity ratings, confidence scores, impact summaries, and one-click execution triggers.
2. **Proactive Priority Allocation Engine**: Ranks customer orders dynamically by priority tier (`URGENT`, `HIGH`, `NORMAL`, `LOW`), SLA target times, order value, and stock availability.
3. **Core Decision Scenario Resolution**: Resolves stock contention gracefully when requested stock exceeds physical inventory.
4. **Interactive Demo Mode & Seed Reset**: One-click "Reset Demo Data" button in the header instantly restores clean seed state.
5. **Operational Exception Center**: Automated triage for stock deficits, damaged stock, missing pick items, failed quality checks, and SLA breach risks.
6. **Warehouse Zone Workload Visualizer**: Real-time storage density bars for Zone A (Fast Pick), Zone B (Bulk), Zone C (Hazmat/Overstock), and Zone D (Cold Storage).
7. **End-to-End Fulfillment Lifecycle**: Enforces strict state transitions (`PENDING` ➔ `ALLOCATED` ➔ `PICKING` ➔ `PACKING` ➔ `QC` ➔ `DISPATCHED`).
8. **Negative Stock & Race Condition Guards**: Physical stock non-negativity enforced at database transaction boundaries.

---

## 🎯 Core Decision Scenario Walkthrough

### Scenario Setup
- **Urgent Order (`ORD-001`)**: Requires **10 units** of `PROD-001` (High-Performance Industrial Sensor).
- **Physical Stock Available**: **7 units** at location `LOC-A01-1-1`.
- **Normal Order (`ORD-002`)**: Requires **5 units** of `PROD-001`.

### Decision Engine Outcome
1. **Urgent Order Allocated First**: Priority scoring ranks `ORD-001` higher than `ORD-002`.
2. **Partial Allocation Executed**: `ORD-001` receives all **7 available units**, changing status to `PARTIALLY_ALLOCATED` with a **3-unit shortage** flagged.
3. **Competing Order Handled**: `ORD-002` receives **0 units** (stock depleted), remaining `PENDING` with a **5-unit shortage exception**.
4. **Transparent Explanation**: The engine logs exact reasons: `"Product 'High-Performance Industrial Sensor' (SKU: SKU-IND-001): Requested 10 units. Allocated 7 units from available stock. Shortage of 3 units identified."`

---

## 🛠️ 12 Tested Operational Scenarios

| # | Scenario Description | Tested Behavior |
|---|----------------------|------------------|
| 1 | **Normal Order (Full Stock)** | Fully allocates inventory, sets status `ALLOCATED`. |
| 2 | **Urgent Order (Shortage)** | Allocates max available units, sets status `PARTIALLY_ALLOCATED`, flags shortage exception. |
| 3 | **Competing Orders** | Priority order receives stock first; lower priority order receives remaining stock or shortage. |
| 4 | **Out-of-Stock Product** | Allocation fails cleanly, flags `INSUFFICIENT_STOCK` exception. |
| 5 | **Damaged Inventory** | Damaged units excluded from available stock pool; generates `DAMAGED_GOODS` alert. |
| 6 | **Missing Item during Picking** | Picker reports missing units; creates `MISSING_ITEM` exception for re-allocation triage. |
| 7 | **Failed Quality Check** | Failed QC creates `QUALITY_CONTROL_FAILURE` exception and resets order status to `PACKING`. |
| 8 | **Delayed Order** | SLA breach risk detector elevates priority and generates prioritization recommendation. |
| 9 | **Multiple Warehouse Locations** | Allocation Engine picks stock across multiple bins in zone order (Zone A ➔ Zone B). |
| 10 | **Reorder Recommendation** | Reorder Engine identifies stock <= reorder level and suggests purchase order quantities. |
| 11 | **Picking Bottleneck** | Detects high pending task queues and recommends staff reallocation. |
| 12 | **Dispatch Backlog** | Monitors QC-passed orders waiting for carrier assignment and alerts warehouse manager. |

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.9+
- Node.js 18+ & npm

### 1. Backend Setup & Test Runner
```bash
# Navigate to project root
cd "waremind ai"

# Install dependencies
pip install -r backend/requirements.txt

# Run database seed
python backend/database/seed.py

# Run all 36 automated unit & workflow tests
python -m pytest

# Start Flask backend server
python run.py
```
*Backend API runs at:* `http://localhost:5000`  
*Health Check:* `GET http://localhost:5000/api/health`

### 2. Frontend Setup
```bash
# Navigate to frontend
cd frontend

# Install npm packages
npm install

# Run Vite dev server
npm run dev

# Build production bundle
npm run build
```
*Frontend runs at:* `http://localhost:3000`

---

## 📡 REST API Reference Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Basic API health status. |
| `GET` | `/api/system/status` | Database connection status & entity counts. |
| `POST` | `/api/system/reset-demo` | Resets SQLite DB to initial demo seed state. |
| `GET` | `/api/analytics/decision-insights` | Main AI Decision Intelligence recommendations. |
| `GET` | `/api/analytics/audit-logs` | Chronological system audit event stream. |
| `GET` | `/api/inventory` | List inventory items with nested location & product. |
| `POST` | `/api/inventory/:id/adjust` | Adjust physical stock (+ / -) with reason log. |
| `POST` | `/api/inventory/:id/damage` | Report damaged stock & create exception alert. |
| `GET` | `/api/orders` | List customer order queue. |
| `POST` | `/api/orders/:id/allocate` | Run AI Allocation Engine on order. |
| `POST` | `/api/picking/tasks` | Create picking task for allocated order. |
| `POST` | `/api/packing/tasks` | Create packing task for picked order. |
| `POST` | `/api/qc/check` | Record QC inspection result (PASS / FAIL). |
| `POST` | `/api/dispatch` | Generate carrier shipping manifest. |
| `POST` | `/api/exceptions/:id/resolve` | Automated exception triage & resolution. |

---

## ⚖️ Hackathon Demo Guide for Judges

1. **Open Dashboard**: Navigate to `http://localhost:3000`. Observe live KPI cards, System Online indicator, AI Operations Center, Exception Center, and Zone Workload bars.
2. **Explore AI Recommendations**: Click **Execute** on any recommendation card in the AI Operations Center to navigate directly to the affected order or stock item.
3. **Try Core Decision Scenario**:
   - Go to **Orders Queue** (`/orders`).
   - Click on **ORD-001** (Urgent Order, Apex Robotics).
   - Click **Run AI Inventory Allocation**. Observe the **Partial Allocation (7 / 10)** decision and explanation text.
   - Go to **ORD-002** (Normal Order). Click **Run AI Inventory Allocation**. Observe that remaining stock is 0 and shortage is flagged.
4. **Simulate Workflow Progression**:
   - For an allocated order, click **Start Picking**, then navigate to Picking Station to complete picking.
   - Proceed to Packing Station ➔ Perform Quality Check ➔ Dispatch with tracking number.
5. **One-Click Demo Reset**:
   - Click **Reset Demo Data** in the top header at any time to instantly restore clean initial seed data!

---

## 🔮 Future Improvements
- **Multi-Warehouse Geospatial Routing**: Expand allocation logic to route orders across multiple distribution centers based on customer proximity.
- **Computer Vision QC Verification**: Integrate camera stream AI for automated barcode and package damage detection during packing.
- **Predictive Demand Forecasting**: Incorporate ARIMA / Prophet models to project seasonal stock demands.
#   w a r e m i n d - a i  
 