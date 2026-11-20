"""PRODUCTION entrypoint — FastAPI Backend for Banking Financial Health Scoring.

Cung cấp các API:
1. GET  /health: Liveness check.
2. GET  /banks: Danh sách ngân hàng trong hệ thống.
3. GET  /periods: Danh sách kỳ báo cáo có dữ liệu.
4. GET  /banks/{symbol}/ratios: Lấy chỉ số và điểm sức khỏe của ngân hàng.
5. POST /analyze: Phân tích sức khỏe ngân hàng (chấm điểm + AI Explanation).
6. GET  /ranking: Bảng xếp hạng sức khỏe tài chính các ngân hàng trong 1 kỳ.
"""

from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from scoring.score import compute_bank_health_score, SCORING_VERSION
from ai_analysis.analyze import analyze_bank, PROMPT_VERSION
from db.supabase_reader import (
    get_bank_ratios_by_period,
    get_bank_ratios_history,
    get_peer_comparison,
    get_available_banks,
    get_available_periods,
)

app = FastAPI(
    title="VN30 Banking Financial Health Scoring API",
    description="Hệ thống chấm điểm sức khỏe tài chính và phân tích xu hướng cho nhóm ngân hàng VN30.",
    version="2.0.0",
)


class BankAnalysisRequest(BaseModel):
    symbol: str = Field(..., description="Mã ngân hàng (ví dụ: VCB, MBB, CTG...)")
    period_id: str = Field(..., description="Kỳ báo cáo cần phân tích (ví dụ: 2026-Q2)")
    include_ai: bool = Field(True, description="Có gọi AI để sinh báo cáo giải thích hay không")


class BankHealthResponse(BaseModel):
    symbol: str
    period_id: str
    ratios: Dict[str, float]
    score: Dict[str, Any]
    ai_explanation: Optional[Dict[str, Any]] = None
    versions: Dict[str, str]
    disclaimer: str = (
        "Thông tin chỉ mang tính chất tham khảo học thuật/nghiên cứu, "
        "không phải là lời khuyên hay khuyến nghị đầu tư cá nhân hóa."
    )


@app.get("/health")
def health_check():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/banks")
def list_banks():
    """Lấy danh sách các mã ngân hàng hiện có."""
    banks = get_available_banks()
    return {"banks": banks}


@app.get("/periods")
def list_periods():
    """Lấy danh sách các quý tài chính có sẵn trong DB."""
    periods = get_available_periods()
    return {"periods": periods}


@app.get("/banks/{symbol}/ratios")
def get_bank_ratios(symbol: str, period_id: str = Query(..., description="Ví dụ: 2026-Q2")):
    """Lấy chỉ số và điểm sức khỏe tài chính nhanh của một ngân hàng trong một quý."""
    symbol = symbol.upper()
    ratios = get_bank_ratios_by_period(symbol, period_id)
    if not ratios:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy dữ liệu chỉ số cho ngân hàng {symbol} trong kỳ {period_id}",
        )
    score = compute_bank_health_score(ratios)
    return {
        "symbol": symbol,
        "period_id": period_id,
        "ratios": ratios,
        "score": score,
    }


@app.post("/analyze", response_model=BankHealthResponse)
def analyze_bank_endpoint(payload: BankAnalysisRequest):
    """Phân tích toàn diện: Tính điểm sức khỏe và gọi AI phân tích xu hướng."""
    symbol = payload.symbol.upper()
    period_id = payload.period_id

    # 1. Đọc dữ liệu từ Supabase
    ratios = get_bank_ratios_by_period(symbol, period_id)
    if not ratios:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy dữ liệu tài chính cho {symbol} tại kỳ {period_id}. Hãy kiểm tra xem pipeline compute.py đã chạy chưa.",
        )

    # 2. Chấm điểm sức khỏe tài chính bằng thuật toán
    score = compute_bank_health_score(ratios)

    # 3. Phân tích AI (tùy chọn)
    ai_explanation = None
    if payload.include_ai:
        try:
            # Lấy chuỗi lịch sử 4-8 quý gần nhất để AI nhìn được xu hướng
            history_df = get_bank_ratios_history(symbol)
            if not history_df.empty:
                history_dict = history_df.to_dict(orient="index")
            else:
                history_dict = {period_id: ratios}

            ai_explanation = analyze_bank(symbol=symbol, ratios_history=history_dict)
        except Exception as e:
            ai_explanation = {
                "error": f"Không thể lấy phân tích AI: {str(e)}",
                "trend_prediction": "N/A",
                "risk_prediction": "N/A",
                "profitability_prediction": "N/A",
            }

    return BankHealthResponse(
        symbol=symbol,
        period_id=period_id,
        ratios=ratios,
        score=score,
        ai_explanation=ai_explanation,
        versions={"scoring_version": SCORING_VERSION, "prompt_version": PROMPT_VERSION},
    )


@app.get("/ranking")
def get_banking_ranking(period_id: str = Query(..., description="Kỳ báo cáo xếp hạng, ví dụ: 2026-Q2")):
    """Bảng xếp hạng sức khỏe tài chính của toàn bộ ngân hàng trong kỳ."""
    peer_df = get_peer_comparison(period_id)
    if peer_df.empty:
        raise HTTPException(status_code=404, detail=f"Chưa có dữ liệu so sánh cho kỳ {period_id}")

    ranking = []
    for symbol, row in peer_df.iterrows():
        ratios_dict = row.dropna().to_dict()
        if not ratios_dict:
            continue
        score_res = compute_bank_health_score(ratios_dict)
        ranking.append({
            "symbol": symbol,
            "financial_health_score": score_res["financial_health_score"],
            "capital_adequacy_score": score_res["capital_adequacy_score"],
            "asset_quality_score": score_res["asset_quality_score"],
            "profitability_score": score_res["profitability_score"],
            "efficiency_score": score_res["efficiency_score"],
            "key_ratios": {
                "ETA_%": ratios_dict.get("ETA"),
                "ROE_%": ratios_dict.get("ROE"),
                "ROA_%": ratios_dict.get("ROA"),
                "NIM_%": ratios_dict.get("NIM"),
                "CIR_%": ratios_dict.get("CIR"),
                "LDR_%": ratios_dict.get("LDR"),
            }
        })

    # Sắp xếp theo điểm tổng hợp giảm dần
    ranking.sort(key=lambda x: x["financial_health_score"], reverse=True)
    return {"period_id": period_id, "ranking": ranking}
