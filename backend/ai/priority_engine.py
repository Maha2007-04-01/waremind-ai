from datetime import datetime, timezone

class PriorityEngine:
    """
    Transparent rule-based Order Priority and Order Risk Engine for WareMind AI.
    Calculates numerical priority score (0-100+) and evaluates order SLA breach risks.
    """
    @staticmethod
    def calculate_priority(order_data):
        """
        Evaluates an order dict or Order object and returns score breakdown.
        """
        score = 0
        reasons = []

        # 1. Flag / Base Priority Weight
        explicit_priority = (order_data.get('priority') or 'NORMAL').upper()
        if explicit_priority == 'URGENT':
            score += 35
            reasons.append("Flagged as URGENT customer priority (+35 pts)")
        elif explicit_priority == 'HIGH':
            score += 25
            reasons.append("Flagged as HIGH customer priority (+25 pts)")
        elif explicit_priority == 'NORMAL':
            score += 10
            reasons.append("Standard NORMAL customer priority (+10 pts)")
        else:
            score += 0
            reasons.append("LOW customer priority (+0 pts)")

        # 2. SLA / Required-By Deadline Urgency
        required_by_str = order_data.get('required_by')
        if required_by_str:
            try:
                req_dt = datetime.fromisoformat(required_by_str.replace('Z', '+00:00'))
                if req_dt.tzinfo is None:
                    req_dt = req_dt.replace(tzinfo=timezone.utc)
                
                now = datetime.now(timezone.utc)
                diff_hours = (req_dt - now).total_seconds() / 3600.0

                if diff_hours < 0:
                    score += 50
                    reasons.append(f"OVERDUE SLA: Required deadline passed {abs(diff_hours):.1f}h ago (+50 pts)")
                elif diff_hours <= 2:
                    score += 40
                    reasons.append(f"Imminent SLA Deadline: Required within {diff_hours:.1f} hours (+40 pts)")
                elif diff_hours <= 6:
                    score += 25
                    reasons.append(f"Tight SLA Deadline: Required within {diff_hours:.1f} hours (+25 pts)")
                elif diff_hours <= 24:
                    score += 15
                    reasons.append(f"Standard SLA Deadline: Required within {diff_hours:.1f} hours (+15 pts)")
            except Exception:
                pass

        # 3. Order Monetary Value
        total_val = float(order_data.get('total_value') or 0.0)
        if total_val >= 5000:
            score += 20
            reasons.append(f"High-Value Order: Total ${total_val:,.2f} (+20 pts)")
        elif total_val >= 1000:
            score += 10
            reasons.append(f"Significant Order Value: Total ${total_val:,.2f} (+10 pts)")

        # 4. Status Triage
        status = (order_data.get('status') or 'PENDING').upper()
        if status == 'PARTIALLY_ALLOCATED':
            score += 15
            reasons.append("Order is PARTIALLY_ALLOCATED — pending bottleneck resolution (+15 pts)")

        if score >= 80:
            level = "CRITICAL"
        elif score >= 60:
            level = "HIGH"
        elif score >= 35:
            level = "MEDIUM"
        else:
            level = "LOW"

        return {
            "priority_level": level,
            "priority_score": score,
            "reasons": reasons
        }

    @staticmethod
    def analyze_order_risks(orders_list):
        """
        Analyzes order list to extract risk categories.
        """
        now = datetime.now(timezone.utc)
        delayed_orders = []
        sla_risk_orders = []
        partially_allocated_orders = []
        high_priority_shortages = []

        for o in orders_list:
            status = o.get('status', 'PENDING')
            if status in ['COMPLETED', 'DISPATCHED', 'CANCELLED']:
                continue

            order_id = o.get('id')
            order_num = o.get('order_number', order_id)
            priority = o.get('priority', 'NORMAL')
            req_str = o.get('required_by')

            diff_hours = None
            if req_str:
                try:
                    req_dt = datetime.fromisoformat(req_str.replace('Z', '+00:00'))
                    if req_dt.tzinfo is None:
                        req_dt = req_dt.replace(tzinfo=timezone.utc)
                    diff_hours = (req_dt - now).total_seconds() / 3600.0
                except Exception:
                    pass

            # Delayed orders: deadline passed and not dispatched
            if diff_hours is not None and diff_hours < 0:
                delayed_orders.append({
                    "order_id": order_id,
                    "order_number": order_num,
                    "customer_name": o.get('customer_name'),
                    "status": status,
                    "overdue_hours": round(abs(diff_hours), 1)
                })
            # SLA risk: deadline within 4 hours and order still pending picking/packing
            elif diff_hours is not None and diff_hours <= 4.0:
                sla_risk_orders.append({
                    "order_id": order_id,
                    "order_number": order_num,
                    "customer_name": o.get('customer_name'),
                    "status": status,
                    "hours_remaining": round(diff_hours, 1)
                })

            # Partially allocated orders
            if status == 'PARTIALLY_ALLOCATED':
                partially_allocated_orders.append({
                    "order_id": order_id,
                    "order_number": order_num,
                    "customer_name": o.get('customer_name'),
                    "priority": priority
                })

            # High priority orders with shortages
            if priority in ['URGENT', 'HIGH'] and status in ['PENDING', 'PARTIALLY_ALLOCATED']:
                items = o.get('items', [])
                shortage_items = [i for i in items if i.get('allocated_quantity', 0) < i.get('requested_quantity', 0)]
                if shortage_items:
                    high_priority_shortages.append({
                        "order_id": order_id,
                        "order_number": order_num,
                        "priority": priority,
                        "shortage_item_count": len(shortage_items)
                    })

        return {
            "delayed_orders": delayed_orders,
            "orders_likely_to_miss_deadline": sla_risk_orders,
            "partially_allocated_orders": partially_allocated_orders,
            "high_priority_shortages": high_priority_shortages
        }
