"""
Tests for Risk Engine Components
Tests: VelocityChecker, MLRiskEngine
"""

import os
import numbers
import pytest

from velocity_checker import VelocityChecker
from ml_risk_engine import MLRiskEngine


# ---------------------------------------------------------------------------
# VelocityChecker
# ---------------------------------------------------------------------------

class TestVelocityChecker:
    def setup_method(self):
        self.checker = VelocityChecker()

    # --- rapid logins ---

    def test_rapid_logins_detected(self):
        history = [
            {"login_time": "10:00", "location": "New York"},
            {"login_time": "10:02", "location": "New York"},
            {"login_time": "10:04", "location": "New York"},
        ]
        is_rapid, msg = self.checker.check_rapid_logins("u1", "10:05", history)
        assert is_rapid is True
        assert msg is not None

    def test_no_rapid_logins_spread_out(self):
        history = [{"login_time": "09:00", "location": "New York"}]
        is_rapid, _ = self.checker.check_rapid_logins("u1", "11:00", history)
        assert is_rapid is False

    def test_rapid_logins_empty_history(self):
        is_rapid, _ = self.checker.check_rapid_logins("u1", "10:00", [])
        assert is_rapid is False

    # --- impossible travel ---

    def test_impossible_travel_detected(self):
        last = {"login_time": "10:00", "location": "New York"}
        current = {"login_time": "10:30", "location": "Tokyo"}
        is_imp, msg = self.checker.check_impossible_travel(current, last)
        assert is_imp is True
        assert "km" in msg.lower() or "impossible" in msg.lower()

    def test_same_location_is_not_impossible(self):
        last = {"login_time": "10:00", "location": "London"}
        current = {"login_time": "10:05", "location": "London"}
        is_imp, _ = self.checker.check_impossible_travel(current, last)
        assert is_imp is False

    def test_realistic_travel_not_flagged(self):
        """London → Paris in 3 hours is perfectly feasible."""
        last = {"login_time": "08:00", "location": "London"}
        current = {"login_time": "11:00", "location": "Paris"}
        is_imp, _ = self.checker.check_impossible_travel(current, last)
        assert is_imp is False

    def test_impossible_travel_no_last_log(self):
        current = {"login_time": "10:00", "location": "New York"}
        is_imp, _ = self.checker.check_impossible_travel(current, None)
        assert is_imp is False

    # --- concurrent sessions ---

    def test_concurrent_sessions_detected(self):
        history = [
            {"login_time": "10:00", "location": "New York"},
            {"login_time": "10:10", "location": "London"},
        ]
        current = {"user_id": "u1", "login_time": "10:20", "location": "Tokyo"}
        is_conc, msg = self.checker.check_concurrent_sessions("u1", "10:20", history)
        assert is_conc is True

    # --- perform_all_checks ---

    def test_perform_all_checks_structure(self):
        current = {"user_id": "u1", "login_time": "10:00", "location": "New York"}
        result = self.checker.perform_all_checks(current, [])
        assert "has_alerts" in result
        assert "alerts" in result
        assert isinstance(result["alerts"], list)
        assert result["severity"] in ("LOW", "MEDIUM", "HIGH")

    def test_perform_all_checks_impossible_travel_high_severity(self):
        history = [{"login_time": "10:00", "location": "New York"}]
        current = {"user_id": "u1", "login_time": "10:30", "location": "Tokyo"}
        result = self.checker.perform_all_checks(current, history)
        assert result["severity"] == "HIGH"
        assert result["has_alerts"] is True


# ---------------------------------------------------------------------------
# MLRiskEngine
# ---------------------------------------------------------------------------

class TestMLRiskEngine:
    def setup_method(self):
        # Use a temp model path so we don't pollute the real model file
        self.engine = MLRiskEngine(model_path="/tmp/test_uba_model.pkl")

    def teardown_method(self):
        for path in ["/tmp/test_uba_model.pkl", "/tmp/test_uba_model.pkl.locations.json"]:
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def test_untrained_engine_returns_zeros(self):
        log = {"login_time": "09:00", "downloads": 5, "failed_attempts": 0, "location": "NYC"}
        score, is_anomaly, confidence = self.engine.predict_anomaly(log)
        assert score == 0.0
        assert is_anomaly is False
        assert confidence == 0.0

    def test_training_needs_minimum_10_logs(self):
        logs = [
            {"login_time": "09:00", "downloads": 5, "failed_attempts": 0, "location": "NYC"}
        ]
        assert self.engine.train(logs) is False

    def test_train_succeeds_with_enough_data(self):
        logs = [
            {
                "login_time": f"{h:02d}:00",
                "downloads": h + 1,
                "failed_attempts": 0,
                "location": "New York",
            }
            for h in range(12)
        ]
        assert self.engine.train(logs) is True
        assert self.engine.is_trained is True

    def test_predict_returns_correct_types_after_training(self):
        logs = [
            {
                "login_time": f"{h:02d}:00",
                "downloads": h,
                "failed_attempts": 0,
                "location": "London",
            }
            for h in range(12)
        ]
        self.engine.train(logs)
        score, is_anomaly, confidence = self.engine.predict_anomaly(
            {"login_time": "03:00", "downloads": 99, "failed_attempts": 8, "location": "Unknown"}
        )
        # Use numbers.Number to accept both Python float and numpy.float64;
        # bool() cast handles numpy.bool_ vs Python bool difference
        assert isinstance(score, numbers.Number)
        assert bool(is_anomaly) == is_anomaly  # coercible to bool
        assert isinstance(confidence, numbers.Number)
        assert 0 <= score <= 100
        assert 0 <= confidence <= 100

    def test_get_model_stats_structure(self):
        stats = self.engine.get_model_stats()
        assert "is_trained" in stats
        assert "model_type" in stats
        assert stats["model_type"] == "Isolation Forest"
