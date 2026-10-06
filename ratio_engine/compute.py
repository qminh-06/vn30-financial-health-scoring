from vnstock import Finance
from vnstock import register_user
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

from db.supabase_loader import seed_all, insert_ratios, insert_financial_details

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

def get_value(df, item_id, period):
    return df.loc[df.item_id == item_id, period].values[0]

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

seed_all(bank_name, PERIODS, ASSET_ITEMS)
all_rows = []

for symbol in BANK_SYMBOLS:
    print(f"\n=== {symbol} ===")
    try:
        finance = Finance(symbol=symbol, source="VCI")
        balance_sheet = finance.balance_sheet(period="quarter")
        income_statement = finance.income_statement(period="quarter")
    except Exception as e:
        print(f"LOI khi lay du lieu {symbol}: {e}")
        continue

    for i, period in enumerate(PERIODS):
        owners_equity = get_value(balance_sheet, "owners_equity", period)
        total_assets = get_value(balance_sheet, "total_assets", period)
        deposits = get_value(balance_sheet, "deposits_from_customers", period)

        # A4
        eta = owners_equity / total_assets * 100

        # A5
        equity_to_deposits = owners_equity / deposits * 100

        # B1: tang truong QoQ
        if i < len(PERIODS) - 1:
            previous_assets = get_value(balance_sheet, "total_assets", PERIODS[i + 1])
            growth_qoq = (total_assets - previous_assets) / previous_assets * 100
        else:
            growth_qoq = None

        # B2
        asset_structure = compute_asset_structure(balance_sheet, period)

        # B7
        accrued_interest = get_value(balance_sheet, "accrued_interest_and_fee_receivables", period)/total_assets * 100

        # C1
        cir = get_value(income_statement, "general_and_admin_expenses", period) / get_value(income_statement, "total_operating_income", period) * 100

        # D1
        roa = get_value(income_statement, "net_profit_loss_after_tax", period) / total_assets * 100

        # D2
        roe = get_value(income_statement, "net_profit_loss_after_tax", period) / owners_equity * 100

        # D3: NIM 
        # D4: YOEA
        if i < len(PERIODS) - 1:
            prev_period = PERIODS[i + 1]
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

            nim = get_value(income_statement, "net_interest_income", period) / avg_earning_assets * 100
            yoea = get_value(income_statement, "interest_and_similar_income", period) / avg_earning_assets * 100
        else:
            nim = None
            yoea = None

        # D5
        cof = get_value(income_statement, "interest_and_similar_expenses", period) / (get_value(balance_sheet, "due_to_gov_and_loans_from_sbv", period)
                                                                            + get_value(balance_sheet, "deposits_and_loans_from_other_credit_institutions", period)
                                                                            + get_value(balance_sheet, "deposits_from_customers", period)
                                                                            + get_value(balance_sheet, "convertible_bonds_cds_and_other_valuable_papers_issued", period)) * 100
        print(f"{period}: ETA={eta:.2f}%, Equity/Deposits={equity_to_deposits:.2f}%, "f"Growth_qoq={'N/A' if growth_qoq is None else f'{growth_qoq:.2f}%'}, "f"Accrued Interest={accrued_interest:.2f}%, CIR={cir:.2f}%, ROA={roa:.2f}%, ROE={roe:.2f}%, "f"NIM={'N/A' if nim is None else f'{nim:.2f}%'}, YOEA={'N/A' if yoea is None else f'{yoea:.2f}%'}, COF={cof:.2f}%")
        all_rows.append({
            "symbol": symbol,
            "period": period,
            "ETA_%": round(eta, 2),
            "equity_to_deposits_%": round(equity_to_deposits, 2),
            "total_assets": total_assets,
            "growth_qoq_%": None if growth_qoq is None else round(growth_qoq, 2),
            "accrued_interest_%": round(accrued_interest, 2),
            "cost_to_income_%": round(cir, 2),
            "ROA_%": round(roa, 2),
            "ROE_%": round(roe, 2),
            "NIM_%": None if nim is None else round(nim, 2),
            "YOEA_%": None if yoea is None else round(yoea, 2),
            "COF_%": round(cof, 2),
            **{f"{k}": v for k, v in asset_structure.items()},
        })
insert_ratios(all_rows)
insert_financial_details(all_rows)

result_df = pd.DataFrame(all_rows)
result_df.to_csv("bank_metrics_13_banks.csv", index=False, encoding="utf-8-sig")
print(f"\n Done, {len(result_df)} dong saved to bank_metrics_13_banks.csv")