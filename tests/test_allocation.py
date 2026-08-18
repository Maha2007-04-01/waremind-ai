import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app import create_app
from database.seed import seed_database
from ai.priority_engine import PriorityEngine

@pytest.fixture(autouse=True)
def reset_db():
    # Fresh database seed prior to each test to ensure clean stock states
    seed_database()

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_priority_engine_scoring():
    urgent_order = {
        "priority": "URGENT",
        "required_by": "2026-08-18T12:00:00Z",
        "total_value": 6000.0,
        "status": "PARTIALLY_ALLOCATED"
    }
    eval_urgent = PriorityEngine.calculate_priority(urgent_order)
    assert eval_urgent['priority_level'] in ['CRITICAL', 'HIGH']
    assert eval_urgent['priority_score'] >= 60

    normal_order = {
        "priority": "LOW",
        "total_value": 150.0,
        "status": "PENDING"
    }
    eval_normal = PriorityEngine.calculate_priority(normal_order)
    assert eval_normal['priority_level'] == 'LOW'
    assert eval_normal['priority_score'] < 35

def test_full_allocation(client):
    # ORD-006 requests 4 units of PROD-006; 25 units available at LOC-A01-2-1
    response = client.post('/api/orders/ORD-006/allocate')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    data = json_data['data']
    assert data['decision'] == 'FULL_ALLOCATION'
    assert len(data['allocations']) > 0
    assert len(data['shortages']) == 0

def test_partial_allocation_and_shortage(client):
    # ORD-001 (URGENT) requests 10 units of PROD-001. Only 7 units available.
    response = client.post('/api/orders/ORD-001/allocate')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    data = json_data['data']
    assert data['decision'] == 'PARTIAL_ALLOCATION'
    assert len(data['allocations']) == 1
    assert data['allocations'][0]['quantity'] == 7
    assert len(data['shortages']) == 1
    assert data['shortages'][0]['shortage_quantity'] == 3
    assert len(data['exceptions']) == 1

def test_zero_stock_allocation(client):
    # ORD-004 requests PROD-008 which has 0 units in stock
    response = client.post('/api/orders/ORD-004/allocate')
    assert response.status_code == 200
    json_data = response.get_json()
    data = json_data['data']
    # Check that shortage for PROD-008 is recorded
    shortage_prod8 = [s for s in data['shortages'] if s['product_id'] == 'PROD-008']
    assert len(shortage_prod8) == 1
    assert shortage_prod8[0]['allocated_quantity'] == 0

def test_competing_orders_priority_protection(client):
    """
    Scenario:
    Urgent Order ORD-001 requests 10 units of PROD-001 (7 available).
    Normal Order ORD-002 requests 5 units of PROD-001.
    Allocate ORD-001 first -> consumes all 7 available units.
    Attempt to allocate ORD-002 afterwards -> receives 0 units because Urgent order consumed stock.
    """
    # 1. Allocate Urgent Order ORD-001
    res1 = client.post('/api/orders/ORD-001/allocate')
    assert res1.status_code == 200
    data1 = res1.get_json()['data']
    assert data1['allocations'][0]['quantity'] == 7

    # 2. Allocate Lower Priority Order ORD-002
    res2 = client.post('/api/orders/ORD-002/allocate')
    assert res2.status_code == 200
    data2 = res2.get_json()['data']
    # ORD-002 should receive 0 allocated units because ORD-001 consumed available stock
    assert data2['decision'] == 'UNALLOCATED_SHORTAGE'
    assert len(data2['allocations']) == 0
    assert data2['shortages'][0]['shortage_quantity'] == 5

def test_damaged_stock_exclusion(client):
    """
    PROD-003 at LOC-C01-1-1 has 10 total units, 8 damaged, leaving 2 available.
    Allocating ORD-004 (requests 5 of PROD-003) must only allocate 2 available units, ignoring damaged stock.
    """
    res = client.post('/api/orders/ORD-004/allocate')
    assert res.status_code == 200
    data = res.get_json()['data']
    prod3_allocs = [a for a in data['allocations'] if a['product_id'] == 'PROD-003']
    if prod3_allocs:
        assert prod3_allocs[0]['quantity'] <= 2

def test_multiple_warehouse_locations_split_pick(client):
    """
    PROD-002 requested 15 units by ORD-003.
    Stock is split across LOC-A01-1-2 (6 units) and LOC-B02-3-2 (10 units).
    Allocation Engine must split allocation across both locations (6 from A01 + 9 from B02 = 15 total).
    """
    res = client.post('/api/orders/ORD-003/allocate')
    assert res.status_code == 200
    data = res.get_json()['data']
    prod2_allocs = [a for a in data['allocations'] if a['product_id'] == 'PROD-002']
    assert len(prod2_allocs) == 2
    total_alloc = sum([a['quantity'] for a in prod2_allocs])
    assert total_alloc == 15

def test_order_decision_explanation_endpoint(client):
    # Execute allocation first
    client.post('/api/orders/ORD-001/allocate')
    
    # Request decision explanation
    response = client.get('/api/orders/ORD-001/decision')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    data = json_data['data']
    assert 'priority_evaluation' in data
    assert 'recommended_warehouse_action' in data
    assert 'shortages_summary' in data
