"""AI Analysis — B3.

Key design rule from the pipeline discussion: the AI receives ALREADY-COMPUTED
ratios (never raw BCTC), and it never decides the Financial Health Score — it
only explains and produces a structured, checkable prediction that B4 can
grade against next year's ground truth.
"""

import json
import os

import google.generativeai as genai

PROMPT_VERSION = "v1"

SYSTEM_INSTRUCTIONS = """Bạn là trợ lý phân tích tài chính. Bạn sẽ nhận vào các chỉ số
tài chính ĐÃ ĐƯỢC TÍNH SẴN (không phải báo cáo tài chính thô) của một doanh nghiệp
qua nhiều năm. Nhiệm vụ của bạn:

1. Phân tích xu hướng theo 5 nhóm: Liquidity, Profitability, Leverage, Efficiency, Cash flow.
2. Đưa ra dự đoán CÓ THỂ KIỂM CHỨNG cho năm tiếp theo trên 3 trục:
   - trend: "improve" | "stable" | "decline"
   - risk: "low" | "moderate" | "high"
   - profitability: "improve" | "stable" | "decline"
3. Giải thích ngắn gọn căn cứ cho dự đoán.

CHỈ trả về JSON đúng theo schema, không thêm text khác:
{
  "trend_prediction": "improve|stable|decline",
  "risk_prediction": "low|moderate|high",
  "profitability_prediction": "improve|stable|decline",
  "explanation": "..."
}
"""


def _configure():
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])


def build_prompt(ratios_by_year: dict) -> str:
    """ratios_by_year: {2022: {...ratios...}, 2023: {...}, ...}"""
    return (
        SYSTEM_INSTRUCTIONS
        + "\n\nDữ liệu chỉ số theo năm:\n"
        + json.dumps(ratios_by_year, ensure_ascii=False, indent=2)
    )


def analyze(ratios_by_year: dict, model_name: str | None = None) -> dict:
    """Calls Gemini and returns the parsed structured prediction.

    Raises ValueError if the model doesn't return valid JSON — callers should
    log the raw_response for debugging rather than silently failing.
    """
    _configure()
    model_name = model_name or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
    model = genai.GenerativeModel(model_name)

    prompt = build_prompt(ratios_by_year)
    response = model.generate_content(
        prompt,
        generation_config={"response_mime_type": "application/json"},
    )

    try:
        parsed = json.loads(response.text)
    except (json.JSONDecodeError, AttributeError) as e:
        raise ValueError(f"AI did not return valid JSON: {response}") from e

    parsed["_prompt_version"] = PROMPT_VERSION
    parsed["_model_name"] = model_name
    parsed["_raw_response"] = response.text
    return parsed
