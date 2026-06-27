import re
import pandas as pd
import numpy as np
from datetime import datetime

# Standard category list
CATEGORIES = [
    "Food", "Travel", "Shopping", "Bills", "EMI", 
    "Subscriptions", "Salary", "Rent", "Investments", "Other"
]

# Quick rule engine mapping keywords to categories
RULE_CATEGORY_MAPPING = {
    r"\b(swiggy|zomato|dominos|pizza|restaurant|food|mcdonald|starbucks|cafe)\b": "Food",
    r"\b(uber|ola|irctc|makemytrip|indigo|rapido|metro|fuel|petrol|hpcl|bpcl|shell|travel|flight)\b": "Travel",
    r"\b(amazon|flipkart|myntra|ajio|shopping|retail|dmart|decathlon|zara|h&m)\b": "Shopping",
    r"\b(netflix|spotify|youtube|hotstar|prime video|apple\.com|itunes|sony liv)\b": "Subscriptions",
    r"\b(salary|payslip|wages|reimbursement|bonus)\b": "Salary",
    r"\b(rent|landlord|housing|pg)\b": "Rent",
    r"\b(sip|zerodha|groww|mutual fund|indmoney|angelone|stocks|securities|ppf|fd|investment)\b": "Investments",
    r"\b(emi|loan|home loan|car loan|personal loan|hdfc bank emi|icici bank emi|sbi emi)\b": "EMI",
    r"\b(electricity|water|gas|broadband|wifi|jio|airtel|vi |telecom|mobile recharge|bill|dth|insurance|lic|act fibernet)\b": "Bills"
}

# Clean merchant labels
MERCHANT_CLEANING_RULES = [
    (r"\bswiggy\b", "Swiggy"),
    (r"\bzomato\b", "Zomato"),
    (r"\bdominos\b", "Dominos"),
    (r"\buber\b", "Uber"),
    (r"\bola\b", "Ola"),
    (r"\bnetflix\b", "Netflix"),
    (r"\bspotify\b", "Spotify"),
    (r"\byoutube\b", "YouTube"),
    (r"\bamazon\b", "Amazon"),
    (r"\bflipkart\b", "Flipkart"),
    (r"\bmyntra\b", "Myntra"),
    (r"\bzerodha\b", "Zerodha"),
    (r"\bgroww\b", "Groww"),
    (r"\bpaytm\b", "Paytm"),
    (r"\bphonepe\b", "PhonePe"),
    (r"\bstarbucks\b", "Starbucks"),
    (r"\bdmart\b", "DMart"),
    (r"\bdecathlon\b", "Decathlon"),
    (r"\bairtel\b", "Airtel"),
    (r"\bjio\b", "Jio"),
    (r"\bact fibernet\b", "ACT Fibernet"),
    (r"\bhotstar\b", "Hotstar"),
    (r"\bprime video\b", "Amazon Prime"),
    (r"\bgoogle\b", "Google"),
]

def clean_description(desc: str) -> tuple[str, str]:
    """
    Cleans messy transaction descriptions (especially Indian UPI/IMPS formats).
    Returns (cleaned_description, mode)
    """
    if not desc or not isinstance(desc, str):
        return "Unknown Transaction", "unknown"
        
    desc_upper = desc.upper()
    mode = "other"
    
    # Detect transaction mode
    if "UPI/" in desc_upper or "UPI-" in desc_upper:
        mode = "UPI"
    elif "NEFT" in desc_upper:
        mode = "NEFT"
    elif "IMPS" in desc_upper:
        mode = "IMPS"
    elif "RTGS" in desc_upper:
        mode = "RTGS"
    elif "CARD" in desc_upper or "POS" in desc_upper:
        mode = "card"
    elif "CASH" in desc_upper or "CHG" in desc_upper:
        mode = "cash"
    elif "EMI" in desc_upper:
        mode = "EMI"
    elif "SIP" in desc_upper:
        mode = "SIP"

    cleaned = desc
    
    # Indian UPI pattern strip: e.g. UPI/DR/123456789012/MerchantName/ref/remarks
    # Or UPI/123456789012/MerchantName/
    # Let's do some general sanitization
    cleaned = re.sub(r'UPI/DR/\d+/', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'UPI/CR/\d+/', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'UPI/\d+/', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'IMPS/\d+/', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'NEFT/\w+/', '', cleaned, flags=re.IGNORECASE)
    
    # Strip random sequences of digits (transaction reference IDs, phone numbers, or merchant IDs)
    cleaned = re.sub(r'\b\d{8,16}\b', '', cleaned)
    
    # Strip common banking acronyms
    cleaned = re.sub(r'\b(UPI|DR|CR|IMPS|NEFT|RTGS|TRANSFER|DEBIT|CREDIT|TFR|REF|TXN)\b', '', cleaned, flags=re.IGNORECASE)
    
    # Clean whitespace and non-alpha-numeric chars, preserve spaces
    cleaned = re.sub(r'[^a-zA-Z0-9\s\-&\.]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Attempt known merchant map
    cleaned_lower = cleaned.lower()
    for pattern, display_name in MERCHANT_CLEANING_RULES:
        if re.search(pattern, cleaned_lower):
            return display_name, mode
            
    # If no known merchant, return capitalized cleaned text (limit length to 40 chars)
    if not cleaned:
        cleaned = "Unknown Merchant"
    else:
        # Title case
        words = cleaned.split()
        cleaned = " ".join([w.capitalize() for w in words])
        
    return cleaned[:40], mode

def parse_date(date_str: str) -> str:
    """
    Standardizes dates into ISO format YYYY-MM-DD.
    Handles DD-MM-YYYY, DD/MM/YY, YYYY-MM-DD, etc.
    """
    if not date_str or not isinstance(date_str, str):
        return datetime.utcnow().strftime("%Y-%m-%d")
    
    # Strip whitespace
    date_str = date_str.strip()
    
    formats = [
        "%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y",
        "%Y-%m-%d", "%Y/%m/%d", "%d %b %Y", "%d-%b-%Y",
        "%b %d, %Y", "%d %B %Y"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    # Try using pandas date parsing
    try:
        dt = pd.to_datetime(date_str, dayfirst=True)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        # Fallback
        return datetime.utcnow().strftime("%Y-%m-%d")

def detect_headers(df: pd.DataFrame) -> dict[str, str]:
    """
    Detects which columns map to Date, Description, Amount (or Debit/Credit), and Balance.
    Returns a dict mapping canonical keys -> column name in df.
    """
    cols = [str(c).lower().strip() for c in df.columns]
    mapping = {}
    
    # Search for Date
    for i, c in enumerate(cols):
        if any(kw in c for kw in ["date", "txn.*date", "transaction.*date"]):
            mapping["date"] = df.columns[i]
            break
    if "date" not in mapping:
        for i, c in enumerate(cols):
            if "val" in c or "value" in c:
                mapping["date"] = df.columns[i]
                break
                
    # Search for Description
    for i, c in enumerate(cols):
        if any(kw in c for kw in ["description", "narration", "particulars", "remarks", "detail"]):
            mapping["description"] = df.columns[i]
            break
            
    # Search for separate Debit / Credit
    debit_col = None
    credit_col = None
    for i, c in enumerate(cols):
        if "withdrawal" in c or "debit" in c or "dr" == c or "dr." in c:
            debit_col = df.columns[i]
        elif "deposit" in c or "credit" in c or "cr" == c or "cr." in c:
            credit_col = df.columns[i]
            
    if debit_col and credit_col:
        mapping["debit"] = debit_col
        mapping["credit"] = credit_col
    else:
        # Search for single Amount column
        for i, c in enumerate(cols):
            if "amount" in c or "amt" in c:
                mapping["amount"] = df.columns[i]
                break
                
    # Search for Balance
    for i, c in enumerate(cols):
        if "balance" in c or "bal" in c:
            mapping["balance"] = df.columns[i]
            break
            
    return mapping

def parse_statement_df(df: pd.DataFrame) -> list[dict]:
    """
    Given a pandas DataFrame, find headers and parse into standard transaction structure.
    """
    # Clean rows: find where the table actually starts by checking for headers
    # Sometimes statements have metadata rows at the top
    start_row = 0
    header_mapping = detect_headers(df)
    
    # If standard columns not found, look at subsequent rows to see if they contain column headers
    if "date" not in header_mapping or ("description" not in header_mapping):
        for idx in range(min(15, len(df))):
            row_vals = [str(val).lower() for val in df.iloc[idx].values]
            # Try to see if this row has headers
            temp_df = pd.DataFrame([df.iloc[idx].values], columns=df.iloc[idx].values)
            temp_mapping = detect_headers(temp_df)
            if "date" in temp_mapping and ("description" in temp_mapping):
                # We found the header row! Re-align df
                df.columns = df.iloc[idx].values
                start_row = idx + 1
                header_mapping = detect_headers(df)
                break

    df = df.iloc[start_row:].copy()
    
    # Final validation: we need at least Date and Description columns
    if "date" not in header_mapping or "description" not in header_mapping:
        raise ValueError("Could not find Date or Description columns in the bank statement.")
        
    date_col = header_mapping["date"]
    desc_col = header_mapping["description"]
    
    transactions = []
    
    for idx, row in df.iterrows():
        # Check if date is empty or invalid
        raw_date = row[date_col]
        if pd.isna(raw_date) or str(raw_date).strip() == "":
            continue
            
        parsed_d = parse_date(str(raw_date))
        raw_desc = str(row[desc_col]) if not pd.isna(row[desc_col]) else ""
        if not raw_desc.strip():
            continue
            
        # Clean description
        clean_desc, mode = clean_description(raw_desc)
        
        # Calculate amount
        amount = 0.0
        txn_type = "debit"
        
        if "debit" in header_mapping and "credit" in header_mapping:
            deb_val = row[header_mapping["debit"]]
            cred_val = row[header_mapping["credit"]]
            
            # Clean values
            def parse_val(v):
                if pd.isna(v): return 0.0
                v_str = str(v).replace(",", "").replace(" ", "").strip()
                if not v_str or v_str == "-" or v_str == ".":
                    return 0.0
                try:
                    return float(v_str)
                except ValueError:
                    return 0.0
            
            debit_amt = parse_val(deb_val)
            credit_amt = parse_val(cred_val)
            
            if credit_amt > 0:
                amount = credit_amt
                txn_type = "credit"
            else:
                amount = -debit_amt
                txn_type = "debit"
        elif "amount" in header_mapping:
            amt_val = str(row[header_mapping["amount"]]).replace(",", "").replace(" ", "").strip()
            try:
                amount = float(amt_val)
            except ValueError:
                amount = 0.0
            
            # Check for Cr/Dr indicator column
            indicator = "debit"
            for c in df.columns:
                if str(c).lower().strip() in ["type", "cr/dr", "transaction type"]:
                    ind_val = str(row[c]).lower().strip()
                    if "cr" in ind_val or "credit" in ind_val or "+" in ind_val:
                        indicator = "credit"
                    break
            
            # If signed directly, infer type
            if amount < 0:
                txn_type = "debit"
            elif amount > 0:
                # If there's an indicator saying debit but amount is positive, make it negative
                if indicator == "debit":
                    amount = -amount
                    txn_type = "debit"
                else:
                    txn_type = "credit"
            else:
                # amount is 0
                txn_type = "debit"
        else:
            # Fallback if no amount column found
            continue
            
        # Extract balance
        balance = None
        if "balance" in header_mapping:
            bal_val = row[header_mapping["balance"]]
            if not pd.isna(bal_val):
                bal_str = str(bal_val).replace(",", "").replace(" ", "").strip()
                try:
                    balance = float(bal_str)
                except ValueError:
                    pass
                    
        # Put under standard structure
        transactions.append({
            "date": parsed_d,
            "description_raw": raw_desc.strip(),
            "description_clean": clean_desc,
            "amount": amount,
            "type": txn_type,
            "balance": balance,
            "metadata": {
                "mode": mode
            }
        })
        
    return transactions
