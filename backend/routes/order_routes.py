from flask import Blueprint, request
from services.order_service import OrderService
from services.allocation_service import AllocationService
from utils.helpers import success_response, error_response

order_bp = Blueprint('orders', __name__, url_prefix='/api/orders')

@order_bp.route('', methods=['GET'])
def get_orders():
    """GET /api/orders — List all orders with items and transparent priority evaluations."""
    try:
        orders = OrderService.get_all_orders()
        return success_response(data=orders)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@order_bp.route('', methods=['POST'])
def create_order():
    """POST /api/orders — Create a new order with items."""
    try:
        payload = request.get_json() or {}
        new_order = OrderService.create_order(payload)
        return success_response(data=new_order, message="Order created successfully", status_code=201)
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@order_bp.route('/<string:order_id>', methods=['GET'])
def get_order_by_id(order_id):
    """GET /api/orders/:id — Get order details by ID or order_number."""
    try:
        order = OrderService.get_order_by_id(order_id)
        if not order:
            return error_response(message=f"Order '{order_id}' not found", status_code=404)
        return success_response(data=order)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@order_bp.route('/<string:order_id>/allocate', methods=['POST'])
def allocate_order(order_id):
    """
    POST /api/orders/:id/allocate
    Core Smart Allocation Decision API.
    Allocates available stock, reserves inventory, creates shortage exceptions, and logs audit trails.
    """
    try:
        allocation_result = AllocationService.allocate_order(order_id)
        return success_response(data=allocation_result, message="Allocation decision executed successfully")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@order_bp.route('/<string:order_id>/decision', methods=['GET'])
def get_order_decision_explanation(order_id):
    """
    GET /api/orders/:id/decision
    Explains priority score, stock allocation, shortages, and recommended warehouse action.
    """
    try:
        explanation = AllocationService.get_allocation_decision_explanation(order_id)
        return success_response(data=explanation)
    except ValueError as ve:
        return error_response(message=str(ve), status_code=404)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@order_bp.route('/<string:order_id>/status', methods=['PATCH'])
def update_order_status(order_id):
    """PATCH /api/orders/:id/status — Update order status."""
    try:
        payload = request.get_json() or {}
        new_status = payload.get('status')
        if not new_status:
            return error_response(message="Missing 'status' field in JSON payload", status_code=400)
        
        updated_order = OrderService.update_order_status(order_id, new_status)
        return success_response(data=updated_order, message=f"Order status updated to '{new_status}'")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)
