"""Bank Valuation Module — Chuyên biệt định giá cổ phiếu Ngân Hàng (VCB).

Đối với ngân hàng, 2 phương pháp chuẩn mực và có độ tin cậy cao nhất trong ngành là:
1. P/B Lịch sử & P/B Target (Price-to-Book):
   - Ngân hàng có tài sản chủ yếu là tài sản tài chính có tính thanh khoản, Book Value phản ánh giá trị nội tại tốt hơn doanh nghiệp sản xuất.
   - Định giá = BVPS * P/B mục tiêu (dựa trên trung vị P/B 3 năm và vị thế đầu ngành của VCB).
2. Mô hình Thu nhập thặng dư (Residual Income Model / Gordon Growth on Equity):
   - Fair P/B = (ROE - g) / (Ke - g)
   - Trong đó:
     * ROE: Tỷ suất sinh lời trên vốn chủ dự phóng.
     * Ke (Cost of Equity): Chi phí vốn chủ sở hữu (tính theo CAPM: Rf + Beta * ERP).
     * g: Tốc độ tăng trưởng dài hạn bền vững.
"""

from typing import Dict, Any


def calculate_cost_of_equity(rf: float = 0.045, beta: float = 0.85, erp: float = 0.08) -> float:
    """Tính chi phí vốn chủ (Ke) theo mô hình CAPM cho VCB.
    - rf: Lãi suất phi rủi ro (Trái phiếu Chính phủ 10 năm tại VN ~ 4.0% - 4.5%).
    - beta: Hệ số beta của VCB (VCB thường biến động thấp hơn thị trường chung ~ 0.8 - 0.9).
    - erp: Phần bù rủi ro vốn cổ phần (Equity Risk Premium ~ 7.5% - 8.5%).
    """
    return rf + beta * erp


def calculate_fair_pb(roe: float, cost_of_equity: float, growth_rate: float = 0.06) -> float:
    """Tính P/B hợp lý (Justified P/B) theo mô hình Gordon Growth:
    Fair P/B = (ROE - g) / (Ke - g)
    """
    if cost_of_equity <= growth_rate:
        raise ValueError("Cost of equity (Ke) phải lớn hơn tốc độ tăng trưởng dài hạn (g)")
    return (roe - growth_rate) / (cost_of_equity - growth_rate)


def value_bank_pb_method(
    bvps: float,
    current_pb: float,
    target_pb: float = 2.8,
) -> Dict[str, Any]:
    """Định giá theo phương pháp P/B mục tiêu.
    - bvps: Giá trị sổ sách mỗi cổ phiếu (Book Value Per Share).
    - current_pb: P/B thị trường tại thời điểm định giá.
    - target_pb: P/B mục tiêu kỳ vọng (VCB trong lịch sử thường dao động từ 2.5x - 3.5x do vị thế số 1 hệ thống).
    """
    target_price = bvps * target_pb
    current_price = bvps * current_pb
    upside = ((target_price - current_price) / current_price) * 100 if current_price else 0.0

    return {
        "method": "Target P/B",
        "bvps": round(bvps, 0),
        "current_pb": round(current_pb, 2),
        "target_pb": round(target_pb, 2),
        "target_price": round(target_price, 0),
        "upside_percent": round(upside, 1),
    }


def value_bank_residual_income(
    bvps: float,
    current_price: float,
    projected_roe: float = 0.20,
    rf: float = 0.045,
    beta: float = 0.85,
    erp: float = 0.08,
    long_term_growth: float = 0.06,
) -> Dict[str, Any]:
    """Định giá theo mô hình Justified P/B (Residual Income)."""
    ke = calculate_cost_of_equity(rf, beta, erp)
    fair_pb = calculate_fair_pb(projected_roe, ke, long_term_growth)
    target_price = bvps * fair_pb
    upside = ((target_price - current_price) / current_price) * 100 if current_price else 0.0

    return {
        "method": "Justified P/B (Residual Income)",
        "projected_roe": f"{projected_roe * 100:.1f}%",
        "cost_of_equity": f"{ke * 100:.2f}%",
        "long_term_growth": f"{long_term_growth * 100:.1f}%",
        "fair_pb": round(fair_pb, 2),
        "bvps": round(bvps, 0),
        "target_price": round(target_price, 0),
        "upside_percent": round(upside, 1),
    }


def generate_valuation_scenarios(
    bvps: float,
    current_price: float,
    base_roe: float = 0.20,
) -> Dict[str, Dict[str, Any]]:
    """Tạo 3 kịch bản định giá (Bear, Base, Bull) cho VCB đến mốc 01/01/2026."""
    scenarios = {
        "bear": {
            "name": "Kịch bản Thận trọng (Bear)",
            "assumption": "Tăng trưởng tín dụng chậm lại, NIM thu hẹp nhẹ, ROE đạt 16.5%",
            "roe": 0.165,
            "target_pb": 2.3,
            "target_price": round(bvps * 2.3, 0),
            "upside": round(((bvps * 2.3 - current_price) / current_price) * 100, 1),
        },
        "base": {
            "name": "Kịch bản Cơ sở (Base)",
            "assumption": "Duy trì vị thế số 1, NIM ổn định ~3.0%, CASA cao, ROE đạt 20.0%",
            "roe": 0.20,
            "target_pb": 2.8,
            "target_price": round(bvps * 2.8, 0),
            "upside": round(((bvps * 2.8 - current_price) / current_price) * 100, 1),
        },
        "bull": {
            "name": "Kịch bản Tích cực (Bull)",
            "assumption": "Tín dụng tăng tốc, thu nhập ngoài lãi bứt phá, phát hành riêng lẻ thành công, ROE đạt 23.0%",
            "roe": 0.23,
            "target_pb": 3.3,
            "target_price": round(bvps * 3.3, 0),
            "upside": round(((bvps * 3.3 - current_price) / current_price) * 100, 1),
        },
    }
    return scenarios
