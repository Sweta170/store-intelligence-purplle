from typing import List, Dict, Any

class HeatmapAgent:
    def __init__(self, confidence_threshold: float = 0.90):
        self.confidence_threshold = confidence_threshold
        self.agent_name = "Heatmap Agent"

    def run(self, events: List[Dict[str, Any]], exclude_staff: bool = True) -> Dict[str, Any]:
        """
        Calculates heatmap statistics for each zone:
        - Total visits (based on ZONE_ENTER and BILLING_QUEUE_JOIN events)
        - Average dwell time (seconds, from ZONE_DWELL / ZONE_EXIT / BILLING_QUEUE_ABANDON events)
        - Engagement score (Visits * Avg Dwell in Minutes)
        - Average confidence score
        - Low confidence warning flag
        
        Returns:
            A dictionary containing:
            - zones: Map of zone_id to its heatmap metrics.
            - reasoning_steps: Explanation logs of heatmap calculations.
        """
        reasoning_steps = []
        reasoning_steps.append("Starting Heatmap aggregation by zone.")
        
        # Filter staff if required
        filtered_events = events
        if exclude_staff:
            filtered_events = [e for e in events if not e.get("is_staff")]
            reasoning_steps.append(f"Excluded staff events from heatmap calculations.")
            
        zone_data = {}
        
        for ev in filtered_events:
            z_id = ev.get("zone_id")
            if not z_id:
                continue
                
            if z_id not in zone_data:
                zone_data[z_id] = {
                    "enter_events": 0,
                    "dwell_times": [],
                    "confidence_scores": []
                }
                
            e_type = ev.get("event_type")
            conf = ev.get("confidence", 1.0)
            dwell = ev.get("dwell_ms", 0)
            
            # Count visits on ENTER or JOIN queue
            if e_type in ("ZONE_ENTER", "BILLING_QUEUE_JOIN"):
                zone_data[z_id]["enter_events"] += 1
                
            # Collect dwell times from DWELL, EXIT, or ABANDON
            if e_type in ("ZONE_DWELL", "ZONE_EXIT", "BILLING_QUEUE_ABANDON") and dwell > 0:
                zone_data[z_id]["dwell_times"].append(dwell / 1000.0) # convert to seconds
                
            # Collect confidence
            zone_data[z_id]["confidence_scores"].append(conf)
            
        zones_summary = {}
        for z_id, data in zone_data.items():
            visits = data["enter_events"]
            dwells = data["dwell_times"]
            confs = data["confidence_scores"]
            
            avg_dwell = sum(dwells) / len(dwells) if dwells else 0.0
            avg_conf = sum(confs) / len(confs) if confs else 1.0
            
            # Calculate engagement score: visits * avg_dwell_minutes
            avg_dwell_mins = avg_dwell / 60.0
            engagement_score = round(visits * avg_dwell_mins, 2)
            
            # Check confidence warning
            low_confidence_flag = avg_conf < self.confidence_threshold
            
            zones_summary[z_id] = {
                "visits": visits,
                "average_dwell_seconds": round(avg_dwell, 1),
                "average_dwell_minutes": round(avg_dwell_mins, 2),
                "engagement_score": engagement_score,
                "average_confidence": round(avg_conf, 3),
                "low_confidence_flag": low_confidence_flag
            }
            
        reasoning_steps.append(
            f"Successfully aggregated metrics for {len(zones_summary)} active zones. "
            f"Zones detected: {', '.join(zones_summary.keys())}."
        )
        
        return {
            "agent_name": self.agent_name,
            "status": "SUCCESS",
            "zones": zones_summary,
            "reasoning_steps": reasoning_steps
        }
