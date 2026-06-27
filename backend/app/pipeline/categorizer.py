import re
import json
import logging
from typing import List, Dict, Optional
from groq import Groq

CATEGORIES = [
    "Food", "Travel", "Shopping", "Bills", "EMI", 
    "Subscriptions", "Salary", "Rent", "Investments", "Other"
]

# Bring over the regexes from cleaner for rule engine
from .cleaner import RULE_CATEGORY_MAPPING

logger = logging.getLogger(__name__)

def categorize_by_rules(desc_clean: str, desc_raw: str, amount: float, txn_type: str) -> Optional[str]:
    """
    Attempt to categorize a transaction using fast, high-precision regex matching.
    """
    desc_clean_lower = desc_clean.lower()
    desc_raw_lower = desc_raw.lower()
    
    # 1. Salary typically credits
    if txn_type == "credit" and any(kw in desc_raw_lower for kw in ["salary", "payslip", "wages"]):
        return "Salary"
        
    # 2. Check general rules
    for regex_pattern, category in RULE_CATEGORY_MAPPING.items():
        if re.search(regex_pattern, desc_clean_lower) or re.search(regex_pattern, desc_raw_lower):
            # Special check: Salary should generally be credits
            if category == "Salary" and txn_type != "credit":
                continue
            return category
            
    # 3. Check credits that look like investments
    if txn_type == "credit" and any(kw in desc_raw_lower for kw in ["dividend", "interest", "refund", "redeem"]):
        return "Investments"

    return None

def categorize_batch_with_groq(transactions: List[Dict], api_key: str) -> List[Dict]:
    """
    Categorizes a batch of transactions using Groq API with structured JSON output.
    Each transaction dict in input list should have: 'id', 'description_clean', 'amount', 'type'.
    """
    if not api_key:
        logger.warning("Groq API key not provided, skipping LLM categorization.")
        return [{"id": t["id"], "category": "Other", "confidence": 0.1} for t in transactions]

    client = Groq(api_key=api_key)
    
    # Prepare batch data to minimize token count and preserve privacy (exclude raw description and balance)
    batch_data = []
    for t in transactions:
        batch_data.append({
            "id": t["id"],
            "desc": t["description_clean"],
            "amt": abs(t["amount"]),
            "type": t["type"]
        })
        
    system_prompt = (
        "You are an expert personal finance assistant mapping bank transaction descriptions to a fixed taxonomy.\n"
        f"The taxonomy of categories is exactly: {', '.join(CATEGORIES)}.\n"
        "Return a JSON object containing a list 'categorized_transactions', where each item has:\n"
        "- 'id' (matching the input id)\n"
        "- 'category' (exactly one of the taxonomy categories)\n"
        "- 'confidence' (a float between 0.0 and 1.0, reflecting your certainty)\n\n"
        "Rules:\n"
        "- Salary and Interest credits should be Salary or Investments.\n"
        "- Subscriptions are recurring debits for media/entertainment (Netflix, Spotify, YouTube Premium).\n"
        "- Bills are utilities, telecoms, or insurance.\n"
        "- EMI covers loan repayments.\n"
        "- Food includes cafes, food delivery, grocery (Swiggy, Zomato, Starbucks, McDonald's).\n"
        "- Travel includes Uber, Ola, petrol, flights, train tickets.\n"
        "- Shopping is retail shopping (Amazon, Flipkart, clothing stores).\n"
        "- Investments cover mutual funds, stock deposits (Zerodha, Groww).\n"
        "- If uncertain, categorize as 'Other' with confidence < 0.5."
    )
    
    user_prompt = f"Categorize the following transactions:\n{json.dumps(batch_data)}"
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Groq's fast & cheap model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        response_content = completion.choices[0].message.content
        result = json.loads(response_content)
        
        # Build mapping
        mapping = {}
        for item in result.get("categorized_transactions", []):
            cat = item.get("category", "Other")
            if cat not in CATEGORIES:
                cat = "Other"
            mapping[item["id"]] = {
                "category": cat,
                "confidence": float(item.get("confidence", 0.5))
            }
            
        return [
            {
                "id": t["id"],
                "category": mapping.get(t["id"], {}).get("category", "Other"),
                "confidence": mapping.get(t["id"], {}).get("confidence", 0.5)
            }
            for t in transactions
        ]
        
    except Exception as e:
        logger.error(f"Error in Groq categorization: {e}")
        # Fallback to Other
        return [{"id": t["id"], "category": "Other", "confidence": 0.3} for t in transactions]

def categorize_transactions_hybrid(transactions: List[Dict], api_key: Optional[str] = None) -> List[Dict]:
    """
    Runs hybrid categorization on a list of standard transaction dicts.
    Assigns 'category' and 'category_confidence' keys to each dict.
    """
    unmatched_txns = []
    
    for t in transactions:
        # Check rule engine
        category = categorize_by_rules(
            t["description_clean"], 
            t["description_raw"], 
            t["amount"], 
            t["type"]
        )
        if category:
            t["category"] = category
            t["category_confidence"] = 1.0
        else:
            unmatched_txns.append(t)
            
    # For any unmatched transactions, attempt Groq LLM if key is available
    if unmatched_txns:
        if api_key:
            # Batch them in chunks of 30 to avoid prompt limits
            chunk_size = 30
            for i in range(0, len(unmatched_txns), chunk_size):
                chunk = unmatched_txns[i:i+chunk_size]
                results = categorize_batch_with_groq(chunk, api_key)
                
                # Apply results
                res_map = {item["id"]: item for item in results}
                for t in chunk:
                    res = res_map.get(t["id"], {"category": "Other", "confidence": 0.5})
                    # If LLM confidence is very low, classify as 'Other'
                    if res["confidence"] < 0.6:
                        t["category"] = "Other"
                    else:
                        t["category"] = res["category"]
                    t["category_confidence"] = res["confidence"]
        else:
            # No Groq key, fall back to "Other"
            for t in unmatched_txns:
                t["category"] = "Other"
                t["category_confidence"] = 0.5
                
    return transactions
