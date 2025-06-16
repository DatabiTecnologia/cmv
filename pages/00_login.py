import streamlit as st
import mysql.connector
from dotenv import load_dotenv
import os

# Carrega variáveis do .env
load_dotenv()

# Configuração da página
st.set_page_config(page_title="Login - Rhino", layout="centered")

# Esconde sidebar, menu e rodapé apenas na página de login
st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Inicia sessão
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

st.title("🔐 Login - Sistema Rhino")
st.image("rhino_logo.png", use_container_width=True)

username = st.text_input("Usuário")
password = st.text_input("Senha", type="password")

if st.button("Entrar"):
    try:
        # Conecta com as variáveis do .env
        conn2 = mysql.connector.connect(
            host=os.environ.get("DB_HOST2"), #os.environ.get("DB_HOST2") / os.getenv("DB_HOST2")
            user=os.environ.get("DB_USER2"),# os.environ.get("DB_USER2") / os.getenv("DB_USER2")
            password=os.environ.get("DB_PASSWORD2"), # os.environ.get("DB_PASSWORD2") / os.getenv("DB_PASSWORD2")
            database=os.environ.get("DB_NAME2") # os.environ.get("DB_NAME2")/os.getenv("DB_NAME2")
        )
        cursor = conn2.cursor()

        query = """
            SELECT UserId, Password
            FROM Users
            WHERE empresa = 'Rhino' AND UserId = %s AND PASSWORD = %s
        """
        cursor.execute(query, (username, password))
        result = cursor.fetchone()

        cursor.close()
        conn2.close()

        if result:
            user_id, nome = result
            st.session_state['logged_in'] = True
            st.session_state['user_id'] = user_id
            st.session_state['Password'] = nome
            st.success(f"Bem-vindo, {nome}!")
            st.switch_page("pages/01_home.py")  # Redireciona para home
        else:
            st.error("Usuário ou senha incorretos.")

    except mysql.connector.Error as e:
        st.error(f"Erro na conexão: {e}")
