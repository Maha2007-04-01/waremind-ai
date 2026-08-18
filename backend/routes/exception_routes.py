from flask import Blueprint, request
from services.exception_service import ExceptionService
from utils.helpers import success_response, error_response

exception_bp = Blueprint('exceptions', __name__, url_prefix='/api/exceptions')

@exception_bp.route('', methods=['GET'])
def get_exceptions():
    """GET /api/exceptions — List all exceptions."""
    try:
        exceptions = ExceptionService.get_all_exceptions()
        return success_response(data=exceptions)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@exception_bp.route('/<string:exception_id>', methods=['GET'])
def get_exception_by_id(exception_id):
    """GET /api/exceptions/:id — Get exception details by ID."""
    try:
        exc = ExceptionService.get_exception_by_id(exception_id)
        if not exc:
            return error_response(message=f"Exception '{exception_id}' not found", status_code=404)
        return success_response(data=exc)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@exception_bp.route('/<string:exception_id>/resolve', methods=['POST'])
def resolve_exception(exception_id):
    """
    POST /api/exceptions/:id/resolve
    Executes automated Decision -> Resolution Engine for an Exception.
    """
    try:
        payload = request.get_json(silent=True) or {}
        resolution_action = payload.get('resolution_action')
        details = payload.get('details')

        resolved = ExceptionService.resolve_exception(exception_id, resolution_action, details)
        return success_response(data=resolved, message="Exception resolved successfully")
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)
