"""
Alerts Blueprint
Routes: /send-alert  /test-alert  /alert-config  /alerts/feed
"""

import os
import logging

from flask import Blueprint, request, jsonify

from auth import token_required, role_required
from audit_logger import audit_logger
from email_service import alert_service
from team_notifications import team_notification_service as team_notifier
from db import get_db_connection

logger = logging.getLogger(__name__)

alerts_bp = Blueprint("alerts", __name__)


# -------------------------
# GET /alerts/feed
# -------------------------
@alerts_bp.route("/alerts/feed", methods=["GET"])
@token_required
def get_alerts_feed():
    """Return the most recent HIGH_RISK and LOCKED activity logs.

    Query params:
        limit  (int, default 50) — Maximum number of alerts to return.
    """
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
    except (TypeError, ValueError):
        limit = 50

    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT id, user_id, login_time, location, downloads,
               failed_attempts, risk_score, status,
               ip_address, device_fingerprint
        FROM   logs
        WHERE  status IN ('HIGH_RISK', 'LOCKED')
        ORDER  BY id DESC
        LIMIT  ?
        """,
        (limit,),
    ).fetchall()
    conn.close()

    alerts = []
    for row in rows:
        d = dict(row)
        # status may come back as None if the column was added later
        if d.get("status") is None:
            score = d.get("risk_score", 0) or 0
            d["status"] = "LOCKED" if score >= 80 else "HIGH_RISK"
        alerts.append(d)

    return jsonify(alerts)



# -------------------------
# POST /send-alert
# -------------------------
@alerts_bp.route("/send-alert", methods=["POST"])
@token_required
@role_required(["Admin"])
def send_manual_alert():
    """Manually send a high-risk alert for a user (Admin only)."""
    try:
        data = request.json or {}
        user_id = data.get("user_id")
        risk_score = data.get("risk_score", 100)
        email = data.get("email") or os.getenv("ALERT_EMAIL")

        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        alert_service.send_high_risk_alert(user_id, risk_score, email)

        audit_logger.log_action(
            request.user_id,
            request.username,
            "SEND_ALERT",
            f"user:{user_id}",
            ip_address=request.remote_addr,
        )

        return jsonify(
            {
                "message": "Email alert sent successfully",
                "user_id": user_id,
                "risk_score": risk_score,
                "email_sent": bool(email),
            }
        )

    except Exception as e:
        logger.exception("send_manual_alert failed")
        return jsonify({"error": "An unexpected error occurred"}), 500


# -------------------------
# POST /test-alert
# -------------------------
@alerts_bp.route("/test-alert", methods=["POST"])
@token_required
@role_required(["Admin"])
def test_alert():
    """Test alert channel configuration (Admin only)."""
    try:
        data = request.json or {}
        alert_type = data.get("alert_type", "email")
        recipient = data.get("recipient")

        if alert_type == "email":
            email = recipient or os.getenv("ALERT_EMAIL")
            if not email:
                return jsonify({"error": "No email configured"}), 400

            success = alert_service.send_email_alert(
                email,
                "🧪 Test Alert — User Behavior Analytics",
                "This is a test email alert. Your email configuration is working correctly!",
                "<h2>🧪 Test Alert</h2><p>Your email configuration is working correctly!</p>",
            )
            return jsonify(
                {
                    "message": "Test email sent" if success else "Failed to send email",
                    "success": success,
                    "recipient": email,
                }
            )

        if alert_type == "slack":
            success = team_notifier.send_slack_notification(
                "🧪 Test Alert",
                "Your Slack integration is working correctly!",
                "#00ff00",
            )
            return jsonify(
                {
                    "message": (
                        "Test Slack notification sent"
                        if success
                        else "Failed to send Slack notification"
                    ),
                    "success": success,
                }
            )

        if alert_type == "teams":
            success = team_notifier.send_teams_notification(
                "🧪 Test Alert", "Your Teams integration is working correctly!"
            )
            return jsonify(
                {
                    "message": (
                        "Test Teams notification sent"
                        if success
                        else "Failed to send Teams notification"
                    ),
                    "success": success,
                }
            )

        return jsonify({"error": "Invalid alert_type"}), 400

    except Exception as e:
        logger.exception("test_alert failed")
        return jsonify({"error": "An unexpected error occurred"}), 500


# -------------------------
# GET /alert-config
# -------------------------
@alerts_bp.route("/alert-config", methods=["GET"])
@token_required
@role_required(["Admin"])
def get_alert_config():
    """Get current alert channel configuration status (Admin only)."""
    return jsonify(
        {
            "email": {
                "configured": bool(
                    os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD")
                ),
                "smtp_host": os.getenv("SMTP_HOST", "Not configured"),
                "from_email": os.getenv("FROM_EMAIL", "Not configured"),
                "alert_recipient": os.getenv("ALERT_EMAIL", "Not configured"),
            },
            "sms": {
                "configured": bool(
                    os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN")
                ),
                "phone_number": os.getenv("TWILIO_PHONE_NUMBER", "Not configured"),
                "alert_recipient": os.getenv("ALERT_PHONE", "Not configured"),
            },
            "slack": {"configured": bool(os.getenv("SLACK_WEBHOOK_URL"))},
            "teams": {"configured": bool(os.getenv("TEAMS_WEBHOOK_URL"))},
        }
    )
