"""
ML Blueprint
Routes: /ml-stats  /train-model  /user-profile/<user_id>
"""

from flask import Blueprint, request, jsonify
import logging

from auth import token_required, role_required
from db import get_db_connection
from ml_risk_engine import ml_engine
from behavior_profiler import profile_manager

logger = logging.getLogger(__name__)

ml_bp = Blueprint("ml", __name__)


# -------------------------
# GET /ml-stats
# -------------------------
@ml_bp.route("/ml-stats", methods=["GET"])
@token_required
@role_required(["Admin"])
def get_ml_stats():
    """Get ML model statistics (Admin only)."""
    return jsonify(ml_engine.get_model_stats())


# -------------------------
# POST /train-model
# -------------------------
@ml_bp.route("/train-model", methods=["POST"])
@token_required
@role_required(["Admin"])
def train_model():
    """Manually trigger ML model training on all stored logs (Admin only)."""
    try:
        conn = get_db_connection()
        logs = conn.execute("SELECT * FROM logs").fetchall()
        conn.close()

        log_dicts = [dict(log) for log in logs]
        success = ml_engine.train(log_dicts)

        if success:
            return jsonify(
                {"message": "Model trained successfully", "logs_used": len(log_dicts)}
            )
        return (
            jsonify(
                {
                    "message": "Training failed — not enough data",
                    "logs_available": len(log_dicts),
                }
            ),
            400,
        )
    except Exception as e:
        logger.exception("train_model failed")
        return jsonify({"error": "An unexpected error occurred"}), 500


# -------------------------
# GET /user-profile/<user_id>
# -------------------------
@ml_bp.route("/user-profile/<user_id>", methods=["GET"])
@token_required
def get_user_profile(user_id):
    """Get a user's behavioural profile."""
    profile = profile_manager.get_profile(user_id)
    return jsonify(profile.to_dict())
