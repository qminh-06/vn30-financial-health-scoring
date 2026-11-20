import sys
from pathlib import Path
# Đảm bảo luôn tìm thấy các package nội bộ (như db) dù chạy từ bất cứ đâu
sys.path.append(str(Path(__file__).resolve().parent.parent))

from vnstock import Finance
from vnstock import register_user
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

from db.supabase_loader import (
    seed_all,
    seed_line_items_from_statements,
    insert_ratios,
    insert_all_statement_lines,
)

register_user()

BANK_SYMBOLS = ["ACB", "BID", "CTG", "HDB", "LPB", "MBB", "SHB", "SSB", "STB", "TCB", "VCB", "VIB", "VPB"]

bank_name = {
    "ACB": "Ngân hàng TMCP Á Châu",
    "BID": "Ngân hàng TMCP Đầu tư và Phát triển Việt Nam",
    "CTG": "Ngân hàng TMCP Công Thương Việt Nam",
    "HDB": "Ngân hàng TMCP Phát triển TP.HCM",
    "LPB": "Ngân hàng TMCP Bưu điện Liên Việt",
    "MBB": "Ngân hàng TMCP Quân đội",
    "SHB": "Ngân hàng TMCP Sài Gòn - Hà Nội",
    "SSB": "Ngân hàng TMCP Đông Nam Á",
    "STB": "Ngân hàng TMCP Sài Gòn Thương Tín",
    "TCB": "Ngân hàng TMCP Technique Commercial Joint Stock",
    "VCB": "Ngân hàng TMCP Ngoại thương Việt Nam",
    "VIB": "Ngân hàng TMCP Quốc tế Việt Nam",
    "VPB": "Ngân hàng TMCP Việt Nam Thịnh Vượng",
}
PERIODS = ["2026-Q2", "2026-Q1", "2025-Q4", "2025-Q3", "2025-Q2", "2025-Q1", "2024-Q4", "2024-Q3"]

def get_value(df, item_id, period, default=0.0):
    if period not in df.columns:
        return default
    row = df.loc[df.item_id == item_id, period]
    if row.empty or pd.isna(row.values[0]):
        return default
    return float(row.values[0])

ASSET_ITEMS = [
    "cash_and_precious_metals",
    "balances_with_the_sbv",
    "placements_with_and_loans_to_other_credit_institutions",
    "trading_securities",
    "derivatives_and_other_financial_assets",
    "loans_and_advances_to_customers",
    "investment_securities",
    "fixed_assets",
    "investment_properties",
    "other_assets",
]

EARNING_ASSET_ITEMS = [
    "placements_with_and_loans_to_other_credit_institutions",
    "trading_securities",
    "loans_and_advances_to_customers",
    "investment_securities",
]

NIM_ASSET_ITEMS = [
    "balances_with_the_sbv",
    "placements_with_and_loans_to_other_credit_institutions",
    "loans_and_advances_to_customers",
    "trading_securities",
    "investment_securities",
]

def compute_asset_structure(balance_sheet, period):
    total_assets = get_value(balance_sheet, "total_assets", period)

    structure = {}
    for item_id in ASSET_ITEMS:
        if item_id not in balance_sheet.item_id.values:
            continue
        value = get_value(balance_sheet, item_id, period)
        structure[item_id] = round(value / total_assets * 100, 2)

    earning_assets = sum(
        get_value(balance_sheet, item_id, period)
        for item_id in EARNING_ASSET_ITEMS
        if item_id in balance_sheet.item_id.values
    )
    structure["earning_assets_ratio_%"] = round(earning_assets / total_assets * 100, 2)
    return structure


def _funded_liabilities(balance_sheet, period):
    """Tổng nguồn vốn trả lãi tại một kỳ — dùng cho tính COF."""
    return (
        get_value(balance_sheet, "due_to_gov_and_loans_from_sbv", period)
        + get_value(balance_sheet, "deposits_and_loans_from_other_credit_institutions", period)
        + get_value(balance_sheet, "deposits_from_customers", period)
        + get_value(balance_sheet, "convertible_bonds_cds_and_other_valuable_papers_issued", period)
    )

seed_all(bank_name, PERIODS)
all_rows = []

for symbol in BANK_SYMBOLS:
    print(f"\n=== {symbol} ===")
    try:
        finance = Finance(symbol=symbol, source="VCI")
        balance_sheet = finance.balance_sheet(period="quarter")
        income_statement = finance.income_statement(period="quarter")
        cash_flow = finance.cash_flow(period="quarter")
    except Exception as e:
        print(f"[LOI] {symbol}: {type(e).__name__}: {e}")
        print(f"  → Bo qua {symbol}, kiem tra lai source VCI hoac thu voi source TCBS.")
        continue

    statements = {
        "balance_sheet": balance_sheet,
        "income_statement": income_statement,
        "cash_flow": cash_flow,
    }
    seed_line_items_from_statements(statements)
    insert_all_statement_lines(symbol, statements, PERIODS)

    # Chi tinh voi cac ky thuc su ton tai trong ca balance_sheet va income_statement cua ngan hang
    valid_periods = [p for p in PERIODS if p in balance_sheet.columns and p in income_statement.columns]
    print(f"  Cac ky hop le cho {symbol}: {valid_periods}")

    for i, period in enumerate(valid_periods):
        owners_equity = get_value(balance_sheet, "owners_equity", period)
        total_assets = get_value(balance_sheet, "total_assets", period)
        deposits = get_value(balance_sheet, "deposits_from_customers", period)

        if total_assets == 0:
            print(f"  [Bo qua] {symbol} {period}: total_assets = 0")
            continue

        # A4
        eta = owners_equity / total_assets * 100

        # A5
        equity_to_deposits = owners_equity / deposits * 100 if deposits else 0.0

        # B1: tang truong QoQ
        if i < len(valid_periods) - 1:
            previous_assets = get_value(balance_sheet, "total_assets", valid_periods[i + 1])
            growth_qoq = (total_assets - previous_assets) / previous_assets * 100 if previous_assets else None
        else:
            growth_qoq = None

        # B2
        asset_structure = compute_asset_structure(balance_sheet, period)

        # B7
        accrued_interest = get_value(balance_sheet, "accrued_interest_and_fee_receivables", period) / total_assets * 100

        # C1
        operating_income = get_value(income_statement, "total_operating_income", period)
        cir = abs(get_value(income_statement, "general_and_admin_expenses", period)) / operating_income * 100 if operating_income else 0.0

        # D1 — ROA theo năm hóa (lợi nhuận quý × 4 / tài sản cuối kỳ)
        # Lý do nhân 4: net_profit_loss_after_tax là lũy kế 1 quý,
        # total_assets là số dư cuối kỳ — cần đưa về cùng thứ nguyên 1 năm.
        roa = get_value(income_statement, "net_profit_loss_after_tax", period) * 4 / total_assets * 100

        # D2 — ROE theo năm hóa (lợi nhuận quý × 4 / vốn chủ cuối kỳ)
        roe = get_value(income_statement, "net_profit_loss_after_tax", period) * 4 / owners_equity * 100 if owners_equity else 0.0

        # D3: NIM — năm hóa (thu nhập lãi thuần quý × 4 / tài sản sinh lời bình quân)
        # D4: YOEA — năm hóa (thu nhập lãi quý × 4 / tài sản sinh lời bình quân)
        # Lý do nhân 4: income_statement ghi lũy kế 1 quý; bình quân earning assets
        # là snapshot cuối 2 kỳ liên tiếp — cần đưa tử số về thứ nguyên 1 năm.
        if i < len(valid_periods) - 1:
            prev_period = valid_periods[i + 1]
            avg_earning_assets = (
                get_value(balance_sheet, "balances_with_the_sbv", period)
                + get_value(balance_sheet, "placements_with_and_loans_to_other_credit_institutions", period)
                + get_value(balance_sheet, "loans_and_advances_to_customers", period)
                + get_value(balance_sheet, "trading_securities", period)
                + get_value(balance_sheet, "investment_securities", period)
                + get_value(balance_sheet, "balances_with_the_sbv", prev_period)
                + get_value(balance_sheet, "placements_with_and_loans_to_other_credit_institutions", prev_period)
                + get_value(balance_sheet, "loans_and_advances_to_customers", prev_period)
                + get_value(balance_sheet, "trading_securities", prev_period)
                + get_value(balance_sheet, "investment_securities", prev_period)
            ) / 2

            nim = get_value(income_statement, "net_interest_income", period) * 4 / avg_earning_assets * 100 if avg_earning_assets else 0.0
            yoea = get_value(income_statement, "interest_and_similar_income", period) * 4 / avg_earning_assets * 100 if avg_earning_assets else 0.0
        else:
            nim = None
            yoea = None

        # D5 — COF theo năm hóa, mẫu số dùng bình quân 2 kỳ
        interest_expenses = abs(get_value(income_statement, "interest_and_similar_expenses", period))

        funded_liab_current = _funded_liabilities(balance_sheet, period)
        if i < len(valid_periods) - 1:
            funded_liab_prev = _funded_liabilities(balance_sheet, valid_periods[i + 1])
            avg_funded_liabilities = (funded_liab_current + funded_liab_prev) / 2
        else:
            avg_funded_liabilities = funded_liab_current

        cof = interest_expenses * 4 / avg_funded_liabilities * 100 if avg_funded_liabilities else 0.0

        # E1 — LDR (Loan-to-Deposit Ratio)
        loans = get_value(balance_sheet, "loans_and_advances_to_customers", period)
        ldr = loans / deposits * 100 if deposits else 0.0
        print(
            f"{period}: ETA={eta:.2f}%, Equity/Deposits={equity_to_deposits:.2f}%, "
            f"Growth_qoq={'N/A' if growth_qoq is None else f'{growth_qoq:.2f}%'}, "
            f"Accrued Interest={accrued_interest:.2f}%, CIR={cir:.2f}%, "
            f"ROA={roa:.2f}% (ann), ROE={roe:.2f}% (ann), "
            f"NIM={'N/A' if nim is None else f'{nim:.2f}% (ann)'}, "
            f"YOEA={'N/A' if yoea is None else f'{yoea:.2f}% (ann)'}, "
            f"COF={cof:.2f}% (ann), LDR={ldr:.2f}%"
        )
        all_rows.append({
            "symbol": symbol,
            "period": period,
            "ETA_%": round(eta, 2),
            "equity_to_deposits_%": round(equity_to_deposits, 2),
            "total_assets": total_assets,
            "growth_qoq_%": None if growth_qoq is None else round(growth_qoq, 2),
            "accrued_interest_%": round(accrued_interest, 2),
            "cost_to_income_%": round(cir, 2),
            "ROA_%": round(roa, 2),          # annualized (×4)
            "ROE_%": round(roe, 2),          # annualized (×4)
            "NIM_%": None if nim is None else round(nim, 2),    # annualized (×4)
            "YOEA_%": None if yoea is None else round(yoea, 2), # annualized (×4)
            "COF_%": round(cof, 2),          # annualized (×4), avg denominator
            "LDR_%": round(ldr, 2),
            **{f"{k}": v for k, v in asset_structure.items()},
        })
insert_ratios(all_rows)

result_df = pd.DataFrame(all_rows)
result_df.to_csv("bank_metrics_13_banks.csv", index=False, encoding="utf-8-sig")
print(f"\n Done, {len(result_df)} dong saved to bank_metrics_13_banks.csv")