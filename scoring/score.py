"""Banking Financial Health Scoring — Deterministic algorithm tailored for Vietnamese Banks.

Khung đánh giá sức khỏe ngân hàng dựa trên các nhóm CAMELS rút gọn từ BCTC:
1. CAPITAL_ADEQUACY (25%):
   - ETA (VCSH / Tổng tài sản)
   - EQ_DEPOSIT (VCSH / Tiền gửi khách hàng)
2. ASSET_QUALITY & LIQUIDITY (25%):
   - LDR (Cho vay / Tiền gửi khách hàng): Chuẩn quy định NHNN trần ~85%
   - ACCRUED_INT (Lãi dự thu / Tổng tài sản): Proxy rủi ro nợ xấu tiềm ẩn (thấp là tốt)
   - EARNING_ASSET_RATIO (Tài sản sinh lời / Tổng tài sản): Hiệu quả phân bổ tài sản
3. PROFITABILITY (30%):
   - ROE (năm hóa): Hiệu quả sử dụng vốn chủ
   - ROA (năm hóa): Hiệu quả sử dụng tổng tài sản
   - NIM (năm hóa): Biên lãi thuần
4. EFFICIENCY (20%):
   - CIR (Cost to Income Ratio): Tỷ lệ chi phí trên thu nhập hoạt động (thấp là tốt)
"""

SCORING_VERSION = "v2_banking"

GROUP_WEIGHTS = {
    "capital_adequacy": 0.25,
    "asset_quality": 0.25,
    "profitability": 0.30,
    "efficiency": 0.20,
}


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(value)))


def _linear_score(val: float, min_val: float, max_val: float, inverse: bool = False) -> float:
    """Chuyển đổi một giá trị sang thang điểm 0 - 100 theo min-max chuẩn ngành.
    inverse=True: giá trị càng thấp càng tốt (ví dụ: CIR, Lãi dự thu).
    """
    if val is None:
        return 50.0
    if max_val == min_val:
        return 50.0
    ratio = (val - min_val) / (max_val - min_val)
    if inverse:
        ratio = 1.0 - ratio
    return _clamp(ratio * 100.0)


# ==========================================
# 1. CAPITAL ADEQUACY (An toàn vốn)
# Ngân hàng Việt Nam: ETA thông thường 6% - 15%
# ==========================================
def score_eta(eta: float) -> float:
    """ETA (VCSH / Tổng tài sản): >=12% xuất sắc, 8-12% an toàn, <6% rủi ro đòn bẩy cao."""
    if eta is None:
        return 50.0
    return _linear_score(eta, min_val=5.0, max_val=14.0)


def score_equity_to_deposits(eq_dep: float) -> float:
    """VCSH / Tiền gửi: 10% - 25%."""
    if eq_dep is None:
        return 50.0
    return _linear_score(eq_dep, min_val=8.0, max_val=25.0)


def compute_capital_score(ratios: dict) -> float:
    s_eta = score_eta(ratios.get("ETA"))
    s_eq_dep = score_equity_to_deposits(ratios.get("EQ_DEPOSIT"))
    return _clamp(s_eta * 0.6 + s_eq_dep * 0.4)


# ==========================================
# 2. ASSET QUALITY & LIQUIDITY (Chất lượng tài sản & Thanh khoản)
# ==========================================
def score_ldr(ldr: float) -> float:
    """LDR (Cho vay / Tiền gửi):
    - Lý tưởng: 75% - 85% (theo trần thông tư NHNN thường tối đa 85%).
    - Quá thấp (<65%): Dư thừa thanh khoản, tối ưu vốn kém.
    - Quá cao (>95%): Căng thẳng thanh khoản, rủi ro thu hồi nợ.
    """
    if ldr is None:
        return 50.0
    if 75.0 <= ldr <= 85.0:
        return 100.0
    if 65.0 <= ldr < 75.0:
        return _linear_score(ldr, min_val=65.0, max_val=75.0) * 0.3 + 70.0
    if 85.0 < ldr <= 95.0:
        return 100.0 - (ldr - 85.0) * 3.0  # 85->100, 95->70
    if ldr > 95.0:
        return _clamp(70.0 - (ldr - 95.0) * 4.0, 10.0, 70.0)
    return _linear_score(ldr, min_val=40.0, max_val=65.0) * 0.7  # < 65%


def score_accrued_interest(acc_int: float) -> float:
    """Lãi dự thu / Tổng tài sản (Càng thấp càng an toàn):
    Thông thường 0.4% - 2.5%. Trên 2% thường là tín hiệu nợ nhóm 2 hoặc đảo nợ tiềm ẩn.
    """
    if acc_int is None:
        return 50.0
    return _linear_score(acc_int, min_val=0.4, max_val=2.2, inverse=True)


def score_earning_assets_ratio(ear: float) -> float:
    """Tỷ lệ tài sản sinh lời: Thường dao động 85% - 98%."""
    if ear is None:
        return 50.0
    return _linear_score(ear, min_val=85.0, max_val=97.0)


def compute_asset_quality_score(ratios: dict) -> float:
    s_ldr = score_ldr(ratios.get("LDR"))
    s_acc = score_accrued_interest(ratios.get("ACCRUED_INT"))
    s_ear = score_earning_assets_ratio(ratios.get("EARNING_ASSET_RATIO"))
    return _clamp(s_ldr * 0.45 + s_acc * 0.35 + s_ear * 0.20)


# ==========================================
# 3. PROFITABILITY (Khả năng sinh lời - đã năm hóa)
# ==========================================
def score_roe(roe_ann: float) -> float:
    """ROE năm hóa: >20% xuất sắc (Top tier), 15-20% tốt, 10-15% trung bình, <10% thấp."""
    if roe_ann is None:
        return 50.0
    return _linear_score(roe_ann, min_val=8.0, max_val=22.0)


def score_roa(roa_ann: float) -> float:
    """ROA năm hóa: >2.0% xuất sắc, 1.2-2.0% tốt, 0.8-1.2% trung bình, <0.8% thấp."""
    if roa_ann is None:
        return 50.0
    return _linear_score(roa_ann, min_val=0.6, max_val=2.4)


def score_nim(nim_ann: float) -> float:
    """NIM năm hóa: >4.0% cao (bán lẻ mạnh), 3.0-4.0% tốt, 2.0-3.0% trung bình, <2.0% mỏng."""
    if nim_ann is None:
        return 50.0
    return _linear_score(nim_ann, min_val=1.8, max_val=4.5)


def compute_profitability_score(ratios: dict) -> float:
    s_roe = score_roe(ratios.get("ROE"))
    s_roa = score_roa(ratios.get("ROA"))
    s_nim = score_nim(ratios.get("NIM"))
    return _clamp(s_roe * 0.4 + s_roa * 0.35 + s_nim * 0.25)


# ==========================================
# 4. EFFICIENCY (Hiệu quả hoạt động)
# ==========================================
def score_cir(cir: float) -> float:
    """CIR (Chi phí / Thu nhập hoạt động) - Càng thấp càng tối ưu:
    <30% xuất sắc, 30-40% tốt, 40-50% trung bình, >50% kém hiệu quả.
    """
    if cir is None:
        return 50.0
    return _linear_score(cir, min_val=25.0, max_val=55.0, inverse=True)


def compute_efficiency_score(ratios: dict) -> float:
    return _clamp(score_cir(ratios.get("CIR")))


# ==========================================
# HÀM CHÍNH TỔNG HỢP HEALTH SCORE
# ==========================================
def compute_bank_health_score(ratios: dict) -> dict:
    """ratios: dictionary chứa các mã chỉ số chuẩn hoá (ETA, ROE, ROA, NIM, CIR, LDR, etc.)
    hoặc wide format từ `compute.py` (ETA_%, ROE_%, etc.).
    """
    # Chuẩn hoá key đầu vào nếu có hậu tố '_%'
    normalized = {}
    for k, v in ratios.items():
        clean_k = k.replace("_%", "")
        normalized[clean_k] = v
        # Map các alias phổ biến
        if clean_k == "equity_to_deposits":
            normalized["EQ_DEPOSIT"] = v
        elif clean_k == "cost_to_income":
            normalized["CIR"] = v
        elif clean_k == "accrued_interest":
            normalized["ACCRUED_INT"] = v
        elif clean_k == "earning_assets_ratio":
            normalized["EARNING_ASSET_RATIO"] = v

    cap_score = compute_capital_score(normalized)
    asset_score = compute_asset_quality_score(normalized)
    prof_score = compute_profitability_score(normalized)
    eff_score = compute_efficiency_score(normalized)

    total_score = (
        cap_score * GROUP_WEIGHTS["capital_adequacy"]
        + asset_score * GROUP_WEIGHTS["asset_quality"]
        + prof_score * GROUP_WEIGHTS["profitability"]
        + eff_score * GROUP_WEIGHTS["efficiency"]
    )

    return {
        "capital_adequacy_score": round(cap_score, 1),
        "asset_quality_score": round(asset_score, 1),
        "profitability_score": round(prof_score, 1),
        "efficiency_score": round(eff_score, 1),
        "financial_health_score": round(_clamp(total_score), 1),
        "scoring_version": SCORING_VERSION,
    }


# Giữ tương thích ngược với compute_financial_health_score cũ
compute_financial_health_score = compute_bank_health_score
