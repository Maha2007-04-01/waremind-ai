from flask import Blueprint, request
from services.packing_service import PackingService
from utils.helpers import success_response, error_response

packing_bp = Blueprint('packing', __name__, url_prefix='/api/packing')

@packing_bp.route('/tasks', methods=['POST'])
def create_packing_task():
    """POST /api/packing/tasks — Create a packing task for a picked order."""
    try:
        payload = request.get_json(silent=True) or {}
        order_id = payload.get('order_id')
        assigned_to = payload.get('assigned_to')
        if not order_id:
            return error_response(message="Missing required field 'order_id'", status_code=400)

        task = PackingService.create_packing_task(order_id, assigned_to)
        return success_response(data=task, message="Packing task created successfully", status_code=201)
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@packing_bp.route('/tasks/<string:task_id>/start', methods=['POST'])
def start_packing(task_id):
    """POST /api/packing/tasks/:id/start — Start packing task."""
    try:
        task = PackingService.start_packing(task_id)
        return success_response(data=task, message="Packing started")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@packing_bp.route('/tasks/<string:task_id>/complete', methods=['POST'])
def complete_packing(task_id):
    """POST /api/packing/tasks/:id/complete — Complete packing and validate picked quantities."""
    try:
        updated_order = PackingService.complete_packing(task_id)
        return success_response(data=updated_order, message="Packing completed successfully")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)
