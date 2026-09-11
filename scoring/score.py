"""Financial Health Score — deterministic scoring algorithm, no AI involved.

Weights and thresholds are named constants (not magic numbers) so the
"model_improvement" loop can log exactly which version produced which
accuracy in evaluation_results.scoring_version.
"""

SCORING_VERSION = "v1"

GROUP_WEIGHTS = {
    "liquidity": 0.20,
    "profitability": 0.30,
    "leverage": 0.20,
    "efficiency": 0.15,
    "cashflow": 0.15,
}


def _clamp(value: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, value))


def score_roe(roe: float) -> float:
    """Example threshold mapping — tune against real VN30 data before final report."""
    if roe > 0.15:
        return 100
    if roe > 0.10:
        return 75
    if roe > 0.05:
        return 50
    return 25


def score_current_ratio(cr: float) -> float:
    if cr > 2.0:
        return 100
    if cr > 1.5:
        return 75
    if cr > 1.0:
        return 50
    return 25


def score_debt_to_equity(de: float) -> float:
    # Lower is better for leverage risk
    if de < 0.5:
        return 100
    if de < 1.0:
        return 75
    if de < 1.5:
        return 50
    return 25


def compute_financial_health_score(ratios: dict) -> dict:
    """ratios: output dict from ratio_engine.compute_all_ratios.

    Returns per-group scores plus the final weighted Financial Health Score (0-100).
    Extend score_* functions per ratio group as the thresholds get calibrated.
    """
    liquidity_score = score_current_ratio(ratios["current_ratio"])
    profitability_score = score_roe(ratios["roe"])
    leverage_score = score_debt_to_equity(ratios["debt_to_equity"])
    # TODO: efficiency_score, cashflow_score — add threshold functions once
    # calibrated against the VN30 sample.
    efficiency_score = 50.0
    cashflow_score = 50.0

    total = (
        liquidity_score * GROUP_WEIGHTS["liquidity"]
        + profitability_score * GROUP_WEIGHTS["profitability"]
        + leverage_score * GROUP_WEIGHTS["leverage"]
        + efficiency_score * GROUP_WEIGHTS["efficiency"]
        + cashflow_score * GROUP_WEIGHTS["cashflow"]
    )

    return {
        "liquidity_score": liquidity_score,
        "profitability_score": profitability_score,
        "leverage_score": leverage_score,
        "efficiency_score": efficiency_score,
        "cashflow_score": cashflow_score,
        "financial_health_score": _clamp(total),
        "scoring_version": SCORING_VERSION,
    }
