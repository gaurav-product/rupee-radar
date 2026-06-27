import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, parsing, processing, ready, failed
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    error_message = Column(String, nullable=True)

    transactions = relationship("Transaction", back_populates="session", cascade="all, delete-orphan")
    recurring_groups = relationship("RecurringGroup", back_populates="session", cascade="all, delete-orphan")
    analysis_result = relationship("AnalysisResult", back_populates="session", uselist=False, cascade="all, delete-orphan")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    date = Column(String, nullable=False)  # YYYY-MM-DD
    description_raw = Column(String, nullable=False)
    description_clean = Column(String, nullable=False)
    amount = Column(Float, nullable=False)  # signed: negative for debit, positive for credit
    type = Column(String, nullable=False)   # credit, debit
    balance = Column(Float, nullable=True)
    category = Column(String, nullable=False, default="Other")
    category_confidence = Column(Float, default=1.0)
    is_recurring = Column(Boolean, default=False)
    recurring_group_id = Column(String, ForeignKey("recurring_groups.id", ondelete="SET NULL"), nullable=True)
    metadata_json = Column(Text, nullable=True)  # Store custom fields

    session = relationship("UploadSession", back_populates="transactions")
    recurring_group = relationship("RecurringGroup", back_populates="transactions")


class RecurringGroup(Base):
    __tablename__ = "recurring_groups"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("upload_sessions.id", ondelete="CASCADE"), nullable=False)
    label = Column(String, nullable=False)
    category = Column(String, nullable=False)
    frequency = Column(String, default="monthly")  # weekly, monthly, quarterly, yearly, unknown
    typical_amount = Column(Float, nullable=False)
    last_seen_date = Column(String, nullable=False)
    transaction_ids = Column(Text, nullable=False)  # JSON-encoded array of IDs
    confidence = Column(Float, default=1.0)

    session = relationship("UploadSession", back_populates="recurring_groups")
    transactions = relationship("Transaction", back_populates="recurring_group")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    session_id = Column(String, ForeignKey("upload_sessions.id", ondelete="CASCADE"), primary_key=True)
    metrics_json = Column(Text, nullable=False)  # JSON summary metrics (total income, spent, savings, savings rate)
    top_categories_json = Column(Text, nullable=False)  # JSON array of category aggregates
    biggest_transactions_json = Column(Text, nullable=False)  # JSON array of biggest transactions
    insights_json = Column(Text, nullable=False)  # JSON array of string insights
    generated_at = Column(DateTime, default=datetime.datetime.utcnow)

    session = relationship("UploadSession", back_populates="analysis_result")
