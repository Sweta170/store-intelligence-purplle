import os
os.environ["TESTING"] = "True"

import pytest
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app, get_db
from database.db import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Setup test database and dependency override using StaticPool
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Prepare tables once
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply override
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_api_health_endpoint():
    """
    Test GET /health returns the system status.
    """
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert "status" in json_data
    # Initially warning/empty DB
    assert json_data["status"] == "WARNING"

def test_api_events_ingest():
    """
    Test POST /events/ingest endpoint with raw CCTV events payload.
    """
    event_payload = [
        {
            "event_id": "api-e1",
            "store_id": "STORE_API_001",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": "VIS_API_01",
            "event_type": "ENTRY",
            "timestamp": "2026-03-03T10:00:00Z",
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.95
        },
        {
            "event_id": "api-e2",
            "store_id": "STORE_API_001",
            "camera_id": "CAM_SKINCARE_01",
            "visitor_id": "VIS_API_01",
            "event_type": "ZONE_ENTER",
            "timestamp": "2026-03-03T10:02:00Z",
            "zone_id": "SKINCARE",
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.95
        },
        {
            "event_id": "api-e3",
            "store_id": "STORE_API_001",
            "camera_id": "CAM_EXIT_01",
            "visitor_id": "VIS_API_01",
            "event_type": "EXIT",
            "timestamp": "2026-03-03T10:10:00Z",
            "dwell_ms": 600000,
            "is_staff": False,
            "confidence": 0.95
        }
    ]
    
    response = client.post("/events/ingest", json=event_payload)
    assert response.status_code == 201
    res_data = response.json()
    assert res_data["status"] == "SUCCESS"
    assert res_data["inserted_count"] == 3

def test_api_store_kpis():
    """
    Test GET /stores/{id}/metrics endpoint.
    """
    # Query KPIs for STORE_API_001
    response = client.get("/stores/STORE_API_001/metrics")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["store_id"] == "STORE_API_001"
    assert res_data["unique_visitors"] == 1
    assert res_data["conversion_rate"] == 0.0

def test_api_store_funnel():
    """
    Test GET /stores/{id}/funnel endpoint.
    """
    response = client.get("/stores/STORE_API_001/funnel")
    assert response.status_code == 200
    res_data = response.json()
    assert "funnel_counts" in res_data
    assert "funnel_percentages" in res_data

def test_api_store_heatmap():
    """
    Test GET /stores/{id}/heatmap endpoint.
    """
    response = client.get("/stores/STORE_API_001/heatmap")
    assert response.status_code == 200
    res_data = response.json()
    assert "zone_visits" in res_data
    assert "avg_dwell" in res_data
    assert "confidence_flag" in res_data

def test_api_store_anomalies():
    """
    Test GET /stores/{id}/anomalies endpoint.
    """
    response = client.get("/stores/STORE_API_001/anomalies")
    assert response.status_code == 200
    res_data = response.json()
    assert isinstance(res_data, list)

def test_api_store_executive_insights():
    """
    Test GET /stores/{id}/executive-insights endpoint.
    """
    response = client.get("/stores/STORE_API_001/executive-insights")
    assert response.status_code == 200
    res_data = response.json()
    assert "summary" in res_data
    assert "recommendations" in res_data

def test_api_missing_store():
    """
    Test GET routes for non-existent store return 404.
    """
    response = client.get("/stores/STORE_MISSING_123/metrics")
    assert response.status_code == 404


def test_api_events_ingest_extra_fields():
    """
    Test that events with extra fields can be successfully ingested and verified in the database.
    """
    event_payload = [
        {
            "event_id": "api-e-extra",
            "store_id": "STORE_API_EXTRA",
            "camera_id": "CAM_ENTRY_01",
            "visitor_id": "VIS_API_EXTRA",
            "event_type": "ENTRY",
            "timestamp": "2026-03-03T11:00:00Z",
            "dwell_ms": 0,
            "is_staff": False,
            "confidence": 0.98,
            "gender_pred": "Male",
            "age_pred": 30,
            "age_bucket": "18-35",
            "group_size": 1,
            "zone_name": "Main Entrance",
            "zone_type": "ENTRY"
        }
    ]
    response = client.post("/events/ingest", json=event_payload)
    assert response.status_code == 201
    
    # Retrieve the event from the test database to confirm it saved the extra fields
    db = next(override_get_db())
    from app.models import Event
    event = db.query(Event).filter(Event.event_id == "api-e-extra").first()
    assert event is not None
    assert event.gender_pred == "Male"
    assert event.age_pred == 30
    assert event.age_bucket == "18-35"
    assert event.group_size == 1
    assert event.zone_name == "Main Entrance"
    assert event.zone_type == "ENTRY"
    db.close()
