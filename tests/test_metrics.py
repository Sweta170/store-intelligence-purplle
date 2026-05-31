import pytest
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.db import Base
from app.models import Event, POSTransaction
from app.metrics import get_store_kpis
from agents.session_agent import SessionAgent

# Setup in-memory SQLite DB for isolated testing
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_empty_store(db_session):
    """
    Test behavior when store is completely empty (no events, no transactions).
    """
    # Simply check that KPI calculation fails gracefully or handles empty data
    # The get_store_kpis function calls the SessionAgent.
    # An empty list of events should yield 0 unique visitors, 0 conversion, etc.
    kpis = get_store_kpis(db_session, "STORE_TEST_001")
    
    assert kpis["unique_visitors"] == 0
    assert kpis["conversion_rate"] == 0.0
    assert kpis["average_dwell_seconds"] == 0.0
    assert kpis["average_queue_depth"] == 0.0
    assert kpis["abandonment_rate"] == 0.0
    assert len(kpis["sessions"]) == 0

def test_no_transactions(db_session):
    """
    Test store analytics with events but no POS transactions.
    """
    base_time = datetime(2026, 3, 3, 10, 0, 0)
    
    # Ingest a customer session (ENTRY -> ZONE_ENTER -> EXIT)
    events = [
        Event(
            event_id="e1", store_id="STORE_TEST_001", camera_id="CAM_ENTRY_01",
            visitor_id="VIS_01", event_type="ENTRY", timestamp=base_time,
            confidence=0.95, is_staff=False
        ),
        Event(
            event_id="e2", store_id="STORE_TEST_001", camera_id="CAM_SKINCARE_01",
            visitor_id="VIS_01", event_type="ZONE_ENTER", timestamp=base_time + timedelta(minutes=2),
            zone_id="SKINCARE", confidence=0.92, is_staff=False
        ),
        Event(
            event_id="e3", store_id="STORE_TEST_001", camera_id="CAM_EXIT_01",
            visitor_id="VIS_01", event_type="EXIT", timestamp=base_time + timedelta(minutes=10),
            confidence=0.95, is_staff=False
        )
    ]
    db_session.add_all(events)
    db_session.commit()
    
    kpis = get_store_kpis(db_session, "STORE_TEST_001")
    
    assert kpis["unique_visitors"] == 1
    assert kpis["conversion_rate"] == 0.0  # No transactions means 0% conversion
    assert kpis["average_dwell_seconds"] == 600.0  # 10 minutes in seconds

def test_staff_exclusion(db_session):
    """
    Test that staff movements are excluded from customer analytics metrics.
    """
    base_time = datetime(2026, 3, 3, 10, 0, 0)
    
    # 1 Customer and 1 Staff member
    events = [
        # Customer Events
        Event(
            event_id="e1", store_id="STORE_TEST_001", camera_id="CAM_ENTRY_01",
            visitor_id="VIS_01", event_type="ENTRY", timestamp=base_time,
            confidence=0.95, is_staff=False
        ),
        Event(
            event_id="e2", store_id="STORE_TEST_001", camera_id="CAM_EXIT_01",
            visitor_id="VIS_01", event_type="EXIT", timestamp=base_time + timedelta(minutes=5),
            confidence=0.95, is_staff=False
        ),
        # Staff Events
        Event(
            event_id="s1", store_id="STORE_TEST_001", camera_id="CAM_ENTRY_01",
            visitor_id="STF_01", event_type="ENTRY", timestamp=base_time,
            confidence=0.95, is_staff=True
        ),
        Event(
            event_id="s2", store_id="STORE_TEST_001", camera_id="CAM_SKINCARE_01",
            visitor_id="STF_01", event_type="ZONE_ENTER", timestamp=base_time + timedelta(minutes=2),
            zone_id="SKINCARE", confidence=0.95, is_staff=True
        )
    ]
    db_session.add_all(events)
    db_session.commit()
    
    kpis = get_store_kpis(db_session, "STORE_TEST_001")
    
    # Unique visitors should be 1 (excluding staff member STF_01)
    assert kpis["unique_visitors"] == 1
    assert len(kpis["sessions"]) == 1
    assert kpis["sessions"][0]["visitor_id"] == "VIS_01"

def test_reentry(db_session):
    """
    Test that SessionAgent identifies visitors who exit and re-enter.
    """
    base_time = datetime(2026, 3, 3, 10, 0, 0)
    
    # Visitor VIS_01 visits twice (session_seq 1 and session_seq 2)
    events = [
        # Session 1
        Event(
            event_id="e1", store_id="STORE_TEST_001", camera_id="CAM_ENTRY_01",
            visitor_id="VIS_01", event_type="ENTRY", timestamp=base_time,
            confidence=0.95, is_staff=False, event_metadata={"session_seq": 1}
        ),
        Event(
            event_id="e2", store_id="STORE_TEST_001", camera_id="CAM_EXIT_01",
            visitor_id="VIS_01", event_type="EXIT", timestamp=base_time + timedelta(minutes=5),
            confidence=0.95, is_staff=False, event_metadata={"session_seq": 1}
        ),
        # Session 2 (Reentry)
        Event(
            event_id="e3", store_id="STORE_TEST_001", camera_id="CAM_ENTRY_01",
            visitor_id="VIS_01", event_type="REENTRY", timestamp=base_time + timedelta(hours=2),
            confidence=0.95, is_staff=False, event_metadata={"session_seq": 2}
        ),
        Event(
            event_id="e4", store_id="STORE_TEST_001", camera_id="CAM_EXIT_01",
            visitor_id="VIS_01", event_type="EXIT", timestamp=base_time + timedelta(hours=2, minutes=10),
            confidence=0.95, is_staff=False, event_metadata={"session_seq": 2}
        )
    ]
    db_session.add_all(events)
    db_session.commit()
    
    kpis = get_store_kpis(db_session, "STORE_TEST_001")
    
    # Unique visitors is still 1
    assert kpis["unique_visitors"] == 1
    # Sessions count should be 2
    assert len(kpis["sessions"]) == 2
    
    # Use SessionAgent directly to verify metrics dict
    raw_list = []
    for e in events:
        raw_list.append({
            "visitor_id": e.visitor_id,
            "store_id": e.store_id,
            "event_type": e.event_type,
            "timestamp": e.timestamp,
            "is_staff": e.is_staff,
            "metadata": e.event_metadata
        })
    agent = SessionAgent()
    res = agent.run(raw_list)
    assert res["metrics"]["reentry_count"] == 1
