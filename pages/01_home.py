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

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📈 Evolução do Faturamento",
            "📦 Evolução das Compras",
            "💰 Faturamento vs Custo",
            "📊 Faturamento vs Compras",
            "🧠 Análise Inteligente",
            "🔮 Previsão e IA"
        ])

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

        with tab3:
            fig = go.Figure()
            for filial in df['filial'].unique():
                dados_filial = df[df['filial'] == filial]
                fig.add_trace(go.Scatter(x=dados_filial['ano_mes'], y=dados_filial['total_faturamento'], mode='lines', name=f"Faturamento - {filial}"))
                fig.add_trace(go.Scatter(x=dados_filial['ano_mes'], y=dados_filial['total_custo'], mode='lines', name=f"Custo - {filial}"))
            fig.update_layout(title="Faturamento vs Custo por Filial", xaxis_title="Ano/Mês", yaxis_title="Valores", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

        with tab4:
            fig = go.Figure()
            for filial in df['filial'].unique():
                dados_filial = df[df['filial'] == filial]
                fig.add_trace(go.Scatter(x=dados_filial['ano_mes'], y=dados_filial['total_faturamento'], mode='lines', name=f"Faturamento - {filial}"))
                fig.add_trace(go.Scatter(x=dados_filial['ano_mes'], y=dados_filial['total_compras'], mode='lines', name=f"Compras - {filial}"))
            fig.update_layout(title="Faturamento vs Compras por Filial", xaxis_title="Ano/Mês", yaxis_title="Valores", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

        with tab5:
            st.markdown("### 🧠 Análise Inteligente da Performance por Filial")
            for filial in df['filial'].unique():
                dados = df[df['filial'] == filial]
                total_faturamento = dados['total_faturamento'].sum()
                total_custo = dados['total_custo'].sum()
                total_compras = dados['total_compras'].sum()
                lucro = total_faturamento - total_custo
                margem_lucro = (lucro / total_faturamento * 100) if total_faturamento > 0 else 0
                tendencia = "positiva 📈" if margem_lucro > 10 else ("neutra ➖" if margem_lucro > 0 else "negativa 📉")

                recomendacao = ""
                if margem_lucro < 5:
                    recomendacao = "🔍 Reduzir custos operacionais e revisar fornecedores."
                elif total_compras > total_faturamento * 0.8:
                    recomendacao = "📦 Verificar excesso de compras em relação às vendas."
                elif margem_lucro > 20:
                    recomendacao = "💡 Boa margem! Avaliar expansão ou investimento."
                else:
                    recomendacao = "📊 Manter monitoramento e buscar otimização de margem."

                st.markdown(f"**📍 Filial: {filial}**")
                st.markdown(f"- Faturamento total: R$ {total_faturamento:,.2f}")
                st.markdown(f"- Custo total: R$ {total_custo:,.2f}")
                st.markdown(f"- Compras totais: R$ {total_compras:,.2f}")
                st.markdown(f"- Lucro estimado: R$ {lucro:,.2f} ({margem_lucro:.2f}%)")
                st.markdown(f"- Tendência atual: **{tendencia}**")
                st.markdown(f"- Recomendação da IA: {recomendacao}")
                st.markdown("---")

        with tab6:
            st.markdown("### 🔮 Previsão Inteligente de Desempenho")
            st.info("Em breve: previsões futuras baseadas em aprendizado de máquina! 🚀")

    else:
        st.info("Ainda não há dados para exibir no resumo anual.")

except Exception as e:
    st.error(f"Erro ao carregar dados do resumo anual: {e}")
