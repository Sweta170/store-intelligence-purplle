# Architectural Design - Retail Store Intelligence Platform

This document describes the architectural layout, data pipelines, schema models, and the Agentic AI design powering the Retail Store Intelligence Platform.

---

## 1. System Architecture

The platform is designed around a decoupled, three-tier service-oriented architecture:

```mermaid
graph TD
    subgraph CCTV Data Source
        A[Synthetic CCTV Generator] -->|Saves CSV & JSONL| B[data/ Directory]
    end

    subgraph Backend Application (FastAPI)
        C[FastAPI Ingestion Endpoint] -->|Ingests & Deduplicates| D[(SQL Database)]
        E[FastAPI Analytics Endpoints] -->|Queries| D
        E -->|Executes| F[7 Specialized Agents]
    end

    subgraph Database Layer
        D -->|Reads / Writes| G[PostgreSQL / SQLite]
    end

    subgraph Dashboard Interface (Streamlit)
        H[Streamlit Application] -->|Requests JSON APIs| E
        H -->|Renders UI Components| I[Plotly Funnels / Heatmaps / Active Alerts]
    end
    
    B -->|Pre-seeds on boot| D
```

1. **Dashboard (Streamlit UI)**: Exposes store KPIs, visualizes customer conversion funnels and zone heatmaps, details anomalies, and hosts a sandbox mock event generator.
2. **Backend Engine (FastAPI)**: Serves endpoints for data ingestion, analytics queries, health status, and triggers agent evaluation.
3. **Database (SQLAlchemy ORM)**: Supports a PostgreSQL engine inside Docker and automatically falls back to an in-memory or file-based SQLite database for local development and testing.
4. **Agent Collective (Specialized Python Classes)**: Models logic as discrete agents carrying out validations, sessionizing traffic, matching POS conversions, aggregating funnels/heatmaps, scanning for anomalies, and generating business summaries.

---

## 2. Data Flow Pipeline

### 2.1 Event Ingestion & Deduplication
When a batch of events is POSTed to `/events/ingest`:
1. The backend queries the database to match the batch's `event_id` keys, preventing re-insertion (idempotency).
2. The **Event Validation Agent** validates schema adherence, checks that confidence scores exceed the `0.5` threshold, and discards batch duplicates.
3. Validated events are written in bulk to the SQL database.

### 2.2 Analytics & Insights Compilation
When the Streamlit dashboard selects a store and requests stats:
1. The database retrieves events and transaction records for that store.
2. The **Session Agent** filters staff out and groups raw entries, exits, and dwells into logical visitor session objects.
3. The **Conversion Agent** executes greedy chronological proximity matching between customer billing queue timestamps and POS transactions within a 5-minute window.
4. The **Funnel Agent** maps session journeys to calculate step-by-step drop-offs.
5. The **Heatmap Agent** aggregates zone metrics and spatial engagement.
6. The **Anomaly Agent** scans metrics for queue surges, drop-offs, stale feeds, and dead departments.
7. The **Executive Insights Agent** reviews all outputs to assemble a Markdown-formatted executive report containing business summaries and manager recommendations.

---

## 3. Database Schema Modeling

The storage layer is defined in [schema.sql](file:///E:/finalyearproject/purplle/store-intelligence/database/schema.sql) and implemented via SQLAlchemy in [models.py](file:///E:/finalyearproject/purplle/store-intelligence/app/models.py).

```
                             +-------------------+
                             |     anomalies     |
                             +-------------------+
                             | id (PK)           |
                             | store_id          |
                             | anomaly_type      |
                             | severity          |
                             | timestamp         |
                             | details           |
                             | suggested_action  |
                             | is_resolved       |
                             +-------------------+
                                       ^
                                       |
+---------------------+      +-------------------+      +---------------------+
|       events        |      |    store_layout   |      |  pos_transactions   |
+---------------------+      +-------------------+      +---------------------+
| event_id (PK)       |      | (Reference JSON)  |      | transaction_id (PK) |
| store_id            |      | - Store ID        |      | store_id            |
| camera_id           |      | - Camera ID       |      | timestamp           |
| visitor_id          |      | - Zones           |      | basket_value_inr    |
| event_type          |      | - Hours           |      +---------------------+
| timestamp           |      +-------------------+
| zone_id             |
| dwell_ms            |
| is_staff            |
| confidence          |
| metadata (JSON)     |
| gender_pred         |
| age_pred            |
| age_bucket          |
| group_size          |
| zone_name           |
| zone_type           |
+---------------------+
```

---

## 4. Agentic AI & Decision Logic

Each of the seven agents is designed to mimic a human operations analyst or store manager.

* **Event Validation Agent**: A data-quality gatekeeper checking fields, time standards, duplication bounds, and confidence limits.
* **Session Agent**: Reconstitutes customer profiles and identifies re-entry behaviors.
* **Conversion Agent**: Matches POS receipts (which lack visitor IDs) with billing camera events using a greedy temporal window, solving the visitor-transaction linkage problem.
* **Funnel Agent**: Identifies customer dropout rates at each phase of the shopping cycle.
* **Heatmap Agent**: Analyzes spatial engagement by calculating an Engagement Score ($\text{visits} \times \text{dwell time}$) to measure merchandising success.
* **Anomaly Agent**: Monitors real-time conditions against threshold limits to alert managers about queue sizes, sales drops, and offline cameras.
* **Executive Insights Agent**: Operates as a senior retail consultant, summarizing metrics and building an actionable operational plan for the store manager.
