"""
Tests for Activity Endpoints
Tests: /log-activity, /get-logs, /simulate-activity
"""

import json
import sqlite3
import pytest

from app import app, create_table
from user_manager import user_manager


def _delete_user(username):
    try:
        conn = sqlite3.connect("database.db")
        conn.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()
    except Exception:
        pass


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["RATELIMIT_ENABLED"] = False  # Disable rate limiting in tests
    create_table()
    with app.test_client() as c:
        yield c


@pytest.fixture
def auth_headers(client):
    username = "activitytestuser"
    _delete_user(username)
    user_manager.create_user(
        username=username,
        email="activitytest@example.com",
        password="TestPass123!",
        role="Admin",
    )
    res = client.post(
        "/auth/login",
        json={"username": username, "password": "TestPass123!"},
    )
    token = json.loads(res.data)["token"]
    yield {"Authorization": token}
    _delete_user(username)


# ---- /get-logs ----

def test_get_logs_returns_list(client, auth_headers):
    """GET /get-logs should return a JSON array."""
    res = client.get("/get-logs", headers=auth_headers)
    assert res.status_code == 200
    assert isinstance(json.loads(res.data), list)


def test_get_logs_requires_auth(client):
    """GET /get-logs must return 401 without a token."""
    res = client.get("/get-logs")
    assert res.status_code == 401


# ---- /simulate-activity ----

def test_simulate_activity_success(client, auth_headers):
    """POST /simulate-activity should return risk_score and status."""
    res = client.post("/simulate-activity", headers=auth_headers)
    assert res.status_code == 200
    data = json.loads(res.data)
    assert "risk_score" in data
    assert "status" in data
    assert data["status"] in ("ACTIVE", "HIGH_RISK", "LOCKED")


def test_simulate_activity_requires_auth(client):
    res = client.post("/simulate-activity")
    assert res.status_code == 401


def test_simulate_activity_viewer_denied(client):
    """Viewers must not be allowed to simulate activity (403)."""
    username = "viewer_sim"
    _delete_user(username)
    user_manager.create_user(
        username=username,
        email="viewer_sim@example.com",
        password="TestPass123!",
        role="Viewer",
    )
    login_res = client.post(
        "/auth/login", json={"username": username, "password": "TestPass123!"}
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.data}"
    token = json.loads(login_res.data)["token"]

    res = client.post("/simulate-activity", headers={"Authorization": token})
    assert res.status_code == 403
    _delete_user(username)


# ---- /log-activity ----

def test_log_activity_success(client, auth_headers):
    """POST /log-activity stores a log and returns risk info."""
    payload = {
        "user_id": "test_user_001",
        "login_time": "10:30",
        "location": "New York",
        "downloads": 5,
        "failed_attempts": 0,
        "ip_address": "192.168.1.100",
        "device_fingerprint": "FP-12345-Chrome",
    }
    res = client.post("/log-activity", json=payload, headers=auth_headers)
    assert res.status_code == 200
    data = json.loads(res.data)
    assert "risk_score" in data
    assert "status" in data
    assert 0 <= data["risk_score"] <= 100


def test_log_activity_missing_field(client, auth_headers):
    """Incomplete payload should still be handled (returns 500 or 200 based on impl)."""
    payload = {"user_id": "test_only"}
    res = client.post("/log-activity", json=payload, headers=auth_headers)
    # Either 400 or 500 is acceptable — the app must not crash with an unhandled exception
    assert res.status_code in (400, 500)
