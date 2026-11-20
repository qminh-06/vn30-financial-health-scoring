from scoring.score import compute_bank_health_score, SCORING_VERSION


def test_bank_scoring_vcb_sample():
    # Giả lập dữ liệu chỉ số của VCB
    sample_vcb = {
        "ETA": 9.35,              # VCSH/TTS 9.35%
        "EQ_DEPOSIT": 14.37,      # VCSH/Tiền gửi 14.37%
        "LDR": 80.5,              # LDR trong vùng lý tưởng 75-85%
        "ACCRUED_INT": 0.43,      # Lãi dự thu rất thấp (tốt)
        "EARNING_ASSET_RATIO": 96.09,
        "ROE": 23.4,              # ROE năm hóa cao
        "ROA": 2.2,               # ROA năm hóa cao
        "NIM": 3.0,               # NIM chuẩn
        "CIR": 32.0,              # CIR tối ưu
    }
    result = compute_bank_health_score(sample_vcb)
    assert result["scoring_version"] == SCORING_VERSION
    assert 70.0 <= result["financial_health_score"] <= 100.0
    assert result["asset_quality_score"] > 80.0
    assert result["profitability_score"] > 80.0


def test_bank_scoring_weak_bank_sample():
    # Giả lập ngân hàng yếu kém (đòn bẩy cao, lãi dự thu phình to, CIR cao, NIM mỏng)
    sample_weak = {
        "ETA": 5.0,
        "EQ_DEPOSIT": 8.0,
        "LDR": 98.0,              # Thanh khoản căng thẳng
        "ACCRUED_INT": 2.5,       # Rủi ro nợ xấu tiềm ẩn
        "EARNING_ASSET_RATIO": 85.0,
        "ROE": 6.0,
        "ROA": 0.4,
        "NIM": 1.5,
        "CIR": 58.0,
    }
    result = compute_bank_health_score(sample_weak)
    assert result["financial_health_score"] < 40.0
    assert result["capital_adequacy_score"] < 30.0
