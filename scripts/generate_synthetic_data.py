import json
import csv
import random
import uuid
from datetime import datetime, timedelta
import os

# Set seed for reproducibility
random.seed(42)

STORES = [
    "STORE_BLR_001",
    "STORE_BLR_002",
    "STORE_DEL_001",
    "STORE_MUM_001",
    "STORE_HYD_001"
]

ZONES = ["SKINCARE", "MAKEUP", "FRAGRANCE", "HAIRCARE", "BILLING"]

CAMERA_MAPPING = {
    "ENTRY": "CAM_ENTRY_01",
    "EXIT": "CAM_EXIT_01",
    "SKINCARE": "CAM_SKINCARE_01",
    "MAKEUP": "CAM_MAKEUP_01",
    "FRAGRANCE": "CAM_FRAGRANCE_01",
    "HAIRCARE": "CAM_HAIRCARE_01",
    "BILLING": "CAM_BILLING_01"
}

OPENING_HOURS = {
    "open": "09:00:00",
    "close": "22:00:00"
}

def generate_layout(output_path):
    layout = {
        "stores": []
    }
    for store in STORES:
        store_layout = {
            "store_id": store,
            "opening_hours": OPENING_HOURS,
            "cameras": [
                {"camera_id": cam_id, "zone": zone}
                for zone, cam_id in CAMERA_MAPPING.items()
            ],
            "zones": [
                {
                    "zone_id": zone,
                    "description": f"{zone.capitalize()} section in {store}",
                    "capacity_threshold": 15 if zone != "BILLING" else 5
                }
                for zone in ZONES
            ]
        }
        layout["stores"].append(store_layout)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(layout, f, indent=2)
    print(f"Generated store layout at {output_path}")

def generate_data(layout_path, events_path, tx_path):
    # Ensure layout exists
    generate_layout(layout_path)
    
    # Configuration for simulation
    start_date = datetime(2026, 3, 3, 9, 0, 0) # Business Day
    end_date = datetime(2026, 3, 3, 22, 0, 0)
    
    # 50+ staff members across all stores
    staff_ids = [f"STF_{i:03d}" for i in range(1, 55)]
    # Store-to-staff mapping (approx 10 staff per store)
    store_staff = {store: [] for store in STORES}
    for i, s_id in enumerate(staff_ids):
        store = STORES[i % len(STORES)]
        store_staff[store].append(s_id)
        
    # 1000+ unique visitors
    visitor_ids = [f"VIS_{i:04d}" for i in range(1, 1100)]
    
    events = []
    transactions = []
    
    # Helper to check if time is within empty period (14:30 - 16:00)
    def is_low_traffic_hour(dt):
        return 14 <= dt.hour < 16

    # Helper to check if time is within peak queue spike hour (12:30-13:30 or 18:30-20:30)
    def is_peak_hour(dt):
        return (12 <= dt.hour < 14) or (18 <= dt.hour < 21)

    print("Simulating staff movements...")
    # Staff movements: they enter in the morning, shift between zones, and exit in the evening
    for store in STORES:
        for s_id in store_staff[store]:
            # Morning arrival
            arrival_time = start_date + timedelta(minutes=random.randint(-15, 30))
            events.append({
                "event_id": str(uuid.uuid4()),
                "store_id": store,
                "camera_id": CAMERA_MAPPING["ENTRY"],
                "visitor_id": s_id,
                "event_type": "ENTRY",
                "timestamp": arrival_time.isoformat() + "Z",
                "zone_id": None,
                "dwell_ms": 0,
                "is_staff": True,
                "confidence": round(random.uniform(0.95, 0.99), 2),
                "metadata": {"session_seq": 1}
            })
            
            # Throughout the day, staff moves between zones
            current_time = arrival_time
            session_seq = 1
            while current_time < end_date - timedelta(hours=1):
                # Staff dwells in a zone
                zone = random.choice(ZONES)
                dwell_mins = random.randint(15, 90)
                current_time += timedelta(minutes=random.randint(5, 20)) # movement gap
                
                enter_time = current_time
                events.append({
                    "event_id": str(uuid.uuid4()),
                    "store_id": store,
                    "camera_id": CAMERA_MAPPING[zone],
                    "visitor_id": s_id,
                    "event_type": "ZONE_ENTER",
                    "timestamp": enter_time.isoformat() + "Z",
                    "zone_id": zone,
                    "dwell_ms": 0,
                    "is_staff": True,
                    "confidence": round(random.uniform(0.90, 0.99), 2),
                    "metadata": {"session_seq": session_seq}
                })
                
                current_time += timedelta(minutes=dwell_mins)
                
                events.append({
                    "event_id": str(uuid.uuid4()),
                    "store_id": store,
                    "camera_id": CAMERA_MAPPING[zone],
                    "visitor_id": s_id,
                    "event_type": "ZONE_DWELL",
                    "timestamp": current_time.isoformat() + "Z",
                    "zone_id": zone,
                    "dwell_ms": dwell_mins * 60 * 1000,
                    "is_staff": True,
                    "confidence": round(random.uniform(0.90, 0.99), 2),
                    "metadata": {"session_seq": session_seq}
                })
                
                events.append({
                    "event_id": str(uuid.uuid4()),
                    "store_id": store,
                    "camera_id": CAMERA_MAPPING[zone],
                    "visitor_id": s_id,
                    "event_type": "ZONE_EXIT",
                    "timestamp": current_time.isoformat() + "Z",
                    "zone_id": zone,
                    "dwell_ms": dwell_mins * 60 * 1000,
                    "is_staff": True,
                    "confidence": round(random.uniform(0.90, 0.99), 2),
                    "metadata": {"session_seq": session_seq}
                })
            
            # Evening departure
            departure_time = end_date - timedelta(minutes=random.randint(0, 30))
            events.append({
                "event_id": str(uuid.uuid4()),
                "store_id": store,
                "camera_id": CAMERA_MAPPING["EXIT"],
                "visitor_id": s_id,
                "event_type": "EXIT",
                "timestamp": departure_time.isoformat() + "Z",
                "zone_id": None,
                "dwell_ms": int((departure_time - arrival_time).total_seconds() * 1000),
                "is_staff": True,
                "confidence": round(random.uniform(0.95, 0.99), 2),
                "metadata": {"session_seq": session_seq}
            })

    print("Simulating visitors...")
    # Track visitor session counts for re-entries
    visitor_sessions = {v_id: 0 for v_id in visitor_ids}
    
    # Store queues state (to track queue depth spikes)
    store_queues = {store: 0 for store in STORES}
    
    for v_id in visitor_ids:
        # Determine how many visits this visitor makes (mostly 1, some 2 for re-entry, few 0)
        num_visits = 1
        rand_val = random.random()
        if rand_val < 0.05:
            num_visits = 2 # Re-entry visitor!
        elif rand_val < 0.08:
            num_visits = 0 # Doesn't visit on this day
            
        if num_visits == 0:
            continue
            
        # Choose primary store for this visitor
        store = random.choice(STORES)
        
        # Select raw base timestamps for entries
        first_entry_hour = random.randint(9, 21)
        # Shift entries to create empty periods and busy periods
        if is_low_traffic_hour(datetime(2026, 3, 3, first_entry_hour, 0)):
            if random.random() < 0.70: # 70% chance to move it out of empty period
                first_entry_hour = random.choice([10, 11, 12, 17, 18, 19, 20])
                
        # Group entries: 15% chance to enter as a group with another visitor
        entry_offset_seconds = 0
        if random.random() < 0.15:
            # Match entry time closely with a group offset
            entry_offset_seconds = random.randint(0, 5)
            
        base_entry_time = start_date + timedelta(hours=first_entry_hour - 9, minutes=random.randint(0, 59), seconds=entry_offset_seconds)
        
        for visit_idx in range(num_visits):
            visitor_sessions[v_id] += 1
            session_seq = visitor_sessions[v_id]
            
            entry_time = base_entry_time if visit_idx == 0 else base_entry_time + timedelta(hours=random.randint(2, 5))
            
            # If second entry, event type is REENTRY or ENTRY? The requirements list REENTRY as a distinct event type.
            # We'll use REENTRY for the entry event if it's session_seq > 1, or just trigger a REENTRY event.
            # Let's generate a REENTRY event type if session_seq > 1.
            entry_event_type = "REENTRY" if session_seq > 1 else "ENTRY"
            
            events.append({
                "event_id": str(uuid.uuid4()),
                "store_id": store,
                "camera_id": CAMERA_MAPPING["ENTRY"],
                "visitor_id": v_id,
                "event_type": entry_event_type,
                "timestamp": entry_time.isoformat() + "Z",
                "zone_id": None,
                "dwell_ms": 0,
                "is_staff": False,
                "confidence": round(random.uniform(0.85, 0.99), 2),
                "metadata": {"session_seq": session_seq}
            })
            
            # Zones visited during session
            # Typically 1 to 4 zones
            num_zones = random.randint(1, 4)
            visited_zones = random.sample([z for z in ZONES if z != "BILLING"], min(num_zones, 4))
            
            current_time = entry_time
            
            for zone in visited_zones:
                # ZONE_ENTER
                current_time += timedelta(seconds=random.randint(10, 60)) # walk to zone
                enter_time = current_time
                
                events.append({
                    "event_id": str(uuid.uuid4()),
                    "store_id": store,
                    "camera_id": CAMERA_MAPPING[zone],
                    "visitor_id": v_id,
                    "event_type": "ZONE_ENTER",
                    "timestamp": enter_time.isoformat() + "Z",
                    "zone_id": zone,
                    "dwell_ms": 0,
                    "is_staff": False,
                    "confidence": round(random.uniform(0.80, 0.99), 2),
                    "metadata": {"session_seq": session_seq}
                })
                
                # Zone dwell time: mixed short vs long dwells
                dwell_type = random.random()
                if dwell_type < 0.20:
                    # Short dwell session (< 1 minute)
                    dwell_sec = random.randint(15, 59)
                elif dwell_type < 0.85:
                    # Normal dwell (1-10 minutes)
                    dwell_sec = random.randint(60, 600)
                else:
                    # Long dwell session (15+ minutes)
                    dwell_sec = random.randint(900, 1800)
                    
                current_time += timedelta(seconds=dwell_sec)
                
                # ZONE_DWELL
                events.append({
                    "event_id": str(uuid.uuid4()),
                    "store_id": store,
                    "camera_id": CAMERA_MAPPING[zone],
                    "visitor_id": v_id,
                    "event_type": "ZONE_DWELL",
                    "timestamp": current_time.isoformat() + "Z",
                    "zone_id": zone,
                    "dwell_ms": dwell_sec * 1000,
                    "is_staff": False,
                    "confidence": round(random.uniform(0.80, 0.99), 2),
                    "metadata": {"session_seq": session_seq}
                })
                
                # ZONE_EXIT
                events.append({
                    "event_id": str(uuid.uuid4()),
                    "store_id": store,
                    "camera_id": CAMERA_MAPPING[zone],
                    "visitor_id": v_id,
                    "event_type": "ZONE_EXIT",
                    "timestamp": current_time.isoformat() + "Z",
                    "zone_id": zone,
                    "dwell_ms": dwell_sec * 1000,
                    "is_staff": False,
                    "confidence": round(random.uniform(0.80, 0.99), 2),
                    "metadata": {"session_seq": session_seq}
                })
                
            # Conversion check: 35% chance to proceed to billing queue
            will_buy = random.random() < 0.35
            # Queue abandon: 8% of those who enter billing queue will abandon it
            will_abandon = will_buy and (random.random() < 0.08)
            
            if will_buy or will_abandon:
                zone = "BILLING"
                current_time += timedelta(seconds=random.randint(10, 30)) # walk to billing
                queue_join_time = current_time
                
                # Queue depth simulation: spikes during peak hours
                q_depth = random.randint(1, 3)
                if is_peak_hour(queue_join_time):
                    q_depth = random.randint(4, 8) # Queue depth spike!
                    
                events.append({
                    "event_id": str(uuid.uuid4()),
                    "store_id": store,
                    "camera_id": CAMERA_MAPPING[zone],
                    "visitor_id": v_id,
                    "event_type": "BILLING_QUEUE_JOIN",
                    "timestamp": queue_join_time.isoformat() + "Z",
                    "zone_id": zone,
                    "dwell_ms": 0,
                    "is_staff": False,
                    "confidence": round(random.uniform(0.85, 0.99), 2),
                    "metadata": {"queue_depth": q_depth, "session_seq": session_seq}
                })
                
                # Time spent in queue before transaction/abandon
                in_queue_sec = random.randint(60, 300)
                current_time += timedelta(seconds=in_queue_sec)
                
                if will_abandon:
                    events.append({
                        "event_id": str(uuid.uuid4()),
                        "store_id": store,
                        "camera_id": CAMERA_MAPPING[zone],
                        "visitor_id": v_id,
                        "event_type": "BILLING_QUEUE_ABANDON",
                        "timestamp": current_time.isoformat() + "Z",
                        "zone_id": zone,
                        "dwell_ms": in_queue_sec * 1000,
                        "is_staff": False,
                        "confidence": round(random.uniform(0.85, 0.99), 2),
                        "metadata": {"queue_depth": max(0, q_depth - 1), "session_seq": session_seq}
                    })
                else:
                    # Converted visitor! Generate POS transaction
                    tx_id = f"TXN_{store}_{len(transactions) + 1:04d}"
                    # Transaction happens within 5 minutes of billing event. Let's make it 30-180 seconds after join.
                    tx_time = queue_join_time + timedelta(seconds=random.randint(30, 180))
                    
                    basket_val = random.randint(199, 4999)
                    
                    transactions.append({
                        "store_id": store,
                        "transaction_id": tx_id,
                        "timestamp": tx_time.isoformat() + "Z",
                        "basket_value_inr": basket_val
                    })
                    
                    # Also write a ZONE_DWELL for billing to show duration in billing zone
                    events.append({
                        "event_id": str(uuid.uuid4()),
                        "store_id": store,
                        "camera_id": CAMERA_MAPPING[zone],
                        "visitor_id": v_id,
                        "event_type": "ZONE_DWELL",
                        "timestamp": current_time.isoformat() + "Z",
                        "zone_id": zone,
                        "dwell_ms": in_queue_sec * 1000,
                        "is_staff": False,
                        "confidence": round(random.uniform(0.85, 0.99), 2),
                        "metadata": {"session_seq": session_seq}
                    })
                    
            # Finally, exit the store
            current_time += timedelta(seconds=random.randint(10, 40)) # walk to exit
            events.append({
                "event_id": str(uuid.uuid4()),
                "store_id": store,
                "camera_id": CAMERA_MAPPING["EXIT"],
                "visitor_id": v_id,
                "event_type": "EXIT",
                "timestamp": current_time.isoformat() + "Z",
                "zone_id": None,
                "dwell_ms": int((current_time - entry_time).total_seconds() * 1000),
                "is_staff": False,
                "confidence": round(random.uniform(0.85, 0.99), 2),
                "metadata": {"session_seq": session_seq}
            })

    # Sort events by timestamp to ensure chronological order in events.jsonl
    events.sort(key=lambda e: e["timestamp"])
    
    # Sort transactions by timestamp as well
    transactions.sort(key=lambda t: t["timestamp"])

    print(f"Generated {len(events)} events (Target: 5000+)")
    print(f"Generated {len(transactions)} POS transactions (Target: 100+)")
    
    # Save to files
    with open(events_path, "w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")
    print(f"Saved events to {events_path}")
            
    with open(tx_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["store_id", "transaction_id", "timestamp", "basket_value_inr"])
        writer.writeheader()
        writer.writerows(transactions)
    print(f"Saved transactions to {tx_path}")

if __name__ == "__main__":
    layout_file = "data/store_layout.json"
    events_file = "data/events.jsonl"
    tx_file = "data/pos_transactions.csv"
    
    generate_data(layout_file, events_file, tx_file)
