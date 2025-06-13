import streamlit as st
import mysql.connector
from datetime import datetime
import pandas as pd

def conectar():
    return mysql.connector.connect(
        host='151.243.0.64',
        user='Usrflym_2265',
        password='FsyMdfYB74_p0',
        database='flymetrics'
    )

def inserir_dados(data, faturamento, pedidos, markup, custo, compras, qtd_dev, valor_dev, filial):
    try:
        conn = conectar()
        cursor = conn.cursor()
        sql = '''
            INSERT INTO bf_cmv 
            (dia_ontem, faturamento, qtd_pedidos, markup, custo, compras, qtd_devolucao, valor_devolucao, filial)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        '''
        cursor.execute(sql, (data, faturamento, pedidos, markup, custo, compras, qtd_dev, valor_dev, filial))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir dados CMV: {e}")
        return False

def inserir_estoque(data, valor_estoque, filial):
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT COUNT(*) FROM bf_estoque_rhino
            WHERE dia_ontem = %s AND filial = %s
        ''', (data, filial))
        existe = cursor.fetchone()[0]

        if existe:
            cursor.execute('''
                UPDATE bf_estoque_rhino
                SET valor_estoque = %s, data_registro = CURRENT_TIMESTAMP
                WHERE dia_ontem = %s AND filial = %s
            ''', (valor_estoque, data, filial))
        else:
            cursor.execute('''
                INSERT INTO bf_estoque_rhino (dia_ontem, valor_estoque, filial)
                VALUES (%s, %s, %s)
            ''', (data, valor_estoque, filial))

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir/atualizar estoque: {e}")
        return False

def atualizar_cmv_corrigido(df_corrigido):
    try:
        conn = conectar()
        cursor = conn.cursor()
        for index, row in df_corrigido.iterrows():
            sql = '''
                UPDATE bf_cmv
                SET faturamento = %s, qtd_pedidos = %s, markup = %s, custo = %s, compras = %s,
                    qtd_devolucao = %s, valor_devolucao = %s
                WHERE dia_ontem = %s AND filial = %s
            '''
            cursor.execute(sql, (
                row['faturamento'], row['qtd_pedidos'], row['markup'], row['custo'], row['compras'],
                row['qtd_devolucao'], row['valor_devolucao'], row['dia_ontem'], row['filial']
            ))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar CMV corrigido: {e}")
        return False

def mostrar_correcao_dados():
    st.subheader("✏️ Correção de CMV")
    query = '''
        SELECT dia_ontem, faturamento, qtd_pedidos, markup, custo, compras, valor_devolucao, qtd_devolucao, filial
        FROM bf_cmv ORDER BY dia_ontem DESC LIMIT 50
    '''
    try:
        conn = conectar()
        df = pd.read_sql(query, conn)
        conn.close()
        if df.empty:
            st.info("Nenhum dado encontrado para correção.")
            return
        df_editado = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="editor_cmv")
        if st.button("💾 Salvar Correções de CMV"):
            sucesso = atualizar_cmv_corrigido(df_editado)
            if sucesso:
                st.success("✅ Dados do CMV atualizados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao carregar dados do CMV: {e}")

def atualizar_estoque_corrigido(df_corrigido):
    try:
        conn = conectar()
        cursor = conn.cursor()
        for index, row in df_corrigido.iterrows():
            sql = '''
                UPDATE bf_estoque_rhino
                SET valor_estoque = %s, data_registro = CURRENT_TIMESTAMP
                WHERE dia_ontem = %s AND filial = %s
            '''
            cursor.execute(sql, (row['valor_estoque'], row['dia_ontem'], row['filial']))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar estoque corrigido: {e}")
        return False

def mostrar_correcao_estoque():
    st.subheader("✏️ Correção de Estoque")
    col1, col2 = st.columns(2)
    with col1:
        data_filtro = st.date_input("📅 Filtrar por data (opcional)", value=None, key="filtro_data_estoque")
    with col2:
        filial_filtro = st.selectbox("🏢 Filtrar por filial", ["Todas", "RJ", "SP", "ES"], key="filtro_filial_estoque")

    query = '''
        SELECT dia_ontem, valor_estoque, filial FROM bf_estoque_rhino
    '''
    condicoes = []
    parametros = []

    if data_filtro:
        condicoes.append("dia_ontem = %s")
        parametros.append(data_filtro)
    if filial_filtro != "Todas":
        condicoes.append("filial = %s")
        parametros.append(filial_filtro)
    if condicoes:
        query += " WHERE " + " AND ".join(condicoes)
    query += " ORDER BY dia_ontem DESC LIMIT 50"

    try:
        conn = conectar()
        df = pd.read_sql(query, conn, params=parametros)
        conn.close()
        if df.empty:
            st.info("Nenhum dado de estoque encontrado com os filtros aplicados.")
            return
        df_editado = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="editor_estoque")
        if st.button("💾 Salvar Correções de Estoque"):
            sucesso = atualizar_estoque_corrigido(df_editado)
            if sucesso:
                st.success("✅ Estoque atualizado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao carregar dados de estoque: {e}")

def mostrar_importador():
    st.title("📥 Importador Manual de Dados - CMV e Estoque")
    senha = st.text_input("🔐 Digite a senha de administrador:", type="password")
    if senha == "rhino123":
        st.success("✅ Acesso autorizado!")

        tab1, tab2, tab3 = st.tabs(["📥 Inserir Dados", "✏️ Corrigir CMV", "✏️ Corrigir Estoque"])

        with tab1:
            with st.form("form_insercao"):
                data_input = st.text_input("Data (formato: AAAA-MM-DD)", value=datetime.today().strftime("%Y-%m-%d"))
                faturamento = st.number_input("Faturamento (R$)", step=0.01)
                pedidos = st.number_input("Quantidade de Pedidos", step=1)
                markup = st.number_input("Markup (%)", step=0.01)
                custo = st.number_input("Custo (R$)", step=0.01)
                compras = st.number_input("Compras (R$)", step=0.01)
                qtd_dev = st.number_input("Quantidade Devolvida", step=1)
                valor_dev = st.number_input("Valor Devolvido (R$)", step=0.01)
                valor_estoque = st.number_input("Valor de Estoque (R$)", step=0.01)
                filial = st.selectbox("Filial", ["RJ", "SP", "ES"])

                enviado = st.form_submit_button("Salvar dados")

                if enviado:
                    try:
                        data_formatada = datetime.strptime(data_input, "%Y-%m-%d").date()
                        data_str = str(data_formatada)
                        sucesso1 = inserir_dados(data_str, faturamento, pedidos, markup, custo, compras, qtd_dev, valor_dev, filial)
                        sucesso2 = inserir_estoque(data_str, valor_estoque, filial)
                        if sucesso1 and sucesso2:
                            st.success("✅ Dados inseridos/atualizados com sucesso!")
                    except ValueError:
                        st.error("❌ Formato de data inválido! Use o formato AAAA-MM-DD (ex: 2025-05-22)")

        with tab2:
            mostrar_correcao_dados()

        with tab3:
            mostrar_correcao_estoque()
    else:
        st.warning("⚠️ Digite a senha para acessar o formulário.")

if __name__ == '__main__':
    mostrar_importador()