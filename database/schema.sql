-- Database Schema for Retail Store Intelligence Platform

CREATE TABLE IF NOT EXISTS events (
    event_id VARCHAR(36) PRIMARY KEY,
    store_id VARCHAR(50) NOT NULL,
    camera_id VARCHAR(50) NOT NULL,
    visitor_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    zone_id VARCHAR(50),
    dwell_ms INTEGER DEFAULT 0,
    is_staff BOOLEAN DEFAULT FALSE,
    confidence REAL NOT NULL,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS pos_transactions (
    transaction_id VARCHAR(100) PRIMARY KEY,
    store_id VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    basket_value_inr INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS anomalies (
    id SERIAL PRIMARY KEY,
    store_id VARCHAR(50) NOT NULL,
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    details TEXT,
    suggested_action TEXT,
    is_resolved BOOLEAN DEFAULT FALSE
);

-- Indexing for fast analytical query responses
CREATE INDEX IF NOT EXISTS idx_events_store_timestamp ON events(store_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_events_visitor_store ON events(visitor_id, store_id);
CREATE INDEX IF NOT EXISTS idx_pos_transactions_store_timestamp ON pos_transactions(store_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_anomalies_store_timestamp ON anomalies(store_id, timestamp);
