from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.models import Event
from agents.event_validation_agent import EventValidationAgent

# Pydantic schemas for request validation
class EventMetadataSchema(BaseModel):
    queue_depth: Optional[int] = None
    session_seq: Optional[int] = 1

class EventIngestSchema(BaseModel):
    event_id: str = Field(..., description="Unique event UUID")
    store_id: str = Field(..., description="Store Identifier")
    camera_id: str = Field(..., description="Camera ID")
    visitor_id: str = Field(..., description="Visitor or Staff Identifier")
    event_type: str = Field(..., description="ENTRY, EXIT, ZONE_ENTER, etc.")
    timestamp: datetime = Field(..., description="ISO 8601 timestamp")
    zone_id: Optional[str] = Field(None, description="Department Zone ID")
    dwell_ms: Optional[int] = Field(0, description="Dwell time in milliseconds")
    is_staff: Optional[bool] = Field(False, description="True if visitor is staff")
    confidence: float = Field(..., description="Camera reading confidence")
    metadata: Optional[EventMetadataSchema] = None

class IngestionResultSchema(BaseModel):
    status: str
    processed_count: int
    inserted_count: int
    duplicates_skipped: int
    low_confidence_skipped: int
    schema_failures: int
    errors: List[Dict[str, Any]]

def ingest_events_batch(db: Session, raw_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ingests a batch of events:
    1. Queries DB to find any pre-existing event IDs in the batch (for idempotency).
    2. Runs EventValidationAgent on the batch.
    3. Saves valid events to the database.
    """
    event_ids = [e.get("event_id") for e in raw_events if e.get("event_id")]
    
    # Query database for existing IDs to enforce idempotency
    existing_ids = []
    if event_ids:
        existing_db_events = db.query(Event.event_id).filter(Event.event_id.in_(event_ids)).all()
        existing_ids = [r[0] for r in existing_db_events]
        
    # Execute Validation Agent
    validation_agent = EventValidationAgent(confidence_threshold=0.5)
    valid_events, report = validation_agent.run(raw_events, existing_event_ids=existing_ids)
    
    # Insert valid events into DB
    db_objects = []
    for ev in valid_events:
        # Standardize metadata serialization
        meta_dict = ev.get("metadata")
        if isinstance(meta_dict, BaseModel):
            meta_dict = meta_dict.dict()
            
        # Parse timestamp string to datetime object if it's a string
        ts = ev.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            
        db_obj = Event(
            event_id=ev.get("event_id"),
            store_id=ev.get("store_id"),
            camera_id=ev.get("camera_id"),
            visitor_id=ev.get("visitor_id"),
            event_type=ev.get("event_type"),
            timestamp=ts,
            zone_id=ev.get("zone_id"),
            dwell_ms=ev.get("dwell_ms", 0),
            is_staff=ev.get("is_staff", False),
            confidence=ev.get("confidence"),
            event_metadata=meta_dict
        )
        db_objects.append(db_obj)
        
    if db_objects:
        db.bulk_save_objects(db_objects)
        db.commit()
        
    return {
        "status": "SUCCESS" if len(valid_events) == len(raw_events) else "PARTIAL_SUCCESS",
        "processed_count": len(raw_events),
        "inserted_count": len(db_objects),
        "duplicates_skipped": report["stats"]["duplicates_discarded"],
        "low_confidence_skipped": report["stats"]["low_confidence_filtered"],
        "schema_failures": report["stats"]["schema_violations"],
        "errors": [{"event_id": item["event"].get("event_id"), "reason": item["reason"]} for item in report["invalid_events"]]
    }
