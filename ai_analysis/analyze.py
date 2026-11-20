"""AI Analysis for Banks — Gemini-based financial explanation and structured outlook.

Quy tắc cốt lõi:
1. Nhận vào các chỉ số tài chính ĐÃ ĐƯỢC TÍNH SẴN từ DB (không nhận BCTC thô).
2. AI chỉ giải thích và dự báo xu hướng định tính, KHÔNG quyết định Financial Health Score.
3. Chống Hallucination: Không tự ý bịa các số liệu tài chính cụ thể không có trong input.
4. Disclaimer: Không đưa ra khuyến nghị mua/bán cổ phiếu cá nhân hóa.
"""

import json
import os
from typing import Dict, Any, Optional
import google.generativeai as genai

PROMPT_VERSION = "v2_banking"

BANKING_SYSTEM_INSTRUCTIONS = """Bạn là chuyên gia phân tích tài chính ngân hàng tại thị trường Việt Nam.
Bạn sẽ nhận được các chỉ số tài chính ĐÃ ĐƯỢC TÍNH SẴN của một ngân hàng qua các kỳ (quý/năm).
Các nhóm chỉ số bao gồm:
- Capital Adequacy: ETA (VCSH/Tổng tài sản), EQ_DEPOSIT (VCSH/Tiền gửi).
- Asset Quality & Liquidity: LDR (Cho vay/Tiền gửi), ACCRUED_INT (Lãi dự thu/Tổng tài sản), EARNING_ASSET_RATIO.
- Profitability: ROA, ROE, NIM, YOEA (các chỉ số đã được năm hóa).
- Efficiency & Funding: CIR (Chi phí/Thu nhập), COF (Chi phí vốn).

Nhiệm vụ của bạn:
1. Phân tích điểm mạnh, điểm yếu và các rủi ro đáng chú ý của ngân hàng dựa trên chuỗi số liệu được cung cấp.
2. Đưa ra dự báo CÓ THỂ KIỂM CHỨNG cho kỳ tiếp theo trên 3 trục:
   - trend_prediction: "improve" | "stable" | "decline" (Xu hướng sức khỏe tổng thể)
   - risk_prediction: "low" | "moderate" | "high" (Mức độ rủi ro thanh khoản và tài sản)
   - profitability_prediction: "improve" | "stable" | "decline" (Xu hướng sinh lời)
3. Tóm tắt giải thích ngắn gọn, súc tích (khoảng 3-5 câu), tuân thủ nguyên tắc:
   - KHÔNG tự bịa các số liệu tài chính không xuất hiện trong input.
   - KHÔNG đưa ra khuyến nghị mua/bán cổ phiếu (tuân thủ quy định pháp luật chứng khoán).

CHỈ trả về JSON đúng theo schema sau, không thêm markdown hay bất kỳ văn bản nào khác ngoài JSON:
{
  "trend_prediction": "improve|stable|decline",
  "risk_prediction": "low|moderate|high",
  "profitability_prediction": "improve|stable|decline",
  "strengths": ["điểm mạnh 1", "điểm mạnh 2"],
  "weaknesses": ["điểm yếu/rủi ro 1", "điểm yếu/rủi ro 2"],
  "explanation": "Tóm tắt phân tích..."
}
"""


def _configure():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Chưa thiết lập biến môi trường GEMINI_API_KEY")
    genai.configure(api_key=api_key)


def build_bank_prompt(symbol: str, ratios_history: Dict[str, Any]) -> str:
    return (
        BANKING_SYSTEM_INSTRUCTIONS
        + f"\n\nNgân hàng: {symbol}\n"
        + "Dữ liệu chỉ số tài chính theo kỳ:\n"
        + json.dumps(ratios_history, ensure_ascii=False, indent=2)
    )


def analyze_bank(symbol: str, ratios_history: Dict[str, Any], model_name: Optional[str] = None) -> Dict[str, Any]:
    """Gọi Gemini API để phân tích chuỗi chỉ số ngân hàng và trả về kết quả JSON đã parse."""
    _configure()
    model_name = model_name or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    model = genai.GenerativeModel(model_name)

    prompt = build_bank_prompt(symbol, ratios_history)
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )

    try:
        parsed = json.loads(response.text)
    except (json.JSONDecodeError, AttributeError) as e:
        raise ValueError(f"AI không trả về JSON hợp lệ: {response.text}") from e

    parsed["_prompt_version"] = PROMPT_VERSION
    parsed["_model_name"] = model_name
    return parsed


# Tương thích ngược với hàm analyze cũ
def analyze(ratios_by_year: dict, model_name: Optional[str] = None) -> dict:
    return analyze_bank(symbol="UNKNOWN", ratios_history=ratios_by_year, model_name=model_name)
