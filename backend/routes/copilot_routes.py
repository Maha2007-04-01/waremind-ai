from flask import Blueprint, request
from ai.warehouse_copilot import WarehouseCopilot
from utils.helpers import success_response, error_response

copilot_bp = Blueprint('copilot', __name__, url_prefix='/api/copilot')


@copilot_bp.route('/ask', methods=['POST'])
def ask_copilot():
    """
    POST /api/copilot/ask
    Body: { "question": "Which orders are at risk today?" }
    Response: { "answer": "...", "intent": "...", "confidence": 0.9, "data": [], "recommendations": [] }
    """
    try:
        payload = request.get_json(silent=True) or {}
        question = (payload.get('question') or '').strip()
        if not question:
            return error_response(message="Please provide a 'question' field in the request body.", status_code=400)
        result = WarehouseCopilot.ask(question)
        return success_response(data=result)
    except Exception as e:
        return error_response(message=str(e), status_code=500)


@copilot_bp.route('/questions', methods=['GET'])
def get_suggested_questions():
    """GET /api/copilot/questions — Returns suggested questions for the Copilot."""
    try:
        questions = WarehouseCopilot.get_suggested_questions()
        return success_response(data=questions)
    except Exception as e:
        return error_response(message=str(e), status_code=500)
