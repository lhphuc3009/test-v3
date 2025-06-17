import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

st.set_page_config(page_title="Demo Login", page_icon="🔐")

with open("auth_config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    hashed_passwords=True
)

name, authentication_status, username = authenticator.login("Login", location="main")

if authentication_status:
    st.success(f"Chào mừng {name}!")
    authenticator.logout("Đăng xuất", "sidebar")
elif authentication_status is False:
    st.error("Sai tên đăng nhập hoặc mật khẩu")
elif authentication_status is None:
    st.warning("Vui lòng nhập thông tin đăng nhập")
