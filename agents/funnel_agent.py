from typing import List, Dict, Any

class FunnelAgent:
    def __init__(self):
        self.agent_name = "Funnel Agent"

    def run(self, sessions: List[Dict[str, Any]], converted_visitor_ids: List[str]) -> Dict[str, Any]:
        """
        Calculates funnel metrics for visitors:
        1. Entry: Total unique customers
        2. Zone Visit: Visited at least one product zone (Skincare, Makeup, Fragrance, Haircare)
        3. Billing Queue: Joined billing queue
        4. Purchase: Converted to transaction
        
        Returns:
            A dictionary containing:
            - funnel_stages: List of stages with counts, percentages, and drop-offs.
            - summary: Basic summary stats.
            - reasoning_steps: Explanation logs of the funnel calculations.
        """
        reasoning_steps = []
        reasoning_steps.append("Starting Funnel Stage calculations.")
        
        # Unique customer sets
        entry_visitors = set()
        zone_visitors = set()
        billing_visitors = set()
        purchase_visitors = set(converted_visitor_ids)
        
        product_zones = {"SKINCARE", "MAKEUP", "FRAGRANCE", "HAIRCARE"}
        
        for sess in sessions:
            v_id = sess["visitor_id"]
            if sess.get("is_staff"):
                continue
                
            entry_visitors.add(v_id)
            
            # Check if they visited product zones
            zones_in_seq = set(sess.get("zone_sequence") or [])
            if zones_in_seq.intersection(product_zones):
                zone_visitors.add(v_id)
                
            # Check if they went to Billing queue
            if "BILLING" in zones_in_seq:
                billing_visitors.add(v_id)
                
        # Purchase visitors must be a subset of entries (in case of data anomalies, align them)
        purchase_visitors = purchase_visitors.intersection(entry_visitors)
        
        # Ensure strict funnel logic (each stage is subset of previous)
        # However, because of anomalies or custom paths, we will compute them as they are and apply hierarchical filtering if preferred,
        # or report actual counts. Let's report actual counts as it reflects realistic data, but keep progression:
        # Billing visitors could potentially be visitors who skipped product zones?
        # Yes, but usually they visit zones. Let's just track:
        # Stage 1: Entered Store
        # Stage 2: Visited Product Zone
        # Stage 3: Entered Billing Queue (and visited a product zone, or just overall billing)
        # Stage 4: Converted (and entered billing queue, or overall)
        # Let's count them directly:
        c_entry = len(entry_visitors)
        c_zone = len(zone_visitors)
        c_billing = len(billing_visitors)
        c_purchase = len(purchase_visitors)
        
        reasoning_steps.append(
            f"Calculated unique customer counts - Entry: {c_entry}, Zone Visit: {c_zone}, "
            f"Billing Queue: {c_billing}, Purchase: {c_purchase}."
        )
        
        # Build stage metrics
        stages = [
            {
                "stage_id": 1,
                "stage_name": "Entry",
                "count": c_entry,
                "conversion_rate_pct": 100.0,
                "dropoff_pct": 0.0
            },
            {
                "stage_id": 2,
                "stage_name": "Zone Visit",
                "count": c_zone,
                "conversion_rate_pct": round((c_zone / c_entry * 100.0), 2) if c_entry > 0 else 0.0,
                "dropoff_pct": round((100.0 - (c_zone / c_entry * 100.0)), 2) if c_entry > 0 else 0.0
            },
            {
                "stage_id": 3,
                "stage_name": "Billing Queue",
                "count": c_billing,
                "conversion_rate_pct": round((c_billing / c_zone * 100.0), 2) if c_zone > 0 else 0.0,
                "dropoff_pct": round((100.0 - (c_billing / c_zone * 100.0)), 2) if c_zone > 0 else 0.0
            },
            {
                "stage_id": 4,
                "stage_name": "Purchase",
                "count": c_purchase,
                "conversion_rate_pct": round((c_purchase / c_billing * 100.0), 2) if c_billing > 0 else 0.0,
                "dropoff_pct": round((100.0 - (c_purchase / c_billing * 100.0)), 2) if c_billing > 0 else 0.0
            }
        ]
        
        reasoning_steps.append("Funnel stages and drop-offs computed successfully.")
        
        return {
            "agent_name": self.agent_name,
            "status": "SUCCESS",
            "stages": stages,
            "summary": {
                "total_entries": c_entry,
                "total_purchases": c_purchase,
                "overall_funnel_conversion_pct": round((c_purchase / c_entry * 100.0), 2) if c_entry > 0 else 0.0
            },
            "reasoning_steps": reasoning_steps
        }
