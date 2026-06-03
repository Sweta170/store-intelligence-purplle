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

# Theme state
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

is_light = st.session_state.theme == "light"

# ─────────────────────────────────────────────────────────────
# 1. DESIGN SYSTEM — Premium Glassmorphism CSS
# ─────────────────────────────────────────────────────────────
# ── Theme-aware CSS variables ──
if is_light:
    _bg_deep       = "#F8FAFC"
    _bg_surface    = "rgba(255, 255, 255, 0.85)"
    _bg_glass      = "rgba(255, 255, 255, 0.7)"
    _border_glass  = "rgba(139, 92, 246, 0.15)"
    _border_hover  = "rgba(236, 72, 153, 0.35)"
    _text_primary  = "#1E293B"
    _text_secondary = "#475569"
    _text_muted    = "#94A3B8"
    _glow_purple   = "rgba(139, 92, 246, 0.12)"
    _glow_pink     = "rgba(236, 72, 153, 0.10)"
    _bg_radial1    = "rgba(139,92,246,0.04)"
    _bg_radial2    = "rgba(236,72,153,0.03)"
    _bg_radial3    = "rgba(6,182,212,0.02)"
    _sidebar_bg    = "linear-gradient(180deg, #F1F5F9 0%, #E2E8F0 100%)"
    _sidebar_border = "rgba(139,92,246,0.1)"
    _kpi_purple_grad = "linear-gradient(135deg, #7C3AED, #6D28D9)"
    _kpi_pink_grad   = "linear-gradient(135deg, #DB2777, #BE185D)"
    _kpi_cyan_grad   = "linear-gradient(135deg, #0891B2, #0E7490)"
    _kpi_amber_grad  = "linear-gradient(135deg, #D97706, #B45309)"
    _kpi_rose_grad   = "linear-gradient(135deg, #E11D48, #BE123C)"
else:
    _bg_deep       = "#0a0e1a"
    _bg_surface    = "rgba(15, 20, 40, 0.65)"
    _bg_glass      = "rgba(20, 25, 50, 0.45)"
    _border_glass  = "rgba(139, 92, 246, 0.18)"
    _border_hover  = "rgba(236, 72, 153, 0.45)"
    _text_primary  = "#E2E8F0"
    _text_secondary = "#94A3B8"
    _text_muted    = "#64748B"
    _glow_purple   = "rgba(139, 92, 246, 0.25)"
    _glow_pink     = "rgba(236, 72, 153, 0.20)"
    _bg_radial1    = "rgba(139,92,246,0.07)"
    _bg_radial2    = "rgba(236,72,153,0.05)"
    _bg_radial3    = "rgba(6,182,212,0.03)"
    _sidebar_bg    = "linear-gradient(180deg, #0c1029 0%, #0a0e1a 100%)"
    _sidebar_border = "rgba(139,92,246,0.12)"
    _kpi_purple_grad = "linear-gradient(135deg, #C4B5FD, #8B5CF6)"
    _kpi_pink_grad   = "linear-gradient(135deg, #F9A8D4, #EC4899)"
    _kpi_cyan_grad   = "linear-gradient(135deg, #67E8F9, #06B6D4)"
    _kpi_amber_grad  = "linear-gradient(135deg, #FDE68A, #F59E0B)"
    _kpi_rose_grad   = "linear-gradient(135deg, #FDA4AF, #F43F5E)"

# 1. ── Theme-aware dynamic CSS variables and overrides ──
st.markdown(f"""
<style>
:root {{
    --bg-deep:        {_bg_deep};
    --bg-surface:     {_bg_surface};
    --bg-glass:       {_bg_glass};
    --border-glass:   {_border_glass};
    --border-hover:   {_border_hover};
    --text-primary:   {_text_primary};
    --text-secondary: {_text_secondary};
    --text-muted:     {_text_muted};
    --accent-purple:  #8B5CF6;
    --accent-pink:    #EC4899;
    --accent-cyan:    #06B6D4;
    --accent-amber:   #F59E0B;
    --accent-rose:    #F43F5E;
    --accent-emerald: #10B981;
    --glow-purple:    {_glow_purple};
    --glow-pink:      {_glow_pink};

    /* ── Streamlit native variables overrides ── */
    --primary-color: #8B5CF6 !important;
    --background-color: {_bg_deep} !important;
    --secondary-background-color: {_bg_glass} !important;
    --text-color: {_text_primary} !important;
}}

div[data-testid="stAppViewContainer"] {{
    background-color: var(--bg-deep) !important;
    background-image:
        radial-gradient(ellipse at 10% 20%, {_bg_radial1} 0%, transparent 50%),
        radial-gradient(ellipse at 90% 80%, {_bg_radial2} 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, {_bg_radial3} 0%, transparent 60%) !important;
    color: var(--text-primary) !important;
}}

section[data-testid="stSidebar"] {{
    background: {_sidebar_bg} !important;
    border-right: 1px solid {_sidebar_border} !important;
}}

.kpi-purple .kpi-value  {{ background: {_kpi_purple_grad}; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.kpi-pink .kpi-value     {{ background: {_kpi_pink_grad}; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.kpi-cyan .kpi-value     {{ background: {_kpi_cyan_grad}; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.kpi-amber .kpi-value    {{ background: {_kpi_amber_grad}; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
.kpi-rose .kpi-value     {{ background: {_kpi_rose_grad}; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}

/* ── Theme Toggle Button ── */
.theme-toggle-wrapper {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 8px 0;
    margin-bottom: 8px;
}}

.theme-label {{
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
}}
</style>
""", unsafe_allow_html=True)

# 2. ── Static Premium Control Panel Layout & styling ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap');

/* ── Global Reset ─────────────────────────────────── */
html, body {
    font-family: 'Inter', sans-serif;
    color: var(--text-primary);
}

div[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border-glass) !important;
}

.main .block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

h1, h2, h3, h4, [data-testid="stHeader"] h1, [data-testid="stHeader"] h2 {
    font-family: 'Outfit', sans-serif !important;
}

/* ── Glassmorphic Surface ─────────────────────────── */
.glass-surface, .st-key-exec_recommendations, .st-key-exec_recommendations_loading {
    background: var(--bg-glass);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border-glass);
    border-radius: 16px;
    padding: 24px;
    transition: all 0.35s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.glass-surface:hover, .st-key-exec_recommendations:hover, .st-key-exec_recommendations_loading:hover {
    border-color: var(--border-hover);
    box-shadow: 0 8px 40px var(--glow-pink);
}

/* ── Brand Header ─────────────────────────────────── */
.brand-header {
    text-align: left;
    margin-bottom: 8px;
}

.brand-title {
    font-family: 'Outfit', sans-serif;
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #A855F7 0%, #EC4899 40%, #F43F5E 70%, #F59E0B 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.5px;
    line-height: 1.15;
    margin: 0;
}

.brand-subtitle {
    font-size: 1.05rem;
    color: var(--text-secondary);
    margin-top: 4px;
    margin-bottom: 28px;
    font-weight: 400;
    letter-spacing: 0.2px;
}

/* ── KPI Card Grid ────────────────────────────────── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 16px;
    margin-bottom: 32px;
}

@media (max-width: 900px) {
    .kpi-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

.kpi-card {
    background: var(--bg-glass);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid var(--border-glass);
    border-radius: 16px;
    padding: 22px 20px 18px;
    position: relative;
    overflow: hidden;
    transition: all 0.35s cubic-bezier(0.25, 0.8, 0.25, 1);
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
    transition: height 0.3s ease;
}

.kpi-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 20px 50px rgba(0,0,0,0.35);
}

.kpi-card:hover::before {
    height: 4px;
}

/* Accent variants */
.kpi-purple::before  { background: linear-gradient(90deg, #8B5CF6, #A78BFA); }
.kpi-purple:hover    { border-color: rgba(139,92,246,0.45); box-shadow: 0 20px 50px rgba(139,92,246,0.15); }

.kpi-pink::before    { background: linear-gradient(90deg, #EC4899, #F472B6); }
.kpi-pink:hover      { border-color: rgba(236,72,153,0.45); box-shadow: 0 20px 50px rgba(236,72,153,0.15); }

.kpi-cyan::before    { background: linear-gradient(90deg, #06B6D4, #22D3EE); }
.kpi-cyan:hover      { border-color: rgba(6,182,212,0.45); box-shadow: 0 20px 50px rgba(6,182,212,0.15); }

.kpi-amber::before   { background: linear-gradient(90deg, #F59E0B, #FBBF24); }
.kpi-amber:hover     { border-color: rgba(245,158,11,0.45); box-shadow: 0 20px 50px rgba(245,158,11,0.15); }

.kpi-rose::before    { background: linear-gradient(90deg, #F43F5E, #FB7185); }
.kpi-rose:hover      { border-color: rgba(244,63,94,0.45); box-shadow: 0 20px 50px rgba(244,63,94,0.15); }

.kpi-icon {
    font-size: 1.5rem;
    margin-bottom: 8px;
    display: inline-block;
}

.kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1.4px;
    margin-bottom: 6px;
}

.kpi-value {
    font-family: 'Outfit', sans-serif;
    font-size: 2.1rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    line-height: 1.1;
}

.kpi-sub {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-top: 6px;
    font-weight: 400;
}

/* ── Section Headers ──────────────────────────────── */
.section-header {
    font-family: 'Outfit', sans-serif;
    font-size: 1.45rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid transparent;
    border-image: linear-gradient(90deg, var(--accent-purple), var(--accent-pink), transparent) 1;
    display: inline-block;
}

/* ── Alert Cards ──────────────────────────────────── */
.alert-card {
    background: var(--bg-glass);
    backdrop-filter: blur(12px);
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 12px;
    border: 1px solid var(--border-glass);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.alert-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 4px;
}

.alert-card:hover {
    transform: translateX(4px);
}

.alert-CRITICAL::before { background: linear-gradient(180deg, #F43F5E, #E11D48); }
.alert-CRITICAL { border-color: rgba(244,63,94,0.25); }
.alert-CRITICAL:hover { box-shadow: 0 4px 25px rgba(244,63,94,0.15); }

.alert-WARN::before { background: linear-gradient(180deg, #F59E0B, #D97706); }
.alert-WARN { border-color: rgba(245,158,11,0.25); }
.alert-WARN:hover { box-shadow: 0 4px 25px rgba(245,158,11,0.15); }

.alert-INFO::before { background: linear-gradient(180deg, #06B6D4, #0891B2); }
.alert-INFO { border-color: rgba(6,182,212,0.25); }
.alert-INFO:hover { box-shadow: 0 4px 25px rgba(6,182,212,0.15); }

.alert-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}

.severity-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    display: inline-block;
    animation: pulse-dot 2s infinite;
}

.severity-dot.critical { background: #F43F5E; box-shadow: 0 0 8px rgba(244,63,94,0.6); }
.severity-dot.warn     { background: #F59E0B; box-shadow: 0 0 8px rgba(245,158,11,0.6); }
.severity-dot.info     { background: #06B6D4; box-shadow: 0 0 8px rgba(6,182,212,0.6); }

@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.85); }
}

.alert-type {
    font-weight: 700;
    font-size: 0.92rem;
    color: var(--text-primary);
}

.alert-severity-badge {
    font-size: 0.65rem;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

.badge-critical { background: rgba(244,63,94,0.2); color: #FB7185; }
.badge-warn     { background: rgba(245,158,11,0.2); color: #FBBF24; }
.badge-info     { background: rgba(6,182,212,0.2); color: #22D3EE; }

.alert-details {
    font-size: 0.88rem;
    color: var(--text-secondary);
    line-height: 1.5;
    margin-bottom: 8px;
}

.alert-action {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--accent-pink);
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

/* ── Summary Callout Cards ────────────────────────── */
.callout-row {
    display: flex;
    gap: 14px;
    margin-bottom: 24px;
}

.callout-card {
    flex: 1;
    background: var(--bg-glass);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-glass);
    border-radius: 12px;
    padding: 16px 18px;
    text-align: center;
    transition: all 0.3s ease;
}

.callout-card:hover {
    border-color: var(--border-hover);
    transform: translateY(-3px);
}

.callout-value {
    font-family: 'Outfit', sans-serif;
    font-size: 1.6rem;
    font-weight: 700;
    margin-bottom: 2px;
}

.callout-label {
    font-size: 0.78rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 500;
}

.callout-purple .callout-value { color: #A78BFA; }
.callout-pink .callout-value   { color: #F472B6; }
.callout-cyan .callout-value   { color: #22D3EE; }
.callout-amber .callout-value  { color: #FBBF24; }
.callout-rose .callout-value   { color: #FB7185; }
.callout-emerald .callout-value { color: #34D399; }

/* ── Anomaly Standalone Cards ─────────────────────── */
.anomaly-card {
    background: var(--bg-glass);
    backdrop-filter: blur(14px);
    border: 1px solid var(--border-glass);
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
    transition: all 0.35s ease;
}

.anomaly-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 5px;
}

.anomaly-card:hover {
    transform: translateX(5px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.3);
}

.anomaly-CRITICAL::before { background: linear-gradient(180deg, #F43F5E, #BE123C); }
.anomaly-CRITICAL { border-color: rgba(244,63,94,0.2); }
.anomaly-CRITICAL:hover { border-color: rgba(244,63,94,0.4); box-shadow: 0 8px 35px rgba(244,63,94,0.12); }

.anomaly-WARN::before { background: linear-gradient(180deg, #F59E0B, #B45309); }
.anomaly-WARN { border-color: rgba(245,158,11,0.2); }
.anomaly-WARN:hover { border-color: rgba(245,158,11,0.4); box-shadow: 0 8px 35px rgba(245,158,11,0.12); }

.anomaly-INFO::before { background: linear-gradient(180deg, #06B6D4, #0E7490); }
.anomaly-INFO { border-color: rgba(6,182,212,0.2); }
.anomaly-INFO:hover { border-color: rgba(6,182,212,0.4); box-shadow: 0 8px 35px rgba(6,182,212,0.12); }

.anomaly-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;
}

.anomaly-type {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    color: var(--text-primary);
}

.anomaly-timestamp {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-left: auto;
    font-family: 'Inter', monospace;
}

.anomaly-details {
    font-size: 0.9rem;
    color: var(--text-secondary);
    line-height: 1.55;
    margin-bottom: 12px;
}

.anomaly-action {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--accent-pink);
    letter-spacing: 0.3px;
}

.anomaly-action span {
    color: var(--text-secondary);
    font-weight: 400;
}

/* ── Sidebar Styling ──────────────────────────────── */
section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}

.sidebar-health-card {
    background: var(--bg-glass);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-glass);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 16px;
}

.sidebar-health-status {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 600;
    font-size: 0.95rem;
}

.status-dot {
    width: 12px; height: 12px;
    border-radius: 50%;
    display: inline-block;
    animation: pulse-dot 2s infinite;
}

.status-dot.online  { background: #10B981; box-shadow: 0 0 10px rgba(16,185,129,0.5); }
.status-dot.warning { background: #F59E0B; box-shadow: 0 0 10px rgba(245,158,11,0.5); }
.status-dot.offline { background: #F43F5E; box-shadow: 0 0 10px rgba(244,63,94,0.5); }

.status-text.online  { color: #34D399; }
.status-text.warning { color: #FBBF24; }
.status-text.offline { color: #FB7185; }

.sidebar-sync-time {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-top: 8px;
    font-family: 'Inter', monospace;
    padding: 4px 8px;
    background: rgba(139,92,246,0.08);
    border-radius: 6px;
    display: inline-block;
}

.agent-card {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 12px;
    border-radius: 8px;
    margin-bottom: 4px;
    transition: background 0.2s ease;
}

.agent-card:hover {
    background: rgba(139,92,246,0.08);
}

.agent-icon {
    width: 30px; height: 30px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
    flex-shrink: 0;
}

.agent-icon.purple  { background: rgba(139,92,246,0.15); }
.agent-icon.pink    { background: rgba(236,72,153,0.15); }
.agent-icon.cyan    { background: rgba(6,182,212,0.15); }
.agent-icon.amber   { background: rgba(245,158,11,0.15); }
.agent-icon.rose    { background: rgba(244,63,94,0.15); }
.agent-icon.emerald { background: rgba(16,185,129,0.15); }
.agent-icon.blue    { background: rgba(59,130,246,0.15); }

.agent-info {
    display: flex;
    flex-direction: column;
}

.agent-name {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text-primary);
}

.agent-role {
    font-size: 0.7rem;
    color: var(--text-muted);
}

/* ── Sandbox Styling ──────────────────────────────── */
.sandbox-panel {
    background: var(--bg-glass);
    backdrop-filter: blur(14px);
    border: 1px solid var(--border-glass);
    border-radius: 14px;
    padding: 22px;
}

.sandbox-section-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--accent-purple);
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 12px;
}

/* ── Divider ──────────────────────────────────────── */
.gradient-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent-purple), var(--accent-pink), transparent);
    margin: 28px 0;
    border: none;
}

/* ── Step Cards (Agent Reasoning) ─────────────────── */
.reasoning-step {
    background: rgba(139,92,246,0.06);
    border-left: 3px solid var(--accent-purple);
    border-radius: 0 8px 8px 0;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 0.88rem;
    color: var(--text-secondary);
    transition: all 0.2s ease;
}

.reasoning-step:hover {
    background: rgba(139,92,246,0.12);
    border-left-color: var(--accent-pink);
}

.reasoning-step-num {
    font-weight: 700;
    color: var(--accent-purple);
    margin-right: 6px;
}

/* ── Zone Highlight Cards ─────────────────────────── */
.zone-highlight {
    display: flex;
    gap: 14px;
    margin-bottom: 22px;
}

.zone-card {
    flex: 1;
    background: var(--bg-glass);
    backdrop-filter: blur(12px);
    border: 1px solid var(--border-glass);
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    transition: all 0.3s ease;
}

.zone-card:hover {
    transform: translateY(-3px);
}

.zone-card-hot {
    border-color: rgba(244,63,94,0.2);
}
.zone-card-hot:hover {
    border-color: rgba(244,63,94,0.4);
    box-shadow: 0 6px 25px rgba(244,63,94,0.1);
}

.zone-card-cold {
    border-color: rgba(6,182,212,0.2);
}
.zone-card-cold:hover {
    border-color: rgba(6,182,212,0.4);
    box-shadow: 0 6px 25px rgba(6,182,212,0.1);
}

.zone-emoji { font-size: 1.8rem; margin-bottom: 6px; }
.zone-name-text { font-family: 'Outfit', sans-serif; font-weight: 700; font-size: 1.05rem; color: var(--text-primary); }
.zone-metric { font-size: 0.8rem; color: var(--text-secondary); margin-top: 4px; }

/* ── Tab Styling ──────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: var(--bg-glass);
    border-radius: 12px;
    padding: 4px;
    border: 1px solid var(--border-glass);
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 10px 20px;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    font-size: 0.88rem;
    color: var(--text-secondary);
    transition: all 0.25s ease;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(139,92,246,0.2), rgba(236,72,153,0.15)) !important;
    color: var(--text-primary) !important;
    font-weight: 600;
}

.stTabs [data-baseweb="tab-highlight"] {
    background: linear-gradient(90deg, var(--accent-purple), var(--accent-pink)) !important;
    height: 3px;
    border-radius: 2px;
}

/* ── Expander ─────────────────────────────────────── */
.streamlit-expanderHeader {
    background: var(--bg-glass) !important;
    border: 1px solid var(--border-glass) !important;
    border-radius: 10px !important;
    font-weight: 600;
}

/* ── No anomalies success state ───────────────────── */
.all-clear-card {
    background: rgba(16,185,129,0.06);
    border: 1px solid rgba(16,185,129,0.2);
    border-radius: 14px;
    padding: 30px;
    text-align: center;
}

.all-clear-icon { font-size: 2.5rem; margin-bottom: 10px; }
.all-clear-text {
    font-family: 'Outfit', sans-serif;
    font-size: 1.15rem;
    font-weight: 600;
    color: #34D399;
}
.all-clear-sub {
    font-size: 0.88rem;
    color: var(--text-secondary);
    margin-top: 4px;
}

/* ── Scrollbar ────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(139,92,246,0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(139,92,246,0.5); }

/* ── Sidebar label override ──────────────────────── */
.sidebar-section-title {
    font-family: 'Outfit', sans-serif;
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 12px;
    margin-top: 8px;
}
.kpi-rose .kpi-value     {{ background: {_kpi_rose_grad}; -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}

/* ── Theme Toggle Button ─────────────────────────── */
.theme-toggle-wrapper {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 8px 0;
    margin-bottom: 8px;
}}

.theme-label {{
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
}}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# 2. PLOTLY CHART THEME
# ─────────────────────────────────────────────────────────────
if is_light:
    CHART_LAYOUT = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.5)",
        font=dict(family="Inter, sans-serif", color="#1E293B", size=13),
        colorway=["#7C3AED", "#DB2777", "#0891B2", "#D97706", "#059669", "#E11D48"],
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#8B5CF6", font_size=13, font_family="Inter", font_color="#1E293B"),
        margin=dict(l=40, r=40, t=30, b=30),
        xaxis=dict(gridcolor="rgba(30,41,59,0.08)", zerolinecolor="rgba(30,41,59,0.08)"),
        yaxis=dict(gridcolor="rgba(30,41,59,0.08)", zerolinecolor="rgba(30,41,59,0.08)"),
    )
else:
    CHART_LAYOUT = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(10,14,26,0.3)",
        font=dict(family="Inter, sans-serif", color="#E2E8F0", size=13),
        colorway=["#8B5CF6", "#EC4899", "#06B6D4", "#F59E0B", "#10B981", "#F43F5E"],
        hoverlabel=dict(bgcolor="#1E1B4B", bordercolor="#8B5CF6", font_size=13, font_family="Inter"),
        margin=dict(l=40, r=40, t=30, b=30),
        xaxis=dict(gridcolor="rgba(148,163,184,0.08)", zerolinecolor="rgba(148,163,184,0.08)"),
        yaxis=dict(gridcolor="rgba(148,163,184,0.08)", zerolinecolor="rgba(148,163,184,0.08)"),
    )


# ─────────────────────────────────────────────────────────────
# 3. HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────
def fetch_from_api(endpoint: str):
    """Fetch data from backend APIs."""
    try:
        response = requests.get(f"{BACKEND_URL}{endpoint}")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.ConnectionError:
        return "CONNECTION_ERROR"


def render_alert_card(alert: dict):
    """Render a single anomaly alert card with severity styling."""
    severity = alert.get("severity", "INFO")
    sev_lower = severity.lower()
    return f"""
    <div class="alert-card alert-{severity}">
        <div class="alert-header">
            <span class="severity-dot {sev_lower}"></span>
            <span class="alert-type">{alert['anomaly_type']}</span>
            <span class="alert-severity-badge badge-{sev_lower}">{severity}</span>
        </div>
        <div class="alert-details">{alert['details']}</div>
        <div class="alert-action">⚡ {alert['suggested_action']}</div>
    </div>
    """


def render_anomaly_card(alert: dict):
    """Render a standalone anomaly card for the anomalies tab."""
    severity = alert.get("severity", "INFO")
    sev_lower = severity.lower()
    ts = alert.get("timestamp", "")
    return f"""
    <div class="anomaly-card anomaly-{severity}">
        <div class="anomaly-meta">
            <span class="severity-dot {sev_lower}"></span>
            <span class="anomaly-type">{alert['anomaly_type']}</span>
            <span class="alert-severity-badge badge-{sev_lower}">{severity}</span>
            <span class="anomaly-timestamp">{ts}</span>
        </div>
        <div class="anomaly-details">{alert['details']}</div>
        <div class="anomaly-action">⚡ Suggested Action: <span>{alert['suggested_action']}</span></div>
    </div>
    """


# ─────────────────────────────────────────────────────────────
# 4. BRAND HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div class="brand-header">
    <h1 class="brand-title">🔮 Purplle Store Intelligence</h1>
    <p class="brand-subtitle">Real-time AI Agent CCTV Analytics & Store Traffic Profiling Platform</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# 5. SIDEBAR — Premium Command Sidebar
# ─────────────────────────────────────────────────────────────
health_data = fetch_from_api("/health")

stores = [
    "STORE_BLR_001",
    "STORE_BLR_002",
    "STORE_DEL_001",
    "STORE_MUM_001",
    "STORE_HYD_001"
]

with st.sidebar:
    st.image("dashboard/purplle_logo.png", width=120)

    # ── Theme Toggle ──
    theme_icon = "☀️" if is_light else "🌙"
    theme_label = "Light Mode" if is_light else "Dark Mode"
    st.markdown(f'<div class="theme-toggle-wrapper"><span class="theme-label">{theme_label}</span></div>', unsafe_allow_html=True)

    def toggle_theme():
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

    st.button(f"{theme_icon} Switch to {'Dark' if is_light else 'Light'} Mode", on_click=toggle_theme, use_container_width=True, key="theme_toggle")

    st.markdown("---")

    # ── Platform Health ──
    st.markdown('<div class="sidebar-section-title">Platform Health</div>', unsafe_allow_html=True)

    if health_data == "CONNECTION_ERROR":
        st.markdown("""
        <div class="sidebar-health-card">
            <div class="sidebar-health-status">
                <span class="status-dot offline"></span>
                <span class="status-text offline">Backend Offline</span>
            </div>
            <div class="sidebar-sync-time">FastAPI @ localhost:8000 unreachable</div>
        </div>
        """, unsafe_allow_html=True)
        st.info("Run `docker-compose up` or start uvicorn manually.")
    elif health_data:
        status = health_data.get("status")
        if status == "OK":
            dot_cls, text_cls, text = "online", "online", "All Systems Operational"
        elif status == "WARNING":
            dot_cls, text_cls, text = "warning", "warning", "Services Degraded"
        else:
            dot_cls, text_cls, text = "offline", "offline", "Service Failure"

        last_sync = health_data.get('last_event_timestamp') or 'N/A'
        st.markdown(f"""
        <div class="sidebar-health-card">
            <div class="sidebar-health-status">
                <span class="status-dot {dot_cls}"></span>
                <span class="status-text {text_cls}">{text}</span>
            </div>
            <div class="sidebar-sync-time">🕐 Last sync: {last_sync}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("System configuration error.")

    # ── Store Selector ──
    st.markdown('<div class="sidebar-section-title">Store Context</div>', unsafe_allow_html=True)
    selected_store = st.selectbox("Active Store Target", stores, label_visibility="collapsed")

    st.markdown("---")

    # ── Agent Roster ──
    st.markdown('<div class="sidebar-section-title">Intelligence Agents</div>', unsafe_allow_html=True)

    agents_info = [
        ("🔍", "purple",  "Validation Agent",  "Schema & quality checks"),
        ("👤", "cyan",    "Session Agent",      "Visitor path grouping"),
        ("💰", "amber",   "Conversion Agent",   "POS receipt matching"),
        ("📊", "pink",    "Funnel Agent",       "Stage dropout tracking"),
        ("🗺️", "emerald", "Heatmap Agent",      "Spatial engagement"),
        ("⚠️", "rose",    "Anomaly Agent",      "Operational alerts"),
        ("📈", "blue",    "Insights Agent",     "Executive reporting"),
    ]

    agents_html = ""
    for emoji, color, name, role in agents_info:
        agents_html += f"""
        <div class="agent-card">
            <div class="agent-icon {color}">{emoji}</div>
            <div class="agent-info">
                <span class="agent-name">{name}</span>
                <span class="agent-role">{role}</span>
            </div>
        </div>
        """
    st.markdown(agents_html, unsafe_allow_html=True)

    st.markdown("---")

    # ── Sync Button ──
    if st.button("🔄 Sync Platform Data", use_container_width=True):
        st.rerun()


# ─────────────────────────────────────────────────────────────
# 6. CONNECTION GUARD
# ─────────────────────────────────────────────────────────────
if health_data == "CONNECTION_ERROR":
    st.markdown("""
    <div class="glass-surface" style="text-align:center; padding:50px 30px; margin-top:40px;">
        <div style="font-size:3rem; margin-bottom:16px;">🔌</div>
        <div style="font-family:'Outfit'; font-size:1.4rem; font-weight:700; color:#FB7185; margin-bottom:8px;">
            Backend Connection Failed
        </div>
        <div style="color:var(--text-secondary); font-size:0.95rem;">
            Ensure the FastAPI application is running on <code style="color:#A78BFA;">localhost:8000</code> or via Docker Compose.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────
# 7. FETCH STORE DATA
# ─────────────────────────────────────────────────────────────
metrics = fetch_from_api(f"/stores/{selected_store}/metrics")
funnel = fetch_from_api(f"/stores/{selected_store}/funnel")
heatmap = fetch_from_api(f"/stores/{selected_store}/heatmap")
anomalies = fetch_from_api(f"/stores/{selected_store}/anomalies")
insights = fetch_from_api(f"/stores/{selected_store}/executive-insights")

if not metrics or not funnel or not heatmap:
    st.markdown("""
    <div class="glass-surface" style="text-align:center; padding:40px 30px; margin-top:30px;">
        <div style="font-size:2.5rem; margin-bottom:12px;">📡</div>
        <div style="font-family:'Outfit'; font-size:1.2rem; font-weight:700; color:#FBBF24; margin-bottom:8px;">
            No Data Available
        </div>
        <div style="color:var(--text-secondary); font-size:0.9rem;">
            Failed to fetch analytics for the selected store. The database may not be seeded.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────
# 8. KPI HERO CARDS
# ─────────────────────────────────────────────────────────────
avg_dwell_mins = round(metrics.get('average_dwell', 0.0) / 60.0, 1)

kpi_html = f"""
<div class="kpi-grid">
    <div class="kpi-card kpi-purple">
        <div class="kpi-icon">👥</div>
        <div class="kpi-label">Total Visitors</div>
        <div class="kpi-value">{metrics.get('unique_visitors', 0):,}</div>
        <div class="kpi-sub">Unique tracked visitors</div>
    </div>
    <div class="kpi-card kpi-pink">
        <div class="kpi-icon">📈</div>
        <div class="kpi-label">Conversion Rate</div>
        <div class="kpi-value">{metrics.get('conversion_rate', 0.0)}%</div>
        <div class="kpi-sub">Visitors → Purchases</div>
    </div>
    <div class="kpi-card kpi-cyan">
        <div class="kpi-icon">⏳</div>
        <div class="kpi-label">Avg Dwell Time</div>
        <div class="kpi-value">{avg_dwell_mins}m</div>
        <div class="kpi-sub">Average per session</div>
    </div>
    <div class="kpi-card kpi-amber">
        <div class="kpi-icon">🚶</div>
        <div class="kpi-label">Avg Queue Depth</div>
        <div class="kpi-value">{metrics.get('queue_depth', 0.0)}</div>
        <div class="kpi-sub">Billing queue average</div>
    </div>
    <div class="kpi-card kpi-rose">
        <div class="kpi-icon">❌</div>
        <div class="kpi-label">Abandonment Rate</div>
        <div class="kpi-value">{metrics.get('abandonment_rate', 0.0)}%</div>
        <div class="kpi-sub">Queue drop-off rate</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)

# Gradient Divider
st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# 9. NAVIGATION TABS
# ─────────────────────────────────────────────────────────────
tab_exec, tab_funnel, tab_heatmap, tab_anomalies, tab_sandbox = st.tabs([
    "📈 Executive Command Center",
    "🎯 Customer Funnel",
    "🗺️ Zone Heatmap",
    "⚠️ Active Anomalies",
    "🧪 Event Sandbox"
])


# ── TAB 1: Executive Command Center ──────────────────────────
with tab_exec:
    st.markdown('<div class="section-header">📋 Daily Operations Summary</div>', unsafe_allow_html=True)

    col_rec, col_alerts = st.columns([3, 2])

    with col_rec:
        if insights:
            with st.container(key="exec_recommendations"):
                st.markdown(insights.get("recommendations", "Generating recommendations..."))
        else:
            with st.container(key="exec_recommendations_loading"):
                st.markdown("""
                <div style="text-align:center; padding:40px;">
                    <div style="font-size:2rem; margin-bottom:8px;">🤖</div>
                    <div style="color:var(--text-secondary);">Generating business summaries from the Executive Insights Agent...</div>
                </div>
                """, unsafe_allow_html=True)

    with col_alerts:
        st.markdown('<div class="section-header">⚡ Operational Alerts</div>', unsafe_allow_html=True)
        store_anomalies = anomalies or []

        if not store_anomalies:
            st.markdown("""
            <div class="all-clear-card">
                <div class="all-clear-icon">✅</div>
                <div class="all-clear-text">All Clear</div>
                <div class="all-clear-sub">No operational anomalies detected for this store.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            alerts_html = ""
            for alert in store_anomalies:
                alerts_html += render_alert_card(alert)
            st.markdown(alerts_html, unsafe_allow_html=True)

    # Agent Reasoning
    st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
    with st.expander("👁️ View Executive Insights Agent Reasoning Path"):
        if insights and insights.get("reasoning_steps"):
            steps_html = ""
            for idx, step in enumerate(insights["reasoning_steps"]):
                steps_html += f"""
                <div class="reasoning-step">
                    <span class="reasoning-step-num">Step {idx+1}</span> {step}
                </div>
                """
            st.markdown(steps_html, unsafe_allow_html=True)
        else:
            st.markdown("*No reasoning steps available.*")


# ── TAB 2: Customer Funnel ────────────────────────────────────
with tab_funnel:
    st.markdown('<div class="section-header">🎯 Visitor Conversion Funnel</div>', unsafe_allow_html=True)

    funnel_counts = funnel.get("funnel_counts", [])
    funnel_percentages = funnel.get("funnel_percentages", [])

    if funnel_counts:
        # Summary callout cards
        total_entries = funnel_counts[0]["count"] if funnel_counts else 0
        final_stage = funnel_counts[-1]["count"] if funnel_counts else 0
        overall_conversion = round((final_stage / total_entries * 100), 1) if total_entries > 0 else 0
        overall_dropout = round(100 - overall_conversion, 1)

        st.markdown(f"""
        <div class="callout-row">
            <div class="callout-card callout-purple">
                <div class="callout-value">{total_entries:,}</div>
                <div class="callout-label">Total Entries</div>
            </div>
            <div class="callout-card callout-emerald">
                <div class="callout-value">{final_stage:,}</div>
                <div class="callout-label">Final Conversions</div>
            </div>
            <div class="callout-card callout-pink">
                <div class="callout-value">{overall_conversion}%</div>
                <div class="callout-label">Overall Conversion</div>
            </div>
            <div class="callout-card callout-rose">
                <div class="callout-value">{overall_dropout}%</div>
                <div class="callout-label">Total Drop-off</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        df_funnel = pd.DataFrame(funnel_counts)

        # Funnel Chart
        fig_funnel = go.Figure(go.Funnel(
            y=df_funnel["stage"],
            x=df_funnel["count"],
            textinfo="value+percent initial",
            textfont=dict(size=14, family="Inter"),
            connector={"fillcolor": "rgba(139,92,246,0.12)", "line": {"color": "rgba(139,92,246,0.3)", "width": 1}},
            marker={"color": ["#8B5CF6", "#A855F7", "#EC4899", "#F43F5E"],
                    "line": {"color": ["#7C3AED", "#9333EA", "#DB2777", "#E11D48"], "width": 1.5}}
        ))

        funnel_layout = {**CHART_LAYOUT, "margin": dict(l=50, r=50, t=20, b=20)}
        fig_funnel.update_layout(**funnel_layout, height=420)

        st.plotly_chart(fig_funnel, use_container_width=True)

        # Detail Table
        st.markdown('<div class="section-header" style="font-size:1.1rem;">📊 Stage Breakdown</div>', unsafe_allow_html=True)
        funnel_details = []
        for c, p in zip(funnel_counts, funnel_percentages):
            funnel_details.append({
                "Funnel Stage": c["stage"],
                "Unique Visitors": c["count"],
                "Conversion % (vs Entry)": f"{p['percentage']}%"
            })
        table_bg = "rgba(255, 255, 255, 0.65)" if is_light else "rgba(15, 20, 40, 0.5)"
        table_fg = "#1E293B" if is_light else "#E2E8F0"
        st.dataframe(
            pd.DataFrame(funnel_details).style.set_properties(**{
                'background-color': table_bg,
                'color': table_fg,
                'font-family': 'Inter',
            }),
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No funnel stage metrics returned.")


# ── TAB 3: Zone Heatmap ──────────────────────────────────────
with tab_heatmap:
    st.markdown('<div class="section-header">🗺️ Store Zone Heatmap & Engagement</div>', unsafe_allow_html=True)

    zone_visits = heatmap.get("zone_visits", {})
    avg_dwell_zones = heatmap.get("avg_dwell", {})
    has_low_conf = heatmap.get("confidence_flag", False)

    if has_low_conf:
        st.warning("⚠️ **Confidence Warning**: Low camera confidence detected in one or more zones. Check active camera feeds.")

    if zone_visits:
        # Build zone records
        records = []
        for zone, visits in zone_visits.items():
            dwell = avg_dwell_zones.get(zone, 0.0)
            engagement = round(visits * (dwell / 60.0), 2)
            records.append({
                "Zone": zone,
                "Foot Traffic": visits,
                "Avg Dwell (sec)": round(dwell, 1),
                "Engagement Index": engagement
            })

        df_zones = pd.DataFrame(records)

        # Hot / Cold zone highlights
        if not df_zones.empty:
            hottest = df_zones.loc[df_zones["Engagement Index"].idxmax()]
            coldest = df_zones.loc[df_zones["Engagement Index"].idxmin()]

            st.markdown(f"""
            <div class="zone-highlight">
                <div class="zone-card zone-card-hot">
                    <div class="zone-emoji">🔥</div>
                    <div class="zone-name-text">{hottest['Zone']}</div>
                    <div class="zone-metric">Engagement: {hottest['Engagement Index']}</div>
                    <div class="zone-metric">{hottest['Foot Traffic']} visits · {hottest['Avg Dwell (sec)']}s dwell</div>
                </div>
                <div class="zone-card zone-card-cold">
                    <div class="zone-emoji">❄️</div>
                    <div class="zone-name-text">{coldest['Zone']}</div>
                    <div class="zone-metric">Engagement: {coldest['Engagement Index']}</div>
                    <div class="zone-metric">{coldest['Foot Traffic']} visits · {coldest['Avg Dwell (sec)']}s dwell</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Visualization toggle
        view_mode = st.radio("Visualization", ["Bar Chart", "Treemap"], horizontal=True, label_visibility="collapsed")

        col_chart, col_table = st.columns([3, 2])

        with col_chart:
            if view_mode == "Bar Chart":
                fig_bar = px.bar(
                    df_zones,
                    x="Zone",
                    y="Foot Traffic",
                    color="Engagement Index",
                    color_continuous_scale=["#1E1B4B", "#7C3AED", "#A855F7", "#EC4899", "#F43F5E"],
                    title=None
                )
                fig_bar.update_traces(marker_line_width=0, marker_cornerradius=6)
                fig_bar.update_layout(**CHART_LAYOUT, height=400, coloraxis_colorbar=dict(
                    title="Engagement",
                    tickfont=dict(color="#94A3B8", size=11),
                    title_font=dict(color="#94A3B8", size=12),
                ))
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                fig_tree = px.treemap(
                    df_zones,
                    path=["Zone"],
                    values="Foot Traffic",
                    color="Engagement Index",
                    color_continuous_scale=["#1E1B4B", "#7C3AED", "#A855F7", "#EC4899", "#F43F5E"],
                )
                fig_tree.update_layout(**CHART_LAYOUT, height=400, coloraxis_colorbar=dict(
                    title="Engagement",
                    tickfont=dict(color="#94A3B8", size=11),
                    title_font=dict(color="#94A3B8", size=12),
                ))
                fig_tree.update_traces(
                    textfont=dict(family="Outfit", size=15, color="#E2E8F0"),
                    marker_line_width=2,
                    marker_line_color="rgba(10,14,26,0.8)"
                )
                st.plotly_chart(fig_tree, use_container_width=True)

        with col_table:
            st.markdown('<div class="section-header" style="font-size:1.1rem;">📋 Zone Performance</div>', unsafe_allow_html=True)
            st.dataframe(
                df_zones.style.background_gradient(
                    cmap="Purples",
                    subset=["Engagement Index"]
                ).set_properties(**{
                    'font-family': 'Inter',
                }),
                hide_index=True,
                use_container_width=True
            )
    else:
        st.info("No zone heatmap metrics returned.")


# ── TAB 4: Active Anomalies ──────────────────────────────────
with tab_anomalies:
    st.markdown('<div class="section-header">⚠️ Active Store Operational Alerts</div>', unsafe_allow_html=True)

    store_anomalies = anomalies or []

    if not store_anomalies:
        st.markdown("""
        <div class="all-clear-card" style="margin-top:10px;">
            <div class="all-clear-icon">🟢</div>
            <div class="all-clear-text">All Operations Normal</div>
            <div class="all-clear-sub">Store operations are running within normal parameters. No active alerts.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Summary badges
        criticals = len([a for a in store_anomalies if a["severity"] == "CRITICAL"])
        warnings = len([a for a in store_anomalies if a["severity"] == "WARN"])
        infos = len([a for a in store_anomalies if a["severity"] == "INFO"])

        st.markdown(f"""
        <div class="callout-row">
            <div class="callout-card callout-rose">
                <div class="callout-value">{criticals}</div>
                <div class="callout-label">Critical</div>
            </div>
            <div class="callout-card callout-amber">
                <div class="callout-value">{warnings}</div>
                <div class="callout-label">Warnings</div>
            </div>
            <div class="callout-card callout-cyan">
                <div class="callout-value">{infos}</div>
                <div class="callout-label">Informational</div>
            </div>
            <div class="callout-card callout-purple">
                <div class="callout-value">{len(store_anomalies)}</div>
                <div class="callout-label">Total Alerts</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Anomaly cards
        anomalies_html = ""
        for alert in store_anomalies:
            anomalies_html += render_anomaly_card(alert)
        st.markdown(anomalies_html, unsafe_allow_html=True)

        # Summary glass panel
        st.markdown(f"""
        <div class="glass-surface" style="margin-top:16px; padding:18px 22px;">
            <div style="font-family:'Outfit'; font-weight:700; color:var(--text-primary); margin-bottom:8px; font-size:0.95rem;">
                📊 Alert Threshold Breakdown
            </div>
            <div style="font-size:0.88rem; color:var(--text-secondary); line-height:1.8;">
                • Active <span style="color:#FB7185; font-weight:600;">Critical Alerts: {criticals}</span> — Immediate store manager attention required<br>
                • Active <span style="color:#FBBF24; font-weight:600;">Warnings: {warnings}</span> — Assess operations and verify feeds<br>
                • Active <span style="color:#22D3EE; font-weight:600;">Info Alerts: {infos}</span> — For monitoring and awareness
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── TAB 5: Event Sandbox ─────────────────────────────────────
with tab_sandbox:
    st.markdown('<div class="section-header">🧪 Ingestion Event Sandbox</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="color:var(--text-secondary); font-size:0.92rem; margin-bottom:20px;">
        Simulate CCTV camera detection events. Build a mock event payload and push it to the ingestion API to watch metrics update in real-time.
    </div>
    """, unsafe_allow_html=True)

    col_inputs, col_json = st.columns([2, 2], gap="large")

    with col_inputs:
        st.markdown('<div class="sandbox-section-label">Event Configuration</div>', unsafe_allow_html=True)

        store_sel = st.selectbox("Store Target", stores, key="sb_store")
        zone_sel = st.selectbox("Zone", ["SKINCARE", "MAKEUP", "FRAGRANCE", "HAIRCARE", "BILLING"], key="sb_zone")
        ev_type = st.selectbox("Event Type", ["ZONE_ENTER", "ZONE_DWELL", "ZONE_EXIT", "BILLING_QUEUE_JOIN", "BILLING_QUEUE_ABANDON"], key="sb_type")
        v_id_sb = st.text_input("Visitor ID", "VIS_9999", key="sb_vid")
        dwell_sb = st.number_input("Dwell Time (ms)", min_value=0, max_value=3600000, value=30000, step=10000, key="sb_dwell")
        conf_sb = st.slider("Detection Confidence", min_value=0.0, max_value=1.0, value=0.95, step=0.05, key="sb_conf")
        is_staff_sb = st.checkbox("Is Staff Member?", value=False, key="sb_staff")

        # Generate event payload
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
        st.markdown('<div class="sandbox-section-label">Validated JSON Payload</div>', unsafe_allow_html=True)
        st.json(mock_event)

        if st.button("🚀 Push Event to API", use_container_width=True):
            try:
                resp = requests.post(f"{BACKEND_URL}/events/ingest", json=[mock_event])
                if resp.status_code == 201:
                    res_json = resp.json()
                    st.success("✅ Event processed successfully!")
                    st.json(res_json)
                    if res_json.get("inserted_count", 0) > 0:
                        st.markdown("""
                        <div class="glass-surface" style="padding:14px 18px; margin-top:8px;">
                            <div style="color:#34D399; font-weight:600; font-size:0.9rem;">
                                ✨ Event written to database. Refresh to see updated metrics.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.error(f"Error {resp.status_code}: {resp.text}")
            except Exception as ex:
                st.error(f"Submission failed: {str(ex)}")
