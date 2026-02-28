"""
Tests for ML Risk Engine
"""

import pytest
from ml_risk_engine import ml_engine

def test_ml_engine_initialization():
    """Test ML engine initializes correctly"""
    assert ml_engine is not None
    assert hasattr(ml_engine, 'model')

def test_predict_anomaly_with_data():
    """Test anomaly prediction"""
    test_data = {
        'downloads': 50,
        'failed_attempts': 5,
        'login_time': '03:00'
    }
    
    score, is_anomaly, confidence = ml_engine.predict_anomaly(test_data)
    
    assert isinstance(score, (int, float))
    assert isinstance(is_anomaly, bool)
    assert isinstance(confidence, (int, float))
    assert 0 <= score <= 100
    assert 0 <= confidence <= 100

def test_model_stats():
    """Test getting model statistics"""
    stats = ml_engine.get_model_stats()
    
    assert isinstance(stats, dict)
    assert 'is_trained' in stats
