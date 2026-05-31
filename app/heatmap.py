from sqlalchemy.orm import Session
from app.models import Event
from agents.heatmap_agent import HeatmapAgent

def get_store_heatmap(db: Session, store_id: str) -> dict:
    """
    Computes spatial and engagement statistics for all zones in a store.
    """
    # 1. Fetch store events
    db_events = db.query(Event).filter(Event.store_id == store_id).all()
    events = []
    for e in db_events:
        events.append({
            "event_id": e.event_id,
            "store_id": e.store_id,
            "camera_id": e.camera_id,
            "visitor_id": e.visitor_id,
            "event_type": e.event_type,
            "timestamp": e.timestamp,
            "zone_id": e.zone_id,
            "dwell_ms": e.dwell_ms,
            "is_staff": e.is_staff,
            "confidence": e.confidence,
            "metadata": e.event_metadata
        })
        
    # 2. Invoke Heatmap Agent
    heatmap_agent = HeatmapAgent(confidence_threshold=0.90)
    heatmap_report = heatmap_agent.run(events, exclude_staff=True)
    
    return {
        "store_id": store_id,
        "zones": heatmap_report["zones"],
        "reasoning_steps": heatmap_report["reasoning_steps"]
    }
