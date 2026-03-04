"""
Flask Extension Instances
Declared here (without an app) so blueprints can import them without
causing circular-import issues. Bound to the Flask app via init_app()
inside app.py.
"""

from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# SocketIO — CORS origins are set in app.py via init_app()
# async_mode='gevent' replaces deprecated eventlet
socketio = SocketIO(async_mode="gevent")

# Rate limiter — default limits can be overridden per-route
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],           # No global default — apply per-route
    storage_uri="memory://",     # In-memory; swap for Redis in production
)
