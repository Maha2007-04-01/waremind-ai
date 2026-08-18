from flask import Blueprint, request
from ai.stockout_predictor import StockoutPredictor
from utils.helpers import success_response, error_response

stockout_bp = Blueprint('predictive_stockout', __name__, url_prefix='/api/predictive-stockout')


@stockout_bp.route('', methods=['GET'])
def get_all_predictions():
    """GET /api/predictive-stockout — All products with stockout risk predictions."""
    try:
        results = StockoutPredictor.predict_all()
        return success_response(data=results)
    except Exception as e:
        return error_response(message=str(e), status_code=500)


@stockout_bp.route('/critical', methods=['GET'])
def get_critical_predictions():
    """GET /api/predictive-stockout/critical — Only CRITICAL and HIGH risk products."""
    try:
        results = StockoutPredictor.predict_critical()
        return success_response(data=results)
    except Exception as e:
        return error_response(message=str(e), status_code=500)


@stockout_bp.route('/<product_id>', methods=['GET'])
def get_product_prediction(product_id):
    """GET /api/predictive-stockout/<product_id> — Prediction for a single product."""
    try:
        result = StockoutPredictor.predict_one(product_id)
        if not result:
            return error_response(message=f"Product '{product_id}' not found.", status_code=404)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e), status_code=500)
