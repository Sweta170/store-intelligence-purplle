import pytest
from datetime import datetime
from agents.event_validation_agent import EventValidationAgent
from agents.heatmap_agent import HeatmapAgent
from agents.executive_insights_agent import ExecutiveInsightsAgent

def test_event_validation_agent():
    """
    Test confidence thresholds, schema checks, and duplicates in EventValidationAgent.
    """
    agent = EventValidationAgent(confidence_threshold=0.6)
    
    events = [
        # Valid event
        {
            "event_id": "v1", "store_id": "ST1", "camera_id": "CAM1",
            "visitor_id": "VIS1", "event_type": "ENTRY", "timestamp": "2026-03-03T10:00:00Z",
            "confidence": 0.8
        },
        # Low confidence event (filtered)
        {
            "event_id": "v2", "store_id": "ST1", "camera_id": "CAM1",
            "visitor_id": "VIS1", "event_type": "ENTRY", "timestamp": "2026-03-03T10:00:00Z",
            "confidence": 0.4
        },
        # Duplicate event in batch (skipped)
        {
            "event_id": "v1", "store_id": "ST1", "camera_id": "CAM1",
            "visitor_id": "VIS1", "event_type": "ENTRY", "timestamp": "2026-03-03T10:00:00Z",
            "confidence": 0.8
        },
        # Missing fields schema failure
        {
            "event_id": "v3", "store_id": "ST1", "camera_id": "CAM1",
            "visitor_id": "VIS1", "event_type": "ENTRY"
            # Missing timestamp & confidence
        },
        # Invalid event type
        {
            "event_id": "v4", "store_id": "ST1", "camera_id": "CAM1",
            "visitor_id": "VIS1", "event_type": "INVALID_TYPE", "timestamp": "2026-03-03T10:00:00Z",
            "confidence": 0.95
        }
    ]
    
    valid_evs, report = agent.run(events, existing_event_ids=["existing-db-id"])
    
    assert len(valid_evs) == 1
    assert valid_evs[0]["event_id"] == "v1"
    
    stats = report["stats"]
    assert stats["duplicates_discarded"] == 1
    assert stats["low_confidence_filtered"] == 1
    assert stats["schema_violations"] == 2

def test_heatmap_agent_engagement():
    """
    Test spatial analytics, dwell sums, and confidence flags in HeatmapAgent.
    """
    agent = HeatmapAgent(confidence_threshold=0.90)
    
    events = [
        # Skincare zone entries and dwells
        {"store_id": "S1", "visitor_id": "V1", "event_type": "ZONE_ENTER", "zone_id": "SKINCARE", "confidence": 0.95},
        {"store_id": "S1", "visitor_id": "V1", "event_type": "ZONE_DWELL", "zone_id": "SKINCARE", "dwell_ms": 120000, "confidence": 0.95}, # 2 mins
        
        # Makeup zone with low confidence
        {"store_id": "S1", "visitor_id": "V2", "event_type": "ZONE_ENTER", "zone_id": "MAKEUP", "confidence": 0.85},
        {"store_id": "S1", "visitor_id": "V2", "event_type": "ZONE_EXIT", "zone_id": "MAKEUP", "dwell_ms": 60000, "confidence": 0.85} # 1 min
    ]
    
    res = agent.run(events, exclude_staff=True)
    zones = res["zones"]
    
    assert zones["SKINCARE"]["visits"] == 1
    assert zones["SKINCARE"]["average_dwell_seconds"] == 120.0
    assert zones["SKINCARE"]["engagement_score"] == 2.0  # 1 visit * 2 mins
    assert not zones["SKINCARE"]["low_confidence_flag"]
    
    assert zones["MAKEUP"]["visits"] == 1
    assert zones["MAKEUP"]["average_dwell_seconds"] == 60.0
    assert zones["MAKEUP"]["engagement_score"] == 1.0  # 1 visit * 1 min
    assert zones["MAKEUP"]["low_confidence_flag"]  # confidence is 0.85 < 0.90

def test_executive_insights_agent_formatting():
    """
    Test markdown compiler output in ExecutiveInsightsAgent.
    """
    agent = ExecutiveInsightsAgent()
    
    metrics = {
        "unique_visitors": 20, "conversion_rate": 25.0, "average_dwell_seconds": 300,
        "reentry_count": 2, "abandonment_rate": 5.0
    }
    funnel_data = {
        "stages": [
            {"stage_name": "Entry", "count": 20},
            {"stage_name": "Zone Visit", "count": 18},
            {"stage_name": "Billing Queue", "count": 10},
            {"stage_name": "Purchase", "count": 5}
        ]
    }
    heatmap_data = {
        "zones": {
            "SKINCARE": {"visits": 15, "engagement_score": 5.0},
            "MAKEUP": {"visits": 0, "engagement_score": 0.0}
        }
    }
    anomalies = [
        {"anomaly_type": "QUEUE_SPIKE", "severity": "CRITICAL", "details": "Queue depth is 9", "suggested_action": "Open counter"}
    ]
    
    insights = agent.run("STORE_BLR_001", metrics, funnel_data, heatmap_data, anomalies)
    recs = insights["recommendations"]
    
    assert "Executive Summary & Recommendations: STORE_BLR_001" in recs
    assert "SKINCARE" in recs
    assert "MAKEUP" in recs # dead zones
    assert "CRITICAL ALERTS IN EFFECT" in recs
