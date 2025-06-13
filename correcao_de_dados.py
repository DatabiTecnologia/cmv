import streamlit as st
import mysql.connector
from datetime import datetime

def conectar():
    return mysql.connector.connect(
        host='151.243.0.64',
        user='Usrflym_2265',
        password='FsyMdfYB74_p0',
        database='flymetrics'
    )

def buscar_dados(limit=20):
    try:
        conn = conectar()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f'''
            SELECT id, dia_ontem, faturamento, qtd_pedidos, markup, custo, compras, qtd_devolucao, valor_devolucao, filial 
            FROM bf_cmv 
            ORDER BY dia_ontem DESC LIMIT {limit}
        ''')
        resultados = cursor.fetchall()
        cursor.close()
        conn.close()
        return resultados
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return []

def atualizar_dado(id, campo, valor):
    try:
        conn = conectar()
        cursor = conn.cursor()
        sql = f"UPDATE bf_cmv SET {campo} = %s WHERE id = %s"
        cursor.execute(sql, (valor, id))
        conn.commit()
        cursor.close()
        conn.close()
        st.success("✅ Dados atualizados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao atualizar dado: {e}")

def excluir_linha(id):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM bf_cmv WHERE id = %s AND origem = 'planilha'", (id,))
        conn.commit()
        cursor.close()
        conn.close()
        st.success("✅ Linha excluída com sucesso!")
    except Exception as e:
        st.error(f"Erro ao excluir linha: {e}")

st.title("Correção de Dados")

st.write("### Últimos registros (até 20)")

dados = buscar_dados(20)

if not dados:
    st.info("Nenhum dado encontrado.")
else:
    for registro in dados:
        with st.expander(f"ID: {registro['id']} - Data: {registro['dia_ontem']} - Filial: {registro['filial']}"):
            col1, col2 = st.columns(2)

            with col1:
                faturamento = st.number_input("Faturamento", value=registro['faturamento'], key=f"fatu_{registro['id']}")
                pedidos = st.number_input("Qtd Pedidos", value=registro['qtd_pedidos'], step=1, key=f"ped_{registro['id']}")
                markup = st.number_input("Markup", value=registro['markup'], format="%.2f", key=f"mark_{registro['id']}")
                custo = st.number_input("Custo", value=registro['custo'], format="%.2f", key=f"custo_{registro['id']}")

            with col2:
                compras = st.number_input("Compras", value=registro['compras'], format="%.2f", key=f"comp_{registro['id']}")
                qtd_dev = st.number_input("Qtd Devolução", value=registro['qtd_devolucao'], step=1, key=f"qtddev_{registro['id']}")
                valor_dev = st.number_input("Valor Devolução", value=registro['valor_devolucao'], format="%.2f", key=f"valdev_{registro['id']}")
                filial = st.text_input("Filial", value=registro['filial'], key=f"filial_{registro['id']}")

            btn_atualizar = st.button("Atualizar", key=f"btn_upd_{registro['id']}")
            btn_excluir = st.button("Excluir (apenas dados importados por planilha)", key=f"btn_del_{registro['id']}")

            if btn_atualizar:
                # Atualiza os campos editados
                atualizar_dado(registro['id'], 'faturamento', faturamento)
                atualizar_dado(registro['id'], 'qtd_pedidos', pedidos)
                atualizar_dado(registro['id'], 'markup', markup)
                atualizar_dado(registro['id'], 'custo', custo)
                atualizar_dado(registro['id'], 'compras', compras)
                atualizar_dado(registro['id'], 'qtd_devolucao', qtd_dev)
                atualizar_dado(registro['id'], 'valor_devolucao', valor_dev)
                atualizar_dado(registro['id'], 'filial', filial)

            if btn_excluir:
                excluir_linha(registro['id'])
                st.experimental_rerun()
