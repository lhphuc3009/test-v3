import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import requests
import io

from rma_ai import query_openai
from rma_utils import bo_loc_da_nang, ensure_time_columns, find_col
import rma_query_templates

load_dotenv()

st.set_page_config(page_title="Trợ lý RMA AI", layout="wide")
st.title("🧠 Trợ lý RMA – AI Phân Tích Dữ Liệu Bảo Hành")

# === 1. Load dữ liệu từ Google Sheet ===
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1fWFLZWyCAXn_B8jcZ0oY4KhJ8krbLPsH/export?format=csv"

def read_google_sheet(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.content.decode("utf-8")))
            df.columns = [col.strip() for col in df.columns]
            return ensure_time_columns(df)
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu: {e}")
    return pd.DataFrame()

data = read_google_sheet(GOOGLE_SHEET_URL)

if data.empty:
    st.stop()

# === 2. Tạo tabs giao diện mới ===
tab1, tab2, tab3 = st.tabs(["📊 Dữ liệu RMA", "🤖 Trợ lý AI", "📋 Báo cáo & Thống kê"])

# === TAB 1: Xem và lọc dữ liệu ===
with tab1:
    st.header("📊 Bảng dữ liệu và bộ lọc")
    data_filtered = bo_loc_da_nang(data)

    with st.expander("🔍 Tìm kiếm nhanh"):
        search_mode = st.radio("Chọn loại tìm kiếm:", ["🔎 Theo khách hàng", "🔎 Theo sản phẩm", "🔎 Theo số serial"], horizontal=True)
        keyword = st.text_input("Nhập từ khóa cần tìm:")

        # GỢI Ý KHỚP
        if keyword:
            if search_mode == "🔎 Theo khách hàng":
                col_name = find_col(data.columns, "khách hàng")
            elif search_mode == "🔎 Theo sản phẩm":
                col_name = find_col(data.columns, "sản phẩm")
            else:
                col_name = None

            if col_name:
                all_values = data[col_name].dropna().unique().tolist()
                suggestions = [s for s in all_values if keyword.lower() in s.lower()]
                if suggestions:
                    st.markdown('<div style="font-size: 0.85rem; color: #aaa;"><b>🔎 Gợi ý khớp:</b></div>', unsafe_allow_html=True)
                    for s in suggestions[:5]:
                        st.markdown(f'<div style="font-size: 0.85rem; color: #ccc;">• {s}</div>', unsafe_allow_html=True)

        # LỌC DỮ LIỆU
        if keyword:
            keyword_lower = keyword.lower()
            if search_mode == "🔎 Theo khách hàng":
                col_name = find_col(data_filtered.columns, "khách hàng")
            elif search_mode == "🔎 Theo sản phẩm":
                col_name = find_col(data_filtered.columns, "sản phẩm")
            else:
                col_name = find_col(data_filtered.columns, "serial")

            if col_name:
                data_filtered = data_filtered[
                    data_filtered[col_name].astype(str).str.lower().str.contains(keyword_lower, na=False)
                ]
            else:
                st.warning("Không tìm thấy cột phù hợp để tìm kiếm.")

    # KẾT QUẢ VÀ XUẤT FILE
    if keyword:
        st.markdown(f"**Số dòng sau khi lọc:** {len(data_filtered)} / {len(data)}")
        st.dataframe(data_filtered, use_container_width=True)

        # Nút tải kết quả Excel
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            data_filtered.to_excel(writer, index=False, sheet_name="RMA_Loc")
            
        buffer.seek(0)
        
        st.download_button(
            label="📥 Tải kết quả Excel",
            data=buffer.getvalue(),
            file_name="RMA_Ketqua_Loc.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# === TAB 2: Hỏi AI ===
with tab2:
    st.header("🤖 Trợ lý AI – Hỏi đáp theo dữ liệu")
    question = st.text_area("Nhập câu hỏi tự nhiên (tiếng Việt):")

    max_rows = st.slider("Giới hạn số dòng gửi AI", 50, 500, 200)
    df_ai = data_filtered.tail(max_rows)

    if st.button("💬 Gửi câu hỏi"):
        csv_data = df_ai.to_csv(index=False)
        api_key = os.getenv("OPENAI_API_KEY")
        ai_response, prompt_used = query_openai(
            user_question=question,
            df_summary=df_ai,
            api_key=api_key
        )
        st.markdown("### 📌 Kết quả:")
        st.write(ai_response)

# === TAB 3: Truy vấn thống kê nhanh ===
with tab3:
    st.header("📋 Thống kê theo mẫu")
    options = [
        "Tổng số sản phẩm tiếp nhận theo tháng/năm/quý",
        "Tỷ lệ sửa chữa thành công theo tháng/năm/quý",
        "Danh sách sản phẩm chưa sửa xong",
        "Top 5 khách hàng gửi nhiều nhất",
        "Top 5 sản phẩm bảo hành nhiều nhất"
    ]
    selected = st.selectbox("Chọn loại thống kê:", options)

    if selected == options[0]:
        group_by = st.selectbox("Nhóm theo:", ["Năm", "Tháng", "Quý"])
        title, df_out = rma_query_templates.query_1_total_by_group(data_filtered, group_by)
        st.subheader(title)
        st.dataframe(df_out)
    elif selected == options[1]:
        group_by = st.selectbox("Nhóm theo:", ["Năm", "Tháng", "Quý"])
        title, df_out = rma_query_templates.query_2_success_rate_by_group(data_filtered, group_by)
        st.subheader(title)
        st.dataframe(df_out)
    elif selected == options[2]:
        title, df_out = rma_query_templates.query_3_unrepaired_products(data_filtered)
        st.subheader(title)
        st.dataframe(df_out)
    elif selected == options[3]:
        title, df_out = rma_query_templates.query_4_top_customers(data_filtered)
        st.subheader(title)
        st.dataframe(df_out)
    elif selected == options[4]:
        title, df_out = rma_query_templates.query_7_top_products(data_filtered)
        st.subheader(title)
        st.dataframe(df_out)
