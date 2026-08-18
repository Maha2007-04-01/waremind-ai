from flask import Blueprint, request
from services.qc_service import QualityCheckService
from utils.helpers import success_response, error_response

qc_bp = Blueprint('qc', __name__, url_prefix='/api/qc')

@qc_bp.route('/check', methods=['POST'])
def perform_qc_check():
    """POST /api/qc/check — Perform Quality Control inspection (PASS / FAIL)."""
    try:
        payload = request.get_json(silent=True) or {}
        order_id = payload.get('order_id')
        result = payload.get('result', 'PASS')
        notes = payload.get('notes', '')
        inspector = payload.get('inspector')

        if not order_id:
            return error_response(message="Missing required field 'order_id'", status_code=400)

        qc_res = QualityCheckService.perform_quality_check(order_id, result, notes, inspector)
        return success_response(data=qc_res, message=f"Quality check completed: {qc_res['qc_result']}")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)
