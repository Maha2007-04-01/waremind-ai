from flask import Blueprint, request
from services.dispatch_service import DispatchService
from utils.helpers import success_response, error_response

dispatch_bp = Blueprint('dispatch', __name__, url_prefix='/api/dispatch')

@dispatch_bp.route('', methods=['POST'])
def create_dispatch():
    """POST /api/dispatch — Create dispatch manifest for QC_PASSED order."""
    try:
        payload = request.get_json(silent=True) or {}
        order_id = payload.get('order_id')
        carrier = payload.get('carrier', 'FedEx Freight')

        if not order_id:
            return error_response(message="Missing required field 'order_id'", status_code=400)

        dispatch = DispatchService.create_dispatch(order_id, carrier)
        return success_response(data=dispatch, message="Dispatch manifest created successfully", status_code=201)
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@dispatch_bp.route('/<string:dispatch_id>/assign-carrier', methods=['POST'])
def assign_carrier(dispatch_id):
    """POST /api/dispatch/:id/assign-carrier — Assign carrier to dispatch."""
    try:
        payload = request.get_json(silent=True) or {}
        carrier_name = payload.get('carrier')
        if not carrier_name:
            return error_response(message="Missing required field 'carrier'", status_code=400)

        dispatch = DispatchService.assign_carrier(dispatch_id, carrier_name)
        return success_response(data=dispatch, message=f"Carrier '{carrier_name}' assigned to dispatch")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@dispatch_bp.route('/<string:dispatch_id>/dispatch', methods=['POST'])
def mark_dispatched(dispatch_id):
    """POST /api/dispatch/:id/dispatch — Finalize dispatch and deduct physical inventory."""
    try:
        dispatch = DispatchService.mark_dispatched(dispatch_id)
        return success_response(data=dispatch, message="Order dispatched and inventory finalized")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)
