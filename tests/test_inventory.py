import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app import create_app
from database.seed import seed_database

@pytest.fixture(scope="module")
def client():
    # Ensure database is seeded prior to running inventory tests
    seed_database()
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_all_inventory(client):
    response = client.get('/api/inventory')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert isinstance(json_data['data'], list)
    assert len(json_data['data']) >= 40

def test_get_inventory_by_id(client):
    response = client.get('/api/inventory/INV-001')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    item = json_data['data']
    assert item['id'] == 'INV-001'
    assert item['product_id'] == 'PROD-001'
    assert 'product' in item
    assert 'location' in item

def test_get_inventory_not_found(client):
    response = client.get('/api/inventory/INV-NONEXISTENT')
    assert response.status_code == 404
    json_data = response.get_json()
    assert json_data['status'] == 'error'

def test_get_low_stock_inventory(client):
    response = client.get('/api/inventory/low-stock')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    items = json_data['data']
    assert isinstance(items, list)
    # Check that returned items have available_quantity <= product reorder_level
    for item in items:
        assert item['available_quantity'] <= item['product']['reorder_level']

def test_get_out_of_stock_inventory(client):
    response = client.get('/api/inventory/out-of-stock')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    items = json_data['data']
    for item in items:
        assert item['available_quantity'] <= 0

def test_get_damaged_inventory(client):
    response = client.get('/api/inventory/damaged')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    items = json_data['data']
    assert len(items) > 0
    for item in items:
        assert item['damaged_quantity'] > 0

def test_search_inventory(client):
    response = client.get('/api/inventory/search?q=Sensor')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    items = json_data['data']
    assert len(items) > 0
    assert 'Sensor' in items[0]['product']['name'] or 'SEN' in items[0]['product']['sku']

def test_patch_inventory(client):
    response = client.patch('/api/inventory/INV-007', json={'reserved_quantity': 25})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['data']['reserved_quantity'] == 25

def test_adjust_inventory_stock_success(client):
    # Get current stock
    res_before = client.get('/api/inventory/INV-007').get_json()['data']
    qty_before = res_before['quantity']

    response = client.post('/api/inventory/INV-007/adjust', json={
        'quantity_change': 10,
        'reason': 'Restock arrival'
    })
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    assert json_data['data']['quantity'] == qty_before + 10

def test_adjust_inventory_stock_prevents_negative(client):
    response = client.post('/api/inventory/INV-007/adjust', json={
        'quantity_change': -9999,
        'reason': 'Excessive deduction'
    })
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['status'] == 'error'
    assert 'cannot be negative' in json_data['error']['message']

def test_report_damage_success(client):
    # INV-007 has positive available stock
    res_before = client.get('/api/inventory/INV-007').get_json()['data']
    dmg_before = res_before['damaged_quantity']

    response = client.post('/api/inventory/INV-007/damage', json={
        'damaged_quantity_added': 2,
        'reason': 'Water damage reported on top box'
    })
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    result = json_data['data']
    assert result['inventory']['damaged_quantity'] == dmg_before + 2
    assert result['exception']['exception_type'] == 'DAMAGED_GOODS'

def test_report_damage_exceeds_available(client):
    response = client.post('/api/inventory/INV-007/damage', json={
        'damaged_quantity_added': 9999,
        'reason': 'Excessive damage'
    })
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['status'] == 'error'

def test_reorder_recommendations(client):
    response = client.get('/api/inventory/reorder-recommendations')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    recs = json_data['data']
    assert isinstance(recs, list)
    assert len(recs) > 0
    first = recs[0]
    assert 'product_id' in first
    assert 'suggested_reorder_quantity' in first
    assert 'urgency' in first
    assert first['urgency'] in ['CRITICAL', 'HIGH', 'MEDIUM']
