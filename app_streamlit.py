"""Streamlit Web Dashboard — Báo Cáo Phân Tích & Định Giá Chiến Lược VCB (Vietcombank)
Mốc thời điểm phân tích: 01/01/2026 | Deadline Cuối tháng
Chạy app: streamlit run app_streamlit.py
"""

import streamlit as st
import pandas as pd
import numpy as np

# Thiết lập trang
st.set_page_config(
    page_title="VCB Investment & Health Analysis (01/01/2026)",
    page_icon="",
    layout="wide",
)

st.title("Báo Cáo Phân Tích & Định Giá Chiến Lược: VCB (Vietcombank)")
st.caption("Mốc phân tích: **01/01/2026** | Hệ thống VN30 Financial Health Scoring")

# Sidebar - Cá nhân hóa nhà đầu tư
st.sidebar.header("Cá Nhân Hóa Nhà Đầu Tư")
investor_profile = st.sidebar.selectbox(
    "Chọn Khẩu Vị Rủi Ro Của Bạn:",
    ["Thận Trọng (Conservative)", "Cân Bằng (Balanced)", "Tăng Trưởng (Growth)"],
    index=1,
)

target_holding_period = st.sidebar.selectbox(
    "Thời Gian Nắm Giữ Dự Kiến:",
    ["Dưới 6 tháng (Ngắn hạn)", "6 - 12 tháng (Trung hạn)", "Trên 1 năm (Dài hạn)"],
    index=1,
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Quy định pháp lý:** Báo cáo được xây dựng tự động cho mục đích nghiên cứu & học thuật. "
    "Không cấu thành lời mời chào hay khuyến nghị đầu tư cá nhân hóa."
)

# Tabs chính
tab1, tab2, tab3, tab4 = st.tabs([
    "Sức Khỏe Tài Chính (FA)",
    "Định Giá & Kịch Bản",
    "Phân Tích Kỹ Thuật (TA)",
    "Khuyến Nghị Cá Nhân Hóa",
])

with tab1:
    st.subheader("1. Đánh Giá Sức Khỏe Tài Chính VCB (Chuẩn CAMELS)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Financial Health Score", "89.2 / 100", "+2.4 so với TB ngành")
    col2.metric("An Toàn Vốn (ETA)", "9.35%", "An toàn cao")
    col3.metric("Khả Năng Sinh Lời (ROE)", "23.4%", "Dẫn đầu hệ thống")
    col4.metric("Chất Lượng Tài Sản (Lãi dự thu/TTS)", "0.43%", "Rất sạch (< 1%)")

    st.markdown("#### Bảng Chỉ Số Chi Tiết Qua Các Quý (2024 - 2025)")
    df_metrics = pd.DataFrame({
        "Kỳ báo cáo": ["2024-Q3", "2024-Q4", "2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4"],
        "ROE (% năm hóa)": [18.0, 17.5, 17.0, 16.5, 16.2, 23.4],
        "ROA (% năm hóa)": [1.8, 1.6, 1.6, 1.6, 1.5, 2.2],
        "NIM (% năm hóa)": [3.1, 2.8, 2.6, 2.6, 2.6, 3.0],
        "LDR (%)": [77.5, 78.2, 79.0, 78.5, 77.8, 78.0],
        "CIR (%)": [34.5, 39.8, 32.7, 33.7, 33.4, 32.0],
    })
    st.dataframe(df_metrics, use_container_width=True)

with tab2:
    st.subheader("2. Định Giá Cổ Phiếu VCB Đến Mốc 01/01/2026")
    st.markdown("Phương pháp chủ đạo: **Justified P/B (Residual Income)** và **P/B Lịch Sử 3 Năm**.")

    col_val1, col_val2, col_val3 = st.columns(3)
    with col_val1:
        st.error("### Kịch Bản Thận Trọng")
        st.write("**Giả định:** Tín dụng chậm lại, ROE đạt 16.5%")
        st.write("**Target P/B:** 2.30x")
        st.metric("Giá mục tiêu", "79,350 VND", "-5.5%")

    with col_val2:
        st.success("### Kịch Bản Cơ Sở (Base)")
        st.write("**Giả định:** Tín dụng hồi phục, ROE đạt 20.5%, NIM 3.0%")
        st.write("**Target P/B:** 2.80x")
        st.metric("Giá mục tiêu", "96,600 VND", "+15.0%")

    with col_val3:
        st.info("### Kịch Bản Tích Cực (Bull)")
        st.write("**Giả định:** Hoàn tất phát hành riêng lẻ 6.5%, ROE > 23%")
        st.write("**Target P/B:** 3.30x")
        st.metric("Giá mục tiêu", "113,850 VND", "+35.5%")

with tab3:
    st.subheader("3. Xu Hướng Kỹ Thuật (TA) Tại 01/01/2026")
    col_ta1, col_ta2 = st.columns(2)
    with col_ta1:
        st.write("#### Các Tín Hiệu Kỹ Thuật Quan Trọng")
        st.write("- **Xu hướng trung - dài hạn:** Cổ phiếu nằm trên SMA50 và SMA200 (Uptrend bền vững).")
        st.write("- **RSI (14):** Đạt **54.2** — Trạng thái cân bằng tích lũy, còn nhiều dư địa tăng.")
        st.write("- **MACD:** Giao cắt dương (MACD > Signal Line).")
    with col_ta2:
        st.write("#### Các Vùng Giá Trọng Yếu")
        st.write("- **Hỗ trợ 1:** 81,000 VND (Đường SMA50)")
        st.write("- **Hỗ trợ cứng:** 78,500 VND (Đường SMA200)")
        st.write("- **Kháng cự ngắn hạn:** 88,000 VND")
        st.write("- **Kháng cự tâm lý:** 95,000 - 100,000 VND")

with tab4:
    st.subheader(f"4. Chiến Lược Cá Nhân Hóa Dành Cho Bạn: {investor_profile}")
    if "Thận Trọng" in investor_profile:
        st.success("### Khuyến nghị: MUA TÍCH LŨY DÀI HẠN")
        st.write("- **Tỷ trọng danh mục:** 25% - 30% (Cổ phiếu trụ cột, nắm giữ phòng thủ).")
        st.write("- **Luận điểm:** VCB là ngân hàng có bảng cân đối sạch nhất Việt Nam, tỷ lệ bao nợ xấu LLR vượt trội, cổ tức ổn định.")
    elif "Cân Bằng" in investor_profile:
        st.info("### Khuyến nghị: MUA VÀ NẮM GIỮ CHO NĂM 2026")
        st.write("- **Giá mục tiêu cơ sở:** 96,600 VND (Biên lợi nhuận kỳ vọng: +15.0%).")
        st.write("- **Tỷ trọng danh mục:** 15% - 20%.")
        st.write("- **Luận điểm:** Đón đầu chu kỳ nới lỏng tiền tệ, VCB có chi phí vốn rẻ nhất sẽ nới rộng biên lãi ròng.")
    else:
        st.warning("### Khuyến nghị: MUA LƯỚT SÓNG THEO NHỊP TÍCH LŨY")
        st.write("- **Vùng mua gom:** 81,000 - 83,500 VND.")
        st.write("- **Điểm chốt lời ngắn hạn:** 92,000 - 95,000 VND.")
        st.write("- **Ngưỡng dừng lỗ:** Khi đóng cửa dưới mốc 78,500 VND (gãy SMA200).")
