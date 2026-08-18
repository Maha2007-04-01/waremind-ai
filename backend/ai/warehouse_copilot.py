"""
AI Warehouse Copilot — deterministic intent-based warehouse assistant.
Answers operational questions using live database data and existing decision engines.
Does NOT require any external AI API (Gemini / OpenAI).
"""
import logging
import re
from database.db import get_db_connection
from services.order_service import OrderService
from services.inventory_service import InventoryService
from ai.stockout_predictor import StockoutPredictor
from ai.bottleneck_engine import BottleneckEngine
from ai.priority_engine import PriorityEngine

logger = logging.getLogger(__name__)

# ─── Intent Definitions ────────────────────────────────────────────────────────
INTENTS = {
    "ORDER_RISK":         ["risk", "at risk", "delayed", "urgent order", "failing order", "critical order", "overdue"],
    "STOCKOUT_RISK":      ["stock out", "stockout", "run out", "deplete", "empty", "out of stock"],
    "REORDER":            ["reorder", "replenish", "restock", "order more", "buy more", "purchase"],
    "ALLOCATION":         ["allocat", "why allocated", "allocation", "assigned stock"],
    "BOTTLENECK":         ["bottleneck", "slow", "backlog", "delay", "queue", "stuck", "congestion"],
    "TRACEABILITY":       ["where is", "journey", "trace", "track", "history", "movement", "lifecycle"],
    "EXCEPTIONS":         ["exception", "alert", "damage", "damaged", "problem", "issue", "error"],
    "DISPATCH":           ["dispatch", "ship", "shipment", "carrier", "tracking", "delivery"],
    "INVENTORY_RISK":     ["inventory risk", "low stock", "inventory problem", "damaged inventory"],
    "GENERAL_STATUS":     ["status", "overview", "summary", "today", "right now", "situation", "what should", "do next"],
}

def _detect_intent(question: str):
    q = question.lower()
    scores = {intent: 0 for intent in INTENTS}
    for intent, keywords in INTENTS.items():
        for kw in keywords:
            if kw in q:
                scores[intent] += 1
    best = max(scores, key=scores.get)
    confidence = min(0.99, 0.5 + scores[best] * 0.15)
    return best if scores[best] > 0 else "GENERAL_STATUS", confidence

def _extract_order_id(question: str):
    """Extract ORD-xxx pattern from question."""
    match = re.search(r"ORD-\w+", question, re.IGNORECASE)
    return match.group(0).upper() if match else None

def _extract_sku(question: str):
    """Extract SKU-xxx pattern from question."""
    match = re.search(r"SKU-\w+", question, re.IGNORECASE)
    return match.group(0).upper() if match else None

# ─── Intent Handlers ───────────────────────────────────────────────────────────

def _handle_order_risk(question):
    orders = OrderService.get_all_orders()
    target_id = _extract_order_id(question)

    risky = []
    for o in orders:
        pe = o.get("priority_evaluation", {})
        risk_score = pe.get("risk_score", 0)
        if risk_score >= 0.5 or o.get("priority") in ("URGENT", "HIGH"):
            risky.append(o)

    if target_id:
        specific = next((o for o in orders if o["id"] == target_id or o.get("order_number", "").upper() == target_id), None)
        if specific:
            pe = specific.get("priority_evaluation", {})
            answer = (
                f"Order {specific['order_number']} for {specific['customer_name']}: "
                f"Status is **{specific['status']}**, Priority: **{specific['priority']}**. "
                f"Risk factors: {pe.get('risk_factors', ['None identified'])}."
            )
            return answer, "ORDER_RISK", [specific], ["Review allocation status and expedite if urgent."]

    count = len(risky)
    if count == 0:
        answer = "✅ No orders are currently at high risk. All orders appear to be on track."
        return answer, "ORDER_RISK", [], ["Continue monitoring order pipeline."]

    answer = f"🚨 {count} order(s) are currently at elevated risk:\n"
    for o in risky[:5]:
        answer += f"• **{o['order_number']}** ({o['customer_name']}) — Status: {o['status']}, Priority: {o['priority']}\n"

    recs = ["Expedite allocation for URGENT orders.", "Check picking queue for delayed orders.", "Notify customers about potential delays."]
    return answer, "ORDER_RISK", risky[:5], recs

def _handle_stockout_risk(question):
    sku = _extract_sku(question)
    predictions = StockoutPredictor.predict_all()

    if sku:
        product = next((p for p in predictions if p["sku"].upper() == sku), None)
        if product:
            answer = (
                f"🔴 **{product['sku']}** ({product['product_name']}): "
                f"Risk level **{product['risk_level']}**. "
                f"{product['explanation']} {product['recommended_action']}"
            )
            return answer, "STOCKOUT_RISK", [product], [product["recommended_action"]]

    critical = [p for p in predictions if p["risk_level"] in ("CRITICAL", "HIGH")]
    count = len(critical)
    if count == 0:
        return "✅ No critical stockout risks detected. Inventory levels look healthy.", "STOCKOUT_RISK", [], []

    answer = f"🚨 **{count} product(s) are at HIGH or CRITICAL stockout risk:**\n"
    for p in critical[:5]:
        answer += f"• **{p['sku']}** ({p['product_name']}) — {p['risk_level']}: {p['explanation'][:100]}...\n"

    recs = [p["recommended_action"] for p in critical[:3]]
    return answer, "STOCKOUT_RISK", critical[:5], recs

def _handle_reorder(question):
    predictions = StockoutPredictor.predict_all()
    needs_reorder = [p for p in predictions if p["recommended_reorder_quantity"] > 0 and p["risk_level"] in ("CRITICAL", "HIGH", "MEDIUM")]

    if not needs_reorder:
        return "✅ No immediate reorders are needed at this time.", "REORDER", [], []

    answer = f"📦 **{len(needs_reorder)} products need reordering:**\n"
    for p in needs_reorder[:6]:
        answer += f"• **{p['sku']}** — Reorder **{p['recommended_reorder_quantity']}** units ({p['risk_level']} risk)\n"

    recs = [f"Reorder {p['recommended_reorder_quantity']} units of {p['sku']}" for p in needs_reorder[:5]]
    return answer, "REORDER", needs_reorder[:6], recs

def _handle_bottleneck(question):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM warehouse_tasks WHERE status != 'COMPLETED';")
        tasks = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT * FROM dispatches WHERE status != 'DELIVERED';")
        dispatches = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT * FROM exceptions WHERE status != 'RESOLVED';")
        exceptions = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT * FROM orders WHERE status NOT IN ('DISPATCHED','DELIVERED','CANCELLED');")
        orders = [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

    result = BottleneckEngine.detect_bottlenecks(tasks, orders, dispatches, exceptions)
    bottlenecks = result.get("all_bottlenecks", []) if isinstance(result, dict) else []

    if not bottlenecks:
        return "✅ No significant bottlenecks detected in the warehouse right now.", "BOTTLENECK", [], []

    answer = f"⚠️ **{len(bottlenecks)} bottleneck(s) identified:**\n"
    for b in bottlenecks[:4]:
        answer += f"• **{b.get('bottleneck_area', 'Unknown')}** [{b.get('severity','')}] — {b.get('recommended_action', '')}\n"

    recs = [b.get("recommended_action", "Investigate and resolve.") for b in bottlenecks[:3]]
    return answer, "BOTTLENECK", bottlenecks[:4], recs


def _handle_allocation(question):
    order_id = _extract_order_id(question)
    conn = get_db_connection()
    try:
        if order_id:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ia.*, p.sku, p.name AS product_name, o.order_number, o.priority, o.customer_name
                FROM inventory_allocations ia
                JOIN products p ON ia.product_id = p.id
                JOIN orders o ON ia.order_id = o.id
                WHERE o.id = ? OR o.order_number = ?
                ORDER BY ia.created_at ASC;
            """, (order_id, order_id))
            allocs = cursor.fetchall()
            if allocs:
                answer = f"📦 Allocation details for **{allocs[0]['order_number']}** ({allocs[0]['customer_name']}, Priority: {allocs[0]['priority']}):\n"
                for a in allocs:
                    answer += f"• {a['product_name']} ({a['sku']}): **{a['quantity_allocated']} units** — Status: {a['status']}\n"
                return answer, "ALLOCATION", [dict(a) for a in allocs], ["Verify all allocations are fulfilled before picking."]

        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) AS cnt, SUM(quantity_allocated) AS total
            FROM inventory_allocations WHERE status != 'RELEASED';
        """)
        row = cursor.fetchone()
        answer = f"📦 Total active allocations: **{row['cnt']}** covering **{row['total'] or 0} units** across all orders."
        return answer, "ALLOCATION", [], ["Review and release stale allocations if needed."]
    finally:
        conn.close()

def _handle_exceptions(question):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM exceptions WHERE status != 'RESOLVED'
            ORDER BY CASE severity WHEN 'CRITICAL' THEN 0 WHEN 'HIGH' THEN 1 WHEN 'MEDIUM' THEN 2 ELSE 3 END;
        """)
        exceptions = [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

    if not exceptions:
        return "✅ No active exceptions or alerts in the system.", "EXCEPTIONS", [], []

    answer = f"⚠️ **{len(exceptions)} active exception(s):**\n"
    for e in exceptions[:5]:
        answer += f"• [{e['severity']}] {e['exception_type']} — {e['description'][:80]}...\n"

    recs = ["Escalate CRITICAL exceptions immediately.", "Assign exceptions to available staff for resolution."]
    return answer, "EXCEPTIONS", exceptions[:5], recs

def _handle_dispatch(question):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, o.order_number, o.customer_name, o.priority
            FROM dispatches d JOIN orders o ON d.order_id = o.id
            WHERE d.status NOT IN ('DELIVERED')
            ORDER BY d.dispatched_at DESC;
        """)
        dispatches = [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

    if not dispatches:
        return "✅ No pending dispatches. All shipments are delivered.", "DISPATCH", [], []

    answer = f"🚚 **{len(dispatches)} shipment(s) in transit:**\n"
    for d in dispatches[:5]:
        answer += f"• **{d['order_number']}** — {d['carrier']} | Tracking: {d['tracking_number']} | Status: {d['status']}\n"

    return answer, "DISPATCH", dispatches[:5], ["Contact carriers for overdue shipments."]

def _handle_inventory_risk(question):
    inventory = InventoryService.get_all_inventory()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products;")
        products = [dict(r) for r in cursor.fetchall()]
    finally:
        conn.close()

    from ai.reorder_engine import ReorderEngine
    risks = ReorderEngine.analyze_inventory_risks(products, inventory)
    low = risks.get("low_stock_products", [])
    stockouts = risks.get("stockout_risks", [])
    damaged = risks.get("damaged_inventory", [])

    answer = (
        f"📊 **Inventory Risk Summary:**\n"
        f"• 🔴 Stockouts (0 stock): **{len(stockouts)}** products\n"
        f"• 🟡 Low Stock: **{len(low)}** products\n"
        f"• 🔵 Damaged Inventory: **{len(damaged)}** records\n"
    )
    recs = ["Replenish stockouts immediately.", "Review low-stock thresholds.", "Quarantine or write off damaged inventory."]
    return answer, "INVENTORY_RISK", {"low": low[:3], "stockouts": stockouts[:3], "damaged": damaged[:3]}, recs

def _handle_general_status(question):
    orders = OrderService.get_all_orders()
    inventory = InventoryService.get_all_inventory()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) AS cnt FROM exceptions WHERE status != 'RESOLVED';")
        exc_count = cursor.fetchone()["cnt"]
        cursor.execute("SELECT COUNT(*) AS cnt FROM warehouse_tasks WHERE status NOT IN ('COMPLETED', 'CANCELLED');")
        active_tasks = cursor.fetchone()["cnt"]
        cursor.execute("SELECT COUNT(*) AS cnt FROM dispatches WHERE status NOT IN ('DELIVERED');")
        in_transit = cursor.fetchone()["cnt"]
    finally:
        conn.close()

    pending_orders = [o for o in orders if o["status"] not in ("DISPATCHED", "DELIVERED", "CANCELLED")]
    stockout_count = len(StockoutPredictor.predict_critical())

    answer = (
        f"🏭 **WareMind AI — Current Warehouse Status:**\n"
        f"• 📋 Active Orders: **{len(pending_orders)}** pending\n"
        f"• ⚠️ Exceptions: **{exc_count}** unresolved\n"
        f"• 👷 Active Tasks: **{active_tasks}**\n"
        f"• 🚚 In Transit: **{in_transit}** shipments\n"
        f"• 🔴 Stockout Risks: **{stockout_count}** critical/high\n"
    )
    recs = []
    if exc_count > 0: recs.append(f"Resolve {exc_count} active exception(s).")
    if stockout_count > 0: recs.append(f"Reorder stock for {stockout_count} at-risk product(s).")
    if active_tasks > 5: recs.append("Check picking/packing bottlenecks.")
    recs.append("Review order pipeline for delays.")
    return answer, "GENERAL_STATUS", {"active_orders": len(pending_orders), "exceptions": exc_count, "tasks": active_tasks}, recs

# ─── Public API ────────────────────────────────────────────────────────────────

INTENT_HANDLERS = {
    "ORDER_RISK": _handle_order_risk,
    "STOCKOUT_RISK": _handle_stockout_risk,
    "REORDER": _handle_reorder,
    "ALLOCATION": _handle_allocation,
    "BOTTLENECK": _handle_bottleneck,
    "TRACEABILITY": lambda q: ("Use the Product Traceability module to trace product/order journeys.", "TRACEABILITY", [], ["Navigate to Product Traceability."]),
    "EXCEPTIONS": _handle_exceptions,
    "DISPATCH": _handle_dispatch,
    "INVENTORY_RISK": _handle_inventory_risk,
    "GENERAL_STATUS": _handle_general_status,
}

SUGGESTED_QUESTIONS = [
    "Which orders are at risk today?",
    "Which products should I reorder?",
    "What are today's warehouse bottlenecks?",
    "Which products may stock out soon?",
    "Show me damaged inventory.",
    "How many active exceptions are there?",
    "What should the warehouse manager do right now?",
    "Which urgent orders are waiting for stock?",
    "Are there any dispatch delays?",
]

class WarehouseCopilot:
    """
    Deterministic AI Warehouse Copilot.
    Answers warehouse-specific questions using live database data and existing engines.
    Works fully offline — no external AI API required.
    """

    @classmethod
    def ask(cls, question: str):
        if not question or not question.strip():
            return {
                "answer": "Please ask a warehouse operations question.",
                "intent": "GENERAL_STATUS",
                "confidence": 1.0,
                "data": [],
                "recommendations": SUGGESTED_QUESTIONS,
            }

        intent, confidence = _detect_intent(question)
        handler = INTENT_HANDLERS.get(intent, _handle_general_status)

        try:
            answer, detected_intent, data, recs = handler(question)
        except Exception as e:
            logger.error(f"Copilot handler error for intent {intent}: {e}", exc_info=True)
            answer = "I encountered an error processing your query. Please try again."
            detected_intent = intent
            data = []
            recs = []

        return {
            "answer": answer,
            "intent": detected_intent,
            "confidence": round(confidence, 2),
            "data": data,
            "recommendations": recs,
            "suggested_questions": SUGGESTED_QUESTIONS[:4],
        }

    @classmethod
    def get_suggested_questions(cls):
        return SUGGESTED_QUESTIONS
