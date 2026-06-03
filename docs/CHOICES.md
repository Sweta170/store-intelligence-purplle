# Design Choices & Technical Rationale

This document details the choices made during the development of the Retail Store Intelligence Platform.

---

## 1. Why Synthetic Events?
* **Problem**: In a real store environment, capturing customer journeys requires high-definition CCTV feeds, edge computers, and advanced computer vision models (e.g. YOLO, ByteTrack) to detect boxes, faces, and trajectories. These models and feeds are not available in a standard coding test.
* **Solution**: By generating synthetic events following the exact target schema, we simulate the end-product of a CCTV computer vision inference pipeline. The generated dataset includes complex patterns (group entries, re-entries, peak queue depth spikes, shifts, empty periods, staff movements) to test the analytical robustness of our backend and agents under realistic store conditions.

---

## 2. Why FastAPI?
* **High Performance**: FastAPI is one of the fastest Python frameworks available, built on Starlette and Uvicorn, which makes it ideal for handling large batches of concurrent ingestion requests.
* **Auto-Validation & Type Safety**: Using Pydantic models, FastAPI automatically validates incoming request bodies, converting timestamps and ensuring types conform to the event schema before routing requests.
* **OpenAPI Documentation**: Exposes interactive API docs (`/docs` and `/redoc`) out of the box, speeding up integration and testing.

---

## 3. Why PostgreSQL?
* **Relational with JSON Support**: Events include flat relational data (`store_id`, `timestamp`) and unstructured context dictionary data (`metadata`). PostgreSQL offers the best of both worlds, providing strong relational structures alongside robust `JSONB` querying and indexing capabilities.
* **Production Ready**: PostgreSQL is ACID-compliant and highly optimized for concurrent reads/writes under heavy loads.
* **ORM Compatibility**: Integrates seamlessly with SQLAlchemy, allowing us to build migrations and swap to SQLite for test isolation.

---

## 4. Why Agentic Architecture?
* **Decoupled Roles**: Instead of writing one massive analytics service, separating concerns into specialized agents (Validation, Session, Conversion, Funnel, Heatmap, Anomaly, Insights) keeps classes focused, reusable, and easy to modify.
* **Traceable Reasoning**: Each agent records its internal steps as a `reasoning_steps` text array. This mimics LLM-style chain-of-thought execution, making it easy to display the reasoning process on the dashboard and audit how anomalies or recommendations were derived.
* **LLM Ready**: By keeping agent interfaces clean, we can drop in Google Gemini or OpenAI LLM API calls in the future to replace or augment the rules/heuristic engines without rewriting the backend APIs.

---

## 5. Why Streamlit?
* **Fast Development**: Streamlit allows building highly interactive, data-dense web apps entirely in Python.
* **Data Integration**: Integrates directly with Pandas, Plotly, and Requests, making it straightforward to pull FastAPI data, run visual transformations, and render high-fidelity charts.
* **Self-Contained**: Eliminates the need for a separate Node.js/React build step, aligning perfectly with the single-command deployment goal.

---

## 6. Why Conversion Matching Uses Temporal Proximity?
* **Lack of Direct Visitor IDs on Receipts**: POS transactions are recorded at checkout registers and contain payment/basket info, but do not naturally associate with a visitor's tracking ID (which is derived from camera feeds).
* **Heuristics for Conversion Linkage**: By linking billing camera zone events with receipts processed in a 5-minute chronological window after queue entry, the platform resolves customer-to-transaction mappings with high confidence. This mimics real-world cashier workflow times.

---

## 7. Why Re-entry Handling Matters?
* **Avoiding Funnel Inflation**: Customers frequently browse, leave, and step back inside a store (e.g. comparing prices or retrieving items). If re-entries are treated as entirely new visitors, unique visitor counts and funnel conversion percentages will be artificially inflated and skewed.
* **Visitor-Level Session Consolidation**: Recognizing re-entry behavior ensures customer paths are aggregated on a unique-visitor basis rather than session-count basis, preserving analytical integrity.
