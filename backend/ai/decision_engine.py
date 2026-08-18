import logging
import os
import json
import urllib.request
from config import Config
from database.db import get_db_connection
from services.inventory_service import InventoryService
from services.order_service import OrderService
from ai.priority_engine import PriorityEngine
from ai.reorder_engine import ReorderEngine
from ai.allocation_engine import AllocationEngine
from ai.bottleneck_engine import BottleneckEngine

logger = logging.getLogger(__name__)

class DecisionEngine:
    """
    Main Proactive Decision Intelligence Orchestrator for WareMind AI.
    Analyzes live database data across orders, inventory, location tasks, exceptions, and dispatches.
    Generates deterministic structured insights with optional Gemini API enhancement.
    """
    @staticmethod
    def generate_decision_insights():
        """
        Gathers live data, executes deterministic decision engines, and formats actionable insights.
        Returns:
            dict containing:
                inventory_risks
                order_risks
                warehouse_bottlenecks
                smart_recommendations
                decision_engine_mode ("RULE_BASED" or "GEMINI_ENHANCED")
        """
        # Fetch live database data
        orders = OrderService.get_all_orders()
        inventory = InventoryService.get_all_inventory()

        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM products;")
        products = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM warehouse_tasks;")
        tasks = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM dispatches;")
        dispatches = [dict(r) for r in cursor.fetchall()]

        cursor.execute("SELECT * FROM exceptions WHERE status != 'RESOLVED';")
        exceptions = [dict(r) for r in cursor.fetchall()]

        conn.close()

        # 1. Evaluate Inventory Risks
        inventory_risks = ReorderEngine.analyze_inventory_risks(products, inventory)

        # 2. Evaluate Order Risks
        order_risks = PriorityEngine.analyze_order_risks(orders)

        # 3. Evaluate Warehouse Bottlenecks
        warehouse_bottlenecks = BottleneckEngine.detect_bottlenecks(tasks, orders, dispatches, exceptions)

        # 4. Generate Smart Recommendations (Deterministic Rules)
        smart_recommendations = DecisionEngine._build_deterministic_recommendations(
            inventory_risks, order_risks, warehouse_bottlenecks, orders, inventory
        )

        # 5. Optional Gemini LLM Enhancement
        decision_mode = "RULE_BASED"
        gemini_api_key = Config.GEMINI_API_KEY or os.environ.get('GEMINI_API_KEY')

        if gemini_api_key:
            try:
                gemini_recs = DecisionEngine._try_gemini_enhancement(
                    gemini_api_key, inventory_risks, order_risks, warehouse_bottlenecks
                )
                if gemini_recs:
                    smart_recommendations.extend(gemini_recs)
                    decision_mode = "GEMINI_ENHANCED"
            except Exception as e:
                logger.warning(f"Gemini API enhancement fallback to rule-based engine: {str(e)}")

        return {
            "inventory_risks": inventory_risks,
            "order_risks": order_risks,
            "warehouse_bottlenecks": warehouse_bottlenecks,
            "smart_recommendations": smart_recommendations,
            "decision_engine_mode": decision_mode
        }

    @staticmethod
    def _build_deterministic_recommendations(inventory_risks, order_risks, warehouse_bottlenecks, orders, inventory):
        recommendations = []

        # A. Stockout & Urgent Order Recommendation
        stockout_prods = inventory_risks.get('stockout_risks', [])
        urgent_shortages = order_risks.get('high_priority_shortages', [])
        
        if stockout_prods and urgent_shortages:
            p_first = stockout_prods[0]
            recommendations.append({
                "title": f"Critical Stockout: Reorder {p_first['sku']} Immediately",
                "severity": "CRITICAL",
                "recommendation": f"Issue emergency purchase order for product '{p_first['name']}' ({p_first['sku']}).",
                "reason": f"Product is completely OUT OF STOCK (0 units) while {len(urgent_shortages)} high-priority orders are blocked.",
                "affected_entities": {
                    "products": [p_first['sku']],
                    "orders": [s['order_number'] for s in urgent_shortages[:3]]
                },
                "expected_impact": "Unblocks critical order fulfillment and prevents imminent SLA penalty.",
                "confidence_score": 0.98
            })

        # B. Picking Zone Relocation Recommendation
        zone_recs = AllocationEngine.analyze_picking_optimization(inventory, orders)
        for z in zone_recs:
            recommendations.append(z)

        # C. Primary Bottleneck Recommendation
        primary_b = warehouse_bottlenecks.get('primary_bottleneck', {})
        if primary_b.get('bottleneck_area') != 'NONE':
            area = primary_b['bottleneck_area']
            recommendations.append({
                "title": f"Fulfillment Bottleneck Detected in {area}",
                "severity": primary_b.get('severity', 'HIGH'),
                "recommendation": primary_b.get('recommended_action', 'Reallocate warehouse staff.'),
                "reason": f"{primary_b.get('queue_count', 0)} tasks/orders queued in {area} stage.",
                "affected_entities": {
                    "orders": primary_b.get('affected_orders', [])[:5],
                    "stage": area
                },
                "expected_impact": "Clears queue congestion and restores target throughput rate.",
                "confidence_score": 0.92
            })

        # D. Delayed Order Prioritization Recommendation
        delayed = order_risks.get('delayed_orders', [])
        if delayed:
            d_first = delayed[0]
            recommendations.append({
                "title": f"Prioritize Overdue Order {d_first['order_number']}",
                "severity": "CRITICAL",
                "recommendation": f"Expedite picking and packing for Order {d_first['order_number']} ({d_first['customer_name']}).",
                "reason": f"Order is overdue by {d_first.get('overdue_hours', 0)} hours.",
                "affected_entities": {
                    "orders": [d_first['order_number']],
                    "customer": d_first['customer_name']
                },
                "expected_impact": "Minimizes customer SLA breach dissatisfaction and prevents escalation.",
                "confidence_score": 0.96
            })

        # E. Damaged Stock Triage Recommendation
        damaged = inventory_risks.get('damaged_inventory', [])
        if damaged:
            dmg_first = damaged[0]
            recommendations.append({
                "title": f"Quarantine Damaged Inventory for {dmg_first['product_sku']}",
                "severity": "MEDIUM",
                "recommendation": f"Quarantine {dmg_first['damaged_quantity']} damaged units of {dmg_first['product_name']} at location {dmg_first['location_label']}.",
                "reason": "Damaged items reduce net available stock for active orders.",
                "affected_entities": {
                    "products": [dmg_first['product_sku']],
                    "location": dmg_first['location_label']
                },
                "expected_impact": "Prevents accidental picking of damaged stock and maintains QA compliance.",
                "confidence_score": 0.90
            })

        return recommendations

    @staticmethod
    def _try_gemini_enhancement(api_key, inventory_risks, order_risks, warehouse_bottlenecks):
        """
        Optional Gemini API call for enhanced natural language executive insights.
        Returns list of recommendation dicts if successful, or None on failure/missing key.
        """
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            prompt_text = (
                "You are the WareMind AI Decision Engine. Analyze these warehouse metrics and return a JSON array of up to 2 high-impact recommendations. "
                f"Metrics: Stockouts={len(inventory_risks.get('stockout_risks', []))}, DelayedOrders={len(order_risks.get('delayed_orders', []))}, "
                f"PrimaryBottleneck={warehouse_bottlenecks.get('primary_bottleneck', {}).get('bottleneck_area')}. "
                "Output ONLY a JSON array with objects containing: title, severity, recommendation, reason, affected_entities, expected_impact, confidence_score."
            )
            
            body = {
                "contents": [{"parts": [{"text": prompt_text}]}]
            }

            req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json'}, method='POST')
            with urllib.request.urlopen(req, timeout=5) as response:
                res_data = json.loads(response.read().decode())
                text_out = res_data['candidates'][0]['content']['parts'][0]['text']
                # Parse JSON output
                clean_json = text_out.strip().strip('```json').strip('```').strip()
                recs = json.loads(clean_json)
                if isinstance(recs, list):
                    return recs
        except Exception as e:
            logger.info(f"Gemini API enhancement unavailable: {str(e)}")
        return None
