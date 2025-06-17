
import streamlit as st
import bcrypt
import yaml
from yaml.loader import SafeLoader

import rma_ai
import rma_query_templates
import rma_utils

# Đọc file users.yaml
with open("users.yaml", "r") as f:
    config = yaml.load(f, Loader=SafeLoader)

users = config["credentials"]["usernames"]

# Form đăng nhập
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""

if not st.session_state.logged_in:
    st.title("🔐 Đăng nhập hệ thống")
    with st.form("login_form"):
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        submitted = st.form_submit_button("Đăng nhập")

        if submitted:
            user = users.get(username)
            if user:
                hashed_pw = user["password"].encode("utf-8")
                if bcrypt.checkpw(password.encode("utf-8"), hashed_pw):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.role = user.get("role", "guest")
                    st.experimental_rerun()
                else:
                    st.error("❌ Sai mật khẩu")
            else:
                st.error("❌ Không tồn tại tài khoản")
    st.stop()

# Sau khi đăng nhập
st.sidebar.success(f"Xin chào {users[st.session_state.username]['name']} 👋")
if st.sidebar.button("Đăng xuất"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.experimental_rerun()

is_admin = st.session_state.role == "admin"

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

# Chức năng riêng cho admin
if is_admin:
    st.sidebar.markdown("---")
    st.sidebar.markdown("🔐 **Quản trị viên:**")
    st.sidebar.selectbox("Chọn mô hình GPT", ["gpt-3.5-turbo", "gpt-4", "gpt-4o"])
