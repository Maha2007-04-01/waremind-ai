from flask import Blueprint, jsonify
from services.system_service import SystemService
from utils.helpers import success_response

system_bp = Blueprint('system', __name__, url_prefix='/api')

@system_bp.route('/health', methods=['GET'])
def health_check():
    """
    GET /api/health
    Basic API health check endpoint.
    """
    return jsonify({
        "status": "ok",
        "service": "WareMind AI"
    }), 200

@system_bp.route('/system/status', methods=['GET'])
def system_status():
    """
    GET /api/system/status
    Detailed system and database status endpoint.
    """
    status_data = SystemService.get_system_status()
    return success_response(data=status_data, status_code=200)

@system_bp.route('/system/reset-demo', methods=['POST'])
def reset_demo():
    """
    POST /api/system/reset-demo
    Resets the database and re-seeds it with clean initial demo state.
    """
    status_data = SystemService.reset_demo_data()
    return success_response(data=status_data, message="Demo database reset completed successfully", status_code=200)

