"""PRODUCTION entrypoint (Phase 2).

This is the only module that gets deployed. It only imports the
already-decided pipeline pieces:

    ratio_engine  -> pure math, always safe to run live
    scoring       -> uses the SCORING_VERSION frozen after Phase-1 tuning
    ai_analysis   -> uses the PROMPT_VERSION frozen after Phase-1 tuning

Run locally:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ratio_engine.compute import StatementInput, compute_all_ratios
from scoring.score import compute_financial_health_score, SCORING_VERSION
from ai_analysis.analyze import analyze, PROMPT_VERSION

app = FastAPI(
    title="VN30 Financial Health Scoring API",
    description="Production API — serves ratios, score and AI explanation "
                 "for a given company/year using the versions frozen in Phase 1.",
    version="1.0.0",
)

class StatementRequest(BaseModel):
    ticker: str
    year: int
    revenue: float
    net_profit: float
    total_assets: float
    total_liabilities: float
    total_equity: float
    current_assets: float
    current_liabilities: float
    cash_from_operations: float


class HealthReportResponse(BaseModel):
    ticker: str
    year: int
    ratios: dict
    score: dict
    ai_explanation: dict | None
    versions: dict


@app.get("/health")
def health_check():
    """Basic liveness check for Render/Railway."""
    return {"status": "ok"}


@app.post("/analyze", response_model=HealthReportResponse)
def analyze_company(payload: StatementRequest, include_ai: bool = True):
    """Main production endpoint — B2 + Scoring (+ optional B3 AI explanation).
    include_ai=False lets the frontend fetch the deterministic score instantly
    and fill in the AI explanation asynchronously, since the Gemini call is
    the slowest and least reliable step.
    """
    statement = StatementInput(
        revenue=payload.revenue,
        net_profit=payload.net_profit,
        total_assets=payload.total_assets,
        total_liabilities=payload.total_liabilities,
        total_equity=payload.total_equity,
        current_assets=payload.current_assets,
        current_liabilities=payload.current_liabilities,
        cash_from_operations=payload.cash_from_operations,
    )

    try:
        ratios = compute_all_ratios(statement)
    except ZeroDivisionError:
        raise HTTPException(status_code=422, detail="Invalid input: a denominator is zero.")

    score = compute_financial_health_score(ratios)

    ai_explanation = None
    if include_ai:
        try:
            ai_explanation = analyze({str(payload.year): ratios})
        except ValueError:
            # AI call failed or returned malformed JSON — degrade gracefully,
            # the deterministic score/ratios are still fully valid.
            ai_explanation = {"error": "AI explanation unavailable, showing score only."}

    return HealthReportResponse(
        ticker=payload.ticker,
        year=payload.year,
        ratios=ratios,
        score=score,
        ai_explanation=ai_explanation,
        versions={"scoring_version": SCORING_VERSION, "prompt_version": PROMPT_VERSION},
    )
