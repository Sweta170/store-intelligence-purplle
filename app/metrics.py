from sqlalchemy.orm import Session
from app.models import Event, POSTransaction
from agents.session_agent import SessionAgent
from agents.conversion_agent import ConversionAgent

def get_store_kpis(db: Session, store_id: str) -> dict:
    """
    Computes high-level KPIs for a store:
    - Unique Visitors
    - Conversion Rate
    - Average Dwell Time (seconds)
    - Average Queue Depth
    - Queue Abandonment Rate
    """
    # 1. Fetch all events for the store
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
        
    # 2. Fetch all transactions for the store
    db_txs = db.query(POSTransaction).filter(POSTransaction.store_id == store_id).all()
    txs = []
    for t in db_txs:
        txs.append({
            "store_id": t.store_id,
            "transaction_id": t.transaction_id,
            "timestamp": t.timestamp,
            "basket_value_inr": t.basket_value_inr
        })

    # 3. Invoke Session Agent
    session_agent = SessionAgent()
    session_report = session_agent.run(events, exclude_staff=True)
    
    unique_visitors = session_report["metrics"]["unique_visitors"]
    avg_dwell = session_report["metrics"]["average_dwell_seconds"]
    
    # 4. Filter billing events for Conversion Agent
    billing_events = [e for e in events if e["event_type"] in ("BILLING_QUEUE_JOIN", "BILLING_QUEUE_ABANDON") or e["zone_id"] == "BILLING"]
    
    # Invoke Conversion Agent
    conversion_agent = ConversionAgent(time_window_seconds=300)
    conversion_report = conversion_agent.run(billing_events, txs, unique_visitors)
    
    conversion_rate = conversion_report["conversion_rate"]
    
    # 5. Queue statistics (joins vs abandons)
    queue_joins = sum(1 for e in events if e["event_type"] == "BILLING_QUEUE_JOIN" and not e["is_staff"])
    queue_abandons = sum(1 for e in events if e["event_type"] == "BILLING_QUEUE_ABANDON" and not e["is_staff"])
    
    abandon_rate = 0.0
    if queue_joins > 0:
        abandon_rate = (queue_abandons / queue_joins) * 100.0
        
    # Average queue depth from joins
    q_depths = [e["metadata"].get("queue_depth", 0) for e in events if e["event_type"] == "BILLING_QUEUE_JOIN" and e.get("metadata") and not e["is_staff"]]
    avg_queue_depth = sum(q_depths) / len(q_depths) if q_depths else 0.0

    return {
        "store_id": store_id,
        "unique_visitors": unique_visitors,
        "conversion_rate": round(conversion_rate, 2),
        "average_dwell_seconds": round(avg_dwell, 1),
        "average_queue_depth": round(avg_queue_depth, 2),
        "abandonment_rate": round(abandon_rate, 2),
        "sessions": session_report["sessions"],
        "converted_visitor_ids": conversion_report["converted_visitor_ids"],
        "raw_events": events,
        "raw_transactions": txs
    }
