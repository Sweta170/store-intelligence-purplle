# Retail Store Intelligence Platform

An agent-driven retail analytics system that transforms CCTV-style behavioral events into actionable business intelligence.

Built as a production-ready solution for the **Purplle Engineering Hiring Challenge**.

---

## 📈 Architecture Flow
```mermaid
flowchart TD
    A[Synthetic Event Generator] -->|Saves CSV & JSONL| B[data/ Directory]
    B -->|Pre-seeds on Boot| C[(SQL Database)]
    
    subgraph FastAPI Analytics Engine
        D[POST /events/ingest] -->|Validate & Deduplicate| E[Event Validation Agent]
        E -->|Store clean events| C
        
        F[GET analytics endpoints] -->|Read DB| C
        F --> G[Session Agent]
        F --> H[Conversion Agent]
        
        G & H --> I[Funnel Agent]
        G --> J[Heatmap Agent]
        G & H & J --> K[Anomaly Agent]
        G & H & I & J & K --> L[Executive Insights Agent]
    end
    
    L -->|Format Markdown Reports| M[Streamlit Dashboard UI]
```

---

## ✨ Features
* **FastAPI Analytics Engine**: Extremely fast, asynchronous endpoints validating payloads with Pydantic type models.
* **Agent-Based Intelligence Pipeline**: 7 decoupled agents analyzing telemetry data, mapping session logic, checking queue bottlenecks, and building markdown executive insights.
* **Visitor Session Reconstruction**: Groups raw time-series camera ticks into logical visits, calculating session dwells and tracking zone pathways.
* **Conversion Funnel Analytics**: Measures traffic transition percentages and step-wise drop-offs.
* **Heatmap Generation**: Computes department foot traffic, average dwell times, and an engagement index ($\text{visits} \times \text{dwell mins}$).
* **Operational Anomaly Detection**: Proactively detects queue spikes, camera stale feeds, dead zones, and conversion drop-offs.
* **PostgreSQL / SQLite Support**: Fully adaptive connections, defaulting to a shared SQLite connection during tests and PostgreSQL in production.
* **Streamlit Dashboard**: Dark-mode frontend showcasing analytics tables, charts, active operational alerts, and an ingestion testing sandbox.
* **Dockerized Deployment**: Fully self-contained multi-container build configuration.

---

## 📊 Dataset Configuration
* **13,184 Synthetic Behavioral Events** (including Entries, Zone Enters, Dwells, Exits, Re-entries, and Queue logs).
* **357 POS Transactions** (ranging from ₹199 to ₹4999).
* **5 Retail Stores** (`STORE_BLR_001`, `STORE_BLR_002`, `STORE_DEL_001`, `STORE_MUM_001`, `STORE_HYD_001`).
* **1,000+ Unique Visitors** and **50+ Staff Members** (staff are excluded from visitor KPI aggregates).

---

## 🚀 Quick Start (Docker Compose)
Launch the entire system on a fresh machine with a single command:
```bash
docker-compose up --build
```
This boots up:
1. **PostgreSQL Database** (port `5432`).
2. **FastAPI Backend** (port `8000`).
3. **Streamlit Dashboard** (port `8501`).

* OpenAPI Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
* Streamlit Dashboard UI: [http://localhost:8501](http://localhost:8501)

### Local Fallback (Without Docker)
If Docker is not running, run it locally using SQLite:
```bash
# 1. Install libraries
pip install -r requirements.txt

# 2. Start Backend API
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 3. Start Streamlit (in a separate terminal)
streamlit run dashboard/streamlit_app.py --server.port 8501
```

---

## 🔌 API Curl Requests Reference

Test the APIs from your terminal using `curl`:

### 1. Ingest Events (`POST /events/ingest`)
```bash
curl -X POST "http://localhost:8000/events/ingest" \
     -H "Content-Type: application/json" \
     -d '[{
       "event_id": "9d90d8a0-f8fb-41a6-880c-26d03541c4ad",
       "store_id": "STORE_BLR_001",
       "camera_id": "CAM_ENTRY_01",
       "visitor_id": "VIS_1099",
       "event_type": "ENTRY",
       "timestamp": "2026-03-03T10:00:00Z",
       "dwell_ms": 0,
       "is_staff": false,
       "confidence": 0.95
     }]'
```

### 2. Get Store KPIs (`GET /stores/{id}/metrics`)
```bash
curl -X GET "http://localhost:8000/stores/STORE_BLR_001/metrics"
```

### 3. Get Conversion Funnel (`GET /stores/{id}/funnel`)
```bash
curl -X GET "http://localhost:8000/stores/STORE_BLR_001/funnel"
```

### 4. Get Heatmap (`GET /stores/{id}/heatmap`)
```bash
curl -X GET "http://localhost:8000/stores/STORE_BLR_001/heatmap"
```

### 5. Get Anomalies (`GET /stores/{id}/anomalies`)
```bash
curl -X GET "http://localhost:8000/stores/STORE_BLR_001/anomalies"
```

### 6. Get Executive Insights (`GET /stores/{id}/executive-insights`)
```bash
curl -X GET "http://localhost:8000/stores/STORE_BLR_001/executive-insights"
```

### 7. Get System Health (`GET /health`)
```bash
curl -X GET "http://localhost:8000/health"
```

---

## 🧪 Running Unit Tests
The test suite compiles in-memory without side effects.
```bash
pip install -r requirements.txt
pytest --cov=app --cov=agents tests/ -v
```

---

## 📁 Project Directory Layout
```
store-intelligence/
├── data/
│   ├── events.jsonl             # Simulated event records
│   ├── pos_transactions.csv     # POS sale transactions
│   └── store_layout.json        # Zone mapping settings
├── app/
│   ├── main.py                  # API routes & Seeder
│   ├── models.py                # SQL Alchemy model schema
│   ├── ingestion.py             # Event Pydantic validator
│   ├── metrics.py               # KPIs helper module
│   ├── funnel.py                # Funnel logic helper
│   ├── heatmap.py               # Heatmap logic helper
│   ├── anomalies.py             # Active anomaly sync
│   └── health.py                # Camera staleness validator
├── agents/
│   ├── event_validation_agent.py# Schema validation agent
│   ├── session_agent.py         # Visitor path session agent
│   ├── conversion_agent.py      # Receipts matching agent
│   ├── funnel_agent.py          # Stage dropout agent
│   ├── heatmap_agent.py         # Foot traffic engagement agent
│   ├── anomaly_agent.py         # Operations alert agent
│   └── executive_insights_agent.py # Executive reporting agent
├── database/
│   ├── db.py                    # Connection engine
│   └── schema.sql               # Reference SQL layout
├── dashboard/
│   ├── streamlit_app.py         # Streamlit UI
│   └── purplle_logo.png         # Brand custom logo asset
├── tests/
│   ├── test_metrics.py          # KPIs & re-entry tests
│   ├── test_funnel.py           # Funnel drop-off tests
│   ├── test_anomalies.py        # Spikes & stale alerts tests
│   ├── test_agents.py           # Direct agent unit tests
│   └── test_api.py              # FastAPI integration tests
├── docs/
│   ├── DESIGN.md                # System documentation
│   └── CHOICES.md               # Rationale documentation
├── docker-compose.yml           # Deployment layout
├── Dockerfile                   # Python container layout
├── requirements.txt             # Project library file
└── README.md                    # Project manual
```
