"""
Authentication Module
Handles JWT token creation/validation and password hashing
"""

import jwt
import bcrypt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv

load_dotenv()

# Secret key for JWT (should be in .env file in production)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production-12345")


# ===== PASSWORD HASHING =====


def hash_password(password):
    """
    Hash password using bcrypt

    Args:
        password (str): Plain text password

    Returns:
        str: Hashed password
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(password, hashed):
    """
    Verify password against hash

    Args:
        password (str): Plain text password
        hashed (str): Hashed password

    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception as e:
        print(f"Error verifying password: {e}")
        return False


# ===== JWT TOKEN MANAGEMENT =====


def create_token(user_id, username, role, expires_in_hours=24):
    """
    Create JWT token

    Args:
        user_id (int): User ID
        username (str): Username
        role (str): User role
        expires_in_hours (int): Token expiration time

    Returns:
        str: JWT token
    """
    payload = {
        "user_id": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=expires_in_hours),
        "iat": datetime.utcnow(),
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def verify_token(token):
    """
    Verify and decode JWT token

    Args:
        token (str): JWT token

    Returns:
        dict: Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return None


# ===== AUTHENTICATION DECORATORS =====


def token_required(f):
    """
    Decorator to require valid JWT token

    Usage:
        @app.route("/protected")
        @token_required
        def protected_route():
            # Access request.user_id, request.user_role
            pass
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from Authorization header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]

            # Remove 'Bearer ' prefix if present
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
            else:
                token = auth_header

        if not token:
            return jsonify({"error": "Authentication token is missing"}), 401

        # Verify token
        payload = verify_token(token)

        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401

        # Add user info to request object
        request.user_id = payload["user_id"]
        request.username = payload["username"]
        request.user_role = payload["role"]

        return f(*args, **kwargs)

    return decorated


def role_required(allowed_roles):
    """
    Decorator to require specific role(s)

    Usage:
        @app.route("/admin")
        @token_required
        @role_required(['Admin'])
        def admin_route():
            pass

    Args:
        allowed_roles (list): List of allowed roles
    """

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Check if user has required role
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


# ===== UTILITY FUNCTIONS =====


def validate_password_strength(password):
    """
    Validate password meets security requirements

    Args:
        password (str): Password to validate

    Returns:
        tuple: (is_valid, error_message)
    """
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
    # Test the authentication module
    print("Testing Authentication Module...")

    # Test password hashing
    print("\n=== Password Hashing ===")
    password = "SecurePass123"
    hashed = hash_password(password)
    print(f"Original: {password}")
    print(f"Hashed: {hashed}")
    print(f"Verification: {verify_password(password, hashed)}")
    print(f"Wrong password: {verify_password('WrongPass', hashed)}")

    # Test token creation
    print("\n=== JWT Token ===")
    token = create_token(1, "admin", "Admin")
    print(f"Token: {token[:50]}...")

    # Test token verification
    payload = verify_token(token)
    print(f"Decoded: {payload}")

    # Test password validation
    print("\n=== Password Validation ===")
    test_passwords = [
        "weak",
        "NoNumbers",
        "nonumbers123",
        "NOLOWERCASE123",
        "ValidPass123",
    ]

    for pwd in test_passwords:
        valid, msg = validate_password_strength(pwd)
        print(f"{pwd}: {'✅ Valid' if valid else f'❌ {msg}'}")
