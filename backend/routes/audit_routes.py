"""
Audit Logs Blueprint
Routes: /audit-logs  /audit-logs/user/<id>  /audit-logs/statistics
"""

from flask import Blueprint, request, jsonify
import logging

from auth import token_required, role_required
from audit_logger import audit_logger

logger = logging.getLogger(__name__)

audit_bp = Blueprint("audit", __name__, url_prefix="/audit-logs")


# -------------------------
# GET /audit-logs
# -------------------------
@audit_bp.route("", methods=["GET"])
@token_required
@role_required(["Admin"])
def get_audit_logs():
    """Get paginated audit logs with optional action filter (Admin only)."""
    try:
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))
        action_filter = request.args.get("action")

        logs = audit_logger.get_all_activity(
            action_filter=action_filter, limit=limit, offset=offset
        )

        return jsonify(logs)
    except Exception:
        logger.exception("get_audit_logs failed")
        return jsonify({"error": "An unexpected error occurred"}), 500
# -------------------------
@audit_bp.route("/user/<int:user_id>", methods=["GET"])
@token_required
def get_user_audit_logs(user_id):
    """Get audit logs for a specific user (own logs, or Admin for any user)."""
    try:
        # Users may only view their own logs unless they are an Admin
        if request.user_id != user_id and request.user_role != "Admin":
            return jsonify({"error": "Insufficient permissions"}), 403

        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))

        logs = audit_logger.get_user_activity(user_id, limit=limit, offset=offset)

        return jsonify(logs)
    except Exception:
        logger.exception("get_user_audit_logs failed")
        return jsonify({"error": "An unexpected error occurred"}), 500


# -------------------------
# GET /audit-logs/statistics
# -------------------------
@audit_bp.route("/statistics", methods=["GET"])
@token_required
@role_required(["Admin"])
def get_audit_statistics():
    """Get audit log statistics (Admin only)."""
    try:
        stats = audit_logger.get_statistics()
        return jsonify(stats)
    except Exception:
        logger.exception("get_audit_statistics failed")
        return jsonify({"error": "An unexpected error occurred"}), 500
