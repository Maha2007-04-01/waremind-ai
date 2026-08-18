import uuid
from datetime import datetime, timezone
from flask import jsonify

def generate_id(prefix="ID"):
    """Generates a unique prefixed ID string."""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"

def get_current_timestamp():
    """Returns current UTC ISO timestamp string."""
    return datetime.now(timezone.utc).isoformat()

def success_response(data=None, message=None, status_code=200):
    """
    Standardized JSON success response builder.
    """
    payload = {"status": "success"}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code

def error_response(message="An error occurred", status_code=400, details=None):
    """
    Standardized JSON error response builder.
    """
    payload = {
        "status": "error",
        "error": {
            "message": message,
            "code": status_code
        }
    }
    if details:
        payload["error"]["details"] = details
    return jsonify(payload), status_code
