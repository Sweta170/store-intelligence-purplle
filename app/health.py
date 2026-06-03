from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Event
from datetime import datetime

def check_system_health(db: Session) -> dict:
    """
    Evaluates system health:
    - Verifies DB connection.
    - Resolves the last ingested event's timestamp.
    - Analyzes camera-level stale feed warnings relative to overall active logs.
    """
    warnings = []
    status = "OK"
    last_timestamp = None
    
    try:
        # Check DB connection by fetching latest event timestamp
        latest_event = db.query(Event.timestamp).order_by(Event.timestamp.desc()).first()
        if latest_event:
            last_timestamp = latest_event[0]
            
            # Find active cameras and their latest event times
            camera_times = db.query(
                Event.camera_id, 
                func.max(Event.timestamp)
            ).group_by(Event.camera_id).all()
            
            for cam_id, cam_max_time in camera_times:
                gap_seconds = (last_timestamp - cam_max_time).total_seconds()
                gap_minutes = gap_seconds / 60.0
                if gap_minutes > 15.0:
                    warnings.append(
                        f"Camera {cam_id} feed is stale: no event received for {round(gap_minutes, 1)} minutes."
                    )
        else:
            status = "WARNING"
            warnings.append("Database is empty. No events ingested yet.")
            
    except Exception as e:
        status = "CRITICAL"
        warnings.append(f"Database connection error: {str(e)}")
        
    return {
        "status": status,
        "service_status": status,
        "last_event_timestamp": last_timestamp.isoformat() + "Z" if last_timestamp else None,
        "latest_event_timestamp": last_timestamp.isoformat() + "Z" if last_timestamp else None,
        "stale_feed_warnings": warnings
    }
