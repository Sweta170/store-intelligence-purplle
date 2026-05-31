import os
import json
import csv
from datetime import datetime
from typing import List
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from database.db import engine, Base, get_db
from app.models import Event, POSTransaction
from app.ingestion import ingest_events_batch, EventIngestSchema, IngestionResultSchema
from app.metrics import get_store_kpis
from app.funnel import get_store_funnel
from app.heatmap import get_store_heatmap
from app.anomalies import get_store_anomalies
from app.health import check_system_health
from agents.executive_insights_agent import ExecutiveInsightsAgent

# Initialize FastAPI application
app = FastAPI(
    title="Retail Store Intelligence Platform API",
    description="CCTV-based retail analytics API simulating traffic, funnel, heatmap and anomalies.",
    version="1.0.0"
)

# Startup DB Migration & Seeding
@app.on_event("startup")
def startup_db_setup():
    print("Database initialization: Creating tables...")
    Base.metadata.create_all(bind=engine)
    if os.getenv("TESTING") == "True":
        return
    
    # Check if database already has records
    db = next(get_db())
    try:
        event_count = db.query(Event).count()
        tx_count = db.query(POSTransaction).count()
        
        print(f"Current DB state: {event_count} events, {tx_count} transactions.")
        
        if event_count == 0 and tx_count == 0:
            print("DB is empty. Seeding with synthetic datasets...")
            
            # 1. Seed POS transactions
            tx_path = "data/pos_transactions.csv"
            if os.path.exists(tx_path):
                print(f"Loading transactions from {tx_path}...")
                with open(tx_path, "r") as f:
                    reader = csv.DictReader(f)
                    db_txs = []
                    for row in reader:
                        ts = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                        db_txs.append(
                            POSTransaction(
                                transaction_id=row["transaction_id"],
                                store_id=row["store_id"],
                                timestamp=ts,
                                basket_value_inr=int(row["basket_value_inr"])
                            )
                        )
                    if db_txs:
                        db.bulk_save_objects(db_txs)
                        db.commit()
                        print(f"Seeded {len(db_txs)} transactions.")
            else:
                print(f"Warning: Transactions file not found at {tx_path}")

            # 2. Seed Events (bulk load in chunks to prevent memory spikes)
            events_path = "data/events.jsonl"
            if os.path.exists(events_path):
                print(f"Loading events from {events_path}...")
                db_events = []
                with open(events_path, "r") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        ev = json.loads(line)
                        ts = datetime.fromisoformat(ev["timestamp"].replace("Z", "+00:00"))
                        db_events.append(
                            Event(
                                event_id=ev["event_id"],
                                store_id=ev["store_id"],
                                camera_id=ev["camera_id"],
                                visitor_id=ev["visitor_id"],
                                event_type=ev["event_type"],
                                timestamp=ts,
                                zone_id=ev.get("zone_id"),
                                dwell_ms=ev.get("dwell_ms", 0),
                                is_staff=ev.get("is_staff", False),
                                confidence=ev["confidence"],
                                event_metadata=ev.get("metadata")
                            )
                        )
                        
                        # Commit in chunks of 2000
                        if len(db_events) >= 2000:
                            db.bulk_save_objects(db_events)
                            db.commit()
                            db_events = []
                            
                if db_events:
                    db.bulk_save_objects(db_events)
                    db.commit()
                print(f"Seeded events database completely.")
            else:
                print(f"Warning: Events file not found at {events_path}")
                
    except Exception as e:
        print(f"Error during startup database setup: {str(e)}")
        db.rollback()
    finally:
        db.close()

# API Routes

@app.post("/events/ingest", response_model=IngestionResultSchema, status_code=201)
def ingest_events(events: List[EventIngestSchema], db: Session = Depends(get_db)):
    """
    Ingests a batch of CCTV events.
    Fails or skips duplicates, low-confidence entries, and schema mismatches.
    """
    # Convert schemas to raw dicts for validation agent
    raw_list = [ev.dict() for ev in events]
    result = ingest_events_batch(db, raw_list)
    return result

@app.get("/stores/{store_id}/metrics")
def get_metrics(store_id: str, db: Session = Depends(get_db)):
    """
    Returns high-level retail store analytics:
    - Unique Visitors
    - Conversion Rate (%)
    - Average Dwell Time (s)
    - Queue Depth
    - Abandonment Rate (%)
    """
    # Check if store exists in database (or general layout)
    store_events_exist = db.query(Event).filter(Event.store_id == store_id).first()
    if not store_events_exist:
        raise HTTPException(status_code=404, detail=f"Store '{store_id}' has no registered events or does not exist.")
        
    kpis = get_store_kpis(db, store_id)
    return {
        "store_id": kpis["store_id"],
        "unique_visitors": kpis["unique_visitors"],
        "conversion_rate": kpis["conversion_rate"],
        "average_dwell": kpis["average_dwell_seconds"],
        "queue_depth": kpis["average_queue_depth"],
        "abandonment_rate": kpis["abandonment_rate"]
    }

@app.get("/stores/{store_id}/funnel")
def get_funnel(store_id: str, db: Session = Depends(get_db)):
    """
    Returns visitor conversion funnel:
    Entry -> Zone Visit -> Billing Queue -> Purchase.
    """
    store_events_exist = db.query(Event).filter(Event.store_id == store_id).first()
    if not store_events_exist:
        raise HTTPException(status_code=404, detail=f"Store '{store_id}' does not exist.")
        
    funnel = get_store_funnel(db, store_id)
    return {
        "store_id": funnel["store_id"],
        "funnel_counts": [
            {"stage": s["stage_name"], "count": s["count"]} for s in funnel["funnel_stages"]
        ],
        "funnel_percentages": [
            {"stage": s["stage_name"], "percentage": s["conversion_rate_pct"]} for s in funnel["funnel_stages"]
        ]
    }

@app.get("/stores/{store_id}/heatmap")
def get_heatmap(store_id: str, db: Session = Depends(get_db)):
    """
    Returns spatial performance metrics (Visits, Avg Dwell) for all zones inside a store.
    """
    store_events_exist = db.query(Event).filter(Event.store_id == store_id).first()
    if not store_events_exist:
        raise HTTPException(status_code=404, detail=f"Store '{store_id}' does not exist.")
        
    heatmap = get_store_heatmap(db, store_id)
    
    # Format zone visits and avg dwell
    zone_visits = {z_id: data["visits"] for z_id, data in heatmap["zones"].items()}
    avg_dwell = {z_id: data["average_dwell_seconds"] for z_id, data in heatmap["zones"].items()}
    
    # Determine if any camera zone is flagged low confidence
    has_low_confidence = any(data["low_confidence_flag"] for data in heatmap["zones"].values())
    
    return {
        "store_id": store_id,
        "zone_visits": zone_visits,
        "avg_dwell": avg_dwell,
        "confidence_flag": has_low_confidence
    }

@app.get("/stores/{store_id}/anomalies")
def get_anomalies(store_id: str, db: Session = Depends(get_db)):
    """
    Scans the database and returns a list of active store operational anomalies.
    """
    store_events_exist = db.query(Event).filter(Event.store_id == store_id).first()
    if not store_events_exist:
        raise HTTPException(status_code=404, detail=f"Store '{store_id}' does not exist.")
        
    anomalies = get_store_anomalies(db, store_id)
    return [
        {
            "anomaly_type": a["anomaly_type"],
            "severity": a["severity"],
            "suggested_action": a["suggested_action"],
            "details": a["details"],
            "timestamp": a["timestamp"].isoformat() + "Z" if isinstance(a["timestamp"], datetime) else a["timestamp"]
        }
        for a in anomalies
    ]

@app.get("/stores/{store_id}/executive-insights")
def get_executive_insights(store_id: str, db: Session = Depends(get_db)):
    """
    Executes ExecutiveInsightsAgent to generate text/markdown reports and actionable suggestions.
    """
    store_events_exist = db.query(Event).filter(Event.store_id == store_id).first()
    if not store_events_exist:
        raise HTTPException(status_code=404, detail=f"Store '{store_id}' does not exist.")
        
    kpis = get_store_kpis(db, store_id)
    funnel = get_store_funnel(db, store_id)
    heatmap = get_store_heatmap(db, store_id)
    anomalies = get_store_anomalies(db, store_id)
    
    insights_agent = ExecutiveInsightsAgent()
    insights = insights_agent.run(store_id, kpis, funnel, heatmap, anomalies)
    
    return {
        "store_id": store_id,
        "summary": insights["summary"],
        "recommendations": insights["recommendations"],
        "reasoning_steps": insights["reasoning_steps"]
    }

@app.get("/health")
def get_health(db: Session = Depends(get_db)):
    """
    Returns general service health status and camera stale feed checks.
    """
    return check_system_health(db)
