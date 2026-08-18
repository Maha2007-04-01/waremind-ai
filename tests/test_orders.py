import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app import create_app
from database.seed import seed_database

@pytest.fixture(scope="module")
def client():
    seed_database()
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_all_orders(client):
    response = client.get('/api/orders')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    orders = json_data['data']
    assert isinstance(orders, list)
    assert len(orders) >= 15

def test_get_order_by_id(client):
    response = client.get('/api/orders/ORD-001')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    order = json_data['data']
    assert order['id'] == 'ORD-001'
    assert 'priority_evaluation' in order
    assert order['priority_evaluation']['priority_level'] in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

def test_create_order_success(client):
    new_order_payload = {
        "customer_name": "Tesla Robotics Division",
        "priority": "URGENT",
        "required_by": "2026-08-18T18:00:00Z",
        "items": [
            {
                "product_id": "PROD-002",
                "requested_quantity": 3
            }
        ]
    }
    response = client.post('/api/orders', json=new_order_payload)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    created = json_data['data']
    assert created['customer_name'] == "Tesla Robotics Division"
    assert created['priority'] == "URGENT"
    assert len(created['items']) == 1

def test_create_order_validation(client):
    response = client.post('/api/orders', json={"customer_name": "No Items Corp", "items": []})
    assert response.status_code == 400

def test_update_order_status(client):
    response = client.patch('/api/orders/ORD-006/status', json={'status': 'PICKING'})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['data']['status'] == 'PICKING'
