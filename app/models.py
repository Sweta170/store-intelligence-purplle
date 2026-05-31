from sqlalchemy import Column, String, Integer, Boolean, Float, DateTime, JSON
from database.db import Base

class Event(Base):
    __tablename__ = "events"

    event_id = Column(String(36), primary_key=True, index=True)
    store_id = Column(String(50), nullable=False, index=True)
    camera_id = Column(String(50), nullable=False)
    visitor_id = Column(String(50), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    zone_id = Column(String(50), nullable=True)
    dwell_ms = Column(Integer, default=0)
    is_staff = Column(Boolean, default=False)
    confidence = Column(Float, nullable=False)
    event_metadata = Column("metadata", JSON, nullable=True)  # Store custom JSON structures

class POSTransaction(Base):
    __tablename__ = "pos_transactions"

    transaction_id = Column(String(100), primary_key=True, index=True)
    store_id = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    basket_value_inr = Column(Integer, nullable=False)

class Anomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    store_id = Column(String(50), nullable=False, index=True)
    anomaly_type = Column(String(50), nullable=False)  # QUEUE_SPIKE, CONVERSION_DROP, etc.
    severity = Column(String(20), nullable=False)  # INFO, WARN, CRITICAL
    timestamp = Column(DateTime(timezone=True), nullable=False)
    details = Column(String(500), nullable=True)
    suggested_action = Column(String(500), nullable=True)
    is_resolved = Column(Boolean, default=False)
