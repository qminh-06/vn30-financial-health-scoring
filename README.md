# VN30 Banking Financial Health Scoring & Strategic Valuation System
> **Dự án Phân tích Sức khỏe Tài chính, Định giá Chuyên sâu & Cá nhân hóa Khuyến nghị Đầu tư (Case Study: VCB - Vietcombank đến mốc 01/01/2026)**

---

## 📌 Giới thiệu dự án

Hệ thống kết hợp giữa **Phân tích cơ bản định lượng (FA)** theo chuẩn CAMELS, **Mô hình định giá chuyên biệt cho ngân hàng** (Residual Income / Justified P/B & P/B Target), **Phân tích kỹ thuật (TA)** và **AI Explanation (Gemini)** nhằm đưa ra ma trận khuyến nghị đầu tư cá nhân hóa theo từng khẩu vị rủi ro.

### Luồng xử lý tổng thể

```
BCTC (Quý/Năm) & Giá OHLCV (vnstock)
                 │
                 ▼
       Data Ingestion & Cleaning
                 │
                 ├───────────────────────────────┐
                 ▼                               ▼
    Banking Ratio Engine & Scoring       Technical Analysis (TA)
    (CAMELS: Capital, Asset, ROE...)      (SMA, EMA, RSI, MACD)
                 │                               │
                 ▼                               ▼
      Bank Valuation Module              AI Qualitative Analysis
    (Justified P/B, Scenarios)           (Gemini Structured Output)
                 │                               │
                 └───────────────┬───────────────┘
                                 ▼
                 Recommendation Matrix (Cá nhân hóa)
               (Conservative / Balanced / Growth)
                                 │
                                 ▼
                     Reports & Web Dashboard
                 (Text Report & Streamlit App)
```

---

## 🎯 Đối chiếu các Module với Yêu cầu Nghiên cứu

| Yêu cầu nghiệp vụ | Module / File phụ trách | Mô tả chi tiết |
|---|---|---|
| **Dữ liệu BCTC 3 năm & OHLCV** | `data_ingestion/collect_vcb_data.py` | Lấy tự động BCTC 12 quý (2023 - 2025) và giá daily từ nguồn miễn phí (VCI / TCBS). |
| **Phân tích FA & Sức khỏe tài chính** | `scoring/score.py`<br>`ratio_engine/compute.py` | Bộ chỉ số chuyên biệt ngành ngân hàng: ETA, LDR, NIM, ROE, CIR, Lãi dự thu/Tổng tài sản. |
| **Định giá & Kịch bản** | `valuation/bank_valuation.py` | Định giá chuyên biệt cho bank bằng Justified P/B (Residual Income) & Target P/B với 3 kịch bản: Thận trọng (79.3k), Cơ sở (96.6k), Tích cực (113.8k). |
| **Phân tích Kỹ thuật (TA)** | `analysis/ta_module.py` | Xác định xu hướng MA (SMA20/50/200, EMA20), đo động lượng RSI14, tín hiệu phân kỳ MACD. |
| **Cá nhân hóa Khuyến nghị** | `analysis/recommendation_matrix.py` | Khuyến nghị hành động & phân bổ danh mục theo 3 khẩu vị: Thận trọng (Bảo toàn vốn), Cân bằng (GARP), Tăng trưởng (Momentum). |
| **AI Giải thích định tính** | `ai_analysis/analyze.py` | Tích hợp Google Gemini phân tích điểm mạnh, rủi ro, dự báo có cấu trúc JSON (không hallucinate số liệu). |
| **Báo cáo phân tích** | `reports/vcb_strategic_report_2026.txt`<br>`app_streamlit.py` | Xuất bản báo cáo chiến lược văn bản đầy đủ và giao diện Web Dashboard trực quan tương tác. |
| **Đánh giá & Kiểm thử** | `evaluation/metrics.py`<br>`tests/` | Đo lường độ chính xác (Accuracy, Precision, Recall, F1, MAE) và hệ thống Unit Test tự động. |

---

## 📁 Cấu trúc thư mục

```
vn30-fhs/
├── ai_analysis/                # Tích hợp LLM Gemini phân tích định tính
│   └── analyze.py
├── analysis/                   # Phân tích kỹ thuật & ma trận khuyến nghị
│   ├── recommendation_matrix.py
│   └── ta_module.py
├── app/                        # FastAPI Backend (Production API)
│   └── main.py
├── app_streamlit.py            # Streamlit Interactive Web Dashboard
├── data_ingestion/             # Thu thập BCTC và giá từ vnstock
│   └── collect_vcb_data.py
├── db/                         # Kết nối DB & truy vấn dữ liệu
├── evaluation/                 # Đo lường sai số & validation mô hình
│   └── metrics.py
├── ratio_engine/               # Tính toán các tỷ số tài chính ngân hàng
│   └── compute.py
├── reports/                    # Báo cáo đầu ra chi tiết
│   └── vcb_strategic_report_2026.txt
├── scoring/                    # Thuật toán chấm điểm sức khỏe tài chính
│   └── score.py
├── tests/                      # Unit tests cho các module
├── valuation/                  # Định giá chuyên biệt ngân hàng
│   └── bank_valuation.py
├── requirements.txt            # Thư viện phụ thuộc
└── README.md
```

---

## 🚀 Hướng dẫn Cài đặt & Chạy hệ thống

### 1. Chuẩn bị môi trường

```bash
# Tạo và kích hoạt virtual environment
python -m venv .venv
source .venv/bin/activate       # Trên Linux/macOS
# .venv\Scripts\Activate.ps1    # Trên Windows PowerShell

# Cài đặt các thư viện phụ thuộc
pip install -r requirements.txt

# Thiết lập biến môi trường
cp .env.example .env
# Điền GEMINI_API_KEY nếu sử dụng tính năng AI Analysis
```

### 2. Thu thập dữ liệu cổ phiếu VCB (BCTC & Giá)

```bash
python data_ingestion/collect_vcb_data.py
```
*Dữ liệu sẽ được lưu tự động vào `data/vcb/` để phục vụ phân tích offline & tái lập kết quả.*

### 3. Khởi chạy Web Dashboard tương tác (Streamlit)

Xem báo cáo trực quan với đầy đủ biểu đồ, kịch bản định giá và lựa chọn khẩu vị rủi ro:

```bash
streamlit run app_streamlit.py
```
Truy cập trình duyệt tại: `http://localhost:8501`

### 4. Khởi chạy FastAPI Backend

```bash
uvicorn app.main:app --reload
```
- API Docs Swagger: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 5. Chạy Unit Tests

```bash
pytest -v
```

---

## ⚖️ Tuyên bố miễn trừ trách nhiệm (Disclaimer)

Báo cáo và các công cụ trong dự án này được phát triển phục vụ mục đích **nghiên cứu học thuật và phân tích dữ liệu tài chính tự động**. Mọi thông tin dự báo, định giá và khuyến nghị trong hệ thống không cấu thành lời mời hay khuyến nghị đầu tư chứng khoán cho bất kỳ cá nhân hay tổ chức nào.
