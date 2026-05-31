import re
from datetime import datetime
from typing import List, Dict, Any, Tuple

class EventValidationAgent:
    def __init__(self, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        self.agent_name = "Event Validation Agent"

    def run(self, events: List[Dict[str, Any]], existing_event_ids: List[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Validates a batch of events.
        Detects duplicates (within the batch and compared to database).
        Verifies schema requirements.
        Checks confidence score range.
        
        Returns:
            Tuple of:
            - List of valid event dictionaries.
            - Agent report metadata (containing logs, stats, and rejected events).
        """
        reasoning_steps = []
        reasoning_steps.append("Starting batch validation process.")
        
        db_event_ids = set(existing_event_ids or [])
        batch_seen_ids = set()
        
        valid_events = []
        invalid_events = []
        duplicates_detected = 0
        low_confidence_filtered = 0
        schema_failures = 0
        
        reasoning_steps.append(f"Received {len(events)} events for validation. Database contains {len(db_event_ids)} pre-existing keys.")
        
        for idx, event in enumerate(events):
            e_id = event.get("event_id")
            
            # 1. Check ID presence
            if not e_id:
                schema_failures += 1
                invalid_events.append({"event": event, "reason": "Missing event_id"})
                continue
                
            # 2. Check Deduplication
            if e_id in db_event_ids:
                duplicates_detected += 1
                invalid_events.append({"event": event, "reason": f"Duplicate event_id (exists in DB)"})
                continue
            if e_id in batch_seen_ids:
                duplicates_detected += 1
                invalid_events.append({"event": event, "reason": f"Duplicate event_id (duplicate in current batch)"})
                continue
            
            batch_seen_ids.add(e_id)
            
            # 3. Schema Check (Required Fields)
            required_fields = ["store_id", "camera_id", "visitor_id", "event_type", "timestamp", "confidence"]
            missing_fields = [f for f in required_fields if event.get(f) is None]
            if missing_fields:
                schema_failures += 1
                invalid_events.append({"event": event, "reason": f"Missing required fields: {', '.join(missing_fields)}"})
                continue
                
            # 4. Event Type Check
            allowed_types = {
                "ENTRY", "EXIT", "ZONE_ENTER", "ZONE_EXIT", "ZONE_DWELL", 
                "BILLING_QUEUE_JOIN", "BILLING_QUEUE_ABANDON", "REENTRY"
            }
            e_type = event.get("event_type")
            if e_type not in allowed_types:
                schema_failures += 1
                invalid_events.append({"event": event, "reason": f"Invalid event_type: '{e_type}'"})
                continue
                
            # 5. Timestamp format check
            ts = event.get("timestamp")
            # Handle possible datetimes if already parsed, or parse strings
            if isinstance(ts, str):
                try:
                    # Remove Z or offsets for parsing if needed
                    clean_ts = ts.replace("Z", "+00:00")
                    datetime.fromisoformat(clean_ts)
                except ValueError:
                    schema_failures += 1
                    invalid_events.append({"event": event, "reason": f"Invalid ISO 8601 timestamp: '{ts}'"})
                    continue
            elif not isinstance(ts, datetime):
                schema_failures += 1
                invalid_events.append({"event": event, "reason": "Timestamp must be string or datetime"})
                continue
                
            # 6. Confidence range check
            conf = event.get("confidence")
            try:
                conf_val = float(conf)
                if not (0.0 <= conf_val <= 1.0):
                    schema_failures += 1
                    invalid_events.append({"event": event, "reason": f"Confidence '{conf}' outside valid range [0, 1]"})
                    continue
                if conf_val < self.confidence_threshold:
                    low_confidence_filtered += 1
                    invalid_events.append({"event": event, "reason": f"Confidence score ({conf_val}) is below threshold ({self.confidence_threshold})"})
                    continue
            except (ValueError, TypeError):
                schema_failures += 1
                invalid_events.append({"event": event, "reason": f"Invalid confidence value: '{conf}'"})
                continue
                
            # If all checks pass
            valid_events.append(event)
            
        reasoning_steps.append(
            f"Validation completed. Results: {len(valid_events)} valid events, "
            f"{duplicates_detected} duplicates, {low_confidence_filtered} low-confidence events filtered, "
            f"{schema_failures} schema violations."
        )
        
        report = {
            "agent_name": self.agent_name,
            "status": "SUCCESS" if not invalid_events else "PARTIAL_SUCCESS",
            "stats": {
                "total_processed": len(events),
                "total_valid": len(valid_events),
                "duplicates_discarded": duplicates_detected,
                "low_confidence_filtered": low_confidence_filtered,
                "schema_violations": schema_failures
            },
            "reasoning_steps": reasoning_steps,
            "invalid_events": invalid_events
        }
        
        return valid_events, report
