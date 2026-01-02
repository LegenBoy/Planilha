import streamlit as st
import pandas as pd
import numpy as np

# Configuração da página
st.set_page_config(page_title="Comparador de Planilhas", layout="wide")

st.title("📊 Comparador de Planilhas de Cubagem")
st.markdown("""
<style>
    .stDataFrame { border: 1px solid #f0f2f6; border-radius: 5px; }
</style>
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
