from sqlalchemy.orm import Session
from app.metrics import get_store_kpis
from agents.funnel_agent import FunnelAgent

def get_store_funnel(db: Session, store_id: str) -> dict:
    """
    Computes funnel counts and conversion rates for a specific store.
    """
    # 1. Reuse high-level metrics calculator (avoids redundant code)
    kpi_data = get_store_kpis(db, store_id)
    
    # 2. Invoke Funnel Agent
    funnel_agent = FunnelAgent()
    funnel_report = funnel_agent.run(
        sessions=kpi_data["sessions"],
        converted_visitor_ids=kpi_data["converted_visitor_ids"]
    )
    
    return {
        "store_id": store_id,
        "funnel_stages": funnel_report["stages"],
        "summary": funnel_report["summary"],
        "reasoning_steps": funnel_report["reasoning_steps"]
    }
