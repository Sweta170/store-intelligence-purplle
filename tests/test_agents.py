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


def test_conversion_agent_chronological():
    """
    Test strict 5-minute BEFORE transaction conversion matching rule.
    """
    from agents.conversion_agent import ConversionAgent
    from datetime import datetime, timedelta

    agent = ConversionAgent(time_window_seconds=300)
    
    base_time = datetime(2026, 3, 3, 10, 0, 0)
    
    # Billing events
    billing_events = [
        # Billing event 1: 2 minutes before transaction (Valid match)
        {"visitor_id": "V1", "event_type": "BILLING_QUEUE_JOIN", "timestamp": base_time - timedelta(minutes=2), "is_staff": False},
        # Billing event 2: 6 minutes before transaction (Too early, invalid match)
        {"visitor_id": "V2", "event_type": "BILLING_QUEUE_JOIN", "timestamp": base_time - timedelta(minutes=6), "is_staff": False},
        # Billing event 3: 2 minutes after transaction (Invalid match because it is after)
        {"visitor_id": "V3", "event_type": "BILLING_QUEUE_JOIN", "timestamp": base_time + timedelta(minutes=2), "is_staff": False},
        # Billing event 4: 1 minute before transaction but visitor is staff (Excluded)
        {"visitor_id": "STF1", "event_type": "BILLING_QUEUE_JOIN", "timestamp": base_time - timedelta(minutes=1), "is_staff": True}
    ]
    
    # Single transaction
    transactions = [
        {"transaction_id": "TX1", "timestamp": base_time, "basket_value_inr": 1000}
    ]
    
    res = agent.run(billing_events, transactions, unique_visitor_count=3)
    
    # Only V1 should be matched
    assert res["total_transactions_matched"] == 1
    assert "V1" in res["converted_visitor_ids"]
    assert "V2" not in res["converted_visitor_ids"]
    assert "V3" not in res["converted_visitor_ids"]
    assert "STF1" not in res["converted_visitor_ids"]


def test_validation_agent_passes_extra_fields():
    """
    Test that extra fields like gender_pred, age_pred, etc., do not break EventValidationAgent.
    """
    agent = EventValidationAgent(confidence_threshold=0.5)
    
    events = [
        {
            "event_id": "ev-extra-1",
            "store_id": "ST1",
            "camera_id": "CAM1",
            "visitor_id": "V1",
            "event_type": "ENTRY",
            "timestamp": "2026-03-03T10:00:00Z",
            "confidence": 0.95,
            "gender_pred": "Female",
            "age_pred": 25,
            "age_bucket": "18-35",
            "group_size": 2,
            "zone_name": "Skincare Entrance",
            "zone_type": "ENTRANCE"
        }
    ]
    
    valid_evs, report = agent.run(events)
    assert len(valid_evs) == 1
    assert valid_evs[0]["event_id"] == "ev-extra-1"
    assert valid_evs[0]["gender_pred"] == "Female"
    assert valid_evs[0]["age_pred"] == 25
