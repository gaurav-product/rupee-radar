from typing import List, Dict

def calculate_financial_metrics(transactions: List[Dict], recurring_groups: List[Dict]) -> Dict:
    """
    Computes key financial metrics from a list of categorized transactions.
    """
    total_income = 0.0
    total_spend = 0.0
    
    category_debits = {}
    category_credits = {}
    
    biggest_debit = None
    biggest_credit = None
    
    monthly_spend = {}
    
    for t in transactions:
        amount = t["amount"]
        txn_type = t["type"]
        category = t.get("category", "Other")
        
        # Parse month from Date (YYYY-MM-DD -> YYYY-MM)
        date_str = t["date"]
        month_str = date_str[:7] if len(date_str) >= 7 else "Unknown"
        
        if txn_type == "credit":
            total_income += amount
            category_credits[category] = category_credits.get(category, 0.0) + amount
            
            if biggest_credit is None or amount > biggest_credit["amount"]:
                biggest_credit = t
        else:
            abs_amount = abs(amount)
            total_spend += abs_amount
            category_debits[category] = category_debits.get(category, 0.0) + abs_amount
            
            if biggest_debit is None or abs_amount > abs(biggest_debit["amount"]):
                biggest_debit = t
                
            # Monthly spend grouping
            monthly_spend[month_str] = monthly_spend.get(month_str, 0.0) + abs_amount
            
    # Calculate savings
    savings = total_income - total_spend
    savings_rate = (savings / total_income * 100) if total_income > 0 else 0.0
    
    # Format top categories list
    top_categories = []
    for cat, val in sorted(category_debits.items(), key=lambda x: x[1], reverse=True):
        top_categories.append({
            "category": cat,
            "amount": round(val, 2),
            "percentage": round((val / total_spend * 100), 2) if total_spend > 0 else 0.0
        })
        
    # Format monthly trends list
    monthly_trend = []
    for month, val in sorted(monthly_spend.items()):
        monthly_trend.append({
            "month": month,
            "spend": round(val, 2)
        })
        
    # Total recurring spend
    recurring_total = sum(group["typical_amount"] for group in recurring_groups)
    
    # Find biggest transactions details
    biggest_transactions = []
    if biggest_debit:
        biggest_transactions.append({
            "type": "debit",
            "description": biggest_debit["description_clean"],
            "amount": round(abs(biggest_debit["amount"]), 2),
            "date": biggest_debit["date"]
        })
    if biggest_credit:
        biggest_transactions.append({
            "type": "credit",
            "description": biggest_credit["description_clean"],
            "amount": round(biggest_credit["amount"], 2),
            "date": biggest_credit["date"]
        })
        
    return {
        "metrics": {
            "total_income": round(total_income, 2),
            "total_spend": round(total_spend, 2),
            "savings": round(savings, 2),
            "savings_rate": round(savings_rate, 2),
            "recurring_total": round(recurring_total, 2)
        },
        "top_categories": top_categories,
        "monthly_trend": monthly_trend,
        "biggest_transactions": biggest_transactions
    }
