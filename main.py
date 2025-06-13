import streamlit as st

st.set_page_config(
    page_title="CMV RHINO",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Redireciona automaticamente para a página de login
st.switch_page("pages/00_login.py")
