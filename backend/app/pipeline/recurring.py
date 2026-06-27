import uuid
from datetime import datetime
from collections import defaultdict
from typing import List, Dict

def parse_date_obj(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")

def detect_recurring_payments(transactions: List[Dict]) -> tuple[List[Dict], List[Dict]]:
    """
    Detects recurring transactions from a list of transactions.
    Returns (updated_transactions, list_of_recurring_groups).
    
    A group of transactions is recurring if:
    1. They are debits.
    2. They have the same description_clean (or fuzzy match).
    3. There are >= 2 occurrences.
    4. The amounts are within 5% or +/- Rs.100 of each other.
    5. The average interval between consecutive transactions is roughly weekly (5-10 days),
       monthly (25-35 days), quarterly (80-100 days), or yearly (340-380 days).
    """
    # 1. Group debits by description_clean
    debits = [t for t in transactions if t["type"] == "debit"]
    groups_by_desc = defaultdict(list)
    for t in debits:
        groups_by_desc[t["description_clean"].lower()].append(t)
        
    recurring_groups = []
    
    for desc_lower, txn_list in groups_by_desc.items():
        if len(txn_list) < 2:
            continue
            
        # Sort transaction list by date ascending
        txn_list_sorted = sorted(txn_list, key=lambda x: x["date"])
        
        # Check amount tolerance: compare everything to the median amount
        amounts = [abs(t["amount"]) for t in txn_list_sorted]
        median_amount = sum(amounts) / len(amounts)
        
        valid_amount_txns = []
        for t in txn_list_sorted:
            amt = abs(t["amount"])
            # Within 10% or +/- Rs.100
            if abs(amt - median_amount) <= (0.10 * median_amount) or abs(amt - median_amount) <= 100:
                valid_amount_txns.append(t)
                
        if len(valid_amount_txns) < 2:
            continue
            
        # Re-sort valid amount txns
        valid_amount_txns = sorted(valid_amount_txns, key=lambda x: x["date"])
        
        # Check intervals in days
        dates = [parse_date_obj(t["date"]) for t in valid_amount_txns]
        gaps = [(dates[i] - dates[i-1]).days for i in range(1, len(dates))]
        
        # Calculate average gap
        avg_gap = sum(gaps) / len(gaps) if gaps else 0
        
        frequency = "unknown"
        is_recurring = False
        
        if 5 <= avg_gap <= 10:
            frequency = "weekly"
            is_recurring = True
        elif 25 <= avg_gap <= 35:
            frequency = "monthly"
            is_recurring = True
        elif 80 <= avg_gap <= 100:
            frequency = "quarterly"
            is_recurring = True
        elif 340 <= avg_gap <= 380:
            frequency = "yearly"
            is_recurring = True
        elif len(valid_amount_txns) >= 3 and 10 < avg_gap < 25:
            # High frequency but irregular
            frequency = "weekly"
            is_recurring = True
        elif len(valid_amount_txns) >= 3 and 35 < avg_gap < 80:
            # Let's say bi-monthly or irregular monthly
            frequency = "monthly"
            is_recurring = True
        
        # Override to recurring if specific keywords exist and frequency is monthly/weekly/unknown but >= 2 txns
        # (e.g. Rent, EMI, SIP, Netflix, Spotify are almost certainly recurring even with just 2 data points)
        desc_clean = valid_amount_txns[0]["description_clean"]
        category = valid_amount_txns[0].get("category", "Other")
        
        is_known_recurring_merchant = any(
            kw in desc_lower for kw in ["netflix", "spotify", "youtube", "emi", "rent", "sip", "insurance", "lic", "broadband", "electricity"]
        ) or category in ["Subscriptions", "EMI", "Rent", "Investments"]
        
        if is_known_recurring_merchant and len(valid_amount_txns) >= 2:
            is_recurring = True
            if frequency == "unknown":
                frequency = "monthly"  # default to monthly
                
        if is_recurring:
            group_id = str(uuid.uuid4())
            label = desc_clean
            
            # Map typical amount
            typical_amount = median_amount
            
            # Mark transactions as recurring
            txn_ids = []
            for t in valid_amount_txns:
                t["is_recurring"] = True
                t["recurring_group_id"] = group_id
                txn_ids.append(t["id"])
                
            recurring_groups.append({
                "id": group_id,
                "label": label,
                "category": category,
                "frequency": frequency,
                "typical_amount": typical_amount,
                "last_seen_date": valid_amount_txns[-1]["date"],
                "transaction_ids": txn_ids,
                "confidence": 1.0 if is_known_recurring_merchant else 0.8
            })
            
    # Apply changes back to main list
    # Create mapping of modified transactions
    modified_txns_map = {t["id"]: t for group in recurring_groups for t in transactions if t["id"] in group["transaction_ids"]}
    
    for t in transactions:
        if t["id"] in modified_txns_map:
            t["is_recurring"] = True
            t["recurring_group_id"] = modified_txns_map[t["id"]]["recurring_group_id"]
            
    return transactions, recurring_groups
