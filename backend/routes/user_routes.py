"""
User Management Blueprint  (Admin only)
Routes: /users  /users/<id>  /users/<id>/reset-password
"""

from flask import Blueprint, request, jsonify
import logging

from auth import token_required, role_required
from user_manager import user_manager
from audit_logger import audit_logger

logger = logging.getLogger(__name__)

users_bp = Blueprint("users", __name__, url_prefix="/users")


# -------------------------
# GET /users
# -------------------------
@users_bp.route("", methods=["GET"])
@token_required
@role_required(["Admin"])
def list_users():
    """List all users (Admin only)."""
    try:
        include_inactive = (
            request.args.get("include_inactive", "false").lower() == "true"
        )
        users = user_manager.list_users(include_inactive=include_inactive)

        audit_logger.log_data_access(
            request.user_id, request.username, "USERS", ip_address=request.remote_addr
        )

        return jsonify(users)
    except Exception as e:
        logger.exception("list_users failed")
        return jsonify({"error": "An unexpected error occurred"}), 500


# -------------------------
# POST /users
# -------------------------
@users_bp.route("", methods=["POST"])
@token_required
@role_required(["Admin"])
def create_user():
    """Create a new user (Admin only)."""
    try:
        data = request.json or {}

        for field in ("username", "email", "password"):
            if field not in data:
                return jsonify({"error": f"{field} is required"}), 400

        user = user_manager.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password"],
            role=data.get("role", "Viewer"),
            full_name=data.get("full_name"),
        )

        audit_logger.log_user_action(
            request.user_id,
            request.username,
            "CREATE_USER",
            user["id"],
            request.remote_addr,
        )

        return jsonify(user), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("create_user failed")
        return jsonify({"error": "An unexpected error occurred"}), 500


# -------------------------
# GET /users/<id>
# -------------------------
@users_bp.route("/<int:user_id>", methods=["GET"])
@token_required
@role_required(["Admin"])
def get_user(user_id):
    """Get user by ID (Admin only)."""
    try:
        user = user_manager.get_user_by_id(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify(user)
    except Exception as e:
        logger.exception("get_user failed")
        return jsonify({"error": "An unexpected error occurred"}), 500


# -------------------------
# PUT /users/<id>
# -------------------------
@users_bp.route("/<int:user_id>", methods=["PUT"])
@token_required
@role_required(["Admin"])
def update_user(user_id):
    """Update user (Admin only)."""
    try:
        data = request.json or {}
        user = user_manager.update_user(user_id, data)

        audit_logger.log_user_action(
            request.user_id,
            request.username,
            "UPDATE_USER",
            user_id,
            request.remote_addr,
        )

        return jsonify(user)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("update_user failed")
        return jsonify({"error": "An unexpected error occurred"}), 500


# -------------------------
# DELETE /users/<id>
# -------------------------
@users_bp.route("/<int:user_id>", methods=["DELETE"])
@token_required
@role_required(["Admin"])
def delete_user(user_id):
    """Delete user (Admin only)."""
    try:
        user_manager.delete_user(user_id)

        audit_logger.log_user_action(
            request.user_id,
            request.username,
            "DELETE_USER",
            user_id,
            request.remote_addr,
        )

        return jsonify({"message": "User deleted successfully"})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("delete_user failed")
        return jsonify({"error": "An unexpected error occurred"}), 500


# -------------------------
# POST /users/<id>/reset-password
# -------------------------
@users_bp.route("/<int:user_id>/reset-password", methods=["POST"])
@token_required
@role_required(["Admin"])
def reset_user_password(user_id):
    """Reset user password (Admin only)."""
    try:
        data = request.json or {}
        new_password = data.get("new_password")

        if not new_password:
            return jsonify({"error": "New password required"}), 400

        user_manager.reset_password(user_id, new_password)

        audit_logger.log_user_action(
            request.user_id,
            request.username,
            "RESET_PASSWORD",
            user_id,
            request.remote_addr,
        )

        return jsonify({"message": "Password reset successfully"})

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception("reset_user_password failed")
        return jsonify({"error": "An unexpected error occurred"}), 500
