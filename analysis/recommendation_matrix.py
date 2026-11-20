"""Recommendation & Personalization Matrix for VCB.

Kết hợp 3 chiều:
1. FA & Sức khỏe tài chính (Sức mạnh vốn, NIM, Nợ xấu).
2. Định giá & Biên an toàn (Target P/B, Fair P/B).
3. TA (Xu hướng xu hướng giá, điểm vào kỹ thuật).

Cá nhân hóa theo 3 hồ sơ nhà đầu tư:
- CONSERVATIVE (Thận trọng): Ưu tiên bảo toàn vốn, mua khi có biên an toàn >20%, cổ tức đều đặn.
- BALANCED (Cân bằng): Kết hợp định giá cơ bản và xu hướng kỹ thuật (MA50/MA200), kỳ vọng sinh lời 15-20%/năm.
- GROWTH (Tăng trưởng / Năng động): Tận dụng đà tăng giá (momentum), chấp nhận biến động ngắn hạn.
"""

from typing import Dict, Any


def personalize_vcb_recommendation(
    investor_profile: str,
    valuation_base: Dict[str, Any],
    ta_signals: Dict[str, Any],
    financial_health_score: float,
) -> Dict[str, Any]:
    """investor_profile: 'conservative' | 'balanced' | 'growth'"""
    profile = investor_profile.lower()
    target_price = valuation_base.get("target_price", 0.0)
    current_price = ta_signals.get("close_price", 0.0)
    upside = valuation_base.get("upside", 0.0)

    # 1. Profile: Thận trọng (Conservative)
    if profile == "conservative":
        strategy = "Đầu tư giá trị & Nắm giữ dài hạn"
        allocation_advice = "Tỷ trọng danh mục khuyến nghị: 20% - 30% (Cổ phiếu trụ cột)"
        action = "MUA TÍCH LŨY" if upside >= 15.0 else "NẮM GIỮ"
        key_rationale = (
            f"VCB là ngân hàng có chất lượng tài sản số 1 toàn ngành (Điểm sức khỏe: {financial_health_score}/100), "
            f"tỷ lệ nợ xấu thấp nhất và đệm dự phòng bao nợ xấu (LLR) vững chắc. "
            f"Phù hợp làm cổ phiếu phòng thủ trong danh mục dài hạn."
        )

    # 2. Profile: Cân bằng (Balanced)
    elif profile == "balanced":
        strategy = "Tăng trưởng bền vững (GARP)"
        allocation_advice = "Tỷ trọng danh mục khuyến nghị: 15% - 25%"
        action = "MUA" if (upside >= 12.0 and "Uptrend" in ta_signals.get("trend_status", "")) else "TÍCH LŨY THEO NHỊP CHỈNH"
        key_rationale = (
            f"Hưởng lợi từ phục hồi kinh tế vĩ mô và tăng trưởng tín dụng. "
            f"Định giá mục tiêu: {target_price:,.0f} VND (Biên tăng kỳ vọng: +{upside}%). "
            f"Trạng thái kỹ thuật: {ta_signals.get('trend_status', 'N/A')}."
        )

    # 3. Profile: Tăng trưởng (Growth)
    else:
        strategy = "Giao dịch theo xu hướng kết hợp FA cơ bản"
        allocation_advice = "Tỷ trọng danh mục khuyến nghị: 10% - 20%"
        action = "MUA LƯỚT SÓNG" if ta_signals.get("RSI", 50) < 65 and ta_signals.get("MACD_status") == "Tích cực" else "QUAN SÁT CHỜ ĐIỂM MUA"
        key_rationale = (
            f"Kỳ vọng xúc tác từ câu chuyện phát hành riêng lẻ cho nhà đầu tư ngoại và chia thưởng cổ phiếu. "
            f"RSI hiện tại: {ta_signals.get('RSI')} ({ta_signals.get('RSI_status')})."
        )

    return {
        "investor_profile": profile.upper(),
        "strategy": strategy,
        "recommendation": action,
        "allocation_advice": allocation_advice,
        "target_price": target_price,
        "upside_percent": upside,
        "key_rationale": key_rationale,
        "risk_warning": "Rủi ro chính: Biến động lãi suất điều hành toàn cầu và sự trầm lắng của thị trường bất động sản tác động tới khả năng hấp thụ vốn.",
    }
