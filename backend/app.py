"""
User Behavior Analytics — Main Application
==========================================
This file is now a *slim factory* (~100 lines).
All route logic lives in the routes/ blueprints.

Blueprint layout
----------------
  auth_routes    →  /auth/*
  user_routes    →  /users/*
  audit_routes   →  /audit-logs/*
  activity_routes→  /log-activity  /get-logs  /simulate-activity
  ml_routes      →  /ml-stats  /train-model  /user-profile/*
  alert_routes   →  /send-alert  /test-alert  /alert-config
"""

import os
from datetime import datetime

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from db import get_db_connection, create_table
from extensions import socketio, limiter
from swagger_config import init_swagger
from error_handlers import register_error_handlers
from ml_risk_engine import ml_engine
from behavior_profiler import profile_manager

# Register blueprints
from routes.auth_routes import auth_bp
from routes.user_routes import users_bp
from routes.audit_routes import audit_bp
from routes.activity_routes import activity_bp
from routes.ml_routes import ml_bp
from routes.alert_routes import alerts_bp
from routes.report_routes import report_bp

load_dotenv()

# -------------------------
# CORS origins
# -------------------------
_cors_origins_env = os.getenv(
    "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
)
_cors_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]

# -------------------------
# Flask app
# -------------------------
app = Flask(__name__)
CORS(app, origins=_cors_origins, supports_credentials=True)

# Bind extensions to this app
socketio.init_app(app, cors_allowed_origins=_cors_origins)
limiter.init_app(app)

# Swagger API docs & global error handlers
init_swagger(app)
register_error_handlers(app)

# -------------------------
# Register blueprints
# -------------------------
app.register_blueprint(auth_bp)
app.register_blueprint(users_bp)
app.register_blueprint(audit_bp)
app.register_blueprint(activity_bp)
app.register_blueprint(ml_bp)
app.register_blueprint(alerts_bp)
app.register_blueprint(report_bp)

# -------------------------
# Health check
# -------------------------
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Docker / load-balancer probes."""
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        return jsonify(
            {
                "status": "ok",
                "ml_ready": ml_engine.is_trained,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 503


# -------------------------
# DB & ML initialisation
# -------------------------
def initialize_ml():
    """Train the ML model on startup if enough history exists."""
    try:
        conn = get_db_connection()
        logs = conn.execute("SELECT * FROM logs").fetchall()
        conn.close()

        if len(logs) >= 10:
            log_dicts = [dict(log) for log in logs]
            ml_engine.train(log_dicts)

            user_logs: dict = {}
            for log in log_dicts:
                user_logs.setdefault(log["user_id"], []).append(log)

            for uid, logs_list in user_logs.items():
                profile_manager.update_profile(uid, logs_list)

            print(
                f"✅ ML initialised with {len(logs)} logs "
                f"and {len(user_logs)} user profiles"
            )
        else:
            print(f"ℹ️  Not enough data for ML training. Need 10+, have {len(logs)}")
    except Exception as e:
        print(f"❌ Error initialising ML: {e}")


# Ensure logs table exists every time the module is imported (including tests)
create_table()

if __name__ == "__main__":
    initialize_ml()
    # use_reloader=False required: gevent and Werkzeug's reloader are incompatible
    socketio.run(app, debug=True, use_reloader=False)
