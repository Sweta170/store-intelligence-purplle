import pytest
from agents.funnel_agent import FunnelAgent

def test_funnel_full_flow():
    """
    Test a perfect funnel progression where visitors advance through all stages.
    """
    # Create 3 mock sessions
    sessions = [
        # Visitor 1: Full flow (Entry -> Zone Visit -> Billing -> Purchase)
        {
            "visitor_id": "VIS_01",
            "is_staff": False,
            "zone_sequence": ["SKINCARE", "BILLING"]
        },
        # Visitor 2: Partial flow (Entry -> Zone Visit -> Exit)
        {
            "visitor_id": "VIS_02",
            "is_staff": False,
            "zone_sequence": ["MAKEUP"]
        },
        # Visitor 3: Entry only (Entry -> Exit)
        {
            "visitor_id": "VIS_03",
            "is_staff": False,
            "zone_sequence": []
        }
    ]
    # Converted list (VIS_01 converted to transaction)
    converted_ids = ["VIS_01"]
    
    agent = FunnelAgent()
    funnel = agent.run(sessions, converted_ids)
    
    # Assert counts:
    # Entry: 3 unique customers (VIS_01, VIS_02, VIS_03)
    # Zone Visit: 2 unique customer (VIS_01, VIS_02)
    # Billing Queue: 1 unique customer (VIS_01)
    # Purchase: 1 unique customer (VIS_01)
    stages = {s["stage_name"]: s for s in funnel["stages"]}
    
    assert stages["Entry"]["count"] == 3
    assert stages["Zone Visit"]["count"] == 2
    assert stages["Billing Queue"]["count"] == 1
    assert stages["Purchase"]["count"] == 1
    
    # Assert conversion rates:
    # Zone Visit rate: (2/3) * 100 = 66.67%
    assert stages["Zone Visit"]["conversion_rate_pct"] == 66.67
    # Billing Queue rate: (1/2) * 100 = 50.0%
    assert stages["Billing Queue"]["conversion_rate_pct"] == 50.0
    # Purchase rate: (1/1) * 100 = 100.0%
    assert stages["Purchase"]["conversion_rate_pct"] == 100.0

def test_funnel_no_transactions():
    """
    Test funnel counts and drop-offs when no conversions (purchases) happen.
    """
    sessions = [
        {
            "visitor_id": "VIS_01",
            "is_staff": False,
            "zone_sequence": ["SKINCARE", "BILLING"]
        }
    ]
    converted_ids = []
    
    agent = FunnelAgent()
    funnel = agent.run(sessions, converted_ids)
    
    stages = {s["stage_name"]: s for s in funnel["stages"]}
    
    assert stages["Entry"]["count"] == 1
    assert stages["Zone Visit"]["count"] == 1
    assert stages["Billing Queue"]["count"] == 1
    assert stages["Purchase"]["count"] == 0
    
    assert stages["Purchase"]["conversion_rate_pct"] == 0.0
    assert stages["Purchase"]["dropoff_pct"] == 100.0
