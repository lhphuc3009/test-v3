
import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

import rma_ai
import rma_query_templates
import rma_utils

# Load dữ liệu người dùng từ file cấu hình
with open("users.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

# Khởi tạo Authenticator
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

# Sử dụng login() KHÔNG truyền tham số (chuẩn mới)
name, authentication_status, username = authenticator.login()

# Kiểm tra trạng thái đăng nhập
if authentication_status is False:
    st.error("❌ Sai tài khoản hoặc mật khẩu.")
elif authentication_status is None:
    st.warning("⏳ Vui lòng đăng nhập để tiếp tục.")
elif authentication_status:
    authenticator.logout("Đăng xuất", "sidebar")
    st.sidebar.success(f"Xin chào {name} 👋")

    # Phân quyền người dùng
    role = config["credentials"]["usernames"].get(username, {}).get("role", "guest")
    is_admin = role == "admin"

    # Giao diện chính
    st.title("🛠️ Trợ Lý Bảo Hành - Network Hub")

    # Tải dữ liệu
    df = rma_utils.get_data_from_google_sheet()

    # Bộ lọc dữ liệu
    with st.sidebar:
        st.header("📅 Bộ lọc thời gian")
        year_options = st.multiselect("Chọn năm", df["year"].unique())
        month_options = st.multiselect("Chọn tháng", df["month"].unique())
        quarter_options = st.multiselect("Chọn quý", df["quarter"].unique())
        from_date = st.date_input("Từ ngày")
        to_date = st.date_input("Đến ngày")

        df = rma_utils.filter_data_by_date(df, year_options, month_options, quarter_options, from_date, to_date)

        st.header("🔍 Bộ lọc nâng cao")
        customer_filter = st.text_input("Lọc theo khách hàng")
        model_filter = st.text_input("Lọc theo model")

        df = rma_utils.filter_data_by_column_values(df, "khách hàng", customer_filter)
        df = rma_utils.filter_data_by_column_values(df, "model", model_filter)

    # Tabs chức năng
    tab = st.radio("Chọn chức năng", ["🔎 Truy vấn nhanh", "💬 Hỏi trợ lý AI"])

    if tab == "🔎 Truy vấn nhanh":
        query_list = rma_query_templates.get_all_queries()
        selected_query = st.selectbox("Chọn truy vấn", list(query_list.keys()))
        if st.button("Thực hiện"):
            result = query_list[selected_query](df)
            st.markdown(f"### 🔹 Kết quả: {selected_query}")
            st.dataframe(result)

    elif tab == "💬 Hỏi trợ lý AI":
        question = st.text_area("Nhập câu hỏi", placeholder="VD: Khách hàng A gửi nhiều sản phẩm nào nhất?")
        if st.button("Gửi"):
            if question.strip():
                response = rma_ai.process_question(question, df)
                st.markdown("### 🤖 Trợ lý AI trả lời:")
                st.write(response)
            else:
                st.warning("Vui lòng nhập câu hỏi.")

    # Tuỳ chọn riêng cho quản trị viên
    if is_admin:
        st.sidebar.markdown("---")
        st.sidebar.markdown("🔐 **Quản trị viên:**")
        st.sidebar.selectbox("Chọn mô hình GPT", ["gpt-3.5-turbo", "gpt-4", "gpt-4o"])
