"""Supabase Data Access Layer — Service đọc dữ liệu tài chính ngân hàng phục vụ API và Streamlit.
"""

from typing import Dict, List, Optional
import pandas as pd
from db.supabase_loader import supabase


def get_bank_ratios_by_period(symbol: str, period_id: str) -> Dict[str, float]:
    """Lấy danh sách các chỉ số tài chính của 1 ngân hàng trong 1 quý cụ thể.
    Trả về dict: {'ETA': 6.76, 'ROE': 23.56, 'ROA': 1.6, 'NIM': 2.88, ...}
    """
    res = (
        supabase.table("fact_computed_ratios")
        .select("ratio_code, ratio_value")
        .eq("symbol", symbol)
        .eq("period_id", period_id)
        .execute()
    )
    if not res.data:
        return {}
    return {row["ratio_code"]: float(row["ratio_value"]) for row in res.data}


def get_bank_ratios_history(symbol: str, periods: Optional[List[str]] = None) -> pd.DataFrame:
    """Lấy chuỗi lịch sử chỉ số của 1 ngân hàng qua các kỳ.
    Trả về DataFrame định dạng wide: index là period_id, các cột là ratio_code.
    """
    query = (
        supabase.table("fact_computed_ratios")
        .select("period_id, ratio_code, ratio_value")
        .eq("symbol", symbol)
    )
    if periods:
        query = query.in_("period_id", periods)
    
    res = query.execute()
    if not res.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(res.data)
    pivoted = df.pivot(index="period_id", columns="ratio_code", values="ratio_value")
    return pivoted


def get_peer_comparison(period_id: str, symbols: Optional[List[str]] = None) -> pd.DataFrame:
    """Lấy bảng so sánh chéo các chỉ số giữa các ngân hàng trong 1 quý cụ thể.
    Trả về DataFrame: index là symbol, các cột là các chỉ số (ETA, ROE, ROA, NIM, CIR, LDR...).
    """
    query = (
        supabase.table("fact_computed_ratios")
        .select("symbol, ratio_code, ratio_value")
        .eq("period_id", period_id)
    )
    if symbols:
        query = query.in_("symbol", symbols)
    
    res = query.execute()
    if not res.data:
        return pd.DataFrame()
    
    df = pd.DataFrame(res.data)
    pivoted = df.pivot(index="symbol", columns="ratio_code", values="ratio_value")
    return pivoted


def get_available_banks() -> List[Dict[str, str]]:
    """Lấy danh sách mã và tên tất cả các ngân hàng trong hệ thống."""
    res = supabase.table("dim_bank_master").select("symbol, bank_name").execute()
    return res.data or []


def get_available_periods() -> List[str]:
    """Lấy danh sách các kỳ báo cáo sắp xếp giảm dần theo thời gian."""
    res = (
        supabase.table("dim_period")
        .select("period_id, year, quarter")
        .order("year", desc=True)
        .order("quarter", desc=True)
        .execute()
    )
    return [row["period_id"] for row in res.data or []]
