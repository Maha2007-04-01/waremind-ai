class ReorderEngine:
    """
    Analyzes product stock velocity, reorder thresholds, safety stock requirements,
    and inventory risk categories (low stock, stockouts, excess, damaged).
    """
    @staticmethod
    def evaluate_reorder_needs(low_stock_products):
        """
        Calculates reorder metrics for low-stock products.
        """
        recommendations = []
        for prod in low_stock_products:
            avail = prod.get('total_available', 0)
            reorder_lvl = prod.get('reorder_level', 10)
            safety = prod.get('safety_stock', 5)

            if avail <= reorder_lvl:
                target_stock = reorder_lvl + (safety * 2)
                suggested_qty = max(0, target_stock - avail)

                if avail <= 0:
                    urgency = "CRITICAL"
                elif avail <= safety:
                    urgency = "HIGH"
                else:
                    urgency = "MEDIUM"

                recommendations.append({
                    "product_id": prod.get('product_id'),
                    "sku": prod.get('sku'),
                    "product_name": prod.get('name'),
                    "current_available_stock": avail,
                    "reorder_level": reorder_lvl,
                    "safety_stock": safety,
                    "suggested_reorder_quantity": suggested_qty,
                    "urgency": urgency
                })

        urgency_rank = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}
        recommendations.sort(key=lambda x: urgency_rank.get(x['urgency'], 3))
        return recommendations

    @staticmethod
    def analyze_inventory_risks(products_data, inventory_data):
        """
        Analyzes products and inventory to classify risk segments:
        - Low stock products
        - Stockout risks (0 stock)
        - Excess inventory (> 5x reorder level)
        - Damaged inventory
        """
        low_stock = []
        stockouts = []
        excess = []
        damaged = []

        # Product level aggregation
        prod_stock_map = {}
        for item in inventory_data:
            pid = item['product_id']
            if pid not in prod_stock_map:
                prod_stock_map[pid] = {
                    "total_quantity": 0,
                    "reserved_quantity": 0,
                    "damaged_quantity": 0,
                    "available_quantity": 0
                }
            prod_stock_map[pid]["total_quantity"] += item.get('quantity', 0)
            prod_stock_map[pid]["reserved_quantity"] += item.get('reserved_quantity', 0)
            prod_stock_map[pid]["damaged_quantity"] += item.get('damaged_quantity', 0)
            prod_stock_map[pid]["available_quantity"] += item.get('available_quantity', 0)

            if item.get('damaged_quantity', 0) > 0:
                damaged.append({
                    "inventory_id": item['id'],
                    "product_id": item['product_id'],
                    "product_sku": item.get('product', {}).get('sku', 'N/A'),
                    "product_name": item.get('product', {}).get('name', 'N/A'),
                    "location_label": f"{item.get('location', {}).get('zone', '')}-{item.get('location', {}).get('aisle', '')}",
                    "damaged_quantity": item['damaged_quantity']
                })

        for p in products_data:
            pid = p['id']
            reorder_lvl = p.get('reorder_level', 10)
            stock_info = prod_stock_map.get(pid, {"total_quantity": 0, "reserved_quantity": 0, "damaged_quantity": 0, "available_quantity": 0})
            avail = stock_info["available_quantity"]

            p_summary = {
                "product_id": pid,
                "sku": p.get('sku'),
                "name": p.get('name'),
                "category": p.get('category'),
                "available_stock": avail,
                "reorder_level": reorder_lvl
            }

            if avail <= 0:
                stockouts.append(p_summary)
            elif avail <= reorder_lvl:
                low_stock.append(p_summary)
            elif avail >= (reorder_lvl * 5):
                excess.append({
                    **p_summary,
                    "excess_multiplier": round(avail / max(1, reorder_lvl), 1)
                })

        return {
            "low_stock_products": low_stock,
            "stockout_risks": stockouts,
            "excess_inventory": excess,
            "damaged_inventory": damaged
        }
