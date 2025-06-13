import streamlit as st
import mysql.connector
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Home - Rhino", layout="wide")

LIMIT_HISTORICO = 20

# Função de conexão com o banco de dados
def conectar():
    return mysql.connector.connect(
        host='151.243.0.64',
        user='Usrflym_2265',
        password='FsyMdfYB74_p0',
        database='flymetrics'
    )

# Sidebar
st.sidebar.title("📊 Menu")
st.sidebar.markdown("✔️ Relatórios\n✔️ Painel de vendas\n✔️ Administração")

# Título de boas-vindas
st.title(f"Olá, {st.session_state.get('nome', 'Usuário')} 👋")
st.write("Seja bem-vindo à área restrita do sistema da Rhino.")

# Resumo CMV Anual
st.markdown("---")
st.subheader("📈 Resumo CMV Anual")

try:
    conn = conectar()
    df = pd.read_sql("""
        SELECT 
            YEAR(dia_ontem) AS ano, 
            MONTH(dia_ontem) AS mes, 
            filial,
            SUM(faturamento) AS total_faturamento, 
            SUM(custo) AS total_custo,
            SUM(compras) AS total_compras
        FROM bf_cmv
        GROUP BY ano, mes, filial
        ORDER BY ano, mes
    """, conn)
    conn.close()

    if not df.empty:
        df['mes_nome'] = df['mes'].apply(lambda x: datetime(1900, x, 1).strftime('%b'))
        df['ano_mes'] = df['ano'].astype(str) + '-' + df['mes'].astype(str).str.zfill(2)

        tab1, tab2 = st.tabs(["📈 Evolução do Faturamento", "📦 Evolução das Compras"])

        with tab1:
            fig = go.Figure()
            for filial in df['filial'].unique():
                dados_filial = df[df['filial'] == filial]
                fig.add_trace(go.Scatter(x=dados_filial['ano_mes'], y=dados_filial['total_faturamento'], mode='lines+markers', name=filial))
            fig.update_layout(title="Evolução do Faturamento por Filial", xaxis_title="Ano/Mês", yaxis_title="Faturamento", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            fig = go.Figure()
            for filial in df['filial'].unique():
                dados_filial = df[df['filial'] == filial]
                fig.add_trace(go.Scatter(x=dados_filial['ano_mes'], y=dados_filial['total_compras'], mode='lines+markers', name=filial))
            fig.update_layout(title="Evolução das Compras por Filial", xaxis_title="Ano/Mês", yaxis_title="Compras", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Ainda não há dados para exibir no resumo anual.")

except Exception as e:
    st.error(f"Erro ao carregar dados do resumo anual: {e}")
