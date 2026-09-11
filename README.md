# VN30 Financial Health Scoring System

## Kiến trúc

```
BCTC VN30 → Data Cleaning → Database → Financial Ratio Engine
                                              │
                          ┌───────────────────┴───────────────────┐
                          ▼                                       ▼
                  Scoring Algorithm                          AI Analysis
                          │                                       │
                  Financial Health Score                    Explanation
                          └───────────────────┬───────────────────┘
                                              ▼
                                        Final Report
                                              │
                                              ▼
                                  Historical Validation
                                              │
                                              ▼
                                 Accuracy / Precision / Recall / F1 / MAE
                                              │
                                              ▼
                                      Model Improvement
```

## Tech Stack & Framework

| Tầng | Công nghệ | Lý do |
|---|---|---|
| Backend / API | Python + FastAPI | Validate input/output bằng Pydantic (khớp yêu cầu AI trả JSON đúng schema để B4 so sánh); tự sinh docs Swagger, tiện demo/bảo vệ; async native cho việc gọi Gemini API |
| Thu thập dữ liệu | vnstock (Python, miễn phí) | Lấy BCTC/giá CK VN30 trực tiếp từ nguồn (SSI, VCI, TCBS) |
| Xử lý dữ liệu | pandas, numpy | Tính ratios, YoY growth, CAGR, moving average |
| Database | PostgreSQL (Supabase free tier) | Lưu BCTC, ratios, dự đoán AI, ground truth, kết quả đánh giá theo năm/doanh nghiệp |
| AI phân tích | Gemini API (free tier) | Nhận input là ratios đã tính sẵn (không phải BCTC thô), trả JSON có cấu trúc |
| Đánh giá độ chính xác | scikit-learn, numpy | Accuracy, Precision, Recall, F1, MAE giữa dự đoán AI và ground truth |
| Frontend / Web report | Streamlit | Streamlit nếu ưu tiên tốc độ (Python thuần) |
| Deployment | Render/Railway (backend), Vercel hoặc Streamlit Community Cloud (frontend) |  |

## Cấu trúc thư mục

| Thư mục | Vai trò |
|---|---|
| `data_ingestion/` | Lấy BCTC/giá cổ phiếu VN30 (vnstock), làm sạch, chuẩn hóa |
| `db/` | Schema & models PostgreSQL (SQLAlchemy) |
| `ratio_engine/` | Tính các nhóm chỉ số: Liquidity, Leverage, Profitability, Efficiency, Cash flow |
| `scoring/` | Scoring Algorithm — tính Financial Health Score từ ratios (không dùng AI) |
| `ai_analysis/` | Gọi Gemini API để phân tích/giải thích từ ratios đã tính, output JSON có cấu trúc |
| `evaluation/` | So khớp dự đoán AI/scoring với ground truth năm sau; tính Accuracy/Precision/Recall/F1/MAE; benchmark 3 model (ratios-only / ratios+scoring / ratios+scoring+AI) |
| `tests/` | Unit test cho từng module |
| `docs/` | Đề cương, ghi chú thiết kế |

## Cài đặt

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # điền GEMINI_API_KEY, DATABASE_URL
```

## Chạy Postgres local (tuỳ chọn, dùng Docker)

```bash
docker compose up -d
```

## Roadmap triển khai

1. `data_ingestion` — lấy dữ liệu VN30 qua vnstock, lưu DB
2. `ratio_engine` — tính ratios theo năm/doanh nghiệp
3. `scoring` — công thức trọng số → Financial Health Score
4. `ai_analysis` — prompt + JSON schema cố định theo 5 nhóm chỉ số
5. `evaluation` — ground truth, metrics, benchmark 3 model
6. Web report (FastAPI backend + frontend riêng)

