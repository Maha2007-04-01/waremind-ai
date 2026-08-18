from flask import Blueprint, request
from services.traceability_service import TraceabilityService
from utils.helpers import success_response, error_response

traceability_bp = Blueprint('traceability', __name__, url_prefix='/api/traceability')


@traceability_bp.route('/product/<product_id>', methods=['GET'])
def trace_product(product_id):
    """GET /api/traceability/product/<product_id> — Full lifecycle timeline for a product."""
    try:
        result = TraceabilityService.trace_product(product_id)
        if not result:
            return error_response(message=f"Product '{product_id}' not found.", status_code=404)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e), status_code=500)


@traceability_bp.route('/order/<order_id>', methods=['GET'])
def trace_order(order_id):
    """GET /api/traceability/order/<order_id> — Full lifecycle timeline for an order."""
    try:
        result = TraceabilityService.trace_order(order_id)
        if not result:
            return error_response(message=f"Order '{order_id}' not found.", status_code=404)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e), status_code=500)


@traceability_bp.route('/search', methods=['GET'])
def search_products():
    """GET /api/traceability/search?q=<query> — Search products by name or SKU."""
    try:
        q = request.args.get('q', '').strip()
        if not q or len(q) < 2:
            return error_response(message="Search query must be at least 2 characters.", status_code=400)
        results = TraceabilityService.search_products(q)
        return success_response(data=results)
    except Exception as e:
        return error_response(message=str(e), status_code=500)
