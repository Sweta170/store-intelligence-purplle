import pytest
from datetime import datetime, timedelta
from agents.anomaly_agent import AnomalyAgent

def test_anomaly_queue_spike():
    """
    Test that queue depths > 5 trigger a QUEUE_SPIKE alert.
    """
    ref_time = datetime(2026, 3, 3, 10, 0, 0)
    events = [
        {
            "event_id": "e1",
            "store_id": "STORE_TEST_001",
            "camera_id": "CAM_BILLING_01",
            "visitor_id": "VIS_01",
            "event_type": "BILLING_QUEUE_JOIN",
            "timestamp": ref_time,
            "is_staff": False,
            "confidence": 0.95,
            "metadata": {"queue_depth": 7}  # Spike depth
        }
    ]
    
    agent = AnomalyAgent()
    res = agent.run(
        store_id="STORE_TEST_001",
        events=events,
        transactions=[],
        heatmap_data={"zones": {"BILLING": {"visits": 1}}},
        conversion_rate=20.0,
        current_reference_time=ref_time
    )
    
    anomalies = res["anomalies"]
    types = [a["anomaly_type"] for a in anomalies]
    
    assert "QUEUE_SPIKE" in types
    # Check severity (7 queue depth is WARN, >8 is CRITICAL)
    spike = [a for a in anomalies if a["anomaly_type"] == "QUEUE_SPIKE"][0]
    assert spike["severity"] == "WARN"

def test_anomaly_conversion_drop():
    """
    Test that a low conversion rate (< 15%) triggers a CONVERSION_DROP alert
    when there is a minimum population threshold (e.g. 10 visitors).
    """
    ref_time = datetime(2026, 3, 3, 10, 0, 0)
    
    # Generate 10 unique customer entry events
    events = []
    for i in range(1, 11):
        events.append({
            "event_id": f"e_{i}",
            "store_id": "STORE_TEST_001",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": f"VIS_{i}",
            "event_type": "ENTRY",
            "timestamp": ref_time,
            "is_staff": False,
            "confidence": 0.95
        })
        
    agent = AnomalyAgent()
    res = agent.run(
        store_id="STORE_TEST_001",
        events=events,
        transactions=[],
        heatmap_data={"zones": {"SKINCARE": {"visits": 5}}},
        conversion_rate=5.0,  # Low conversion rate (5% < 15%)
        current_reference_time=ref_time
    )
    
    anomalies = res["anomalies"]
    types = [a["anomaly_type"] for a in anomalies]
    
    assert "CONVERSION_DROP" in types
    drop = [a for a in anomalies if a["anomaly_type"] == "CONVERSION_DROP"][0]
    assert drop["severity"] == "CRITICAL" # 5% is under 8% critical threshold

def test_anomaly_dead_zone():
    """
    Test that a zone with 0 visits triggers a DEAD_ZONE warning.
    """
    ref_time = datetime(2026, 3, 3, 10, 0, 0)
    events = [
        {
            "event_id": "e1",
            "store_id": "STORE_TEST_001",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": "VIS_01",
            "event_type": "ENTRY",
            "timestamp": ref_time,
            "is_staff": False,
            "confidence": 0.95
        }
    ]
    
    # Heatmap shows SKINCARE has visits, but MAKEUP is missing or has 0 visits
    heatmap = {
        "zones": {
            "SKINCARE": {"visits": 5, "average_dwell_seconds": 120.0},
            "MAKEUP": {"visits": 0, "average_dwell_seconds": 0.0}
        }
    }
    
    agent = AnomalyAgent()
    res = agent.run(
        store_id="STORE_TEST_001",
        events=events,
        transactions=[],
        heatmap_data=heatmap,
        conversion_rate=25.0,
        current_reference_time=ref_time
    )
    
    anomalies = res["anomalies"]
    types = [a["anomaly_type"] for a in anomalies]
    
    # MAKEUP, FRAGRANCE, HAIRCARE, BILLING will be flagged dead zones if missing/0 in heatmap
    assert "DEAD_ZONE" in types
    dead_zones = [a["details"] for a in anomalies if a["anomaly_type"] == "DEAD_ZONE"]
    # Check that makeup is mentioned
    assert any("MAKEUP" in desc for desc in dead_zones)

def test_anomaly_stale_feed():
    """
    Test that cameras that haven't sent events for more than 15 minutes
    trigger a STALE_FEED CRITICAL alert.
    """
    ref_time = datetime(2026, 3, 3, 10, 0, 0)
    
    # We have two events. One is at 10:00:00 (Entry), the other is at 10:25:00 (Skincare)
    # The time gap is 25 minutes. Since Entry camera CAM_ENTRY_01's latest event is 10:00:00,
    # and the overall store max event is 10:25:00, CAM_ENTRY_01 should be flagged stale (> 15 min lag).
    events = [
        {
            "event_id": "e1",
            "store_id": "STORE_TEST_001",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": "VIS_01",
            "event_type": "ENTRY",
            "timestamp": ref_time,
            "is_staff": False,
            "confidence": 0.95
        },
        {
            "event_id": "e2",
            "store_id": "STORE_TEST_001",
            "camera_id": "CAM_SKINCARE_01",
            "visitor_id": "VIS_02",
            "event_type": "ZONE_ENTER",
            "timestamp": ref_time + timedelta(minutes=25),
            "zone_id": "SKINCARE",
            "is_staff": False,
            "confidence": 0.95
        }
    ]
    
    agent = AnomalyAgent()
    res = agent.run(
        store_id="STORE_TEST_001",
        events=events,
        transactions=[],
        heatmap_data={"zones": {"SKINCARE": {"visits": 1}, "ENTRY": {"visits": 1}}},
        conversion_rate=20.0,
        current_reference_time=ref_time + timedelta(minutes=25)
    )
    
    anomalies = res["anomalies"]
    stale_alerts = [a for a in anomalies if a["anomaly_type"] == "STALE_FEED"]
    
    assert len(stale_alerts) > 0
    # CAM_ENTRY_01 has 25 min gap, so it must be critical stale
    cams_stale = [a["details"] for a in stale_alerts]
    assert any("CAM_ENTRY_01" in details for details in cams_stale)
