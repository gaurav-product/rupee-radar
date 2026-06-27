import pytest
from app.pipeline.cleaner import clean_description, parse_date
from app.pipeline.categorizer import categorize_by_rules
from app.pipeline.recurring import detect_recurring_payments

def test_clean_description():
    desc1, mode1 = clean_description("UPI/DR/321456987126/NETFLIX-SUBS/ref/4")
    assert desc1 == "Netflix"
    assert mode1 == "UPI"

    desc2, mode2 = clean_description("UPI/DR/321456987123/SWIGGY-BANGALORE-12345/ref/1")
    assert desc2 == "Swiggy"
    assert mode2 == "UPI"

def test_parse_date():
    assert parse_date("27-06-2026") == "2026-06-27"
    assert parse_date("28/06/2026") == "2026-06-28"
    assert parse_date("2026-06-29") == "2026-06-29"

def test_categorize_by_rules():
    cat1 = categorize_by_rules("Swiggy", "UPI/DR/321456987123/SWIGGY-BANGALORE-12345/ref/1", -450.00, "debit")
    assert cat1 == "Food"

    cat2 = categorize_by_rules("Netflix", "UPI/DR/321456987126/NETFLIX-SUBS/ref/4", -199.00, "debit")
    assert cat2 == "Subscriptions"

def test_detect_recurring_payments():
    # Construct a repeating sequence of payments
    txns = [
        {"id": "1", "date": "2026-04-01", "description_clean": "Netflix", "amount": -199.00, "type": "debit"},
        {"id": "2", "date": "2026-05-01", "description_clean": "Netflix", "amount": -199.00, "type": "debit"},
        {"id": "3", "date": "2026-06-01", "description_clean": "Netflix", "amount": -199.00, "type": "debit"},
    ]
    
    updated_txns, groups = detect_recurring_payments(txns)
    assert len(groups) == 1
    assert groups[0]["label"] == "Netflix"
    assert groups[0]["frequency"] == "monthly"
    assert updated_txns[0]["is_recurring"] is True
    assert updated_txns[0]["recurring_group_id"] == groups[0]["id"]
