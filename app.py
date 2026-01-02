import streamlit as st
import pandas as pd
import numpy as np

# Configuração da página
st.set_page_config(page_title="Comparador de Planilhas", layout="wide")

st.title("📊 Comparador de Planilhas de Cubagem")
st.markdown("""
<style>
    .stDataFrame { border: 1px solid #f0f2f6; border-radius: 5px; }
</style>import streamlit as st
import pandas as pd
import numpy as np

# Configuração da página para modo amplo
st.set_page_config(page_title="Comparador de Planilhas", layout="wide")

st.title("📊 Comparador de Cubagem Inteligente")
st.markdown("""
<style>
    /* Ajuste visual para destacar tabelas */
    .stDataFrame { border: 1px solid #e0e0e0; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

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

        # Tentar usar a coluna 'rotas' como índice (Identificador Único)
        id_col = 'rotas'
        if id_col in df_old.columns and id_col in df_new.columns:
            df_old = df_old.set_index(id_col)
            df_new = df_new.set_index(id_col)
            # Garantir que o índice seja string para evitar problemas
            df_old.index = df_old.index.astype(str)
            df_new.index = df_new.index.astype(str)
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
                    # Verifica tolerância numérica pequena para floats (ex: 1.0000001 vs 1.0)
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

                    # Adiciona à lista detalhada
                    changes_list.append({
                        "Rota (ID)": idx,
                        "Coluna": col,
                        "Valor Antigo": str_old,
                        "Valor Novo": str_new
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

            # DataFrame de Alterações (Lista)
            df_changes = pd.DataFrame(changes_list)
            
            # Exibir lista interativa com seleção habilitada
            event = st.dataframe(
                df_changes,
                use_container_width=True,
                hide_index=True,
                selection_mode="single-row",
                on_select="rerun",
                height=300
            )

            # Lógica de Filtro: Verifica se o usuário clicou em algo
            selected_rota = None
            if len(event.selection.rows) > 0:
                # Pega o índice numérico da linha selecionada na lista de alterações
                selected_idx = event.selection.rows[0]
                # Descobre qual é a Rota correspondente
                selected_rota = df_changes.iloc[selected_idx]["Rota (ID)"]

            # Renderiza a Tabela Principal (Filtrada ou Completa)
            with main_table_placeholder.container():
                if selected_rota:
                    st.info(f"🔎 Filtrando visualização para a Rota: **{selected_rota}**")
                    # Mostra apenas a linha selecionada
                    # .loc[[rota]] garante que retorne um DataFrame e não uma Series
                    st.dataframe(df_display.loc[[selected_rota]], use_container_width=True)
                    
                    # Botão para limpar filtro
                    if st.button("🔄 Mostrar Tabela Completa"):
                        st.rerun()
                else:
                    # Mostra tabela completa padrão
                    st.dataframe(df_display, use_container_width=True)

            # Opção de Download da Lista
            csv = df_changes.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Relatório de Alterações (CSV)",
                data=csv,
                file_name="relatorio_alteracoes.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Erro ao processar as planilhas: {e}")
""", unsafe_allow_html=True)

st.info("Faça o upload das duas planilhas. O sistema mostrará uma visão geral e uma lista detalhada das mudanças abaixo.")

# Função para carregar os arquivos
def load_file(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        try:
            return pd.read_csv(uploaded_file)
        except:
            return pd.read_csv(uploaded_file, sep=';')
    else:
        return pd.read_excel(uploaded_file)

# Upload dos arquivos
col1, col2 = st.columns(2)
with col1:
    file_original = st.file_uploader("📂 1. Planilha Original (Antiga)", type=["xlsx", "xls", "csv"])
with col2:
    file_alterada = st.file_uploader("📂 2. Planilha Alterada (Nova)", type=["xlsx", "xls", "csv"])

if file_original and file_alterada:
    try:
        # Carregar DataFrames
        df_old = load_file(file_original)
        df_new = load_file(file_alterada)

        # Tentar definir 'rotas' como índice para facilitar a identificação (ajuste conforme o nome real da coluna na sua planilha)
        # Se não encontrar a coluna 'rotas', usa o índice numérico padrão
        index_col = 'rotas' if 'rotas' in df_old.columns else None
        
        if index_col:
            df_old = df_old.set_index(index_col)
            df_new = df_new.set_index(index_col)
            # Garantir que o índice seja string para evitar erros de comparação
            df_old.index = df_old.index.astype(str)
            df_new.index = df_new.index.astype(str)

        # Criar DataFrames para resultados e lista de alterações
        df_result = df_new.copy().astype(object)
        changes_list = []

        # Identificar colunas e índices comuns
        common_cols = df_old.columns.intersection(df_new.columns)
        common_index = df_old.index.intersection(df_new.index)
        
        # Iteração de Comparação
        for idx in common_index:
            for col in common_cols:
                val_old = df_old.at[idx, col]
                val_new = df_new.at[idx, col]

                is_diff = False
                
                # Lógica de comparação (numérica e texto)
                if pd.isna(val_old) and pd.isna(val_new):
                    is_diff = False
                elif pd.isna(val_old) or pd.isna(val_new):
                    is_diff = True
                else:
                    try:
                        # Tenta comparar como número
                        v1 = float(val_old)
                        v2 = float(val_new)
                        if not np.isclose(v1, v2):
                            is_diff = True
                    except:
                        # Compara como texto limpo
                        if str(val_old).strip() != str(val_new).strip():
                            is_diff = True

                if is_diff:
                    str_old = str(val_old) if not pd.isna(val_old) else "Vazio"
                    str_new = str(val_new) if not pd.isna(val_new) else "Vazio"
                    
                    # Atualiza a visualização da tabela principal
                    df_result.at[idx, col] = f"{str_old} ➡️ {str_new}"
                    
                    # Adiciona à lista de alterações detalhada
                    changes_list.append({
                        "Identificador (Rota)": idx,
                        "Coluna Alterada": col,
                        "Valor Antigo": str_old,
                        "Valor Novo": str_new
                    })

        # --- Exibição dos Resultados ---
        
        st.divider()

        if len(changes_list) > 0:
            df_changes = pd.DataFrame(changes_list)
            
            # --- SEÇÃO 1: Lista Interativa de Alterações ---
            st.subheader("📝 Lista de Alterações Detectadas")
            st.write("Selecione uma linha abaixo para filtrar a planilha principal e ver o contexto.")
            
            # Tabela interativa de alterações
            # selection_mode='single-row' permite clicar em uma linha
            event = st.dataframe(
                df_changes,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )

            # Lógica de Filtro baseada na seleção
            rota_selecionada = None
            if len(event.selection.rows) > 0:
                row_idx = event.selection.rows[0]
                rota_selecionada = df_changes.iloc[row_idx]["Identificador (Rota)"]
                st.info(f"🔎 Filtrando visualização pela Rota: **{rota_selecionada}**")

            # --- SEÇÃO 2: Visualização da Planilha ---
            st.subheader("📋 Visualização na Planilha (Resultado)")
            
            if rota_selecionada:
                # Filtra o dataframe principal para mostrar apenas a rota selecionada na lista
                # Usamos loc[[rota]] para manter o formato de DataFrame
                st.dataframe(df_result.loc[[rota_selecionada]], use_container_width=True)
                
                if st.button("Mostrar Tabela Completa"):
                    st.rerun() # Reseta a seleção
            else:
                # Mostra tudo se nada estiver selecionado
                st.dataframe(df_result, use_container_width=True)

            # Botão de Download
            csv_changes = df_changes.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Lista de Alterações (.csv)",
                data=csv_changes,
                file_name="lista_de_alteracoes.csv",
                mime="text/csv",
            )

        else:
            st.success("✅ Nenhuma alteração encontrada entre as planilhas!")
            st.dataframe(df_result, use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao processar arquivos: {e}")

