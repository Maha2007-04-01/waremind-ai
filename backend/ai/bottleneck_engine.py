class BottleneckEngine:
    """
    Fulfillment Bottleneck Engine for WareMind AI.
    Analyzes live task queues, packing backlogs, QC failures, and dispatch bottlenecks
    to identify operational constraints and recommend corrective actions.
    """
    @staticmethod
    def detect_bottlenecks(tasks_list, orders_list, dispatches_list, exceptions_list):
        """
        Analyzes live warehouse state to detect queue bottlenecks across picking, packing, QC, and dispatch.

        Returns:
            dict containing:
                primary_bottleneck: dict
                all_bottlenecks: list[dict]
        """
        bottlenecks = []

        # 1. Picking Stage Analysis
        pending_picking_tasks = [t for t in tasks_list if t.get('task_type') == 'PICKING' and t.get('status') in ['PENDING', 'IN_PROGRESS']]
        picking_affected_orders = [t.get('order_id') for t in pending_picking_tasks if t.get('order_id')]

        if len(pending_picking_tasks) >= 3:
            severity = "CRITICAL" if len(pending_picking_tasks) >= 5 else "HIGH"
            bottlenecks.append({
                "bottleneck_area": "PICKING",
                "severity": severity,
                "queue_count": len(pending_picking_tasks),
                "affected_orders": picking_affected_orders,
                "recommended_action": f"Reassign {min(2, len(pending_picking_tasks))} cross-trained workers to Zone A picking tasks to clear queue backlog."
            })

        # 2. Packing Stage Analysis
        pending_packing_tasks = [t for t in tasks_list if t.get('task_type') == 'PACKING' and t.get('status') in ['PENDING', 'IN_PROGRESS']]
        packing_affected_orders = [t.get('order_id') for t in pending_packing_tasks if t.get('order_id')]

        if len(pending_packing_tasks) >= 3:
            severity = "CRITICAL" if len(pending_packing_tasks) >= 5 else "HIGH"
            bottlenecks.append({
                "bottleneck_area": "PACKING",
                "severity": severity,
                "queue_count": len(pending_packing_tasks),
                "affected_orders": packing_affected_orders,
                "recommended_action": "Open secondary packing station #2 and activate automated barcode verification."
            })

        # 3. Quality Control (QC) Backlog Analysis
        packed_waiting_qc = [o for o in orders_list if o.get('status') == 'PACKED']
        qc_failed_orders = [o for o in orders_list if o.get('status') == 'QC_FAILED']
        qc_affected_orders = [o['id'] for o in packed_waiting_qc] + [o['id'] for o in qc_failed_orders]

        if len(packed_waiting_qc) >= 2 or len(qc_failed_orders) >= 1:
            severity = "HIGH" if len(qc_failed_orders) >= 2 or len(packed_waiting_qc) >= 4 else "MEDIUM"
            bottlenecks.append({
                "bottleneck_area": "QUALITY_CONTROL",
                "severity": severity,
                "queue_count": len(packed_waiting_qc) + len(qc_failed_orders),
                "affected_orders": qc_affected_orders,
                "recommended_action": f"Prioritize QC inspection for {len(packed_waiting_qc)} packed orders and resolve {len(qc_failed_orders)} failed packaging exceptions."
            })

        # 4. Dispatch Backlog Analysis
        qc_passed_waiting_dispatch = [o for o in orders_list if o.get('status') == 'QC_PASSED']
        preparing_dispatches = [d for d in dispatches_list if d.get('status') == 'PREPARING']
        dispatch_affected_orders = [o['id'] for o in qc_passed_waiting_dispatch]

        if len(qc_passed_waiting_dispatch) >= 2 or len(preparing_dispatches) >= 2:
            severity = "HIGH" if len(qc_passed_waiting_dispatch) >= 4 else "MEDIUM"
            bottlenecks.append({
                "bottleneck_area": "DISPATCH",
                "severity": severity,
                "queue_count": len(qc_passed_waiting_dispatch),
                "affected_orders": dispatch_affected_orders,
                "recommended_action": "Assign carriers and generate dispatch shipping manifests to release orders for loading."
            })

        # 5. Stock Allocation Shortage Bottleneck
        shortage_orders = [o for o in orders_list if o.get('status') == 'PARTIALLY_ALLOCATED']
        if len(shortage_orders) >= 2:
            bottlenecks.append({
                "bottleneck_area": "STOCK_ALLOCATION",
                "severity": "HIGH",
                "queue_count": len(shortage_orders),
                "affected_orders": [o['id'] for o in shortage_orders],
                "recommended_action": "Review inventory reorder recommendations and approve partial pick dispatch for urgent lines."
            })

        # Determine primary bottleneck (highest severity)
        severity_map = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        bottlenecks.sort(key=lambda b: severity_map.get(b['severity'], 4))

        primary_bottleneck = bottlenecks[0] if bottlenecks else {
            "bottleneck_area": "NONE",
            "severity": "LOW",
            "queue_count": 0,
            "affected_orders": [],
            "recommended_action": "All fulfillment pipeline queues operating within optimal performance thresholds."
        }

        return {
            "primary_bottleneck": primary_bottleneck,
            "all_bottlenecks": bottlenecks
        }
