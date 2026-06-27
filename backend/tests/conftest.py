"""
Test configuration for CI.
Sets environment variables BEFORE importing the Flask app so every
module (db.py, user_manager, auth.py, …) picks up the correct settings.
"""

import os
import tempfile
import pytest

# ── Must happen before any app import ──────────────────────────────
os.environ.setdefault("JWT_SECRET_KEY", "ci-test-secret-do-not-use-in-production")
os.environ.setdefault("FLASK_ENV", "testing")

# Use a temp file DB so every test session starts fresh and there
# are no :memory: isolation issues (each sqlite3.connect() call must
# hit the same physical file for state to be shared across connections).
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
os.environ["DATABASE_PATH"] = _tmp.name


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Ensure all required tables are created in the setup test DB."""
    # Import locally to avoid circular dependencies when conftest runs too early
    from db import create_table
    from user_manager import user_manager
    from auth import token_blocklist
    from behavior_profiler import profile_manager
    from audit_logger import audit_logger
    
    create_table()
    user_manager._init_users_table()
    token_blocklist._init_table()
    profile_manager._ensure_table()
    audit_logger._init_audit_table()
    yield
    try:
        os.unlink(_tmp.name)
    except Exception:
        pass
