import os
import json
import logging
from functools import wraps
from flask import Blueprint, request, session, jsonify
from werkzeug.security import check_password_hash

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__)

CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "..", "credentials.json")
CREDENTIALS_EXAMPLE = os.path.join(os.path.dirname(__file__), "..", "credentials.json.example")

def load_credentials() -> dict:
    """Load user credentials from JSON file."""
    path = CREDENTIALS_FILE if os.path.exists(CREDENTIALS_FILE) else CREDENTIALS_EXAMPLE
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load credentials from {path}: {e}")
        return {}

def login_required(f):
    """Decorator to require session authentication for protected routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return jsonify({
                "error": "Authentication required. Please log in first.",
                "code": "UNAUTHORIZED"
            }), 401
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user with username and password, setting session cookie."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    users = load_credentials()
    hashed_pw = users.get(username)

    if not hashed_pw or not check_password_hash(hashed_pw, password):
        logger.warning(f"Failed login attempt for user: '{username}'")
        return jsonify({"error": "Invalid username or password"}), 401

    session["user"] = username
    session.permanent = True
    logger.info(f"User '{username}' logged in successfully.")
    return jsonify({
        "success": True,
        "message": "Login successful",
        "user": username
    }), 200

@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Clear user session."""
    user = session.pop("user", None)
    if user:
        logger.info(f"User '{user}' logged out.")
    return jsonify({
        "success": True,
        "message": "Logged out successfully"
    }), 200

@auth_bp.route("/me", methods=["GET"])
def current_user():
    """Get active session user status."""
    user = session.get("user")
    if user:
        return jsonify({
            "authenticated": True,
            "user": user
        }), 200
    return jsonify({
        "authenticated": False,
        "user": None
    }), 200

