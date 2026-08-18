from flask import Blueprint, request
from services.picking_service import PickingService
from utils.helpers import success_response, error_response

picking_bp = Blueprint('picking', __name__, url_prefix='/api/picking')

@picking_bp.route('/tasks', methods=['POST'])
def create_picking_task():
    """POST /api/picking/tasks — Create a picking task for an allocated order."""
    try:
        payload = request.get_json(silent=True) or {}
        order_id = payload.get('order_id')
        assigned_to = payload.get('assigned_to')
        if not order_id:
            return error_response(message="Missing required field 'order_id'", status_code=400)
            
        task = PickingService.create_picking_task(order_id, assigned_to)
        return success_response(data=task, message="Picking task created successfully", status_code=201)
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@picking_bp.route('/tasks/<string:task_id>/assign', methods=['POST'])
def assign_picker(task_id):
    """POST /api/picking/tasks/:id/assign — Assign picker worker to task."""
    try:
        payload = request.get_json(silent=True) or {}
        worker_name = payload.get('assigned_to') or payload.get('worker_name')
        if not worker_name:
            return error_response(message="Missing required field 'assigned_to'", status_code=400)

        task = PickingService.assign_picker(task_id, worker_name)
        return success_response(data=task, message=f"Assigned picker '{worker_name}' to task {task_id}")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@picking_bp.route('/tasks/<string:task_id>/start', methods=['POST'])
def start_picking(task_id):
    """POST /api/picking/tasks/:id/start — Start picking task execution."""
    try:
        task = PickingService.start_picking(task_id)
        return success_response(data=task, message="Picking started")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@picking_bp.route('/tasks/<string:task_id>/complete', methods=['POST'])
def complete_picking(task_id):
    """POST /api/picking/tasks/:id/complete — Complete picking task and update order status to PICKED."""
    try:
        updated_order = PickingService.complete_picking(task_id)
        return success_response(data=updated_order, message="Picking completed successfully")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@picking_bp.route('/tasks/<string:task_id>/report-missing', methods=['POST'])
def report_missing_item(task_id):
    """POST /api/picking/tasks/:id/report-missing — Report missing item during picking."""
    try:
        payload = request.get_json(silent=True) or {}
        product_id = payload.get('product_id')
        missing_qty = payload.get('missing_quantity', 1)
        reason = payload.get('reason', 'Missing from bin location')

        if not product_id:
            return error_response(message="Missing required field 'product_id'", status_code=400)

        result = PickingService.report_missing_item(task_id, product_id, missing_qty, reason)
        return success_response(data=result, message="Missing item reported")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@picking_bp.route('/tasks/<string:task_id>/report-damaged', methods=['POST'])
def report_damaged_item(task_id):
    """POST /api/picking/tasks/:id/report-damaged — Report damaged item during picking."""
    try:
        payload = request.get_json(silent=True) or {}
        product_id = payload.get('product_id')
        damaged_qty = payload.get('damaged_quantity', 1)
        location_id = payload.get('location_id')
        reason = payload.get('reason', 'Damaged item found on bin location')

        if not product_id:
            return error_response(message="Missing required field 'product_id'", status_code=400)

        result = PickingService.report_damaged_item(task_id, product_id, damaged_qty, location_id, reason)
        return success_response(data=result, message="Damaged item reported")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)
