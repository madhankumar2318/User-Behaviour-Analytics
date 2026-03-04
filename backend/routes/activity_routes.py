"""
Activity Blueprint — Log, Get-Logs, Simulate
Includes the shared _run_risk_pipeline() helper (Fix 6: eliminates duplication).

Routes:
  POST /log-activity
  GET  /get-logs
  POST /simulate-activity
"""

import os
import random

from flask import Blueprint, request, jsonify

from auth import token_required, role_required
from db import get_db_connection
from extensions import socketio
from risk_engine import calculate_risk
from ml_risk_engine import ml_engine
from velocity_checker import velocity_checker
from behavior_profiler import profile_manager
from email_service import alert_service
from team_notifications import team_notification_service as team_notifier

activity_bp = Blueprint("activity", __name__)


# ===================================================
# Private helpers
# ===================================================


def _determine_status(risk_score: float) -> str:
    """Map a numeric risk score to a status label."""
    if risk_score >= 80:
        return "LOCKED"
    if risk_score >= 50:
        return "HIGH_RISK"
    return "ACTIVE"


def _run_risk_pipeline(data: dict, user_history: list) -> dict:
    """
    Run the full four-signal risk pipeline and return a results dict.

    Signals
    -------
    1. Rule-based score  (weight 0.40)
    2. ML Isolation Forest anomaly score (weight 0.30)
    3. Behaviour profile deviation score (weight 0.20)
    4. Velocity-check boost (+10 MEDIUM / +20 HIGH)
    """
    # 1. Rule-based
    base_risk_score, base_risk_reasons = calculate_risk(data, user_history)

    # 2. ML anomaly detection
    ml_score, is_anomaly, ml_confidence = ml_engine.predict_anomaly(data)
    ml_reasons = []
    if is_anomaly:
        ml_reasons.append(
            f"🤖 ML: Anomalous behavior detected "
            f"(score: {ml_score:.1f}, confidence: {ml_confidence:.1f}%)"
        )

    # 3. Velocity checks
    velocity_result = velocity_checker.perform_all_checks(data, user_history)
    velocity_reasons = velocity_result["alerts"]

    # 4. Behaviour profile deviation
    profile_score, profile_reasons = profile_manager.calculate_deviation(
        data["user_id"], data
    )
    profile_manager.update_profile(data["user_id"], user_history + [data])

    # Combine
    velocity_boost = {"HIGH": 20, "MEDIUM": 10}.get(velocity_result["severity"], 0)
    final_score = min(
        100,
        base_risk_score * 0.4
        + ml_score * 0.3
        + profile_score * 0.2
        + velocity_boost,
    )
    all_reasons = base_risk_reasons + ml_reasons + velocity_reasons + profile_reasons
    status = _determine_status(final_score)

    return {
        "final_risk_score": final_score,
        "status": status,
        "all_reasons": all_reasons,
        "is_anomaly": is_anomaly,
        "ml_score": ml_score,
        "ml_confidence": ml_confidence,
        "velocity_result": velocity_result,
    }


def _send_alerts(data: dict, status: str, final_risk_score: float) -> None:
    """Send email + webhook alerts for HIGH_RISK / LOCKED events."""
    try:
        if status in ("LOCKED", "HIGH_RISK"):
            alert_email = os.getenv("ALERT_EMAIL")
            if alert_email:
                alert_service.send_high_risk_alert(
                    user_id=data["user_id"],
                    risk_score=round(final_risk_score, 2),
                    email=alert_email,
                )
                print(f"🚨 Email alert sent for {data['user_id']} — Risk: {final_risk_score:.2f}")

        if status == "LOCKED":
            team_notifier.send_high_risk_alert(
                user_id=data["user_id"],
                risk_score=round(final_risk_score, 2),
                location=data.get("location", "Unknown"),
                slack=True,
                teams=True,
            )
    except Exception as e:
        print(f"⚠️  Alert sending failed: {e}")


def _fetch_user_history(user_id: str) -> list:
    """Return lightweight history rows for a given user_id."""
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT login_time, downloads, location, failed_attempts FROM logs WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ===================================================
# Routes
# ===================================================


# -------------------------
# POST /log-activity
# -------------------------
@activity_bp.route("/log-activity", methods=["POST"])
@token_required
@role_required(["Admin", "Analyst"])
def log_activity():
    """Log a user activity event and run the full risk pipeline."""
    data = request.json or {}

    ip_address = data.get("ip_address", request.remote_addr)
    device_fingerprint = data.get("device_fingerprint", "")

    # Persist log
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO logs
           (user_id, login_time, location, downloads, failed_attempts, ip_address, device_fingerprint)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            data["user_id"],
            data["login_time"],
            data["location"],
            data["downloads"],
            data["failed_attempts"],
            ip_address,
            device_fingerprint,
        ),
    )
    conn.commit()
    conn.close()

    user_history = _fetch_user_history(data["user_id"])
    result = _run_risk_pipeline(data, user_history)

    _send_alerts(data, result["status"], result["final_risk_score"])

    # Broadcast real-time event
    socketio.emit(
        "new_activity",
        {
            "user_id": data["user_id"],
            "login_time": data["login_time"],
            "location": data["location"],
            "downloads": data["downloads"],
            "failed_attempts": data["failed_attempts"],
            "risk_score": round(result["final_risk_score"], 2),
            "risk_reasons": result["all_reasons"],
            "status": result["status"],
            "ml_anomaly": result["is_anomaly"],
            "ml_confidence": round(result["ml_confidence"], 2),
            "velocity_alerts": result["velocity_result"]["has_alerts"],
        },
    )

    return jsonify(
        {
            "message": "Activity logged successfully",
            "risk_score": round(result["final_risk_score"], 2),
            "risk_reasons": result["all_reasons"],
            "status": result["status"],
            "ml_insights": {
                "is_anomaly": result["is_anomaly"],
                "ml_score": round(result["ml_score"], 2),
                "confidence": round(result["ml_confidence"], 2),
            },
            "velocity_insights": result["velocity_result"],
        }
    )


# -------------------------
# GET /get-logs
# -------------------------
@activity_bp.route("/get-logs", methods=["GET"])
@token_required
def get_logs():
    """Return all activity logs enriched with rule-based risk scores."""
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM logs").fetchall()
    conn.close()

    result = []
    for row in logs:
        log = dict(row)
        user_history = _fetch_user_history(log["user_id"])
        risk_score, risk_reasons = calculate_risk(log, user_history)
        log["risk_score"] = risk_score
        log["risk_reasons"] = risk_reasons
        log["status"] = _determine_status(risk_score)
        result.append(log)

    return jsonify(result)


# -------------------------
# POST /simulate-activity
# -------------------------
@activity_bp.route("/simulate-activity", methods=["POST"])
@token_required
@role_required(["Admin", "Analyst"])
def simulate_activity():
    """Generate a random user activity event and run the full risk pipeline."""
    user_ids = [f"user_{i:03d}" for i in range(1, 11)]
    locations = [
        "New York", "London", "Tokyo", "Mumbai", "Berlin",
        "Singapore", "Sydney", "Toronto", "Paris", "Dubai",
    ]

    scenario = random.choice(["normal", "normal", "normal", "moderate", "high"])
    if scenario == "normal":
        downloads = random.randint(1, 10)
        failed_attempts = 0
    elif scenario == "moderate":
        downloads = random.randint(10, 20)
        failed_attempts = random.randint(1, 3)
    else:
        downloads = random.randint(20, 50)
        failed_attempts = random.randint(3, 8)

    data = {
        "user_id": random.choice(user_ids),
        "login_time": f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}",
        "location": random.choice(locations),
        "downloads": downloads,
        "failed_attempts": failed_attempts,
        "ip_address": (
            f"{random.randint(1,255)}.{random.randint(1,255)}"
            f".{random.randint(1,255)}.{random.randint(1,255)}"
        ),
        "device_fingerprint": (
            f"FP-{random.randint(10000,99999)}"
            f"-{random.choice(['Chrome','Firefox','Safari','Edge'])}"
        ),
    }

    # Persist log
    conn = get_db_connection()
    conn.execute(
        """INSERT INTO logs
           (user_id, login_time, location, downloads, failed_attempts,
            ip_address, device_fingerprint)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            data["user_id"], data["login_time"], data["location"],
            data["downloads"], data["failed_attempts"],
            data["ip_address"], data["device_fingerprint"],
        ),
    )
    conn.commit()
    conn.close()

    user_history = _fetch_user_history(data["user_id"])
    result = _run_risk_pipeline(data, user_history)

    _send_alerts(data, result["status"], result["final_risk_score"])

    # Broadcast real-time event
    socketio.emit(
        "new_activity",
        {
            "user_id": data["user_id"],
            "login_time": data["login_time"],
            "location": data["location"],
            "downloads": data["downloads"],
            "failed_attempts": data["failed_attempts"],
            "risk_score": round(result["final_risk_score"], 2),
            "risk_reasons": result["all_reasons"],
            "status": result["status"],
            "ml_anomaly": result["is_anomaly"],
            "ml_confidence": round(result["ml_confidence"], 2),
            "velocity_alerts": result["velocity_result"]["has_alerts"],
        },
    )

    return jsonify(
        {
            "message": "Activity simulated successfully",
            "user_id": data["user_id"],
            "risk_score": round(result["final_risk_score"], 2),
            "status": result["status"],
            "ml_insights": {
                "is_anomaly": result["is_anomaly"],
                "ml_score": round(result["ml_score"], 2),
                "confidence": round(result["ml_confidence"], 2),
            },
            "velocity_insights": result["velocity_result"],
        }
    )
