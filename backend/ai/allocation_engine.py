class AllocationEngine:
    """
    Smart Inventory Allocation and Pick Path Optimization Engine for WareMind AI.
    Handles order allocations, stock reservations, shortage calculation, and picking optimization recommendations.
    """
    @staticmethod
    def evaluate_allocation(order_id, order_items, inventory_by_product):
        """
        Evaluates order allocation against available inventory.
        """
        allocations = []
        shortages = []
        exceptions_to_create = []
        reasoning_lines = []

        total_requested_units = 0
        total_allocated_units = 0

        for item in order_items:
            prod_id = item['product_id']
            requested_qty = item['requested_quantity']
            prod_name = item.get('product_name', prod_id)
            prod_sku = item.get('product_sku', 'N/A')

            total_requested_units += requested_qty

            available_locs = inventory_by_product.get(prod_id, [])
            valid_locs = [loc for loc in available_locs if loc.get('available_quantity', 0) > 0]
            valid_locs.sort(key=lambda loc: (loc.get('location_zone', 'Z'), loc.get('location_aisle', '99')))

            needed_qty = requested_qty
            item_allocated_qty = 0

            for loc in valid_locs:
                loc_avail = loc['available_quantity']
                alloc_qty = min(needed_qty, loc_avail)

                if alloc_qty > 0:
                    allocations.append({
                        "order_id": order_id,
                        "product_id": prod_id,
                        "inventory_id": loc['id'],
                        "location_id": loc['location_id'],
                        "quantity": alloc_qty,
                        "location_label": f"{loc.get('location_zone', '')}-{loc.get('location_aisle', '')}-{loc.get('location_bin', '')}"
                    })

                    item_allocated_qty += alloc_qty
                    total_allocated_units += alloc_qty
                    needed_qty -= alloc_qty
                    loc['available_quantity'] -= alloc_qty

                if needed_qty == 0:
                    break

            if needed_qty > 0:
                shortage_qty = needed_qty
                shortages.append({
                    "product_id": prod_id,
                    "product_sku": prod_sku,
                    "product_name": prod_name,
                    "requested_quantity": requested_qty,
                    "allocated_quantity": item_allocated_qty,
                    "shortage_quantity": shortage_qty
                })

                severity = "CRITICAL" if item_allocated_qty == 0 else "HIGH"
                exceptions_to_create.append({
                    "order_id": order_id,
                    "product_id": prod_id,
                    "exception_type": "INSUFFICIENT_STOCK",
                    "severity": severity,
                    "description": f"Stock shortage of {shortage_qty} units for Product '{prod_name}' (SKU: {prod_sku}). Requested: {requested_qty}, Allocated: {item_allocated_qty}."
                })

                reasoning_lines.append(
                    f"Product '{prod_name}' (SKU: {prod_sku}): Requested {requested_qty} units. "
                    f"Allocated {item_allocated_qty} units from available stock. Shortage of {shortage_qty} units identified."
                )
            else:
                reasoning_lines.append(
                    f"Product '{prod_name}' (SKU: {prod_sku}): Fully allocated {requested_qty} units from primary warehouse locations."
                )

        if total_allocated_units == total_requested_units and total_requested_units > 0:
            decision = "FULL_ALLOCATION"
            summary_reasoning = f"Full allocation achieved. All {total_requested_units} requested units allocated across inventory locations."
        elif total_allocated_units > 0:
            decision = "PARTIAL_ALLOCATION"
            summary_reasoning = f"Partial allocation executed. Allocated {total_allocated_units} of {total_requested_units} requested units. Stock shortages flagged for triage."
        else:
            decision = "UNALLOCATED_SHORTAGE"
            summary_reasoning = f"Allocation failed due to zero available stock. All {total_requested_units} requested units marked as shortages."

        full_reasoning = summary_reasoning + " Details: " + " ".join(reasoning_lines)

        return {
            "decision": decision,
            "allocations": allocations,
            "shortages": shortages,
            "exceptions_to_create": exceptions_to_create,
            "reasoning": full_reasoning
        }

    @staticmethod
    def analyze_picking_optimization(inventory_data, pending_orders):
        """
        Analyzes zone stock distribution against urgent pending orders to generate
        zone relocation recommendations.
        """
        relocation_recommendations = []
        
        # Count urgent orders requiring specific products
        urgent_product_demand = {}
        for o in pending_orders:
            if o.get('priority') in ['URGENT', 'HIGH'] and o.get('status') in ['PENDING', 'ALLOCATED', 'PICKING']:
                for item in o.get('items', []):
                    pid = item['product_id']
                    urgent_product_demand[pid] = urgent_product_demand.get(pid, 0) + item.get('requested_quantity', 1)

        # Check stock location distribution per product
        for pid, demand_qty in urgent_product_demand.items():
            locs_for_p = [inv for inv in inventory_data if inv['product_id'] == pid]
            
            fast_pick_stock = sum([loc.get('available_quantity', 0) for loc in locs_for_p if loc.get('location', {}).get('zone') == 'Zone A'])
            bulk_stock = [loc for loc in locs_for_p if loc.get('location', {}).get('zone') in ['Zone B', 'Zone C'] and loc.get('available_quantity', 0) > 0]

            if fast_pick_stock < demand_qty and bulk_stock:
                target_bulk = bulk_stock[0]
                transfer_qty = min(demand_qty - fast_pick_stock, target_bulk.get('available_quantity', 0))
                
                if transfer_qty > 0:
                    prod_sku = target_bulk.get('product', {}).get('sku', 'SKU-UNKNOWN')
                    prod_name = target_bulk.get('product', {}).get('name', 'Product')
                    source_zone = target_bulk.get('location', {}).get('zone', 'Zone B')
                    
                    relocation_recommendations.append({
                        "title": f"Relocate {transfer_qty} units of {prod_sku} to Zone A",
                        "severity": "HIGH",
                        "recommendation": f"Move {transfer_qty} units of {prod_name} ({prod_sku}) from {source_zone} to Zone A (Fast-Pick Zone).",
                        "reason": f"Zone A has urgent order demand for {demand_qty} units of {prod_sku}, but only {fast_pick_stock} units available in Zone A.",
                        "affected_entities": {
                            "product": prod_sku,
                            "source_zone": source_zone,
                            "destination_zone": "Zone A"
                        },
                        "expected_impact": "Reduces picker travel distance across zones and prevents SLA delay.",
                        "confidence_score": 0.95
                    })

        return relocation_recommendations
