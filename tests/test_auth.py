import sys
import os
import pytest

# sys.path is configured by tests/conftest.py (auto-loaded by pytest)
from app import create_app
from database.seed import seed_database


@pytest.fixture(autouse=True)
def reset_db():
    seed_database()

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_register_manager_account(client):
    res = client.post('/api/auth/register', json={
        "name": "Mahalakshmi Manager",
        "email": "maha.manager@waremind.ai",
        "username": "MahaManager",
        "password": "waremind2026password",
        "role": "Manager"
    })
    print("REGISTER RESP:", res.get_json())
    assert res.status_code == 201

    json_data = res.get_json()
    assert json_data['status'] == 'success'
    assert json_data['data']['user']['username'] == 'MahaManager'
    assert json_data['data']['user']['role'] == 'MANAGER'
    assert 'token' in json_data['data']

def test_register_admin_account(client):
    res = client.post('/api/auth/register', json={
        "name": "Mahalakshmi Admin",
        "email": "maha.admin@waremind.ai",
        "username": "MahaAdmin",
        "password": "waremind2026password",
        "role": "Admin"
    })
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data['data']['user']['role'] == 'ADMIN'

def test_register_customer_account(client):
    res = client.post('/api/auth/register', json={
        "name": "Mahalakshmi Customer",
        "email": "maha401@gmail.com",
        "username": "Maha",
        "password": "waremind2026password",
        "role": "Customer"
    })
    assert res.status_code == 201
    json_data = res.get_json()
    assert json_data['data']['user']['role'] == 'CUSTOMER'

def test_duplicate_username_rejection(client):
    # Try registering with existing username 'manager'
    res = client.post('/api/auth/register', json={
        "name": "Duplicate User",
        "email": "unique.email@waremind.ai",
        "username": "manager",
        "password": "waremind2026password",
        "role": "Manager"
    })
    assert res.status_code == 400
    json_data = res.get_json()
    assert "Username already exists" in json_data['error']['message']

def test_duplicate_email_rejection(client):
    # Try registering with existing email 'manager@waremind.ai'
    res = client.post('/api/auth/register', json={
        "name": "Duplicate Email User",
        "email": "manager@waremind.ai",
        "username": "unique_user_99",
        "password": "waremind2026password",
        "role": "Manager"
    })
    assert res.status_code == 400
    json_data = res.get_json()
    assert "Email already registered" in json_data['error']['message']

def test_login_with_username(client):
    res = client.post('/api/auth/login', json={
        "usernameOrEmail": "manager",
        "password": "waremind2026"
    })
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['data']['user']['username'] == 'manager'
    assert 'token' in json_data['data']

def test_login_with_email(client):
    res = client.post('/api/auth/login', json={
        "usernameOrEmail": "admin@waremind.ai",
        "password": "waremind2026"
    })
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['data']['user']['username'] == 'admin'

def test_login_invalid_password(client):
    res = client.post('/api/auth/login', json={
        "usernameOrEmail": "manager",
        "password": "wrongpassword123"
    })
    assert res.status_code == 401
    json_data = res.get_json()
    assert "Invalid username/email or password" in json_data['error']['message']

def test_login_demo_accounts(client):
    for demo in ["manager", "admin", "customer", "picker"]:
        res = client.post('/api/auth/login', json={
            "usernameOrEmail": demo,
            "password": "waremind2026"
        })
        assert res.status_code == 200
        assert res.get_json()['data']['user']['username'] == demo

def test_token_auth_me_endpoint(client):
    # Login to get token
    login_res = client.post('/api/auth/login', json={
        "usernameOrEmail": "manager",
        "password": "waremind2026"
    })
    token = login_res.get_json()['data']['token']

    # Call /api/auth/me
    me_res = client.get('/api/auth/me', headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.get_json()['data']['username'] == 'manager'
