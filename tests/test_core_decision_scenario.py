"""
Test Core Decision Scenario for WareMind AI
Scenario:
- Urgent Order (ORD-001) requires 10 units of PROD-001.
- Available physical stock of PROD-001 is 7 units.
- Normal Order (ORD-002) requires 5 units of PROD-001.

Verification:
1. Priority engine & allocation service allocate all 7 available units to Urgent Order first.
2. Urgent Order receives PARTIALLY_ALLOCATED status, allocating 7 units with a shortage of 3 units flagged.
3. Normal Order receives 0 units due to depleted stock and flags a shortage of 5 units.
4. Structured decision explanation clearly details stock trade-off and shortage exceptions.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from database.seed import seed_database
from database.db import get_db_connection
from services.order_service import OrderService
from services.allocation_service import AllocationService


@pytest.fixture(autouse=True)
def setup_db():
    seed_database()

def test_core_decision_scenario_urgent_vs_normal():
    # 1. Inspect initial order states
    ord1 = OrderService.get_order_by_id("ORD-001")
    ord2 = OrderService.get_order_by_id("ORD-002")

    assert ord1['priority'] == "URGENT"
    assert ord2['priority'] == "NORMAL"
    assert ord1['items'][0]['requested_quantity'] == 10
    assert ord2['items'][0]['requested_quantity'] == 5

    # 2. Execute allocation for Urgent Order (ORD-001)
    result1 = AllocationService.allocate_order("ORD-001")

    assert result1['decision'] == "PARTIAL_ALLOCATION"
    assert len(result1['allocations']) == 1
    assert result1['allocations'][0]['quantity'] == 7
    assert len(result1['shortages']) == 1
    assert result1['shortages'][0]['shortage_quantity'] == 3
    assert "Allocated 7 units" in result1['reasoning']

    # 3. Check updated order status for ORD-001
    updated_ord1 = OrderService.get_order_by_id("ORD-001")
    assert updated_ord1['status'] == "PARTIALLY_ALLOCATED"

    # 4. Execute allocation for Competing Normal Order (ORD-002)
    result2 = AllocationService.allocate_order("ORD-002")

    assert result2['decision'] == "UNALLOCATED_SHORTAGE"
    assert len(result2['allocations']) == 0
    assert len(result2['shortages']) == 1
    assert result2['shortages'][0]['shortage_quantity'] == 5
    assert "zero available stock" in result2['reasoning'] or "shortage" in result2['reasoning'].lower()

    # 5. Verify database exceptions created
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM exceptions WHERE order_id IN ('ORD-001', 'ORD-002');")
    exc_count = cursor.fetchone()[0]
    conn.close()

    assert exc_count >= 2
