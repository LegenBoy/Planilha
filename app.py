import streamlit as st
import pandas as pd
import numpy as np

# Configuração da página
st.set_page_config(page_title="Comparador de Planilhas", layout="wide")

st.title("📊 Comparador de Cubagem Inteligente")
st.info("Faça o upload da planilha Original e da Alterada. O sistema mostrará as diferenças e permitirá navegar por elas.")

# --- 1. FUNÇÕES DE CARREGAMENTO ---
def load_file(uploaded_file):
    """Carrega CSV ou Excel e tenta tratar separadores comuns."""
    if uploaded_file.name.endswith('.csv'):
        try:
            return pd.read_csv(uploaded_file)
        except:
            return pd.read_csv(uploaded_file, sep=';')
    else:
        return pd.read_excel(uploaded_file)

def normalize_value(val):
    """Normaliza valores para comparação (trata floats e strings vazias)."""
    if pd.isna(val) or val == "":
        return None
    try:
        return float(val)
    except:
        return str(val).strip()

# --- 2. UPLOAD DE ARQUIVOS ---
col_up1, col_up2 = st.columns(2)
with col_up1:
    file_original = st.file_uploader("📂 1. Planilha Original", type=["xlsx", "xls", "csv"])
with col_up2:
    file_alterada = st.file_uploader("📂 2. Planilha Alterada", type=["xlsx", "xls", "csv"])

# --- 3. PROCESSAMENTO PRINCIPAL ---
if file_original and file_alterada:
    try:
        # Carregar
        df_old = load_file(file_original)
        df_new = load_file(file_alterada)

        # Guardar a ordem original das colunas para classificação por posição (Letras do Excel)
        original_cols_order = df_old.columns.tolist()

        # Tentar usar a coluna 'rotas' como índice (Identificador Único)
        id_col = 'rotas'
        if id_col in df_old.columns and id_col in df_new.columns:
            if df_old[id_col].is_unique and df_new[id_col].is_unique:
                df_old = df_old.set_index(id_col)
                df_new = df_new.set_index(id_col)
                # Garantir que o índice seja string para evitar problemas
                df_old.index = df_old.index.astype(str)
                df_new.index = df_new.index.astype(str)
            else:
                st.warning(f"A coluna '{id_col}' possui valores duplicados. Usando número da linha como referência.")
        else:
            st.warning(f"A coluna '{id_col}' não foi encontrada. Usando número da linha como referência.")

        # Dataframes para visualização
        df_display = df_new.copy().astype(object) # Cópia para mostrar X -> Y
        changes_list = [] # Lista para armazenar o resumo das alterações

        # Interseção de linhas e colunas (para comparar apenas o que existe em ambas)
        common_cols = df_old.columns.intersection(df_new.columns)
        common_index = df_old.index.intersection(df_new.index)

        # --- COMPARAÇÃO ---
        total_changes = 0
        for idx in common_index:
            # Identificar o nome da rota (seja pelo índice ou pela coluna)
            rota_name = idx
            if id_col in df_new.columns:
                rota_name = df_new.at[idx, id_col]

            for col in common_cols:
                val1 = df_old.at[idx, col]
                val2 = df_new.at[idx, col]

                v1_norm = normalize_value(val1)
                v2_norm = normalize_value(val2)

                # Verifica diferença
                is_diff = False
                if v1_norm is None and v2_norm is None:
                    is_diff = False
                elif v1_norm != v2_norm:
                    # Verifica tolerância numérica pequena para floats
                    if isinstance(v1_norm, float) and isinstance(v2_norm, float):
                        if not np.isclose(v1_norm, v2_norm):
                            is_diff = True
                    else:
                        is_diff = True

                if is_diff:
                    total_changes += 1
                    # Formatação para tabela visual
                    str_old = str(val1) if not pd.isna(val1) else "Vazio"
                    str_new = str(val2) if not pd.isna(val2) else "Vazio"
                    
                    df_display.at[idx, col] = f"{str_old} ➡️ {str_new}"

                    # Classificação da alteração baseada na posição da coluna (A=0, B=1, C=2, D=3, E=4...)
                    col_idx = -1
                    if col in original_cols_order:
                        col_idx = original_cols_order.index(col)
                    
                    categoria = "Geral"
                    if 4 <= col_idx <= 15: # Colunas E (4) até P (15)
                        categoria = "Alterações Filiais"
                    elif 20 <= col_idx <= 25: # Colunas U (20) até Z (25)
                        categoria = "Alterações de Transporte"
                    elif col_idx == 26: # Coluna AA (26)
                        categoria = "Alteração de Frete Retorno"

                    # Adiciona à lista detalhada
                    changes_list.append({
                        "Rota": str(rota_name),
                        "Coluna": col,
                        "Valor Antigo": str_old,
                        "Valor Novo": str_new,
                        "Categoria": categoria,
                        "ID_REF": idx # Referência interna para filtragem
                    })

        # --- 4. EXIBIÇÃO DA INTERFACE ---
        
        st.divider()
        
        if total_changes == 0:
            st.success("✅ Nenhuma alteração encontrada. As planilhas são idênticas nos campos comuns.")
            st.dataframe(df_display, use_container_width=True)
        else:
            st.warning(f"⚠️ Foram encontradas **{total_changes}** alterações.")

            # Container para a Tabela Principal (será filtrada depois)
            st.subheader("📋 Visualização da Planilha")
            main_table_placeholder = st.empty()

            st.markdown("---")
            st.subheader("📝 Lista de Alterações (Clique para filtrar acima)")
            st.caption("Clique em uma linha abaixo para ver a alteração correspondente na tabela principal.")

            # DataFrame de Alterações (Lista Detalhada)
            df_changes_detailed = pd.DataFrame(changes_list)

            # Agrupar por Rota/ID para exibição compacta
            # Cria uma string com todas as alterações daquela rota
            df_changes_grouped = df_changes_detailed.groupby(["ID_REF", "Rota"]).apply(
                lambda x: pd.Series({
                    "Alterações": " | ".join([f"[{row['Categoria']}] {row['Coluna']} ({row['Valor Antigo']} ➡️ {row['Valor Novo']})" for _, row in x.iterrows()])
                })
            ).reset_index()
            
            # Exibir lista interativa com seleção habilitada
            event = st.dataframe(
                df_changes_grouped,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                height=300,
                column_config={
                    "ID_REF": None, # Oculta a coluna de ID interno
                    "Alterações": st.column_config.TextColumn("Detalhes das Alterações", width="large")
                }
            )

            # Lógica de Filtro: Verifica se o usuário clicou em algo
            selected_id_ref = None
            selected_rota_name = None

            if len(event.selection.rows) > 0:
                # Pega o índice numérico da linha selecionada na lista de alterações
                selected_idx = event.selection.rows[0]
                # Descobre qual é o ID de referência e o nome da rota
                selected_id_ref = df_changes_grouped.iloc[selected_idx]["ID_REF"]
                selected_rota_name = df_changes_grouped.iloc[selected_idx]["Rota"]

            # Renderiza a Tabela Principal (Filtrada ou Completa)
            with main_table_placeholder.container():
                if selected_id_ref is not None:
                    st.info(f"🔎 Filtrando visualização para a Rota: **{selected_rota_name}**")
                    # Mostra apenas a linha selecionada
                    st.dataframe(df_display.loc[[selected_id_ref]], use_container_width=True)
                    
                    # Botão para limpar filtro
                    if st.button("🔄 Mostrar Tabela Completa"):
                        st.rerun()
                else:
                    # Mostra tabela completa padrão
                    st.dataframe(df_display, use_container_width=True)

            # Opção de Download da Lista
            csv = df_changes_detailed.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Relatório de Alterações (CSV)",
                data=csv,
                file_name="relatorio_alteracoes.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Erro ao processar as planilhas: {e}")
