import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app import create_app
from database.seed import seed_database
from ai.decision_engine import DecisionEngine

@pytest.fixture(scope="module")
def client():
    seed_database()
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_decision_engine_direct():
    insights = DecisionEngine.generate_decision_insights()
    assert "inventory_risks" in insights
    assert "order_risks" in insights
    assert "warehouse_bottlenecks" in insights
    assert "smart_recommendations" in insights
    assert "decision_engine_mode" in insights
    assert insights["decision_engine_mode"] in ["RULE_BASED", "GEMINI_ENHANCED"]

    recommendations = insights["smart_recommendations"]
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0

    for rec in recommendations:
        assert "title" in rec
        assert "severity" in rec
        assert rec["severity"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert "recommendation" in rec
        assert "reason" in rec
        assert "affected_entities" in rec
        assert "expected_impact" in rec
        assert "confidence_score" in rec
        assert 0.0 <= rec["confidence_score"] <= 1.0

def test_decision_insights_api_endpoint(client):
    response = client.get('/api/analytics/decision-insights')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    data = json_data['data']

    # Inventory Risks assertions
    inv_risks = data['inventory_risks']
    assert 'low_stock_products' in inv_risks
    assert 'stockout_risks' in inv_risks
    assert 'excess_inventory' in inv_risks
    assert 'damaged_inventory' in inv_risks

    # Order Risks assertions
    order_risks = data['order_risks']
    assert 'delayed_orders' in order_risks
    assert 'orders_likely_to_miss_deadline' in order_risks
    assert 'partially_allocated_orders' in order_risks
    assert 'high_priority_shortages' in order_risks

    # Bottlenecks assertions
    bottlenecks = data['warehouse_bottlenecks']
    assert 'primary_bottleneck' in bottlenecks
    assert 'bottleneck_area' in bottlenecks['primary_bottleneck']
    assert 'severity' in bottlenecks['primary_bottleneck']
    assert 'recommended_action' in bottlenecks['primary_bottleneck']

    # Smart Recommendations assertions
    recs = data['smart_recommendations']
    assert len(recs) > 0
    first = recs[0]
    assert isinstance(first['title'], str)
    assert isinstance(first['recommendation'], str)
    assert isinstance(first['confidence_score'], float)

def test_analytics_summary_endpoint(client):
    response = client.get('/api/analytics/summary')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'success'
    data = json_data['data']
    assert 'total_orders' in data
    assert 'completed_orders' in data
    assert 'active_alerts' in data
    assert 'active_tasks' in data
