from typing import List, Dict, Any

class ExecutiveInsightsAgent:
    def __init__(self):
        self.agent_name = "Executive Insights Agent"

    def run(
        self, 
        store_id: str, 
        metrics: Dict[str, Any], 
        funnel_data: Dict[str, Any], 
        heatmap_data: Dict[str, Any], 
        anomalies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesizes store performance and provides executive business summaries and recommendations.
        
        Returns:
            A dictionary containing:
            - summary: Plain text summary.
            - recommendations: Markdown-formatted list of business insights and actions.
            - reasoning_steps: Explanation logs of how decisions were compiled.
        """
        reasoning_steps = []
        reasoning_steps.append(f"Compiling executive intelligence report for store {store_id}.")
        
        unique_visitors = metrics.get("unique_visitors", 0)
        conversion_rate = metrics.get("conversion_rate", 0.0)
        avg_dwell_sec = metrics.get("average_dwell_seconds", 0.0)
        reentry_count = metrics.get("reentry_count", 0)
        abandonment_rate = metrics.get("abandonment_rate", 0.0)
        
        # 1. Identify best and worst zones from heatmap
        zones = heatmap_data.get("zones", {})
        best_zone = None
        best_score = -1.0
        dead_zones = []
        
        for z_name, z_metrics in zones.items():
            if z_name == "BILLING":
                continue
            engagement = z_metrics.get("engagement_score", 0.0)
            if engagement > best_score:
                best_score = engagement
                best_zone = z_name
            if z_metrics.get("visits", 0) == 0:
                dead_zones.append(z_name)
                
        reasoning_steps.append("Analyzed heatmaps to identify top-performing zones and dead zones.")

        # 2. Identify largest drop-off in funnel
        stages = funnel_data.get("stages", [])
        largest_drop_pct = -1.0
        largest_drop_stage = None
        
        for i in range(1, len(stages)):
            prev = stages[i-1]
            curr = stages[i]
            # Drop-off rate is (prev_count - curr_count) / prev_count
            if prev["count"] > 0:
                drop_pct = ((prev["count"] - curr["count"]) / prev["count"]) * 100
                if drop_pct > largest_drop_pct:
                    largest_drop_pct = drop_pct
                    largest_drop_stage = f"{prev['stage_name']} -> {curr['stage_name']}"
                    
        reasoning_steps.append(f"Analyzed customer funnel. Identified largest drop-off at: {largest_drop_stage} ({round(largest_drop_pct, 1)}%).")

        # 3. Analyze active anomalies
        critical_alerts = [a for a in anomalies if a.get("severity") == "CRITICAL"]
        warn_alerts = [a for a in anomalies if a.get("severity") == "WARN"]
        
        # 4. Generate Business Recommendations in Markdown
        rec_md = f"### Executive Summary & Recommendations: {store_id}\n\n"
        
        # Traffic summary
        rec_md += f"**Store Performance Summary:**\n"
        rec_md += f"* During the analyzed business period, **{unique_visitors} unique customers** entered the store. "
        rec_md += f"The conversion rate stands at **{round(conversion_rate, 2)}%** with a queue checkout abandonment rate of **{round(abandonment_rate, 2)}%**.\n"
        rec_md += f"* Customers spend an average of **{round(avg_dwell_sec / 60.0, 1)} minutes** inside the store. "
        rec_md += f"We observed **{reentry_count} customer re-entries**, reflecting a segment of shoppers returning to complete purchases or browse further.\n\n"
        
        # Hotspots and layout
        rec_md += f"#### 🛒 Zone Engagement Insights\n"
        if best_zone:
            rec_md += f"* **Top Department**: The **{best_zone}** department recorded the highest customer engagement score (**{best_score}** engagement index). Continue leveraging this zone for cross-product placements and special promotional banners.\n"
        if dead_zones:
            rec_md += f"* **Dead Zones Alert**: The following sections recorded zero customer interactions: **{', '.join(dead_zones)}**. This suggests poor signage, suboptimal product density, or camera feed failures.\n"
        else:
            rec_md += f"* **Zone Distribution**: All departments recorded active foot traffic, indicating balanced customer layout circulation.\n"
        rec_md += "\n"
        
        # Funnel recommendations
        rec_md += f"#### 📉 Funnel Optimization Opportunities\n"
        if largest_drop_stage:
            rec_md += f"* **Drop-off Bottleneck**: The largest drop-off occurs during **{largest_drop_stage}** with **{round(largest_drop_pct, 1)}%** of customers dropping out of the purchase path. \n"
            if "Entry -> Zone Visit" in largest_drop_stage:
                rec_md += "  * *Actionable Tip*: Customers enter but fail to visit product zones. Improve storefront attraction, use floor decals, or rearrange entrance layouts to guide customers towards skincare and cosmetics counters.\n"
            elif "Zone Visit -> Billing Queue" in largest_drop_stage:
                rec_md += "  * *Actionable Tip*: Customers browse products but do not head to checkout. Evaluate assistance levels in skincare/makeup, add digital trial kiosks, or review product-price alignment.\n"
            elif "Billing Queue -> Purchase" in largest_drop_stage:
                rec_md += "  * *Actionable Tip*: High billing queue dropout. This is directly caused by long wait times. Verify cashier staffing shifts to ensure coverage aligns with traffic spikes.\n"
        rec_md += "\n"
        
        # Operational Risks
        rec_md += f"#### ⚠️ Operational Risks & Alerts\n"
        if critical_alerts:
            rec_md += f"* **CRITICAL ALERTS IN EFFECT**:\n"
            for alert in critical_alerts:
                rec_md += f"  * **{alert['anomaly_type']}**: {alert['details']} -> *Action:* {alert['suggested_action']}\n"
        if warn_alerts:
            rec_md += f"* **Warning Alerts**:\n"
            for alert in warn_alerts:
                rec_md += f"  * **{alert['anomaly_type']}**: {alert['details']} -> *Action:* {alert['suggested_action']}\n"
        if not critical_alerts and not warn_alerts:
            rec_md += "* No active operational anomalies detected. Camera feeds and checkout workflows are stable.\n"
        rec_md += "\n"
        
        # Concrete numbered list
        rec_md += f"#### 📋 Recommended Manager Checklist\n"
        idx = 1
        if critical_alerts:
            rec_md += f"{idx}. **Urgent Operations Reset**: Address active {critical_alerts[0]['anomaly_type']} immediately to restore data integrity or customer throughput.\n"
            idx += 1
        if abandonment_rate > 5.0 or "Billing Queue -> Purchase" in (largest_drop_stage or ""):
            rec_md += f"{idx}. **Optimize Checkout Staffing**: Introduce queue-busting cashiers during rush hours (12:00-14:00 and 18:00-21:00) to pull the abandonment rate below 5%.\n"
            idx += 1
        if dead_zones:
            rec_md += f"{idx}. **Department Audit**: Conduct a physical walk of the **{dead_zones[0]}** section to inspect illumination, product availability, and shelf arrangement.\n"
            idx += 1
        if best_zone:
            rec_md += f"{idx}. **Cross-merchandising**: Position related items (e.g. accessories or tools) from lower-performing sections next to popular items in **{best_zone}**.\n"
            idx += 1
        rec_md += f"{idx}. **System Calibration**: Double-check camera confidence readings. Any feed showing low camera reliability (avg < 90%) should be recalibrated to prevent analytical drift.\n"
        
        reasoning_steps.append("Successfully compiled executive summary text and manager recommendations checklist.")
        
        summary = f"Summary for {store_id}: traffic of {unique_visitors} visitors, conversion rate of {round(conversion_rate, 2)}%, best zone is {best_zone or 'None'}."
        
        return {
            "agent_name": self.agent_name,
            "status": "SUCCESS",
            "summary": summary,
            "recommendations": rec_md,
            "reasoning_steps": reasoning_steps
        }
