"""
Authentication Blueprint
Routes: /auth/login  /auth/logout  /auth/me  /auth/change-password
"""

from flask import Blueprint, request, jsonify
import logging

from auth import create_token, token_required, token_blocklist
from user_manager import user_manager
from audit_logger import audit_logger
from extensions import limiter

logger = logging.getLogger(__name__)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# -------------------------
# POST /auth/login
# -------------------------
@auth_bp.route("/login", methods=["POST"])
@limiter.limit("30 per minute")
def login():
    """User login with JWT authentication."""
    try:
        data = request.json or {}
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400

        user = user_manager.authenticate(username, password)
        if not user:
            audit_logger.log_login(None, username, False, request.remote_addr)
            return jsonify({"error": "Invalid username or password"}), 401

        token = create_token(user["id"], user["username"], user["role"])
        user_manager.update_last_login(user["id"])
        audit_logger.log_login(user["id"], user["username"], True, request.remote_addr)

        return jsonify(
            {
                "token": token,
                "user": {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "full_name": user["full_name"],
                },
            }
        )

    except Exception as e:
        logger.exception("login failed")
        return jsonify({"error": "An unexpected error occurred"}), 500


# -------------------------
# POST /auth/logout
# -------------------------
@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    """User logout — revokes the current JWT token in the DB blocklist."""
    try:
        auth_header = request.headers.get("Authorization", "")
        token = auth_header[7:] if auth_header.startswith("Bearer ") else auth_header
        if token:
            token_blocklist.revoke(token)
            # Clean up old revocations opportunistically (non-blocking)
            try:
                token_blocklist.cleanup(ttl_hours=48)
            except Exception:
                pass

        audit_logger.log_logout(request.user_id, request.username, request.remote_addr)
        return jsonify({"message": "Logged out successfully"})
    except Exception as e:
        logger.exception("logout failed")
        return jsonify({"error": "An unexpected error occurred"}), 500


# -------------------------
# GET /auth/me
# -------------------------
@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user():
    """Get current authenticated user info."""
    try:
        user = user_manager.get_user_by_id(request.user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user)
    except Exception as e:
        logger.exception("get_current_user failed")
        return jsonify({"error": "An unexpected error occurred"}), 500


# -------------------------
# POST /auth/change-password
# -------------------------
@auth_bp.route("/change-password", methods=["POST"])
@token_required
@limiter.limit("3 per minute")
def change_password():
    """Change current user's password."""
    try:
        data = request.json or {}
        old_password = data.get("old_password")
        new_password = data.get("new_password")

        if not old_password or not new_password:
            return jsonify({"error": "Old and new passwords required"}), 400

        user_manager.change_password(request.user_id, old_password, new_password)

        audit_logger.log_action(
            request.user_id,
            request.username,
            "CHANGE_PASSWORD",
            f"user:{request.user_id}",
            ip_address=request.remote_addr,
        )

        return jsonify({"message": "Password changed successfully"})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("change_password failed")
        return jsonify({"error": "An unexpected error occurred"}), 500
