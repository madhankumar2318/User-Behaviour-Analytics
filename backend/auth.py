"""
Authentication Module
Handles JWT token creation/validation, password hashing,
and DB-backed token revocation.
"""

import jwt
import bcrypt
import os
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv

load_dotenv()

# Secret key for JWT (set JWT_SECRET_KEY in .env; never use the default in production)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production-12345")


# ===== DB-BACKED TOKEN REVOCATION BLOCKLIST =====


class TokenBlocklist:
    """
    Persists revoked JWT tokens in SQLite so revocations survive server restarts.
    Includes automatic cleanup of entries older than `ttl_hours` hours.
    """

    def __init__(self, db_path: str | None = None):
        self._db_path = db_path or os.getenv("DATABASE_PATH", "database.db")
        self._init_table()

    def _conn(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_table(self):
        conn = self._conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS revoked_tokens (
                token_hash TEXT PRIMARY KEY,
                revoked_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def revoke(self, token: str) -> None:
        """Add *token* to the revocation list."""
        conn = self._conn()
        conn.execute(
            "INSERT OR IGNORE INTO revoked_tokens (token_hash) VALUES (?)",
            (token,),
        )
        conn.commit()
        conn.close()

    def is_revoked(self, token: str) -> bool:
        """Return True if *token* has been revoked."""
        conn = self._conn()
        row = conn.execute(
            "SELECT 1 FROM revoked_tokens WHERE token_hash = ?", (token,)
        ).fetchone()
        conn.close()
        return row is not None

    def cleanup(self, ttl_hours: int = 48) -> None:
        """Remove revoked-token records older than *ttl_hours* hours."""
        conn = self._conn()
        conn.execute(
            """DELETE FROM revoked_tokens
               WHERE revoked_at < datetime('now', '-' || ? || ' hours')""",
            (ttl_hours,),
        )
        conn.commit()
        conn.close()


# Global singleton — imported by route modules and token_required decorator
token_blocklist = TokenBlocklist()


# ===== PASSWORD HASHING =====


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False


# ===== JWT TOKEN MANAGEMENT =====


def create_token(user_id: int, username: str, role: str, expires_in_hours: int = 24) -> str:
    """Create a signed JWT token."""
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_token(token: str) -> dict | None:
    """Verify and decode a JWT token. Returns None on failure."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return None


# ===== AUTHENTICATION DECORATORS =====


def token_required(f):
    """
    Decorator that requires a valid, non-revoked JWT token.

    Attaches ``request.user_id``, ``request.username``, ``request.user_role``
    for use inside the decorated view function.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            token = auth_header[7:] if auth_header.startswith("Bearer ") else auth_header

        if not token:
            return jsonify({"error": "Authentication token is missing"}), 401

        # Check DB-backed revocation list (no circular import needed)
        if token_blocklist.is_revoked(token):
            return jsonify({"error": "Token has been revoked — please log in again"}), 401

        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        request.user_id = payload["user_id"]
        request.username = payload["username"]
        request.user_role = payload["role"]

        return f(*args, **kwargs)

    return decorated


def role_required(allowed_roles: list):
    """
    Decorator to require specific role(s).
    Must be applied *after* ``@token_required``.
    """

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, "user_role"):
                return jsonify({"error": "Authentication required"}), 401

            if request.user_role not in allowed_roles:
                return (
                    jsonify(
                        {
                            "error": "Insufficient permissions",
                            "required_roles": allowed_roles,
                            "your_role": request.user_role,
                        }
                    ),
                    403,
                )

            return f(*args, **kwargs)

        return decorated

    return decorator


# ===== UTILITY =====


def validate_password_strength(password: str) -> tuple[bool, str | None]:
    """Return (is_valid, error_message)."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, None


if __name__ == "__main__":
    # Quick smoke-test
    print("Testing Authentication Module...")

    password = "SecurePass123"
    hashed = hash_password(password)
    print(f"Hash OK: {verify_password(password, hashed)}")

    token = create_token(1, "admin", "Admin")
    payload = verify_token(token)
    print(f"Token decoded: {payload}")

    token_blocklist.revoke(token)
    print(f"Revoked: {token_blocklist.is_revoked(token)}")
