"""
Unit Tests for Authentication
"""

import pytest
import json
from app import app, create_table
from user_manager import user_manager

@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    create_table()
    
    with app.test_client() as client:
        yield client
    
    # Cleanup after tests
    import os
    if os.path.exists('test_database.db'):
        os.remove('test_database.db')

@pytest.fixture
def auth_headers(client):
    """Get authentication headers for testing"""
    # Create test user
    user_manager.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        role='Admin'
    )
    
    # Login
    response = client.post('/auth/login', 
        json={'username': 'testuser', 'password': 'testpass123'})
    
    data = json.loads(response.data)
    token = data['token']
    
    return {'Authorization': token}

def test_login_success(client):
    """Test successful login"""
    # Create user first
    user_manager.create_user(
        username='logintest',
        email='login@example.com',
        password='password123',
        role='Viewer'
    )
    
    response = client.post('/auth/login',
        json={'username': 'logintest', 'password': 'password123'})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'token' in data
    assert 'user' in data

def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    response = client.post('/auth/login',
        json={'username': 'nonexistent', 'password': 'wrongpass'})
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data

def test_protected_route_without_token(client):
    """Test accessing protected route without token"""
    response = client.get('/get-logs')
    assert response.status_code == 401

def test_protected_route_with_token(client, auth_headers):
    """Test accessing protected route with valid token"""
    response = client.get('/get-logs', headers=auth_headers)
    assert response.status_code == 200
