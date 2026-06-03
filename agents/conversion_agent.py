from datetime import datetime
from typing import List, Dict, Any

class ConversionAgent:
    def __init__(self, time_window_seconds: int = 300):
        self.time_window_seconds = time_window_seconds
        self.agent_name = "Conversion Agent"

    def run(self, billing_events: List[Dict[str, Any]], transactions: List[Dict[str, Any]], unique_visitor_count: int) -> Dict[str, Any]:
        """
        Matches visitor billing events to POS transactions.
        Rule: A visitor is converted if a billing event occurs within 5 minutes (300s) of a transaction.
        
        Uses a greedy matching strategy:
        - Sorts transactions and billing events.
        - Matches each transaction to the closest unmatched billing event in time.
        
        Returns:
            A dictionary containing:
            - conversion_rate: Converted visitors / unique visitors.
            - matched_pairs: List of matches (visitor_id, transaction_id, time_diff).
            - converted_visitor_ids: Set/list of visitor IDs who converted.
            - reasoning_steps: Explanation logs of matching results.
        """
        reasoning_steps = []
        reasoning_steps.append("Starting conversion matching between billing events and POS transactions.")
        
        # Sort helper
        def get_timestamp(obj):
            t = obj.get("timestamp")
            if isinstance(t, str):
                return datetime.fromisoformat(t.replace("Z", "+00:00"))
            return t
            
        # Filter out staff and sort events
        customer_billing = [e for e in billing_events if not e.get("is_staff")]
        customer_billing.sort(key=get_timestamp)
        
        # Sort transactions
        sorted_txs = sorted(transactions, key=get_timestamp)
        
        reasoning_steps.append(
            f"Loaded {len(customer_billing)} customer billing events and {len(sorted_txs)} transactions."
        )
        
        matched_pairs = []
        converted_visitors = set()
        matched_tx_ids = set()
        
        for event in customer_billing:
            e_time = get_timestamp(event)
            v_id = event.get("visitor_id")
            
            # Skip if visitor already marked converted (to avoid duplicate conversions)
            if v_id in converted_visitors:
                continue
                
            best_tx = None
            best_diff = float("inf")
            
            for tx in sorted_txs:
                tx_id = tx.get("transaction_id")
                if tx_id in matched_tx_ids:
                    continue
                    
                tx_time = get_timestamp(tx)
                time_diff = (tx_time - e_time).total_seconds()
                
                # Check 5 minutes window rule: billing event must be within 5 mins before transaction
                if 0 <= time_diff <= self.time_window_seconds:
                    if time_diff < best_diff:
                        best_diff = time_diff
                        best_tx = tx
                        
            if best_tx:
                tx_id = best_tx.get("transaction_id")
                matched_tx_ids.add(tx_id)
                converted_visitors.add(v_id)
                matched_pairs.append({
                    "visitor_id": v_id,
                    "transaction_id": tx_id,
                    "event_timestamp": e_time.isoformat(),
                    "transaction_timestamp": best_tx.get("timestamp"),
                    "basket_value_inr": best_tx.get("basket_value_inr"),
                    "time_difference_sec": best_diff
                })
                
        converted_count = len(converted_visitors)
        
        # Calculate conversion rate
        conversion_rate = 0.0
        if unique_visitor_count > 0:
            conversion_rate = (converted_count / unique_visitor_count) * 100
            
        reasoning_steps.append(
            f"Matching completed. Successfully matched {len(matched_pairs)} transactions to unique visitors. "
            f"Unique Visitors: {unique_visitor_count}, Converted Visitors: {converted_count}. "
            f"Calculated Conversion Rate: {round(conversion_rate, 2)}%."
        )
        
        return {
            "agent_name": self.agent_name,
            "status": "SUCCESS",
            "conversion_rate": conversion_rate,
            "converted_visitors_count": converted_count,
            "total_transactions_matched": len(matched_pairs),
            "matched_pairs": matched_pairs,
            "converted_visitor_ids": list(converted_visitors),
            "reasoning_steps": reasoning_steps
        }
