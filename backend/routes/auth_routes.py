from flask import Blueprint, request
from services.auth_service import AuthService
from utils.helpers import success_response, error_response

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    POST /api/auth/register
    Registers a new user into the SQLite database.
    """
    try:
        payload = request.get_json(silent=True) or {}
        result = AuthService.register_user(payload)
        return success_response(data=result, message="User registered successfully", status_code=201)
    except ValueError as ve:
        return error_response(message=str(ve), status_code=400)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    POST /api/auth/login
    Authenticates user with username/email and password.
    """
    try:
        payload = request.get_json(silent=True) or {}
        result = AuthService.login_user(payload)
        return success_response(data=result, message="Authentication successful", status_code=200)
    except ValueError as ve:
        return error_response(message=str(ve), status_code=401)
    except Exception as e:
        return error_response(message=str(e), status_code=500)

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """
    GET /api/auth/me
    Returns current user profile based on Bearer token in Authorization header.
    """
    try:
        auth_header = request.headers.get('Authorization', '')
        token = ''
        if auth_header.startswith('Bearer '):
            token = auth_header[7:].strip()
        elif auth_header:
            token = auth_header.strip()

        if not token:
            return error_response(message="Authorization token missing", status_code=401)

        user_data = AuthService.get_current_user_from_token(token)
        return success_response(data=user_data, status_code=200)
    except ValueError as ve:
        return error_response(message=str(ve), status_code=401)
    except Exception as e:
        return error_response(message=str(e), status_code=500)
