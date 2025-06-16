import streamlit as st
import mysql.connector
from datetime import datetime
import pandas as pd
from io import BytesIO
import os
from dotenv import load_dotenv
load_dotenv()


LIMIT_HISTORICO = 20

host = os.environ.get("DB_HOST")# os.environ.get("DB_HOST") / host = os.getenv("DB_HOST")
user = os.environ.get("DB_USER")# os.environ.get("DB_USER") / os.getenv("DB_USER")
password = os.environ.get("DB_PASSWORD")# os.environ.get("DB_PASSWORD") / os.getenv("DB_PASSWORD")
database = os.environ.get("DB_NAME")# os.environ.get("DB_NAME")/os.getenv("DB_NAME")

def conectar():
    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

def inserir_dados(dia_ontem, faturamento, qtd_pedidos, markup, custo, compras, qtd_devolucao, valor_devolucao, filial):
    try:
        conn = conectar()
        cursor = conn.cursor()

        sql = """
            INSERT INTO bf_cmv (
                dia_ontem, faturamento, qtd_pedidos, markup, custo, compras,
                qtd_devolucao, valor_devolucao, filial
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                faturamento = VALUES(faturamento),
                qtd_pedidos = VALUES(qtd_pedidos),
                markup = VALUES(markup),
                custo = VALUES(custo),
                compras = VALUES(compras),
                qtd_devolucao = VALUES(qtd_devolucao),
                valor_devolucao = VALUES(valor_devolucao)
        """
        valores = (
            dia_ontem, faturamento, qtd_pedidos, markup, custo, compras,
            qtd_devolucao, valor_devolucao, filial
        )
        cursor.execute(sql, valores)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir dados CMV: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


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
                INSERT INTO bf_estoque_rhino (dia_ontem, valor_estoque, filial, origem)
                VALUES (%s, %s, %s, 'planilha')
            ''', (data, valor_estoque, filial))

        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir/atualizar estoque: {e}")
        return False

def excluir_linha_cmv(id):
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

def baixar_modelo():
    df = pd.DataFrame(columns=[
        "dia_ontem", "faturamento", "qtd_pedidos", "markup", "custo",
        "compras", "qtd_devolucao", "valor_devolucao", "filial"
    ])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='CMV')
    output.seek(0)
    return output
def to_float(valor):
    try:
        if pd.isna(valor) or str(valor).strip() in ["-", "R$ -", "R$", "nan", "NaN", ""]:
            return 0.0
        return float(str(valor).replace("R$", "").replace(",", "").strip())
    except:
        return 0.0

def processar_planilha(file):
    try:
        df = pd.read_excel(file, sheet_name='CMV')

        colunas_esperadas = [
            "dia_ontem", "faturamento", "qtd_pedidos", "markup", "custo",
            "compras", "qtd_devolucao", "valor_devolucao", "filial"
        ]
        colunas_faltando = [col for col in colunas_esperadas if col not in df.columns]
        if colunas_faltando:
            st.error(f"❌ A planilha está faltando as colunas: {', '.join(colunas_faltando)}")
            return

        def to_float(valor):
            try:
                if pd.isna(valor) or str(valor).strip() in ["-", "R$ -", "R$", "nan", "NaN", ""]:
                    return 0.0
                return float(str(valor).replace("R$", "").replace(",", "").strip())
            except:
                return 0.0

        inseridos = 0
        for _, row in df.iterrows():
            try:
                data = pd.to_datetime(row['dia_ontem']).date()
                sucesso = inserir_dados(
                    data,
                    to_float(row['faturamento']),
                    int(row['qtd_pedidos']),
                    to_float(row['markup']),
                    to_float(row['custo']),
                    to_float(row['compras']),
                    int(row['qtd_devolucao']),
                    to_float(row['valor_devolucao']),
                    row['filial']
                )
                if sucesso:
                    inseridos += 1
            except Exception as e:
                st.warning(f"⚠️ Erro ao processar linha: {e}")

        st.success(f"✅ {inseridos} linhas inseridas com sucesso!")

    except Exception as e:
        st.error(f"❌ Erro ao processar planilha: {e}")
def aba_importar_planilha():
    st.subheader("📤 Importar CMV e Estoque por Planilha")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📄 Baixar modelo de planilha",
            data=baixar_modelo(),
            file_name="modelo_importacao_cmv.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    with col2:
        arquivo = st.file_uploader("📁 Enviar planilha preenchida", type=[".xlsx"])

    if arquivo:
        processar_planilha(arquivo)

    st.markdown("---")
    st.subheader(f"📋 Últimos {LIMIT_HISTORICO} registros importados via planilha")
    try:
        conn = conectar()
        df = pd.read_sql(
            f"SELECT id, dia_ontem, faturamento, markup, custo, filial FROM bf_cmv ORDER BY dia_ontem DESC LIMIT {LIMIT_HISTORICO}",
            conn
        )
        conn.close()

        if not df.empty:
            for i, row in df.iterrows():
                with st.expander(f"📅 {row['dia_ontem']} | Filial: {row['filial']}"):
                    st.write(row)
                    if st.button(f"🗑️ Excluir ID {row['id']}", key=f"excluir_{row['id']}"):
                        excluir_linha_cmv(row['id'])
        else:
            st.info("Nenhum registro encontrado.")

    except Exception as e:
        st.error(f"Erro ao buscar registros: {e}")

def aba_correcao_dados():
    st.subheader("🛠️ Correção de Dados CMV")
    try:
        conn = conectar()
        filiais = pd.read_sql("SELECT DISTINCT filial FROM bf_cmv", conn)['filial'].tolist()
        conn.close()

        filial_selecionada = st.selectbox("🏢 Escolha a filial para correção:", filiais)

        if filial_selecionada:
            conn = conectar()
            df = pd.read_sql(f"""
                SELECT id, dia_ontem, faturamento, qtd_pedidos, markup, custo, compras, qtd_devolucao, valor_devolucao
                FROM bf_cmv
                WHERE filial = %s
                ORDER BY dia_ontem DESC LIMIT {LIMIT_HISTORICO}
            """, conn, params=(filial_selecionada,))
            conn.close()

            if not df.empty:
                for _, row in df.iterrows():
                    with st.expander(f"📅 {row['dia_ontem']}"):
                        faturamento = st.number_input("Faturamento", value=float(row['faturamento']), key=f"fat_{row['id']}")
                        pedidos = st.number_input("Qtd. Pedidos", value=int(row['qtd_pedidos']), key=f"ped_{row['id']}")
                        markup = st.number_input("Markup", value=float(row['markup']), key=f"markup_{row['id']}")
                        custo = st.number_input("Custo", value=float(row['custo']), key=f"custo_{row['id']}")
                        compras = st.number_input("Compras", value=float(row['compras']), key=f"compras_{row['id']}")
                        qtd_dev = st.number_input("Qtd. Devolução", value=int(row['qtd_devolucao']), key=f"qtddev_{row['id']}")
                        valor_dev = st.number_input("Valor Devolução", value=float(row['valor_devolucao']), key=f"valdev_{row['id']}")

                        if st.button("💾 Atualizar", key=f"update_{row['id']}"):
                            try:
                                conn = conectar()
                                cursor = conn.cursor()
                                cursor.execute("""
                                    UPDATE bf_cmv
                                    SET faturamento = %s, qtd_pedidos = %s, markup = %s, custo = %s, compras = %s,
                                        qtd_devolucao = %s, valor_devolucao = %s
                                    WHERE id = %s
                                """, (faturamento, pedidos, markup, custo, compras, qtd_dev, valor_dev, row['id']))
                                conn.commit()
                                cursor.close()
                                conn.close()
                                st.success("✅ Dados atualizados com sucesso!")
                            except Exception as e:
                                st.error(f"Erro ao atualizar dados: {e}")
            else:
                st.info("Nenhum registro encontrado para esta filial.")

    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

def aba_correcao_estoque():
    st.subheader(f"🛠️ Correção de Estoque (últimos {LIMIT_HISTORICO} registros)")

    # Formulário para inserção manual
    st.markdown("### ➕ Inserir novo valor de estoque manualmente")

    with st.form("form_estoque_manual"):
        nova_data = st.date_input("📅 Data do estoque")
        novo_valor = st.number_input("💰 Valor de estoque", min_value=0.0, step=0.01, format="%.2f")
        nova_filial = st.text_input("🏢 Filial")

        submitted = st.form_submit_button("📥 Inserir")
        if submitted:
            if nova_filial.strip() == "":
                st.warning("⚠️ Preencha a filial.")
            else:
                sucesso = inserir_estoque(nova_data, novo_valor, nova_filial.strip())
                if sucesso:
                    st.success("✅ Estoque inserido com sucesso!")

    st.markdown("---")

    # Tabela de registros recentes
    try:
        conn = conectar()
        df = pd.read_sql(
            f"SELECT id, dia_ontem, valor_estoque, filial FROM bf_estoque_rhino ORDER BY dia_ontem DESC LIMIT {LIMIT_HISTORICO}",
            conn
        )
        conn.close()

        if not df.empty:
            for _, row in df.iterrows():
                with st.expander(f"📅 {row['dia_ontem']} | Filial: {row['filial']}"):
                    novo_valor = st.number_input(
                        f"💰 Valor de estoque atual: {row['valor_estoque']}",
                        value=float(row['valor_estoque']),
                        step=0.01,
                        key=f"input_{row['id']}"
                    )
                    if st.button(f"💾 Atualizar ID {row['id']}", key=f"atualizar_{row['id']}"):
                        try:
                            conn = conectar()
                            cursor = conn.cursor()
                            cursor.execute("""
                                UPDATE bf_estoque_rhino
                                SET valor_estoque = %s, data_registro = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (novo_valor, row['id']))
                            conn.commit()
                            cursor.close()
                            conn.close()
                            st.success(f"✅ Estoque do ID {row['id']} atualizado com sucesso!")
                        except Exception as e:
                            st.error(f"Erro ao atualizar estoque: {e}")
        else:
            st.info("Nenhum registro encontrado.")

    except Exception as e:
        st.error(f"Erro ao buscar registros: {e}")


# Exibe as abas principais
aba = st.sidebar.radio("📚 Selecione uma opção:", ["Correção de Dados", "Importar Planilha", "Correção Estoque"])

if aba == "Correção de Dados":
    aba_correcao_dados()
elif aba == "Importar Planilha":
    aba_importar_planilha()
elif aba == "Correção Estoque":
    aba_correcao_estoque()
