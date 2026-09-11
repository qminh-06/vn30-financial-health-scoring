"""SQLAlchemy models for the VN30 Financial Health Scoring system.

Tables map directly to the pipeline stages:
    companies              -> B1 (master list of VN30 tickers)
    financial_statements   -> B1 (raw/cleaned BCTC per company/year)
    ratios                 -> B2 (computed by ratio_engine, not by AI)
    scores                 -> Scoring Algorithm output (Financial Health Score)
    ai_predictions          -> B3 (AI's structured analysis/prediction)
    ground_truth            -> B4 (actual outcome of the following year)
    evaluation_results      -> B4 (accuracy/precision/recall/f1/mae per run)
"""

from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, ForeignKey, DateTime, JSON, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(10), unique=True, nullable=False)  # e.g. "VCB"
    name = Column(String(255), nullable=False)
    sector = Column(String(100))

    statements = relationship("FinancialStatement", back_populates="company")


class FinancialStatement(Base):
    __tablename__ = "financial_statements"
    __table_args__ = (UniqueConstraint("company_id", "year", name="uq_company_year"),)

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    year = Column(Integer, nullable=False)

    # Raw line items pulled from BCTC (extend as needed)
    revenue = Column(Float)
    net_profit = Column(Float)
    total_assets = Column(Float)
    total_liabilities = Column(Float)
    total_equity = Column(Float)
    current_assets = Column(Float)
    current_liabilities = Column(Float)
    cash_from_operations = Column(Float)

    raw_payload = Column(JSON)  # full raw record for traceability

    company = relationship("Company", back_populates="statements")


class Ratios(Base):
    """Output of ratio_engine (B2) — always computed in code, never by the AI."""
    __tablename__ = "ratios"
    __table_args__ = (UniqueConstraint("company_id", "year", name="uq_ratios_company_year"),)

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    year = Column(Integer, nullable=False)

    # Liquidity
    current_ratio = Column(Float)
    quick_ratio = Column(Float)
    # Leverage
    debt_to_equity = Column(Float)
    debt_to_asset = Column(Float)
    # Profitability
    roe = Column(Float)
    roa = Column(Float)
    net_profit_margin = Column(Float)
    # Efficiency
    asset_turnover = Column(Float)
    # Cash flow
    cfo_to_net_income = Column(Float)


class Score(Base):
    """Output of the Scoring Algorithm — NOT produced by AI."""
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    year = Column(Integer, nullable=False)

    liquidity_score = Column(Float)
    profitability_score = Column(Float)
    leverage_score = Column(Float)
    efficiency_score = Column(Float)
    cashflow_score = Column(Float)
    financial_health_score = Column(Float)  # weighted total, 0-100

    scoring_version = Column(String(50))  # for tracking weight/threshold changes


class AIPrediction(Base):
    """Structured output of ai_analysis (B3) — analysis + forward-looking prediction."""
    __tablename__ = "ai_predictions"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    year = Column(Integer, nullable=False)  # year the prediction is made FOR (i.e. predicts year+1)

    trend_prediction = Column(String(20))    # e.g. "improve" / "stable" / "decline"
    risk_prediction = Column(String(20))     # e.g. "low" / "moderate" / "high"
    profitability_prediction = Column(String(20))
    explanation_text = Column(String)
    raw_response = Column(JSON)

    prompt_version = Column(String(50))      # for tracking prompt iterations
    model_name = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class GroundTruth(Base):
    """Actual outcome for year+1, derived automatically from Ratios/Score — B4."""
    __tablename__ = "ground_truth"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    year = Column(Integer, nullable=False)  # the year being evaluated (year+1 vs base year)

    trend_actual = Column(String(20))
    risk_actual = Column(String(20))
    profitability_actual = Column(String(20))


class EvaluationResult(Base):
    """One row per benchmark run (Model 1/2/3) — B4 metrics + model_improvement history."""
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True)
    run_label = Column(String(100))   # e.g. "model1_ratios_only", "model3_ratios_scoring_ai"
    run_at = Column(DateTime, default=datetime.utcnow)

    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1 = Column(Float)
    mae = Column(Float)

    n_samples = Column(Integer)
    notes = Column(String)
