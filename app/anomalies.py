from sqlalchemy.orm import Session
from app.models import Anomaly
from app.metrics import get_store_kpis
from app.heatmap import get_store_heatmap
from agents.anomaly_agent import AnomalyAgent

def get_store_anomalies(db: Session, store_id: str) -> list:
    """
    Runs the AnomalyAgent, stores active alerts in the database, 
    and returns a serialized list of unresolved anomalies.
    """
    # 1. Fetch current store stats and heatmap
    kpi_data = get_store_kpis(db, store_id)
    heatmap_data = get_store_heatmap(db, store_id)
    
    # 2. Run Anomaly Agent detection rules
    anomaly_agent = AnomalyAgent()
    agent_report = anomaly_agent.run(
        store_id=store_id,
        events=kpi_data["raw_events"],
        transactions=kpi_data["raw_transactions"],
        heatmap_data=heatmap_data,
        conversion_rate=kpi_data["conversion_rate"]
    )
    
    detected = agent_report["anomalies"]
    
    # 3. Idempotent storage: Clear previous unresolved anomalies and sync
    db.query(Anomaly).filter(
        Anomaly.store_id == store_id, 
        Anomaly.is_resolved == False
    ).delete()
    
    db_anomalies = []
    for item in detected:
        db_anomalies.append(
            Anomaly(
                store_id=store_id,
                anomaly_type=item["anomaly_type"],
                severity=item["severity"],
                timestamp=item["timestamp"],
                details=item["details"],
                suggested_action=item["suggested_action"],
                is_resolved=False
            )
        )
        
    if db_anomalies:
        db.bulk_save_objects(db_anomalies)
        db.commit()
        
    # 4. Fetch the synced records
    active_db = db.query(Anomaly).filter(
        Anomaly.store_id == store_id, 
        Anomaly.is_resolved == False
    ).all()
    
    return [
        {
            "id": a.id,
            "store_id": a.store_id,
            "anomaly_type": a.anomaly_type,
            "severity": a.severity,
            "timestamp": a.timestamp,
            "details": a.details,
            "suggested_action": a.suggested_action,
            "is_resolved": a.is_resolved
        }
        for a in active_db
    ]
