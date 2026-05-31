from datetime import datetime, timedelta
from typing import List, Dict, Any

class AnomalyAgent:
    def __init__(self):
        self.agent_name = "Anomaly Agent"

    def run(
        self, 
        store_id: str, 
        events: List[Dict[str, Any]], 
        transactions: List[Dict[str, Any]], 
        heatmap_data: Dict[str, Any], 
        conversion_rate: float,
        current_reference_time: datetime = None
    ) -> Dict[str, Any]:
        """
        Scans events and metrics to detect store anomalies:
        - QUEUE_SPIKE: Queue depth exceeds threshold (> 5).
        - CONVERSION_DROP: Conversion rate falls below threshold (< 15%).
        - DEAD_ZONE: Zone has 0 or extremely low visits.
        - STALE_FEED: No events from a camera for > 15 minutes during operating hours.
        
        Returns:
            A dictionary containing:
            - anomalies: List of detected anomalies.
            - reasoning_steps: Explanation logs.
        """
        reasoning_steps = []
        reasoning_steps.append(f"Starting anomaly scan for store {store_id}.")
        
        anomalies = []
        
        # Sort helper
        def get_timestamp(obj):
            t = obj.get("timestamp")
            if isinstance(t, str):
                return datetime.fromisoformat(t.replace("Z", "+00:00"))
            return t

        if not events:
            reasoning_steps.append("No event data available. Stale feed triggered for the whole store.")
            anomalies.append({
                "store_id": store_id,
                "anomaly_type": "STALE_FEED",
                "severity": "CRITICAL",
                "timestamp": current_reference_time or datetime.utcnow(),
                "details": "No events received for this store. Entire feed appears offline.",
                "suggested_action": "Check main network router and verify edge computer status."
            })
            return {
                "agent_name": self.agent_name,
                "status": "SUCCESS",
                "anomalies": anomalies,
                "reasoning_steps": reasoning_steps
            }

        sorted_events = sorted(events, key=get_timestamp)
        latest_event_time = get_timestamp(sorted_events[-1])
        ref_time = current_reference_time or latest_event_time
        
        # 1. QUEUE_SPIKE Detection
        # Check all queue join events for large queue depths
        max_q_depth = 0
        spike_time = None
        for ev in events:
            if ev.get("event_type") == "BILLING_QUEUE_JOIN":
                meta = ev.get("metadata") or {}
                depth = meta.get("queue_depth", 0)
                if depth > max_q_depth:
                    max_q_depth = depth
                    spike_time = get_timestamp(ev)
                    
        if max_q_depth > 5:
            severity = "CRITICAL" if max_q_depth > 8 else "WARN"
            anomalies.append({
                "store_id": store_id,
                "anomaly_type": "QUEUE_SPIKE",
                "severity": severity,
                "timestamp": spike_time or ref_time,
                "details": f"Billing queue depth reached {max_q_depth} (Threshold: 5). High customer wait time.",
                "suggested_action": "Open additional billing counter and deploy backup cashier."
            })
            reasoning_steps.append(f"Detected QUEUE_SPIKE anomaly with max depth of {max_q_depth}.")

        # 2. CONVERSION_DROP Detection
        # We need at least some traffic to evaluate conversion drops reliably
        unique_visitors = len(set(e.get("visitor_id") for e in events if not e.get("is_staff")))
        if unique_visitors >= 10:
            if conversion_rate < 15.0:
                severity = "CRITICAL" if conversion_rate < 8.0 else "WARN"
                anomalies.append({
                    "store_id": store_id,
                    "anomaly_type": "CONVERSION_DROP",
                    "severity": severity,
                    "timestamp": ref_time,
                    "details": f"Conversion rate dropped to {round(conversion_rate, 2)}% (Threshold: 15%).",
                    "suggested_action": "Verify if queue times are causing checkout abandonment, or adjust pricing/promotions."
                })
                reasoning_steps.append(f"Detected CONVERSION_DROP anomaly: {round(conversion_rate, 2)}%.")

        # 3. DEAD_ZONE Detection
        # Compare defined zones to active ones in heatmap_data
        defined_zones = ["SKINCARE", "MAKEUP", "FRAGRANCE", "HAIRCARE", "BILLING"]
        active_zones = heatmap_data.get("zones", {})
        
        for zone in defined_zones:
            zone_visits = active_zones.get(zone, {}).get("visits", 0)
            if zone_visits == 0:
                anomalies.append({
                    "store_id": store_id,
                    "anomaly_type": "DEAD_ZONE",
                    "severity": "WARN",
                    "timestamp": ref_time,
                    "details": f"Zone '{zone}' recorded zero visitor interactions during active business hours.",
                    "suggested_action": f"Check visual display setup in '{zone}' or verify camera CAM_{zone}_01 feed status."
                })
                reasoning_steps.append(f"Detected DEAD_ZONE anomaly for zone '{zone}'.")

        # 4. STALE_FEED Detection
        # We check the difference between the overall latest event and each camera's latest event.
        # If a camera hasn't sent events for > 15 minutes while the store is active, it's stale.
        camera_latest = {}
        for ev in events:
            cam = ev.get("camera_id")
            if cam:
                t = get_timestamp(ev)
                if cam not in camera_latest or t > camera_latest[cam]:
                    camera_latest[cam] = t
                    
        # Check standard cameras mapping
        for cam_name, cam_id in [
            ("Entry", "CAM_ENTRY_01"),
            ("Exit", "CAM_EXIT_01"),
            ("Skincare", "CAM_SKINCARE_01"),
            ("Makeup", "CAM_MAKEUP_01"),
            ("Fragrance", "CAM_FRAGRANCE_01"),
            ("Haircare", "CAM_HAIRCARE_01"),
            ("Billing", "CAM_BILLING_01")
        ]:
            if cam_id in camera_latest:
                cam_last_time = camera_latest[cam_id]
                gap_minutes = (latest_event_time - cam_last_time).total_seconds() / 60.0
                if gap_minutes > 15.0:
                    anomalies.append({
                        "store_id": store_id,
                        "anomaly_type": "STALE_FEED",
                        "severity": "CRITICAL",
                        "timestamp": latest_event_time,
                        "details": f"Camera '{cam_id}' ({cam_name}) has not sent feeds for {round(gap_minutes, 1)} minutes.",
                        "suggested_action": f"Verify hardware connection and restart streaming container for '{cam_id}'."
                    })
                    reasoning_steps.append(f"Detected STALE_FEED anomaly for camera {cam_id} (gap: {round(gap_minutes, 1)}m).")
            else:
                # Camera has never sent an event in this session
                anomalies.append({
                    "store_id": store_id,
                    "anomaly_type": "STALE_FEED",
                    "severity": "CRITICAL",
                    "timestamp": latest_event_time,
                    "details": f"Camera '{cam_id}' ({cam_name}) is completely missing from logs (no events sent).",
                    "suggested_action": f"Inspect camera wiring and verify configuration settings in layout JSON."
                })
                reasoning_steps.append(f"Detected STALE_FEED anomaly: camera {cam_id} missing completely.")

        reasoning_steps.append(f"Scan completed. Total anomalies found: {len(anomalies)}.")
        
        return {
            "agent_name": self.agent_name,
            "status": "SUCCESS",
            "anomalies": anomalies,
            "reasoning_steps": reasoning_steps
        }
