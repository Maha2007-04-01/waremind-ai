import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

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

def test_health_check(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'ok'
    assert json_data['service'] == 'WareMind AI'

def test_system_status(client):
    response = client.get('/api/system/status')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    data = json_data['data']
    assert data['application_status'] == 'ok'
    assert data['database_status'] == 'connected'

def test_complete_valid_fulfillment_workflow(client):
    """
    Tests full valid pipeline:
    Order Created -> Allocation -> Picking -> Packing -> QC Pass -> Dispatch -> Inventory Finalized.
    """
    # 1. Create Order
    new_order = {
        "customer_name": "Acme Logistics Inc",
        "priority": "HIGH",
        "items": [{"product_id": "PROD-006", "requested_quantity": 2}]
    }
    create_res = client.post('/api/orders', json=new_order)
    assert create_res.status_code == 201
    order_id = create_res.get_json()['data']['id']

    # 2. Allocate Stock
    alloc_res = client.post(f'/api/orders/{order_id}/allocate')
    assert alloc_res.status_code == 200
    assert alloc_res.get_json()['data']['decision'] == 'FULL_ALLOCATION'

    # 3. Create, Start, & Complete Picking Task
    pick_task_res = client.post('/api/picking/tasks', json={"order_id": order_id, "assigned_to": "Worker-01"})
    assert pick_task_res.status_code == 201
    task_id = pick_task_res.get_json()['data']['id']

    start_pick_res = client.post(f'/api/picking/tasks/{task_id}/start')
    assert start_pick_res.status_code == 200

    comp_pick_res = client.post(f'/api/picking/tasks/{task_id}/complete')
    assert comp_pick_res.status_code == 200
    assert comp_pick_res.get_json()['data']['status'] == 'PICKED'

    # 4. Create, Start, & Complete Packing Task
    pack_task_res = client.post('/api/packing/tasks', json={"order_id": order_id, "assigned_to": "Worker-02"})
    assert pack_task_res.status_code == 201
    pack_task_id = pack_task_res.get_json()['data']['id']

    start_pack_res = client.post(f'/api/packing/tasks/{pack_task_id}/start')
    assert start_pack_res.status_code == 200

    comp_pack_res = client.post(f'/api/packing/tasks/{pack_task_id}/complete')
    assert comp_pack_res.status_code == 200
    assert comp_pack_res.get_json()['data']['status'] == 'PACKED'

    # 5. Quality Check Pass
    qc_res = client.post('/api/qc/check', json={"order_id": order_id, "result": "PASS", "notes": "Inspected all seals intact"})
    assert qc_res.status_code == 200
    assert qc_res.get_json()['data']['status'] == 'QC_PASSED'

    # 6. Dispatch Manifest Creation & Dispatch
    dsp_manifest_res = client.post('/api/dispatch', json={"order_id": order_id, "carrier": "FedEx Freight"})
    assert dsp_manifest_res.status_code == 201
    dsp_id = dsp_manifest_res.get_json()['data']['id']
    assert 'TRK-WM-' in dsp_manifest_res.get_json()['data']['tracking_number']

    dispatch_res = client.post(f'/api/dispatch/{dsp_id}/dispatch')
    assert dispatch_res.status_code == 200
    assert dispatch_res.get_json()['data']['status'] == 'DISPATCHED'

    # Check final order status
    final_order = client.get(f'/api/orders/{order_id}').get_json()['data']
    assert final_order['status'] == 'DISPATCHED'

def test_invalid_workflow_transition_violations(client):
    """
    Tests strict state machine validation rules:
    Rule 1: Cannot pick without allocation.
    Rule 5: Cannot pack before picking complete.
    Rule 6: Cannot QC before packing complete.
    Rule 7: Cannot dispatch before QC passes.
    """
    # Create unallocated order
    create_res = client.post('/api/orders', json={
        "customer_name": "Invalid Transition Corp",
        "items": [{"product_id": "PROD-007", "requested_quantity": 1}]
    })
    order_id = create_res.get_json()['data']['id']

    # Violation 1: Picking unallocated order
    res_pick = client.post('/api/picking/tasks', json={"order_id": order_id})
    assert res_pick.status_code == 400
    assert "Allocation required first" in res_pick.get_json()['error']['message']

    # Violation 5: Packing before picking complete
    res_pack = client.post('/api/packing/tasks', json={"order_id": order_id})
    assert res_pack.status_code == 400
    assert "Picking must be completed first" in res_pack.get_json()['error']['message']

    # Violation 6: QC before packing complete
    res_qc = client.post('/api/qc/check', json={"order_id": order_id, "result": "PASS"})
    assert res_qc.status_code == 400
    assert "Packing must be completed first" in res_qc.get_json()['error']['message']

    # Violation 7: Dispatch before QC passes
    res_dsp = client.post('/api/dispatch', json={"order_id": order_id})
    assert res_dsp.status_code == 400
    assert "Quality Check must be PASSED first" in res_dsp.get_json()['error']['message']

def test_picking_missing_and_damaged_item_exceptions(client):
    # Setup allocated order
    create_res = client.post('/api/orders', json={
        "customer_name": "Exception Test Corp",
        "items": [{"product_id": "PROD-006", "requested_quantity": 3}]
    })
    order_id = create_res.get_json()['data']['id']
    client.post(f'/api/orders/{order_id}/allocate')

    task_res = client.post('/api/picking/tasks', json={"order_id": order_id})
    task_id = task_res.get_json()['data']['id']

    # Report Missing Item
    res_missing = client.post(f'/api/picking/tasks/{task_id}/report-missing', json={
        "product_id": "PROD-006",
        "missing_quantity": 1
    })
    assert res_missing.status_code == 200
    exc_id_missing = res_missing.get_json()['data']['exception_id']

    # Report Damaged Item
    res_damaged = client.post(f'/api/picking/tasks/{task_id}/report-damaged', json={
        "product_id": "PROD-006",
        "damaged_quantity": 1,
        "location_id": "LOC-A01-2-1"
    })
    assert res_damaged.status_code == 200

    # Resolve Missing Item Exception via Exception Engine
    res_resolve = client.post(f'/api/exceptions/{exc_id_missing}/resolve', json={"resolution_action": "REALLOCATE"})
    assert res_resolve.status_code == 200
    assert res_resolve.get_json()['data']['status'] == 'RESOLVED'

def test_qc_failure_workflow(client):
    # Setup order up to QC stage
    create_res = client.post('/api/orders', json={
        "customer_name": "QC Fail Test",
        "items": [{"product_id": "PROD-007", "requested_quantity": 2}]
    })
    order_id = create_res.get_json()['data']['id']
    client.post(f'/api/orders/{order_id}/allocate')

    pick_id = client.post('/api/picking/tasks', json={"order_id": order_id}).get_json()['data']['id']
    client.post(f'/api/picking/tasks/{pick_id}/start')
    client.post(f'/api/picking/tasks/{pick_id}/complete')

    pack_id = client.post('/api/packing/tasks', json={"order_id": order_id}).get_json()['data']['id']
    client.post(f'/api/packing/tasks/{pack_id}/start')
    client.post(f'/api/packing/tasks/{pack_id}/complete')

    # Execute QC Failure
    qc_fail_res = client.post('/api/qc/check', json={"order_id": order_id, "result": "FAIL", "notes": "Box seal torn"})
    assert qc_fail_res.status_code == 200
    exc_id = qc_fail_res.get_json()['data']['exception_id']
    assert exc_id is not None

    # Resolve QC Failure Exception -> resets order status back to PACKING
    resolve_res = client.post(f'/api/exceptions/{exc_id}/resolve')
    assert resolve_res.status_code == 200
    assert resolve_res.get_json()['data']['status'] == 'RESOLVED'

    order_after = client.get(f'/api/orders/{order_id}').get_json()['data']
    assert order_after['status'] == 'PACKING'
