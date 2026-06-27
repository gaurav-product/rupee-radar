import logging
from typing import List, Dict, Optional
from groq import Groq

logger = logging.getLogger(__name__)

def generate_template_insights(analysis_data: Dict) -> List[str]:
    """
    Generates deterministic, template-based insights using computed metrics.
    """
    insights = []
    metrics = analysis_data["metrics"]
    top_categories = analysis_data["top_categories"]
    biggest_txns = analysis_data["biggest_transactions"]
    
    # 1. Largest spending category insight
    if top_categories:
        top_cat = top_categories[0]
        insights.append(
            f"You spent ₹{top_cat['amount']:,} on {top_cat['category']} — "
            f"this is your largest category, representing {top_cat['percentage']}% of your total spending."
        )
        
    # 2. Biggest debit transaction insight
    biggest_debit = next((t for t in biggest_txns if t["type"] == "debit"), None)
    if biggest_debit:
        insights.append(
            f"Your single largest debit was ₹{biggest_debit['amount']:,} "
            f"to {biggest_debit['description']} on {biggest_debit['date']}."
        )
        
    # 3. Recurring transactions total insight
    recurring_total = metrics.get("recurring_total", 0.0)
    if recurring_total > 0:
        insights.append(
            f"We detected recurring subscriptions and EMIs totalling ₹{recurring_total:,} per month."
        )
    else:
        insights.append(
            "We did not detect any recurring subscriptions or EMIs in your transaction patterns."
        )
        
    # 4. Savings rate insight
    savings_rate = metrics.get("savings_rate", 0.0)
    total_income = metrics.get("total_income", 0.0)
    if total_income > 0:
        if savings_rate > 20:
            insights.append(
                f"Great job! Your savings rate is healthy at {savings_rate:.1f}%. "
                f"You saved ₹{metrics['savings']:,} out of ₹{total_income:,} this period."
            )
        elif savings_rate > 0:
            insights.append(
                f"Your savings rate is {savings_rate:.1f}%. You saved ₹{metrics['savings']:,} "
                f"from your total income of ₹{total_income:,}. Consider cutting back on discretionary categories like Food/Shopping."
            )
        else:
            insights.append(
                f"Warning: Your monthly spending exceeded your income. You spent ₹{metrics['total_spend']:,} "
                f"against an income of ₹{total_income:,}, resulting in negative savings of ₹{metrics['savings']:,}."
            )
            
    return insights

def generate_llm_insights(analysis_data: Dict, api_key: Optional[str] = None) -> List[str]:
    """
    Feeds aggregated metrics and top categories (no PII/raw details) to Groq 
    to generate narrative observations.
    """
    if not api_key:
        logger.warning("Groq API key not provided. Skipping LLM insights.")
        return []
        
    client = Groq(api_key=api_key)
    
    metrics = analysis_data["metrics"]
    top_categories = analysis_data["top_categories"]
    biggest_txns = analysis_data["biggest_transactions"]
    
    summary = {
        "income": metrics["total_income"],
        "spend": metrics["total_spend"],
        "savings": metrics["savings"],
        "savings_rate": metrics["savings_rate"],
        "recurring_spend": metrics["recurring_total"],
        "top_categories": top_categories,
        "biggest_transactions": biggest_txns
    }
    
    system_prompt = (
        "You are an elite, professional financial advisor. You analyze high-level spend summaries and provide "
        "personalized, actionable financial insights. Ensure you:\n"
        "1. Focus on specific numeric details from the summary.\n"
        "2. Do NOT mention hypothetical figures; cite actual category percentages and values.\n"
        "3. Provide exactly 2 bullet points of concise, narrative analysis (spending habits, potential leaks, or structural shifts).\n"
        "4. Output a JSON object containing a list 'narrative_insights', which are plain text sentences."
    )
    
    user_prompt = f"Analyze this financial summary:\n{summary}"
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        response_content = completion.choices[0].message.content
        result = json.loads(response_content)
        return result.get("narrative_insights", [])
        
    except Exception as e:
        logger.error(f"Error in LLM insights generation: {e}")
        return []
        
import json  # Added import for json
