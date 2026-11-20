import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

# KET NOI (lazy - chi tao client khi lan dau can dung, khong tao ngay luc import)
_supabase_client = None


def _normalize_url(url: str) -> str:
    url = url.strip().strip('"').strip("'").rstrip("/")
    for suffix in ("/rest/v1", "/auth/v1", "/storage/v1"):
        if url.endswith(suffix):
            url = url[: -len(suffix)]
    return url


def get_client():
    global _supabase_client
    if _supabase_client is None:
        raw_url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if not raw_url or not key:
            raise RuntimeError(
                "Thieu SUPABASE_URL hoac SUPABASE_SERVICE_ROLE_KEY. "
                "Kiem tra file .env co nam o thu muc goc project (ngang hang "
                "voi db/ va ratio_engine/) va co dung 2 bien nay khong."
            )
        _supabase_client = create_client(_normalize_url(raw_url), key)
    return _supabase_client


class _LazyClient:
    def __getattr__(self, name):
        return getattr(get_client(), name)

supabase = _LazyClient()

# DANH MUC CO DINH (seed 1 lan)

RATIO_CATALOG = [
    {"ratio_code": "ETA",         "ratio_name_vn": "VCSH/Tổng tài sản",        "unit": "%", "category": "CAPITAL_ADEQUACY", "source_type": "BCTC"},
    {"ratio_code": "EQ_DEPOSIT",  "ratio_name_vn": "VCSH/Tổng tiền gửi",       "unit": "%", "category": "CAPITAL_ADEQUACY", "source_type": "BCTC"},
    {"ratio_code": "GROWTH_QOQ",  "ratio_name_vn": "Tăng trưởng TTS QoQ",      "unit": "%", "category": "ASSET_QUALITY",    "source_type": "BCTC"},
    {"ratio_code": "ACCRUED_INT", "ratio_name_vn": "Lãi dự thu/Tổng tài sản",  "unit": "%", "category": "ASSET_QUALITY",    "source_type": "BCTC"},
    {"ratio_code": "CIR",         "ratio_name_vn": "Chi phí/Thu nhập",         "unit": "%", "category": "EFFICIENCY",       "source_type": "BCTC"},
    {"ratio_code": "ROA",         "ratio_name_vn": "ROA (năm hóa)",            "unit": "%", "category": "PROFITABILITY",    "source_type": "BCTC"},
    {"ratio_code": "ROE",         "ratio_name_vn": "ROE (năm hóa)",            "unit": "%", "category": "PROFITABILITY",    "source_type": "BCTC"},
    {"ratio_code": "NIM",         "ratio_name_vn": "NIM (năm hóa)",            "unit": "%", "category": "PROFITABILITY",    "source_type": "BCTC"},
    {"ratio_code": "YOEA",        "ratio_name_vn": "YOEA (năm hóa)",           "unit": "%", "category": "PROFITABILITY",    "source_type": "BCTC"},
    {"ratio_code": "COF",         "ratio_name_vn": "COF (năm hóa, bình quân)", "unit": "%", "category": "FUNDING",          "source_type": "BCTC"},
    {"ratio_code": "LDR",         "ratio_name_vn": "Tỷ lệ cho vay/tiền gửi",  "unit": "%", "category": "LIQUIDITY",        "source_type": "BCTC"},
    {"ratio_code": "EARNING_ASSET_RATIO", "ratio_name_vn": "Tài sản sinh lời/TTS", "unit": "%", "category": "ASSET_QUALITY", "source_type": "BCTC"},
]

# Map ten cot trong all_rows (compute.py) -> ratio_code trong dim_ratio_master
COLUMN_TO_RATIO_CODE = {
    "ETA_%": "ETA",
    "equity_to_deposits_%": "EQ_DEPOSIT",
    "growth_qoq_%": "GROWTH_QOQ",
    "accrued_interest_%": "ACCRUED_INT",
    "cost_to_income_%": "CIR",
    "ROA_%": "ROA",
    "ROE_%": "ROE",
    "NIM_%": "NIM",
    "YOEA_%": "YOEA",
    "COF_%": "COF",
    "LDR_%": "LDR",
    "earning_assets_ratio_%": "EARNING_ASSET_RATIO",
}
STATEMENT_TYPES = {"balance_sheet": "BS", "income_statement": "IS", "cash_flow": "CF"}
RATIO_CONFLICT = "symbol,period_id,report_type,is_forecast,ratio_code"
STATEMENT_CONFLICT = "symbol,period_id,report_type,is_forecast,item_code"
# SEED (chay 1 lan, hoac moi khi them ma/chi so moi)
def seed_banks(bank_name: dict):
    rows = [{"symbol": s, "bank_name": name} for s, name in bank_name.items()]
    supabase.table("dim_bank_master").upsert(rows, on_conflict="symbol").execute()

def seed_periods(periods: list):
    rows = []
    for p in periods:
        year, q = p.split("-Q")
        rows.append({
            "period_id": p, "period_name": p,
            "year": int(year), "quarter": int(q),
            "period_type": "QUARTERLY",
        })
    supabase.table("dim_period").upsert(rows, on_conflict="period_id").execute()


def seed_ratio_catalog():
    supabase.table("dim_ratio_master").upsert(RATIO_CATALOG, on_conflict="ratio_code").execute()


def _clean(df):
    """Bo item_id trung (giu dong dau = dong chinh) va dong khong co item_id."""
    return df.dropna(subset=["item_id"]).drop_duplicates(subset="item_id", keep="first")

def seed_line_items_from_statements(statements: dict):
    """statements = {"balance_sheet": df, "income_statement": df, "cash_flow": df}.
    Seed dim_financial_line_item thang tu DataFrame cua vnstock (item / item_en / item_id)."""
    rows = {}
    for name, df in statements.items():
        for order, r in enumerate(_clean(df).itertuples(index=False)):
            rows.setdefault(r.item_id, {
                "item_code": r.item_id,
                "item_name_vn": r.item,
                "item_name_en": r.item_en,
                "statement_type": STATEMENT_TYPES[name],
                "display_order": order,
            })
    supabase.table("dim_financial_line_item").upsert(
        list(rows.values()), on_conflict="item_code").execute()
    print(f"Seed {len(rows)} dong vao dim_financial_line_item")


def seed_all(bank_name: dict, periods: list):
    seed_banks(bank_name)
    seed_periods(periods)
    seed_ratio_catalog()
    print("Seed xong: dim_bank_master, dim_period, dim_ratio_master")
# LOAD FACT (chay moi lan co du lieu moi) - upsert, chay lai nhieu lan khong loi

def _batch_upsert(table_name: str, rows: list, on_conflict: str, batch_size: int = 500):
    for i in range(0, len(rows), batch_size):
        supabase.table(table_name).upsert(rows[i:i + batch_size], on_conflict=on_conflict).execute()

def insert_ratios(all_rows: list):
    """all_rows: list dict tu compute.py (wide format) -> chuyen sang long format."""
    fact_rows = []
    for row in all_rows:
        for col, ratio_code in COLUMN_TO_RATIO_CODE.items():
            value = row.get(col)
            if value is None:
                continue
            fact_rows.append({
                "symbol": row["symbol"],
                "period_id": row["period"],
                "report_type": "CONSOLIDATED",
                "is_forecast": False,
                "ratio_code": ratio_code,
                "ratio_value": value,
            })
    _batch_upsert("fact_computed_ratios", fact_rows, RATIO_CONFLICT)
    print(f"Da upsert {len(fact_rows)} dong vao fact_computed_ratios")


def insert_all_statement_lines(symbol: str, statements: dict, periods: list):
    unique_rows = {}
    for name, df in statements.items():
        df = _clean(df)
        for period in periods:
            if period not in df.columns:
                continue
            for item_id, amount in zip(df["item_id"], df[period]):
                if pd.isna(amount):
                    continue
                key = (period, item_id)
                if key in unique_rows:
                    if unique_rows[key]["amount"] != float(amount):
                        print(f"  [canh bao] {symbol} {period} {item_id}: gia tri khac nhau giua "f"cac bao cao, giu ban dau tien")
                    continue
                unique_rows[key] = {
                    "symbol": symbol,
                    "period_id": period,
                    "report_type": "CONSOLIDATED",
                    "is_forecast": False,
                    "item_code": item_id,
                    "amount": float(amount),
                }
    fact_rows = list(unique_rows.values())
    _batch_upsert("fact_financial_statement_details", fact_rows, STATEMENT_CONFLICT)
    print(f"{symbol}: upsert {len(fact_rows)} dong vao fact_financial_statement_details")