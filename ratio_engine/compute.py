"""Financial ratio computation — B2.

Pure Python/pandas math. AI never touches this step; keeping it deterministic
is what lets the report claim controllable, auditable accuracy.
"""

from dataclasses import dataclass


@dataclass
class StatementInput:
    revenue: float
    net_profit: float
    total_assets: float
    total_liabilities: float
    total_equity: float
    current_assets: float
    current_liabilities: float
    cash_from_operations: float


def current_ratio(s: StatementInput) -> float:
    return s.current_assets / s.current_liabilities


def quick_ratio(s: StatementInput, inventory: float = 0.0) -> float:
    return (s.current_assets - inventory) / s.current_liabilities


def debt_to_equity(s: StatementInput) -> float:
    return s.total_liabilities / s.total_equity


def debt_to_asset(s: StatementInput) -> float:
    return s.total_liabilities / s.total_assets


def roe(s: StatementInput) -> float:
    return s.net_profit / s.total_equity


def roa(s: StatementInput) -> float:
    return s.net_profit / s.total_assets


def net_profit_margin(s: StatementInput) -> float:
    return s.net_profit / s.revenue


def asset_turnover(s: StatementInput) -> float:
    return s.revenue / s.total_assets


def cfo_to_net_income(s: StatementInput) -> float:
    return s.cash_from_operations / s.net_profit


def compute_all_ratios(s: StatementInput) -> dict:
    """Returns every ratio as a flat dict, ready to insert into the `ratios` table
    or to pass straight into ai_analysis as structured input."""
    return {
        "current_ratio": current_ratio(s),
        "quick_ratio": quick_ratio(s),
        "debt_to_equity": debt_to_equity(s),
        "debt_to_asset": debt_to_asset(s),
        "roe": roe(s),
        "roa": roa(s),
        "net_profit_margin": net_profit_margin(s),
        "asset_turnover": asset_turnover(s),
        "cfo_to_net_income": cfo_to_net_income(s),
    }
