from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
import sqlite3
from risk_engine import calculate_risk
import random
from datetime import datetime
import os
from dotenv import load_dotenv

# Import ML components
from ml_risk_engine import ml_engine
from velocity_checker import velocity_checker
from behavior_profiler import profile_manager

# Import Authentication components
from auth import create_token, verify_token, token_required, role_required, hash_password, verify_password
from user_manager import user_manager
from audit_logger import audit_logger

# Import Production components
from swagger_config import init_swagger
from error_handlers import register_error_handlers

# Import Alert & Notification components
from team_notifications import team_notification_service as team_notifier

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize Swagger API Documentation
swagger = init_swagger(app)

# Register error handlers
register_error_handlers(app)

socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize ML components on startup
ml_initialized = False

def initialize_ml():
    """Initialize ML model with existing data"""
    global ml_initialized
    if ml_initialized:
        return
    
    try:
        conn = get_db_connection()
        logs = conn.execute("SELECT * FROM logs").fetchall()
        conn.close()
        
        if len(logs) >= 10:
            log_dicts = [dict(log) for log in logs]
            ml_engine.train(log_dicts)
            
            # Build user profiles
            user_logs = {}
            for log in log_dicts:
                user_id = log['user_id']
                if user_id not in user_logs:
                    user_logs[user_id] = []
                user_logs[user_id].append(log)
            
            for user_id, logs_list in user_logs.items():
                profile_manager.update_profile(user_id, logs_list)
            
            print(f"✅ ML initialized with {len(logs)} logs and {len(user_logs)} user profiles")
        else:
            print(f"ℹ️ Not enough data for ML training. Need 10+, have {len(logs)}")
        
        ml_initialized = True
    except Exception as e:
        print(f"❌ Error initializing ML: {e}")


# -------------------------
# Database Connection
# -------------------------
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------
# Create Table
# -------------------------
def create_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            login_time TEXT,
            location TEXT,
            downloads INTEGER,
            failed_attempts INTEGER,
            status TEXT DEFAULT 'Active',
            ip_address TEXT,
            device_fingerprint TEXT
        )
    """)
    conn.commit()
    conn.close()

create_table()


# -------------------------
# Helper: Determine Status
# -------------------------
def determine_status(risk_score):
    if risk_score >= 80:
        return "LOCKED"
    elif risk_score >= 50:
        return "HIGH_RISK"
    else:
        return "ACTIVE"


# -------------------------
# Authentication Endpoints
# -------------------------

@app.route("/auth/login", methods=["POST"])
def login():
    """User login with JWT authentication"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Authenticate user
        user = user_manager.authenticate(username, password)
        
        if not user:
            # Log failed login
            audit_logger.log_login(None, username, False, request.remote_addr)
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Create JWT token
        token = create_token(user['id'], user['username'], user['role'])
        
        # Update last login
        user_manager.update_last_login(user['id'])
        
        # Log successful login
        audit_logger.log_login(user['id'], user['username'], True, request.remote_addr)
        
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'full_name': user['full_name']
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/auth/logout", methods=["POST"])
@token_required
def logout():
    """User logout"""
    try:
        audit_logger.log_logout(request.user_id, request.username, request.remote_addr)
        return jsonify({'message': 'Logged out successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/auth/me", methods=["GET"])
@token_required
def get_current_user():
    """Get current authenticated user info"""
    try:
        user = user_manager.get_user_by_id(request.user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/auth/change-password", methods=["POST"])
@token_required
def change_password():
    """Change current user's password"""
    try:
        data = request.json
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Old and new passwords required'}), 400
        
        user_manager.change_password(request.user_id, old_password, new_password)
        
        audit_logger.log_action(
            request.user_id,
            request.username,
            'CHANGE_PASSWORD',
            f"user:{request.user_id}",
            ip_address=request.remote_addr
        )
        
        return jsonify({'message': 'Password changed successfully'})
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------
# User Management Endpoints (Admin Only)
# -------------------------

@app.route("/users", methods=["GET"])
@token_required
@role_required(['Admin'])
def list_users():
    """List all users (Admin only)"""
    try:
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
        users = user_manager.list_users(include_inactive=include_inactive)
        
        audit_logger.log_data_access(
            request.user_id,
            request.username,
            'USERS',
            ip_address=request.remote_addr
        )
        
        return jsonify(users)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/users", methods=["POST"])
@token_required
@role_required(['Admin'])
def create_user():
    """Create new user (Admin only)"""
    try:
        data = request.json
        
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        user = user_manager.create_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            role=data.get('role', 'Viewer'),
            full_name=data.get('full_name')
        )
        
        audit_logger.log_user_action(
            request.user_id,
            request.username,
            'CREATE_USER',
            user['id'],
            request.remote_addr
        )
        
        return jsonify(user), 201
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/users/<int:user_id>", methods=["GET"])
@token_required
@role_required(['Admin'])
def get_user(user_id):
    """Get user by ID (Admin only)"""
    try:
        user = user_manager.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/users/<int:user_id>", methods=["PUT"])
@token_required
@role_required(['Admin'])
def update_user(user_id):
    """Update user (Admin only)"""
    try:
        data = request.json
        user = user_manager.update_user(user_id, data)
        
        audit_logger.log_user_action(
            request.user_id,
            request.username,
            'UPDATE_USER',
            user_id,
            request.remote_addr
        )
        
        return jsonify(user)
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/users/<int:user_id>", methods=["DELETE"])
@token_required
@role_required(['Admin'])
def delete_user(user_id):
    """Delete user (Admin only)"""
    try:
        user_manager.delete_user(user_id)
        
        audit_logger.log_user_action(
            request.user_id,
            request.username,
            'DELETE_USER',
            user_id,
            request.remote_addr
        )
        
        return jsonify({'message': 'User deleted successfully'})
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/users/<int:user_id>/reset-password", methods=["POST"])
@token_required
@role_required(['Admin'])
def reset_user_password(user_id):
    """Reset user password (Admin only)"""
    try:
        data = request.json
        new_password = data.get('new_password')
        
        if not new_password:
            return jsonify({'error': 'New password required'}), 400
        
        user_manager.reset_password(user_id, new_password)
        
        audit_logger.log_user_action(
            request.user_id,
            request.username,
            'RESET_PASSWORD',
            user_id,
            request.remote_addr
        )
        
        return jsonify({'message': 'Password reset successfully'})
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------
# Audit Log Endpoints (Admin Only)
# -------------------------

@app.route("/audit-logs", methods=["GET"])
@token_required
@role_required(['Admin'])
def get_audit_logs():
    """Get audit logs (Admin only)"""
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        action_filter = request.args.get('action')
        
        logs = audit_logger.get_all_activity(
            action_filter=action_filter,
            limit=limit,
            offset=offset
        )
        
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/audit-logs/user/<int:user_id>", methods=["GET"])
@token_required
def get_user_audit_logs(user_id):
    """Get audit logs for specific user (own logs or Admin)"""
    try:
        # Users can only view their own logs unless they're Admin
        if request.user_id != user_id and request.user_role != 'Admin':
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        logs = audit_logger.get_user_activity(user_id, limit=limit, offset=offset)
        
        return jsonify(logs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/audit-logs/statistics", methods=["GET"])
@token_required
@role_required(['Admin'])
def get_audit_statistics():
    """Get audit log statistics (Admin only)"""
    try:
        stats = audit_logger.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------
# Log Activity API
# -------------------------
@app.route("/log-activity", methods=["POST"])
@token_required
@role_required(['Admin', 'Analyst'])
def log_activity():
    data = request.json

    # Capture IP address and device fingerprint
    ip_address = data.get('ip_address', request.remote_addr)
    device_fingerprint = data.get('device_fingerprint', '')

    # Insert log
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO logs (user_id, login_time, location, downloads, failed_attempts, ip_address, device_fingerprint)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["user_id"],
        data["login_time"],
        data["location"],
        data["downloads"],
        data["failed_attempts"],
        ip_address,
        device_fingerprint
    ))
    conn.commit()
    conn.close()

    # Fetch full user history
    conn = get_db_connection()
    history = conn.execute(
        "SELECT login_time, downloads, location, failed_attempts FROM logs WHERE user_id = ?",
        (data["user_id"],)
    ).fetchall()
    conn.close()

    user_history = [dict(row) for row in history]

    # ===== ENHANCED RISK CALCULATION WITH ML =====
    
    # 1. Base rule-based risk score
    base_risk_score, base_risk_reasons = calculate_risk(data, user_history)
    
    # 2. ML Anomaly Detection
    ml_score, is_anomaly, ml_confidence = ml_engine.predict_anomaly(data)
    ml_reasons = []
    if is_anomaly:
        ml_reasons.append(f"🤖 ML: Anomalous behavior detected (score: {ml_score:.1f}, confidence: {ml_confidence:.1f}%)")
    
    # 3. Velocity Checks
    velocity_result = velocity_checker.perform_all_checks(data, user_history)
    velocity_reasons = velocity_result['alerts']
    
    # 4. Behavior Profile Deviation
    profile_score, profile_reasons = profile_manager.calculate_deviation(data['user_id'], data)
    
    # Update user profile with new activity
    profile_manager.update_profile(data['user_id'], user_history + [data])
    
    # 5. Combine all scores
    velocity_boost = 0
    if velocity_result['severity'] == 'HIGH':
        velocity_boost = 20
    elif velocity_result['severity'] == 'MEDIUM':
        velocity_boost = 10
    
    final_risk_score = (
        base_risk_score * 0.4 +
        ml_score * 0.3 +
        profile_score * 0.2 +
        velocity_boost
    )
    
    final_risk_score = min(100, final_risk_score)
    all_reasons = base_risk_reasons + ml_reasons + velocity_reasons + profile_reasons
    status = determine_status(final_risk_score)

    # ===== SEND EMAIL ALERTS FOR HIGH-RISK ACTIVITIES =====
    try:
        # Send Email alerts for LOCKED or HIGH_RISK status
        if status in ['LOCKED', 'HIGH_RISK']:
            alert_email = os.getenv('ALERT_EMAIL')
            
            if alert_email:
                alert_service.send_high_risk_alert(
                    user_id=data["user_id"],
                    risk_score=round(final_risk_score, 2),
                    email=alert_email
                )
                print(f"🚨 Email alert sent for {data['user_id']} - Risk: {final_risk_score:.2f}")
        
        # Send Slack/Teams notifications for LOCKED status
        if status == 'LOCKED':
            team_notifier.send_high_risk_alert(
                user_id=data["user_id"],
                risk_score=round(final_risk_score, 2),
                location=data.get("location", "Unknown"),
                slack=True,
                teams=True
            )
    except Exception as e:
        print(f"⚠️ Alert sending failed: {e}")
        # Don't fail the request if alerts fail

    # Emit real-time update
    socketio.emit("new_activity", {
        "user_id": data["user_id"],
        "login_time": data["login_time"],
        "location": data["location"],
        "downloads": data["downloads"],
        "failed_attempts": data["failed_attempts"],
        "risk_score": round(final_risk_score, 2),
        "risk_reasons": all_reasons,
        "status": status,
        "ml_anomaly": is_anomaly,
        "ml_confidence": round(ml_confidence, 2),
        "velocity_alerts": velocity_result['has_alerts']
    })

    return jsonify({
        "message": "Activity logged successfully",
        "risk_score": round(final_risk_score, 2),
        "risk_reasons": all_reasons,
        "status": status,
        "ml_insights": {
            "is_anomaly": is_anomaly,
            "ml_score": round(ml_score, 2),
            "confidence": round(ml_confidence, 2)
        },
        "velocity_insights": velocity_result
    })



# -------------------------
# Get All Logs
# -------------------------
@app.route("/get-logs", methods=["GET"])
@token_required
def get_logs():
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM logs").fetchall()
    conn.close()

    result = []

    for row in logs:
        log = dict(row)

        # Fetch history for that user
        conn = get_db_connection()
        history = conn.execute(
            "SELECT login_time, downloads, location, failed_attempts FROM logs WHERE user_id = ?",
            (log["user_id"],)
        ).fetchall()
        conn.close()

        user_history = [dict(h) for h in history]

        # Calculate Risk
        risk_score, risk_reasons = calculate_risk(log, user_history)

        # Determine Status
        status = determine_status(risk_score)

        log["risk_score"] = risk_score
        log["risk_reasons"] = risk_reasons
        log["status"] = status

        result.append(log)

    return jsonify(result)


# -------------------------
# Simulate Activity API
# -------------------------
@app.route("/simulate-activity", methods=["POST"])
@token_required
@role_required(['Admin', 'Analyst'])
def simulate_activity():
    # Generate random user activity
    user_ids = ["user_001", "user_002", "user_003", "user_004", "user_005", 
                "user_006", "user_007", "user_008", "user_009", "user_010"]
    locations = ["New York", "London", "Tokyo", "Mumbai", "Berlin", 
                 "Singapore", "Sydney", "Toronto", "Paris", "Dubai"]
    
    # Random data generation
    user_id = random.choice(user_ids)
    login_time = f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}"
    location = random.choice(locations)
    
    # Create different risk scenarios
    scenario = random.choice(["normal", "normal", "normal", "moderate", "high"])
    
    if scenario == "normal":
        downloads = random.randint(1, 10)
        failed_attempts = 0
    elif scenario == "moderate":
        downloads = random.randint(10, 20)
        failed_attempts = random.randint(1, 3)
    else:  # high risk
        downloads = random.randint(20, 50)
        failed_attempts = random.randint(3, 8)
    
    data = {
        "user_id": user_id,
        "login_time": login_time,
        "location": location,
        "downloads": downloads,
        "failed_attempts": failed_attempts
    }
    
    # Generate random IP and device fingerprint
    ip_address = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    device_fingerprint = f"FP-{random.randint(10000, 99999)}-{random.choice(['Chrome', 'Firefox', 'Safari', 'Edge'])}"
    
    # Insert log
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO logs (user_id, login_time, location, downloads, failed_attempts, ip_address, device_fingerprint)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["user_id"],
        data["login_time"],
        data["location"],
        data["downloads"],
        data["failed_attempts"],
        ip_address,
        device_fingerprint
    ))
    conn.commit()
    conn.close()
    
    # Fetch full user history
    conn = get_db_connection()
    history = conn.execute(
        "SELECT login_time, downloads, location, failed_attempts FROM logs WHERE user_id = ?",
        (data["user_id"],)
    ).fetchall()
    conn.close()
    
    user_history = [dict(row) for row in history]
    
    # Calculate AI Risk
    risk_score, risk_reasons = calculate_risk(data, user_history)
    
    # Determine User Status
    status = determine_status(risk_score)
    
    # ===== SEND EMAIL ALERTS FOR HIGH-RISK SIMULATED ACTIVITIES =====
    try:
        if status in ['LOCKED', 'HIGH_RISK']:
            alert_email = os.getenv('ALERT_EMAIL')
            
            if alert_email:
                alert_service.send_high_risk_alert(
                    user_id=data["user_id"],
                    risk_score=risk_score,
                    email=alert_email
                )
                print(f"🚨 Email alert sent for simulated activity: {data['user_id']} - Risk: {risk_score:.2f}")
    except Exception as e:
        print(f"⚠️ Alert sending failed: {e}")
    
    # Emit real-time update
    socketio.emit("new_activity", {
        "user_id": data["user_id"],
        "login_time": data["login_time"],
        "location": data["location"],
        "downloads": data["downloads"],
        "failed_attempts": data["failed_attempts"],
        "risk_score": risk_score,
        "risk_reasons": risk_reasons,
        "status": status
    })
    
    return jsonify({
        "message": "Activity simulated successfully",
        "user_id": data["user_id"],
        "risk_score": risk_score,
        "status": status
    })



# -------------------------
# ML API Endpoints
# -------------------------
@app.route("/ml-stats", methods=["GET"])
@token_required
@role_required(['Admin'])
def get_ml_stats():
    """Get ML model statistics"""
    return jsonify(ml_engine.get_model_stats())

@app.route("/train-model", methods=["POST"])
@token_required
@role_required(['Admin'])
def train_model():
    """Manually trigger model training"""
    try:
        conn = get_db_connection()
        logs = conn.execute("SELECT * FROM logs").fetchall()
        conn.close()
        
        log_dicts = [dict(log) for log in logs]
        success = ml_engine.train(log_dicts)
        
        if success:
            return jsonify({
                "message": "Model trained successfully",
                "logs_used": len(log_dicts)
            })
        else:
            return jsonify({
                "message": "Training failed - not enough data",
                "logs_available": len(log_dicts)
            }), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/user-profile/<user_id>", methods=["GET"])
@token_required
def get_user_profile(user_id):
    """Get user behavior profile"""
    profile = profile_manager.get_profile(user_id)
    return jsonify(profile.to_dict())


# -------------------------
# Alert Management Endpoints
# -------------------------
@app.route("/send-alert", methods=["POST"])
@token_required
@role_required(['Admin'])
def send_manual_alert():
    """
    Manually send alert for a user (Admin only)
    ---
    tags:
      - Alerts
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - user_id
            - risk_score
          properties:
            user_id:
              type: string
            risk_score:
              type: number
            email:
              type: string
            phone:
              type: string
    """
    try:
        data = request.json
        user_id = data.get('user_id')
        risk_score = data.get('risk_score', 100)
        email = data.get('email') or os.getenv('ALERT_EMAIL')
        
        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        
        # Send alert
        alert_service.send_high_risk_alert(user_id, risk_score, email)
        
        # Log the action
        audit_logger.log_action(
            request.user_id,
            request.username,
            'SEND_ALERT',
            f"user:{user_id}",
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'message': 'Email alert sent successfully',
            'user_id': user_id,
            'risk_score': risk_score,
            'email_sent': bool(email)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/test-alert", methods=["POST"])
@token_required
@role_required(['Admin'])
def test_alert():
    """
    Test alert configuration (Admin only)
    ---
    tags:
      - Alerts
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            alert_type:
              type: string
              enum: [email, sms, slack, teams]
            recipient:
              type: string
    """
    try:
        data = request.json
        alert_type = data.get('alert_type', 'email')
        recipient = data.get('recipient')
        
        if alert_type == 'email':
            email = recipient or os.getenv('ALERT_EMAIL')
            if not email:
                return jsonify({'error': 'No email configured'}), 400
            
            success = alert_service.send_email_alert(
                email,
                '🧪 Test Alert - User Behavior Analytics',
                'This is a test email alert. Your email configuration is working correctly!',
                '<h2>🧪 Test Alert</h2><p>Your email configuration is working correctly!</p>'
            )
            return jsonify({
                'message': 'Test email sent' if success else 'Failed to send email',
                'success': success,
                'recipient': email
            })
        
        elif alert_type == 'slack':
            success = team_notifier.send_slack_notification(
                '🧪 Test Alert',
                'Your Slack integration is working correctly!',
                '#00ff00'
            )
            return jsonify({
                'message': 'Test Slack notification sent' if success else 'Failed to send Slack notification',
                'success': success
            })
        
        elif alert_type == 'teams':
            success = team_notifier.send_teams_notification(
                '🧪 Test Alert',
                'Your Teams integration is working correctly!'
            )
            return jsonify({
                'message': 'Test Teams notification sent' if success else 'Failed to send Teams notification',
                'success': success
            })
        
        else:
            return jsonify({'error': 'Invalid alert_type'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route("/alert-config", methods=["GET"])
@token_required
@role_required(['Admin'])
def get_alert_config():
    """
    Get current alert configuration status (Admin only)
    ---
    tags:
      - Alerts
    """
    return jsonify({
        'email': {
            'configured': bool(os.getenv('SMTP_USER') and os.getenv('SMTP_PASSWORD')),
            'smtp_host': os.getenv('SMTP_HOST', 'Not configured'),
            'from_email': os.getenv('FROM_EMAIL', 'Not configured'),
            'alert_recipient': os.getenv('ALERT_EMAIL', 'Not configured')
        },
        'sms': {
            'configured': bool(os.getenv('TWILIO_ACCOUNT_SID') and os.getenv('TWILIO_AUTH_TOKEN')),
            'phone_number': os.getenv('TWILIO_PHONE_NUMBER', 'Not configured'),
            'alert_recipient': os.getenv('ALERT_PHONE', 'Not configured')
        },
        'slack': {
            'configured': bool(os.getenv('SLACK_WEBHOOK_URL'))
        },
        'teams': {
            'configured': bool(os.getenv('TEAMS_WEBHOOK_URL'))
        }
    })


# -------------------------
# Run Server
# -------------------------
if __name__ == "__main__":
    # Initialize ML components on startup
    initialize_ml()
    
    # Run server
    socketio.run(app, debug=True)