"""
Predictive Stockout Engine
Estimates when inventory will run out based on demand, pending orders, and safety stock.
This is distinct from the existing low-stock detection — it projects future depletion.
"""
import logging
from datetime import datetime, timedelta, timezone
from database.db import get_db_connection

logger = logging.getLogger(__name__)

RISK_LEVELS = {
    "CRITICAL": {"min": 0, "max": 0.25, "color": "red"},
    "HIGH":     {"min": 0.25, "max": 0.50, "color": "orange"},
    "MEDIUM":   {"min": 0.50, "max": 0.75, "color": "yellow"},
    "LOW":      {"min": 0.75, "max": 1.00, "color": "green"},
}

class StockoutPredictor:
    """
    Predicts which products are at risk of stocking out based on:
    - current available quantity
    - pending order demand (reserved but not yet shipped)
    - historical average daily consumption (estimated from recent orders)
    - safety stock and reorder level thresholds
    """

    @staticmethod
    def _get_pending_demand_by_product(conn):
        """Sum of unshipped order item quantities per product."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT oi.product_id, SUM(oi.requested_quantity - COALESCE(oi.allocated_quantity, 0)) AS pending_qty
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.status NOT IN ('DISPATCHED', 'DELIVERED', 'CANCELLED')
            GROUP BY oi.product_id;
        """)
        return {row["product_id"]: max(0, row["pending_qty"] or 0) for row in cursor.fetchall()}

    @staticmethod
    def _get_avg_daily_demand(conn, product_id):
        """
        Estimates average daily demand from completed orders in last 30 days.
        Falls back to reorder_level / 10 if insufficient data.
        """
        cursor = conn.cursor()
        cursor.execute("""
            SELECT SUM(oi.allocated_quantity) AS total_allocated, COUNT(DISTINCT o.id) AS order_count
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE oi.product_id = ?
              AND o.status IN ('DISPATCHED', 'DELIVERED')
              AND o.created_at >= datetime('now', '-30 days');
        """, (product_id,))
        row = cursor.fetchone()
        total_alloc = row["total_allocated"] or 0
        # Average over 30 days
        avg_daily = total_alloc / 30.0 if total_alloc > 0 else 0
        return avg_daily

    @staticmethod
    def _get_all_inventory_aggregated(conn):
        """Returns aggregate stock per product."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                p.id AS product_id,
                p.sku,
                p.name,
                p.category,
                p.reorder_level,
                p.safety_stock,
                p.unit_price,
                COALESCE(SUM(i.quantity), 0) AS total_quantity,
                COALESCE(SUM(i.reserved_quantity), 0) AS total_reserved,
                COALESCE(SUM(i.damaged_quantity), 0) AS total_damaged,
                COALESCE(SUM(i.quantity - i.reserved_quantity - i.damaged_quantity), 0) AS total_available
            FROM products p
            LEFT JOIN inventory i ON i.product_id = p.id
            GROUP BY p.id;
        """)
        return cursor.fetchall()

    @staticmethod
    def _compute_risk_score(available, avg_daily, pending_demand, safety_stock, reorder_level):
        """
        Returns a 0.0–1.0 risk score where 0 = critical, 1 = safe.
        Accounts for pending demand and average daily consumption.
        """
        effective_demand_per_day = max(avg_daily, 0.1)
        # Net available after subtracting pending demand
        net_available = max(0, available - pending_demand)

        days_remaining = net_available / effective_demand_per_day if effective_demand_per_day > 0 else 999

        # Normalise: 0 days = 0.0 (CRITICAL), 30+ days = 1.0 (LOW)
        score = min(1.0, days_remaining / 30.0)

        # Reduce score further if below safety stock
        if net_available <= safety_stock:
            score = score * 0.5

        return round(score, 3), round(days_remaining, 1)

    @staticmethod
    def _risk_level_from_score(score):
        if score < 0.25:
            return "CRITICAL"
        elif score < 0.50:
            return "HIGH"
        elif score < 0.75:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _build_explanation(product_name, sku, available, avg_daily, pending, days_remaining, risk_level, reorder_qty):
        net = max(0, available - pending)
        if risk_level == "CRITICAL":
            exp = f"{sku} ({product_name}) has critically low stock ({net} units net). "
        elif risk_level == "HIGH":
            exp = f"{sku} ({product_name}) is at high stockout risk with only {net} units available net. "
        elif risk_level == "MEDIUM":
            exp = f"{sku} ({product_name}) has moderate stockout risk with {net} units net. "
        else:
            exp = f"{sku} ({product_name}) has sufficient stock for now ({net} units net). "

        if avg_daily > 0:
            exp += f"Average daily demand is {round(avg_daily, 1)} units."
        if pending > 0:
            exp += f" Pending order demand: {pending} units."
        if days_remaining < 999:
            exp += f" Projected to stock out in approximately {int(days_remaining)} day(s)."

        action = f"Reorder {reorder_qty} units of {sku} immediately." if reorder_qty > 0 else "No immediate reorder needed."
        return exp, action

    @classmethod
    def predict_all(cls):
        """Returns predictive stockout analysis for all products."""
        conn = get_db_connection()
        try:
            products = cls._get_all_inventory_aggregated(conn)
            pending_map = cls._get_pending_demand_by_product(conn)
            results = []

            for p in products:
                pid = p["product_id"]
                available = p["total_available"]
                reserved = p["total_reserved"]
                damaged = p["total_damaged"]
                reorder_level = p["reorder_level"] or 10
                safety_stock = p["safety_stock"] or 5

                avg_daily = cls._get_avg_daily_demand(conn, pid)
                pending = pending_map.get(pid, 0)

                score, days_remaining = cls._compute_risk_score(
                    available, avg_daily, pending, safety_stock, reorder_level
                )
                risk_level = cls._risk_level_from_score(score)

                # Recommended reorder: enough for 30 days + safety
                target = max(reorder_level * 2, int(avg_daily * 30) + safety_stock)
                reorder_qty = max(0, target - available)

                stockout_date = None
                if days_remaining < 999 and avg_daily > 0:
                    stockout_date = (datetime.now(timezone.utc) + timedelta(days=days_remaining)).strftime("%Y-%m-%d")

                explanation, action = cls._build_explanation(
                    p["name"], p["sku"], available, avg_daily, pending,
                    days_remaining, risk_level, reorder_qty
                )

                results.append({
                    "product_id": pid,
                    "product_name": p["name"],
                    "sku": p["sku"],
                    "category": p["category"],
                    "current_quantity": p["total_quantity"],
                    "reserved_quantity": reserved,
                    "damaged_quantity": damaged,
                    "available_stock": available,
                    "pending_demand": pending,
                    "net_available": max(0, available - pending),
                    "avg_daily_demand": round(avg_daily, 2),
                    "projected_days_until_stockout": min(days_remaining, 999),
                    "projected_stockout_date": stockout_date,
                    "stockout_risk_score": score,
                    "risk_level": risk_level,
                    "reorder_level": reorder_level,
                    "safety_stock": safety_stock,
                    "recommended_reorder_quantity": reorder_qty,
                    "explanation": explanation,
                    "recommended_action": action
                })

            # Sort: CRITICAL > HIGH > MEDIUM > LOW
            rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            results.sort(key=lambda x: (rank.get(x["risk_level"], 4), x["stockout_risk_score"]))
            return results
        finally:
            conn.close()

    @classmethod
    def predict_one(cls, product_id):
        """Returns predictive stockout for a single product."""
        all_results = cls.predict_all()
        for r in all_results:
            if r["product_id"] == product_id:
                return r
        return None

    @classmethod
    def predict_critical(cls):
        """Returns only CRITICAL and HIGH risk products."""
        return [r for r in cls.predict_all() if r["risk_level"] in ("CRITICAL", "HIGH")]
