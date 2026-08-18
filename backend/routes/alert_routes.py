from flask import Blueprint, jsonify

alert_bp = Blueprint('alerts', __name__, url_prefix='/api/alerts')

@alert_bp.route('', methods=['GET'])
def get_alerts():
    return jsonify({"status": "success", "data": []}), 200
