import logging
import base64
import json
import time
from database.db import db_transaction, get_db_connection
from utils.helpers import generate_id, get_current_timestamp
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

logger = logging.getLogger(__name__)

def _format_user_dict(row):
    if not row:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "email": row["email"],
        "name": row["name"],
        "role": row["role"],
        "created_at": row["created_at"],
        "last_login": row["last_login"]
    }

def _generate_auth_token(user_id, role):
    payload = {
        "user_id": user_id,
        "role": role,
        "iat": int(time.time()),
        "exp": int(time.time()) + (86400 * 7) # 7 days
    }
    json_bytes = json.dumps(payload).encode('utf-8')
    encoded_payload = base64.urlsafe_b64encode(json_bytes).decode('utf-8').rstrip('=')
    return f"wmtoken.{user_id}.{encoded_payload}"

def _decode_auth_token(token):
    if not token or not token.startswith("wmtoken."):
        return None
    try:
        parts = token.split(".", 2)
        if len(parts) < 3:
            return None
        user_id = parts[1]
        encoded_payload = parts[2]
        # Re-pad base64 string if needed
        padded = encoded_payload + "=" * (-len(encoded_payload) % 4)
        json_bytes = base64.urlsafe_b64decode(padded)
        payload = json.loads(json_bytes.decode('utf-8'))
        return payload.get("user_id")
    except Exception:
        return None


class AuthService:
    @staticmethod
    def register_user(data):
        """
        Registers a new user into the SQLite database.
        Checks for duplicate username and duplicate email.
        Hashes password securely using Werkzeug PBKDF2/scrypt.
        Returns auth token and user profile.
        """
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''
        role = (data.get('role') or 'MANAGER').strip().upper()

        if not name:
            raise ValueError("Full name is required")
        if not email or '@' not in email:
            raise ValueError("Valid work email address is required")
        if not username:
            raise ValueError("Username is required")
        if not password or len(password) < 4:
            raise ValueError("Password must be at least 4 characters long")

        # Map role titles to database standard role values
        role_map = {
            'ADMIN': 'ADMIN',
            'SYSTEM ADMINISTRATOR': 'ADMIN',
            'MANAGER': 'MANAGER',
            'FULFILLMENT CENTER MANAGER': 'MANAGER',
            'CUSTOMER': 'CUSTOMER',
            'ENTERPRISE CLIENT': 'CUSTOMER',
            'OPERATOR': 'OPERATOR',
            'PICKER': 'OPERATOR',
            'QUALITY CONTROL': 'OPERATOR'
        }
        clean_role = role_map.get(role, 'MANAGER')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check duplicate username
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?;", (username.lower(),))
        if cursor.fetchone():
            conn.close()
            raise ValueError("Username already exists")

        # Check duplicate email
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?;", (email,))
        if cursor.fetchone():
            conn.close()
            raise ValueError("Email already registered")

        conn.close()

        # Securely hash password
        password_hash = generate_password_hash(password)
        user_id = generate_id("USR")
        now = get_current_timestamp()

        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (id, username, email, password_hash, name, role, created_at, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (user_id, username, email, password_hash, name, clean_role, now, now))

            # Audit log
            audit_id = generate_id("AUD")
            cursor.execute("""
                INSERT INTO audit_logs (id, action, entity_type, entity_id, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (audit_id, "USER_REGISTERED", "USER", user_id, f"Registered new user '{username}' with role '{clean_role}'.", now))

        token = _generate_auth_token(user_id, clean_role)
        user_dict = {
            "id": user_id,
            "username": username,
            "email": email,
            "name": name,
            "role": clean_role,
            "created_at": now,
            "last_login": now
        }

        return {
            "token": token,
            "user": user_dict
        }

    @staticmethod
    def login_user(data):
        """
        Authenticates user using username OR email + password.
        Verifies password hash.
        Updates last_login and returns auth token + user profile.
        """
        username_or_email = (data.get('usernameOrEmail') or data.get('username') or data.get('email') or '').strip().lower()
        password = data.get('password') or ''

        if not username_or_email:
            raise ValueError("Username or email is required")
        if not password:
            raise ValueError("Password is required")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users 
            WHERE LOWER(username) = ? OR LOWER(email) = ?;
        """, (username_or_email, username_or_email))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError("Invalid username/email or password")

        # Verify password hash
        if not check_password_hash(row["password_hash"], password):
            raise ValueError("Invalid username/email or password")

        user_id = row["id"]
        role = row["role"]
        now = get_current_timestamp()

        # Update last login timestamp
        with db_transaction() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?;", (now, user_id))

        user_dict = _format_user_dict(row)
        user_dict["last_login"] = now
        token = _generate_auth_token(user_id, role)

        return {
            "token": token,
            "user": user_dict
        }

    @staticmethod
    def get_current_user_from_token(token):
        """
        Validates token and returns current user data.
        """
        user_id = _decode_auth_token(token)
        if not user_id:
            raise ValueError("Invalid or expired token")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?;", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise ValueError("User account not found")

        return _format_user_dict(row)
