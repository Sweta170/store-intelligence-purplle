from datetime import datetime
from typing import List, Dict, Any

class SessionAgent:
    def __init__(self):
        self.agent_name = "Session Agent"

    def run(self, events: List[Dict[str, Any]], exclude_staff: bool = True) -> Dict[str, Any]:
        """
        Processes a list of raw events to reconstruct visitor sessions.
        
        A session represents a single continuous visit to a store.
        It calculates:
        - Visitor ID
        - Store ID
        - Session Sequence Number
        - Start and End Timestamps
        - Session Duration (seconds)
        - Sequence of Zones Visited
        - Whether the visitor is staff
        
        Returns:
            A dictionary containing:
            - sessions: List of session objects.
            - visitor_summary: Map of visitor_id to their session count, total dwell time, etc.
            - reasoning_steps: List of text explanation logs of the agent's work.
        """
        reasoning_steps = []
        reasoning_steps.append("Starting visitor session reconstruction.")
        
        # Filter staff if required
        filtered_events = events
        if exclude_staff:
            filtered_events = [e for e in events if not e.get("is_staff")]
            reasoning_steps.append(f"Excluded staff events. Active event count: {len(filtered_events)} (original: {len(events)})")
        else:
            reasoning_steps.append(f"Processing all events including staff. Active event count: {len(filtered_events)}")
            
        # Group events by (visitor_id, store_id, session_seq)
        groups = {}
        for ev in filtered_events:
            v_id = ev.get("visitor_id")
            s_id = ev.get("store_id")
            meta = ev.get("metadata") or {}
            s_seq = meta.get("session_seq", 1)
            
            if not v_id or not s_id:
                continue
                
            key = (v_id, s_id, s_seq)
            if key not in groups:
                groups[key] = []
            groups[key].append(ev)
            
        sessions = []
        visitor_history = {} # visitor_id -> list of store sessions
        
        reasoning_steps.append(f"Grouped events into {len(groups)} distinct potential sessions.")
        
        for (v_id, s_id, s_seq), ev_list in groups.items():
            # Sort events in the session by timestamp
            def get_timestamp(e):
                t = e.get("timestamp")
                if isinstance(t, str):
                    return datetime.fromisoformat(t.replace("Z", "+00:00"))
                return t
            
            ev_list.sort(key=get_timestamp)
            
            start_ev = ev_list[0]
            end_ev = ev_list[-1]
            
            start_time = get_timestamp(start_ev)
            end_time = get_timestamp(end_ev)
            
            # Reconstruct zone sequences
            zone_sequence = []
            last_zone = None
            for ev in ev_list:
                z_id = ev.get("zone_id")
                e_type = ev.get("event_type")
                if z_id and e_type in ("ZONE_ENTER", "BILLING_QUEUE_JOIN"):
                    # Deduplicate consecutive transitions to same zone
                    if z_id != last_zone:
                        zone_sequence.append(z_id)
                        last_zone = z_id
            
            # Find explicit entry/exit points
            entry_type = None
            exit_type = None
            has_reentry = False
            
            for ev in ev_list:
                if ev.get("event_type") == "ENTRY":
                    entry_type = "ENTRY"
                elif ev.get("event_type") == "REENTRY":
                    entry_type = "REENTRY"
                    has_reentry = True
                elif ev.get("event_type") == "EXIT":
                    exit_type = "EXIT"
                    
            # Calculate duration in seconds
            duration_sec = (end_time - start_time).total_seconds()
            
            # If the session has zone dwell, maybe use that or total entry-exit time
            # For EXIT, the dwell_ms field usually contains total session duration.
            # Let's trust the timestamp difference as it is robust.
            
            session_data = {
                "visitor_id": v_id,
                "store_id": s_id,
                "session_seq": s_seq,
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": max(0.0, duration_sec),
                "zone_sequence": zone_sequence,
                "is_staff": start_ev.get("is_staff", False),
                "has_reentry": has_reentry or (s_seq > 1),
                "events_count": len(ev_list)
            }
            
            sessions.append(session_data)
            
            if v_id not in visitor_history:
                visitor_history[v_id] = []
            visitor_history[v_id].append(session_data)
            
        # Analyze re-entries and patterns
        reentrant_visitors_count = 0
        total_dwell_all = 0.0
        
        for v_id, s_list in visitor_history.items():
            if len(s_list) > 1:
                reentrant_visitors_count += 1
            for s in s_list:
                total_dwell_all += s["duration_seconds"]
                
        reasoning_steps.append(
            f"Reconstructed {len(sessions)} clean visitor sessions. "
            f"Detected {reentrant_visitors_count} visitors showing re-entry behavior. "
            f"Average session duration: {round(total_dwell_all / len(sessions), 1) if sessions else 0} seconds."
        )
        
        return {
            "agent_name": self.agent_name,
            "status": "SUCCESS",
            "sessions": sessions,
            "visitor_summary": {
                v_id: {
                    "sessions_count": len(s_list),
                    "total_dwell_seconds": sum(s["duration_seconds"] for s in s_list),
                    "reentered": len(s_list) > 1
                }
                for v_id, s_list in visitor_history.items()
            },
            "metrics": {
                "total_sessions": len(sessions),
                "unique_visitors": len(visitor_history),
                "reentry_count": reentrant_visitors_count,
                "average_dwell_seconds": total_dwell_all / len(sessions) if sessions else 0.0
            },
            "reasoning_steps": reasoning_steps
        }
