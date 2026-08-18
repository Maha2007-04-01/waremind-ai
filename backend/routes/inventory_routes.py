from flask import Blueprint, request
from services.inventory_service import InventoryService
from utils.helpers import success_response, error_response

inventory_bp = Blueprint('inventory', __name__, url_prefix='/api/inventory')

@inventory_bp.route('', methods=['GET'])
def get_inventory():
    """GET /api/inventory — List all inventory items."""
    try:
        items = InventoryService.get_all_inventory()
        return success_response(data=items)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@inventory_bp.route('/low-stock', methods=['GET'])
def get_low_stock():
    """GET /api/inventory/low-stock — List items with available stock <= reorder level."""
    try:
        items = InventoryService.get_low_stock_inventory()
        return success_response(data=items)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@inventory_bp.route('/out-of-stock', methods=['GET'])
def get_out_of_stock():
    """GET /api/inventory/out-of-stock — List items with available stock <= 0."""
    try:
        items = InventoryService.get_out_of_stock_inventory()
        return success_response(data=items)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@inventory_bp.route('/damaged', methods=['GET'])
def get_damaged():
    """GET /api/inventory/damaged — List items with damaged stock > 0."""
    try:
        items = InventoryService.get_damaged_inventory()
        return success_response(data=items)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@inventory_bp.route('/reorder-recommendations', methods=['GET'])
def get_reorder_recommendations():
    """GET /api/inventory/reorder-recommendations — Get calculated reorder suggestions for low-stock products."""
    try:
        recommendations = InventoryService.get_reorder_recommendations()
        return success_response(data=recommendations)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@inventory_bp.route('/search', methods=['GET'])
def search_inventory():
    """GET /api/inventory/search?q= — Search inventory by query string."""
    try:
        query_term = request.args.get('q', '')
        items = InventoryService.search_inventory(query_term)
        return success_response(data=items)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@inventory_bp.route('/<string:inventory_id>', methods=['GET'])
def get_inventory_by_id(inventory_id):
    """GET /api/inventory/:id — Get inventory details by ID."""
    try:
        item = InventoryService.get_inventory_by_id(inventory_id)
        if not item:
            return error_response(message=f"Inventory record '{inventory_id}' not found", status_code=404)
        return success_response(data=item)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@inventory_bp.route('/<string:inventory_id>', methods=['PATCH'])
def patch_inventory(inventory_id):
    """PATCH /api/inventory/:id — Partially update inventory fields."""
    try:
        payload = request.get_json() or {}
        updated = InventoryService.patch_inventory(inventory_id, payload)
        return success_response(data=updated, message="Inventory updated successfully")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@inventory_bp.route('/<string:inventory_id>/adjust', methods=['GET', 'POST'])
def adjust_inventory_stock(inventory_id):
    """POST /api/inventory/:id/adjust — Adjust inventory quantity."""
    if request.method == 'GET':
        item = InventoryService.get_inventory_by_id(inventory_id)
        if not item:
            return error_response(message=f"Inventory record '{inventory_id}' not found", status_code=404)
        return success_response(data=item)

    try:
        payload = request.get_json() or {}
        if 'quantity_change' not in payload and 'adjustment_quantity' not in payload:
            return error_response(message="Missing 'quantity_change' or 'adjustment_quantity' parameter", status_code=400)

        adjustment_qty = payload.get('quantity_change', payload.get('adjustment_quantity'))
        reason = payload.get('reason', 'Manual stock adjustment')

        updated = InventoryService.adjust_stock(inventory_id, adjustment_qty, reason)
        return success_response(data=updated, message="Stock adjusted successfully")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@inventory_bp.route('/<string:inventory_id>/damage', methods=['GET', 'POST'])
def report_inventory_damage(inventory_id):
    """POST /api/inventory/:id/damage — Report damaged inventory items."""
    if request.method == 'GET':
        item = InventoryService.get_inventory_by_id(inventory_id)
        if not item:
            return error_response(message=f"Inventory record '{inventory_id}' not found", status_code=404)
        return success_response(data=item)

    try:
        payload = request.get_json() or {}
        if 'damaged_quantity' not in payload and 'damaged_quantity_added' not in payload:
            return error_response(message="Missing 'damaged_quantity' or 'damaged_quantity_added' parameter", status_code=400)

        damaged_qty_add = payload.get('damaged_quantity_added', payload.get('damaged_quantity'))
        reason = payload.get('reason', 'Damaged stock reported')

        result = InventoryService.report_damage(inventory_id, damaged_qty_add, reason)
        return success_response(data=result, message="Damaged stock reported successfully")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)
