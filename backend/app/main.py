import os
import uuid
import datetime
import json
import logging
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

# Database modules
from app.models.database import engine, Base, get_db
from app.models.models import UploadSession, Transaction, RecurringGroup, AnalysisResult

# Pipeline modules
from app.pipeline.cleaner import parse_statement_df, pd
from app.pipeline.categorizer import categorize_transactions_hybrid
from app.pipeline.recurring import detect_recurring_payments
from app.pipeline.metrics import calculate_financial_metrics
from app.pipeline.insights import generate_template_insights, generate_llm_insights

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="RupeeRadar API", version="1.0.0")

# CORS middleware config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request schema for category override
class CategoryOverride(BaseModel):
    category: str

# Healthcheck endpoint
@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat()}

# Helper to run pipeline and save to DB
def run_pipeline(session_id: str, df: pd.DataFrame, db: Session):
    try:
        # 1. Parse and standardise transactions
        txns_raw = parse_statement_df(df)
        if not txns_raw:
            raise ValueError("No transactions found in statement.")
            
        # 2. Categorize transactions (Rule Engine + LLM fallback)
        api_key = os.getenv("GROQ_API_KEY")
        txns_categorized = categorize_transactions_hybrid(txns_raw, api_key)
        
        # Add generated UUIDs
        for t in txns_categorized:
            t["id"] = str(uuid.uuid4())
            t["session_id"] = session_id
            
        # 3. Detect recurring patterns
        txns_final, recurring_groups_data = detect_recurring_payments(txns_categorized)
        
        # 4. Calculate metrics & insights
        analysis_data = calculate_financial_metrics(txns_final, recurring_groups_data)
        
        # Generate Insights
        template_insights = generate_template_insights(analysis_data)
        llm_insights = generate_llm_insights(analysis_data, api_key)
        all_insights = template_insights + llm_insights
        
        # Save to Database
        # Transactions
        db_transactions = []
        for t in txns_final:
            db_txn = Transaction(
                id=t["id"],
                session_id=t["session_id"],
                date=t["date"],
                description_raw=t["description_raw"],
                description_clean=t["description_clean"],
                amount=t["amount"],
                type=t["type"],
                balance=t.get("balance"),
                category=t.get("category", "Other"),
                category_confidence=t.get("category_confidence", 1.0),
                is_recurring=t.get("is_recurring", False),
                recurring_group_id=t.get("recurring_group_id"),
                metadata_json=json.dumps(t.get("metadata", {}))
            )
            db_transactions.append(db_txn)
        db.add_all(db_transactions)
        
        # Recurring Groups
        db_groups = []
        for rg in recurring_groups_data:
            db_rg = RecurringGroup(
                id=rg["id"],
                session_id=session_id,
                label=rg["label"],
                category=rg["category"],
                frequency=rg["frequency"],
                typical_amount=rg["typical_amount"],
                last_seen_date=rg["last_seen_date"],
                transaction_ids=json.dumps(rg["transaction_ids"]),
                confidence=rg["confidence"]
            )
            db_groups.append(db_rg)
        db.add_all(db_groups)
        
        # Analysis Result
        db_analysis = AnalysisResult(
            session_id=session_id,
            metrics_json=json.dumps(analysis_data["metrics"]),
            top_categories_json=json.dumps(analysis_data["top_categories"]),
            biggest_transactions_json=json.dumps(analysis_data["biggest_transactions"]),
            insights_json=json.dumps(all_insights)
        )
        db.add(db_analysis)
        
        # Update Session status
        session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
        if session:
            session.status = "ready"
            
        db.commit()
        
    except Exception as e:
        logger.error(f"Pipeline processing failed for session {session_id}: {e}")
        db.rollback()
        session = db.query(UploadSession).filter(UploadSession.id == session_id).first()
        if session:
            session.status = "failed"
            session.error_message = str(e)
            db.commit()
        raise e

@app.post("/api/v1/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_statement(file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Validate file type
    filename = file.filename
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Unsupported format. Try CSV or Excel export from your bank."
        )
        
    # Read file contents into pandas
    try:
        contents = await file.read()
        import io
        if filename.endswith(".csv"):
            # Try sniffing delimiter
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Failed to read file: {str(e)}"
        )
        
    # Create session record
    session_id = str(uuid.uuid4())
    uploaded_at = datetime.datetime.utcnow()
    expires_at = uploaded_at + datetime.timedelta(hours=24)  # TTL of 24 hours
    
    session = UploadSession(
        id=session_id,
        filename=filename,
        file_type="csv" if filename.endswith(".csv") else "excel",
        status="processing",
        uploaded_at=uploaded_at,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    
    # Process synchronously for small files
    try:
        run_pipeline(session_id, df, db)
    except Exception as e:
        # Even if pipeline fails, we return the session so client can inspect error_message
        logger.error(f"Synchronous processing failed: {e}")
        
    db.refresh(session)
    return {
        "session_id": session_id,
        "status": session.status,
        "error_message": session.error_message
    }

@app.get("/api/v1/sessions/{id}")
def get_session_status(id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter(UploadSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
    return {
        "id": session.id,
        "filename": session.filename,
        "status": session.status,
        "uploaded_at": session.uploaded_at,
        "expires_at": session.expires_at,
        "error_message": session.error_message
    }

@app.get("/api/v1/sessions/{id}/transactions")
def get_transactions(id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter(UploadSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
        
    transactions = db.query(Transaction).filter(Transaction.session_id == id).all()
    
    return [
        {
            "id": t.id,
            "date": t.date,
            "description_raw": t.description_raw,
            "description_clean": t.description_clean,
            "amount": t.amount,
            "type": t.type,
            "balance": t.balance,
            "category": t.category,
            "category_confidence": t.category_confidence,
            "is_recurring": t.is_recurring,
            "recurring_group_id": t.recurring_group_id,
            "metadata": json.loads(t.metadata_json or "{}")
        }
        for t in transactions
    ]

@app.patch("/api/v1/sessions/{id}/transactions/{txn_id}")
def override_category(id: str, txn_id: str, override: CategoryOverride, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter(UploadSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
        
    txn = db.query(Transaction).filter(Transaction.session_id == id, Transaction.id == txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    # Update category
    txn.category = override.category
    txn.category_confidence = 1.0  # User override is 100% confident
    db.commit()
    
    # Recalculate everything!
    all_txns = db.query(Transaction).filter(Transaction.session_id == id).all()
    
    # Convert database models back to list of dicts for calculation pipelines
    txns_list = []
    for t in all_txns:
        txns_list.append({
            "id": t.id,
            "date": t.date,
            "description_raw": t.description_raw,
            "description_clean": t.description_clean,
            "amount": t.amount,
            "type": t.type,
            "balance": t.balance,
            "category": t.category,
            "category_confidence": t.category_confidence,
            "is_recurring": False,
            "recurring_group_id": None
        })
        
    # Redetect recurring patterns (since changing category can affect group categorization)
    txns_final, recurring_groups_data = detect_recurring_payments(txns_list)
    
    # Update transaction is_recurring fields in database
    for t_data in txns_final:
        db_txn = db.query(Transaction).filter(Transaction.id == t_data["id"]).first()
        if db_txn:
            db_txn.is_recurring = t_data["is_recurring"]
            db_txn.recurring_group_id = t_data["recurring_group_id"]
            
    # Clear previous recurring groups
    db.query(RecurringGroup).filter(RecurringGroup.session_id == id).delete()
    
    # Save new recurring groups
    db_groups = []
    for rg in recurring_groups_data:
        db_rg = RecurringGroup(
            id=rg["id"],
            session_id=id,
            label=rg["label"],
            category=rg["category"],
            frequency=rg["frequency"],
            typical_amount=rg["typical_amount"],
            last_seen_date=rg["last_seen_date"],
            transaction_ids=json.dumps(rg["transaction_ids"]),
            confidence=rg["confidence"]
        )
        db_groups.append(db_rg)
    db.add_all(db_groups)
    
    # Recalculate metrics
    analysis_data = calculate_financial_metrics(txns_final, recurring_groups_data)
    
    # Generate insights
    template_insights = generate_template_insights(analysis_data)
    api_key = os.getenv("GROQ_API_KEY")
    llm_insights = generate_llm_insights(analysis_data, api_key)
    all_insights = template_insights + llm_insights
    
    # Update AnalysisResult
    analysis_result = db.query(AnalysisResult).filter(AnalysisResult.session_id == id).first()
    if analysis_result:
        analysis_result.metrics_json = json.dumps(analysis_data["metrics"])
        analysis_result.top_categories_json = json.dumps(analysis_data["top_categories"])
        analysis_result.biggest_transactions_json = json.dumps(analysis_data["biggest_transactions"])
        analysis_result.insights_json = json.dumps(all_insights)
    else:
        db_analysis = AnalysisResult(
            session_id=id,
            metrics_json=json.dumps(analysis_data["metrics"]),
            top_categories_json=json.dumps(analysis_data["top_categories"]),
            biggest_transactions_json=json.dumps(analysis_data["biggest_transactions"]),
            insights_json=json.dumps(all_insights)
        )
        db.add(db_analysis)
        
    db.commit()
    
    return {"message": "Category updated and metrics recalculated successfully"}

@app.get("/api/v1/sessions/{id}/recurring")
def get_recurring_groups(id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter(UploadSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
        
    groups = db.query(RecurringGroup).filter(RecurringGroup.session_id == id).all()
    
    return [
        {
            "id": g.id,
            "label": g.label,
            "category": g.category,
            "frequency": g.frequency,
            "typical_amount": g.typical_amount,
            "last_seen_date": g.last_seen_date,
            "transaction_ids": json.loads(g.transaction_ids),
            "confidence": g.confidence
        }
        for g in groups
    ]

@app.get("/api/v1/sessions/{id}/analytics")
def get_analytics(id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter(UploadSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
        
    analysis = db.query(AnalysisResult).filter(AnalysisResult.session_id == id).first()
    if not analysis:
        # Fallback recalculate metrics manually if missing
        raise HTTPException(status_code=404, detail="Analytics data not generated yet")
        
    transactions = db.query(Transaction).filter(Transaction.session_id == id).all()
    txns_list = [{"date": t.date, "amount": t.amount, "type": t.type, "category": t.category, "description_clean": t.description_clean} for t in transactions]
    
    groups = db.query(RecurringGroup).filter(RecurringGroup.session_id == id).all()
    groups_list = [{"typical_amount": g.typical_amount} for g in groups]
    
    # Rerun metrics to compute the full response payload (including trends)
    analysis_data = calculate_financial_metrics(txns_list, groups_list)
    
    return {
        "metrics": json.loads(analysis.metrics_json),
        "top_categories": json.loads(analysis.top_categories_json),
        "monthly_trend": analysis_data["monthly_trend"],
        "biggest_transactions": json.loads(analysis.biggest_transactions_json)
    }

@app.get("/api/v1/sessions/{id}/insights")
def get_insights(id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter(UploadSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
        
    analysis = db.query(AnalysisResult).filter(AnalysisResult.session_id == id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Insights data not generated yet")
        
    return json.loads(analysis.insights_json)

@app.delete("/api/v1/sessions/{id}")
def delete_session(id: str, db: Session = Depends(get_db)):
    session = db.query(UploadSession).filter(UploadSession.id == id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
        
    db.delete(session)
    db.commit()
    return {"message": f"Session {id} and all associated data successfully deleted"}
