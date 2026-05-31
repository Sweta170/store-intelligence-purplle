import streamlit as st
import requests
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Set page configurations
st.set_page_config(
    page_title="Purplle Store Intelligence Control Panel",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration from Environment Variables
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Inject premium theme layout and brand CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

/* Main font setup */
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

/* Background gradients for cards */
.kpi-container {
    display: flex;
    justify-content: space-between;
    gap: 15px;
    margin-bottom: 25px;
}

.kpi-card {
    flex: 1;
    background: linear-gradient(135deg, rgba(40, 20, 70, 0.75) 0%, rgba(20, 10, 40, 0.85) 100%);
    border: 1px solid rgba(221, 160, 221, 0.2);
    border-radius: 12px;
    padding: 22px;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(10px);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.kpi-card:hover {
    transform: translateY(-4px);
    border-color: rgba(255, 0, 127, 0.5);
    box-shadow: 0 12px 40px 0 rgba(255, 0, 127, 0.15);
}

.kpi-label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #DDA0DD;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 6px;
}

.kpi-value {
    font-size: 2.2rem;
    font-weight: 700;
    color: #FFFFFF;
    background: linear-gradient(90deg, #FFFFFF 0%, #FFB6C1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* Alert Styling */
.alert-box {
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 12px;
    color: #FFFFFF;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.alert-CRITICAL {
    background: linear-gradient(90deg, rgba(120, 20, 40, 0.85) 0%, rgba(60, 10, 20, 0.9) 100%);
    border-left: 6px solid #FF3366;
    border-top: 1px solid rgba(255, 51, 102, 0.3);
    border-right: 1px solid rgba(255, 51, 102, 0.3);
    border-bottom: 1px solid rgba(255, 51, 102, 0.3);
}

.alert-WARN {
    background: linear-gradient(90deg, rgba(100, 60, 10, 0.85) 0%, rgba(50, 30, 5, 0.9) 100%);
    border-left: 6px solid #FFA500;
    border-top: 1px solid rgba(255, 165, 0, 0.3);
    border-right: 1px solid rgba(255, 165, 0, 0.3);
    border-bottom: 1px solid rgba(255, 165, 0, 0.3);
}

.alert-INFO {
    background: linear-gradient(90deg, rgba(20, 60, 100, 0.85) 0%, rgba(10, 30, 50, 0.9) 100%);
    border-left: 6px solid #00CCFF;
    border-top: 1px solid rgba(0, 204, 255, 0.3);
    border-right: 1px solid rgba(0, 204, 255, 0.3);
    border-bottom: 1px solid rgba(0, 204, 255, 0.3);
}

.alert-title {
    font-weight: 700;
    font-size: 1rem;
    margin-bottom: 4px;
}

.alert-desc {
    font-size: 0.9rem;
    opacity: 0.9;
}

.alert-action {
    margin-top: 8px;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    color: #FFB6C1;
}

/* Title text */
.brand-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(90deg, #A855F7 0%, #EC4899 50%, #F43F5E 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}

</style>
""", unsafe_allow_html=True)

# Helper function to fetch data from backend APIs
def fetch_from_api(endpoint: str):
    try:
        response = requests.get(f"{BACKEND_URL}{endpoint}")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.ConnectionError:
        return "CONNECTION_ERROR"

# Main Layout
st.markdown("<h1 class='brand-title'>🔮 Purplle Store Intelligence</h1>", unsafe_allow_html=True)
st.markdown("<p style='color:#A09EAD; font-size:1.1rem; margin-top:-10px; margin-bottom:25px;'>Real-time AI Agent CCTV Analytics & Store Traffic Profiling Platform</p>", unsafe_allow_html=True)

# System Health Check in Sidebar
health_data = fetch_from_api("/health")

with st.sidebar:
    st.image("dashboard/purplle_logo.png", width=60) # Sleek visual indicator
    st.markdown("### 🖥️ Platform Health")
    
    if health_data == "CONNECTION_ERROR":
        st.error("Backend Server Offline")
        st.markdown("`FastAPI at http://localhost:8000 is unreachable.`")
        st.info("Check Docker Containers status by running: `docker-compose ps`")
    elif health_data:
        status = health_data.get("status")
        if status == "OK":
            st.success("Services Online")
        elif status == "WARNING":
            st.warning("Services Degraded")
        else:
            st.error("Service Failure")
            
        st.markdown(f"**Last Sync Timestamp:**\n`{health_data.get('last_event_timestamp') or 'N/A'}`")
        
        st.markdown("---")
        st.markdown("### 🏬 Store Context Selection")
        
        stores = [
            "STORE_BLR_001",
            "STORE_BLR_002",
            "STORE_DEL_001",
            "STORE_MUM_001",
            "STORE_HYD_001"
        ]
        selected_store = st.selectbox("Active Store Target", stores)
        
        st.markdown("---")
        st.markdown("### 🤖 Configured Agents")
        st.markdown("""
        * 🔍 Event Validation Agent
        * 👤 Session Agent
        * 💰 Conversion Agent
        * 📊 Funnel Agent
        * 🗺️ Heatmap Agent
        * ⚠️ Anomaly Agent
        * 📈 Executive Insights Agent
        """)
        
        # Add a refresh trigger
        if st.button("🔄 Sync Platform Data"):
            st.rerun()
    else:
        st.error("System configuration error.")

# Stop execution and prompt user to launch backend if connection error
if health_data == "CONNECTION_ERROR":
    st.warning("⚠️ Waiting for the backend service to start. Ensure the FastAPI application is running locally on port 8000 or via Docker Compose.")
    st.stop()

# Load stats for selected store
metrics = fetch_from_api(f"/stores/{selected_store}/metrics")
funnel = fetch_from_api(f"/stores/{selected_store}/funnel")
heatmap = fetch_from_api(f"/stores/{selected_store}/heatmap")
anomalies = fetch_from_api(f"/stores/{selected_store}/anomalies")
insights = fetch_from_api(f"/stores/{selected_store}/executive-insights")

if not metrics or not funnel or not heatmap:
    st.error(f"Failed to fetch data for {selected_store} from backend. DB might not be seeded or store is invalid.")
    st.stop()

# 1. KPI Cards section (HTML styled for premium aesthetics)
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">👥 Total Visitors</div>
        <div class="kpi-value">{metrics.get('unique_visitors', 0)}</div>
    </div>
    """, unsafe_allow_html=True)
    
with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">📈 Conversion Rate</div>
        <div class="kpi-value">{metrics.get('conversion_rate', 0.0)}%</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    avg_dwell_mins = round(metrics.get('average_dwell', 0.0) / 60.0, 1)
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">⏳ Avg Dwell Time</div>
        <div class="kpi-value">{avg_dwell_mins}m</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">🚶 Avg Queue Depth</div>
        <div class="kpi-value">{metrics.get('queue_depth', 0.0)}</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">❌ Abandonment Rate</div>
        <div class="kpi-value">{metrics.get('abandonment_rate', 0.0)}%</div>
    </div>
    """, unsafe_allow_html=True)

# Main Navigation Tabs
tab_exec, tab_funnel, tab_heatmap, tab_anomalies, tab_sandbox = st.tabs([
    "📈 Executive Command Center",
    "🎯 Customer Funnel",
    "🗺️ Zone Heatmap",
    "⚠️ Active Anomalies",
    "🧪 Event Sandbox"
])

# Tab 1: Executive Command Center
with tab_exec:
    st.markdown("### 📋 Daily Operations Summary")
    
    col_rec, col_alerts = st.columns([3, 2])
    
    with col_rec:
        if insights:
            st.markdown(insights.get("recommendations", "Generating recommendations..."))
        else:
            st.info("Generating business summaries from the Executive Insights Agent...")
            
    with col_alerts:
        st.markdown("#### ⚡ Active Operational Alerts")
        store_anomalies = anomalies or []
        if not store_anomalies:
            st.success("🟢 No operational anomalies detected for this store.")
        else:
            for alert in store_anomalies:
                severity = alert.get("severity", "INFO")
                st.markdown(f"""
                <div class="alert-box alert-{severity}">
                    <div class="alert-title">⚠️ {alert['anomaly_type']} [{severity}]</div>
                    <div class="alert-desc">{alert['details']}</div>
                    <div class="alert-action">👉 Suggested Action: {alert['suggested_action']}</div>
                </div>
                """, unsafe_allow_html=True)
                
        # Agent Reasoning Accordion
        st.markdown("---")
        with st.expander("👁️ View Executive Insights Agent Reasoning Path"):
            if insights and insights.get("reasoning_steps"):
                for idx, step in enumerate(insights["reasoning_steps"]):
                    st.markdown(f"**Step {idx+1}:** {step}")

# Tab 2: Customer Funnel
with tab_funnel:
    st.markdown("### 🎯 Visitor Conversion Funnel")
    
    funnel_counts = funnel.get("funnel_counts", [])
    funnel_percentages = funnel.get("funnel_percentages", [])
    
    if funnel_counts:
        df_funnel = pd.DataFrame(funnel_counts)
        
        # Draw the funnel diagram using Plotly
        fig_funnel = go.Figure(go.Funnel(
            y=df_funnel["stage"],
            x=df_funnel["count"],
            textinfo="value+percent initial",
            connector={"fillcolor": "rgba(221, 160, 221, 0.25)"},
            marker={"color": ["#8B5CF6", "#C084FC", "#F472B6", "#FB7185"]}
        ))
        
        fig_funnel.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#FFFFFF",
            font_family="Outfit",
            margin=dict(l=40, r=40, t=10, b=10),
            height=400
        )
        
        st.plotly_chart(fig_funnel, use_container_width=True)
        
        # Display as styled dataframe table below
        st.markdown("#### Detail Funnel Stage Metrics")
        funnel_details = []
        for c, p in zip(funnel_counts, funnel_percentages):
            funnel_details.append({
                "Funnel Stage": c["stage"],
                "Unique Visitor Count": c["count"],
                "Conversion Rate (vs stage 1)": f"{p['percentage']}%"
            })
        st.table(pd.DataFrame(funnel_details))
    else:
        st.info("No funnel stage metrics returned.")

# Tab 3: Zone Heatmap & Spatial Analytics
with tab_heatmap:
    st.markdown("### 🗺️ Store Zone Heatmap & Engagement Score")
    
    zone_visits = heatmap.get("zone_visits", {})
    avg_dwell = heatmap.get("avg_dwell", {})
    has_low_conf = heatmap.get("confidence_flag", False)
    
    if has_low_conf:
        st.warning("⚠️ **Confidence Warning**: Low camera confidence detected in one or more zones. Check active camera feeds.")
        
    if zone_visits:
        # Build DataFrame for zones
        records = []
        for zone, visits in zone_visits.items():
            dwell = avg_dwell.get(zone, 0.0)
            engagement = round(visits * (dwell / 60.0), 2)
            records.append({
                "Zone": zone,
                "Foot Traffic (Visits)": visits,
                "Average Dwell (sec)": dwell,
                "Engagement Index": engagement
            })
            
        df_zones = pd.DataFrame(records)
        
        col_chart, col_table = st.columns([3, 2])
        
        with col_chart:
            # Bar chart of visits colored by Dwell
            fig_bar = px.bar(
                df_zones,
                x="Zone",
                y="Foot Traffic (Visits)",
                color="Engagement Index",
                color_continuous_scale="Purples",
                title="Zone Visits Colored by Engagement Index"
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#FFFFFF",
                font_family="Outfit",
                height=380
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_table:
            st.markdown("#### Zone Performance Breakdown")
            st.dataframe(
                df_zones.style.background_gradient(cmap="Purples", subset=["Engagement Index"]),
                hide_index=True,
                use_container_width=True
            )
    else:
        st.info("No zone heatmap metrics returned.")

# Tab 4: Active Anomalies
with tab_anomalies:
    st.markdown("### ⚠️ Active Store Operational Alerts")
    
    store_anomalies = anomalies or []
    if not store_anomalies:
        st.success("🟢 Complete store operations are currently running within normal parameters.")
    else:
        df_anom = pd.DataFrame(store_anomalies)
        
        # Display as a table
        st.dataframe(
            df_anom[["anomaly_type", "severity", "details", "suggested_action", "timestamp"]],
            hide_index=True,
            use_container_width=True
        )
        
        # Dynamic advice based on severity
        criticals = len([a for a in store_anomalies if a["severity"] == "CRITICAL"])
        warnings = len([a for a in store_anomalies if a["severity"] == "WARN"])
        
        st.markdown(f"""
        > **Alert Threshold Breakdown:**
        > * Active **Critical Alerts**: `{criticals}` (Immediate store manager attention required)
        > * Active **Warnings**: `{warnings}` (Assess operations shifts and verify feeds)
        """)

# Tab 5: Sandbox Event Ingest Tool
with tab_sandbox:
    st.markdown("### 🧪 Ingestion Event Sandbox")
    st.markdown("Simulate CCTV camera detection. Use this sandbox to push mock events and watch metrics update in real-time.")
    
    col_inputs, col_json = st.columns([2, 2])
    
    with col_inputs:
        store_sel = st.selectbox("Store Target", stores, key="sb_store")
        zone_sel = st.selectbox("Zone", ["SKINCARE", "MAKEUP", "FRAGRANCE", "HAIRCARE", "BILLING"], key="sb_zone")
        ev_type = st.selectbox("Event Type", ["ZONE_ENTER", "ZONE_DWELL", "ZONE_EXIT", "BILLING_QUEUE_JOIN", "BILLING_QUEUE_ABANDON"], key="sb_type")
        v_id_sb = st.text_input("Visitor ID", "VIS_9999", key="sb_vid")
        dwell_sb = st.number_input("Dwell Time (ms)", min_value=0, max_value=3600000, value=30000, step=10000, key="sb_dwell")
        conf_sb = st.slider("Detection Confidence", min_value=0.0, max_value=1.0, value=0.95, step=0.05, key="sb_conf")
        is_staff_sb = st.checkbox("Is Staff Member?", value=False, key="sb_staff")
        
        # Generate JSON representation
        mock_uuid = "mock-" + datetime.utcnow().strftime("%y%m%d%H%M%S") + "-9999"
        mock_event = {
            "event_id": mock_uuid,
            "store_id": store_sel,
            "camera_id": f"CAM_{zone_sel}_01",
            "visitor_id": v_id_sb,
            "event_type": ev_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "zone_id": zone_sel,
            "dwell_ms": int(dwell_sb),
            "is_staff": is_staff_sb,
            "confidence": float(conf_sb),
            "metadata": {
                "queue_depth": 3 if ev_type == "BILLING_QUEUE_JOIN" else 0,
                "session_seq": 1
            }
        }
        
    with col_json:
        st.markdown("#### Validated JSON Payload")
        st.json(mock_event)
        
        if st.button("🚀 Push Event to API"):
            try:
                # API batch endpoint expects a list of events
                resp = requests.post(f"{BACKEND_URL}/events/ingest", json=[mock_event])
                if resp.status_code == 201:
                    res_json = resp.json()
                    st.success("Successfully processed!")
                    st.json(res_json)
                    if res_json.get("inserted_count", 0) > 0:
                        st.info("Event successfully written to database. Refreshing dashboard metrics...")
                else:
                    st.error(f"Error {resp.status_code}: {resp.text}")
            except Exception as ex:
                st.error(f"Submission failed: {str(ex)}")
