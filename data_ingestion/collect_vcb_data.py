
"""VCB 3-Year Data Ingestion (2023 - 2025)

Collect:
1. Quarterly financial statements.
2. Annual financial statements.
3. Daily OHLCV history.
4. Save datasets to CSV for offline analysis.

Compatible with vnstock v6.
"""

import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

# Resolve project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

from vnstock import Fundamental, Market

DATA_DIR = PROJECT_ROOT / "data" / "vcb"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SYMBOL = "VCB"
START_DATE = "2023-01-01"
END_DATE = "2026-01-01"


def save_csv(df, filename):
    """Save DataFrame to CSV."""
    if df is not None and not df.empty:
        path = DATA_DIR / filename
        df.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"     Saved {len(df)} rows -> {path}")
    else:
        print(f"     [Warning] Empty data: {filename}")


def collect_financial_statements():
    """Collect quarterly and annual financial statements."""

    print(f"=== 1. Collecting financial statements for {SYMBOL} ===")

    finance = Fundamental().equity(SYMBOL)

    statements = {
        "balance_sheet": "vcb_bs",
        "income_statement": "vcb_is",
        "cash_flow": "vcb_cf",
    }

    # Quarterly financial statements
    for statement, filename_prefix in statements.items():
        print(f"  -> Downloading {statement} (quarter)...")

        try:
            method = getattr(finance, statement)
            df = method(period="quarter", source="fhsc")
            save_csv(df, f"{filename_prefix}_quarter.csv")

        except Exception as e:
            print(f"     [Error] {statement} quarterly: {e}")

    # Annual financial statements
    for statement, filename_prefix in statements.items():
        print(f"  -> Downloading {statement} (year)...")

        try:
            method = getattr(finance, statement)
            df = method(period="year", source="fhsc")
            save_csv(df, f"{filename_prefix}_year.csv")

        except Exception as e:
            print(f"     [Error] {statement} yearly: {e}")

    print(f"  Financial statements saved in {DATA_DIR}")


def collect_historical_price():
    """Collect daily OHLCV history from 2023 to 2026."""

    print(
        f"\n=== 2. Collecting OHLCV for {SYMBOL} "
        f"({START_DATE} -> {END_DATE}) ==="
    )

    try:
        market = Market("tcbs")
        df_price = market.equity(SYMBOL).ohlcv(
            start=START_DATE,
            end=END_DATE,
            interval="1D",
        )

        save_csv(df_price, "vcb_price_daily.csv")

        if df_price is not None and not df_price.empty:
            return df_price

    except Exception as e:
        print(f"  [Error] Historical price: {e}")

    return None


if __name__ == "__main__":
    collect_financial_statements()
    collect_historical_price()

    print("\nCompleted VCB data ingestion!")
