import streamlit as st
import pandas as pd
import numpy as np

# Configuração da página
st.set_page_config(page_title="Comparador de Planilhas", layout="wide")

st.title("📊 Comparador de Planilhas de Cubagem")
st.write("""
Faça o upload da planilha original e da planilha alterada para visualizar as diferenças.
O sistema irá apontar onde houve alteração e qual foi o valor modificado.
""")

# Função para carregar os arquivos (suporta CSV e Excel)
def load_file(uploaded_file):
    if uploaded_file.name.endswith('.csv'):
        # Tenta ler com diferentes separadores caso necessário
        try:
            return pd.read_csv(uploaded_file)
        except:
            return pd.read_csv(uploaded_file, sep=';')
    else:
        return pd.read_excel(uploaded_file)

# Upload dos arquivos
col1, col2 = st.columns(2)
with col1:
    file_original = st.file_uploader("📂 Upload Planilha Original (Primeira)", type=["xlsx", "xls", "csv"])
with col2:
    file_alterada = st.file_uploader("📂 Upload Planilha Alterada", type=["xlsx", "xls", "csv"])

if file_original and file_alterada:
    try:
        # Carregar DataFrames
        df_old = load_file(file_original)
        df_new = load_file(file_alterada)

        st.divider()
        st.subheader("Resultado da Comparação")

        # Verificar se as dimensões são iguais
        if df_old.shape != df_new.shape:
            st.warning(f"⚠️ As planilhas têm tamanhos diferentes! (Original: {df_old.shape}, Alterada: {df_new.shape}). A comparação será feita até o limite das linhas/colunas comuns.")

        # Criar DataFrame de resultado (cópia do novo como string para poder escrever "X -> Y")
        df_result = df_new.copy().astype(object)
        
        # Identificar colunas e linhas comuns para iteração
        common_cols = df_old.columns.intersection(df_new.columns)
        common_index = df_old.index.intersection(df_new.index)
        
        changes_count = 0

        # Iterar e comparar
        for col in common_cols:
            for idx in common_index:
                val_old = df_old.at[idx, col]
                val_new = df_new.at[idx, col]

                # Lógica de comparação
                is_diff = False
                
                # Tratamento para NaNs (vazio)
                if pd.isna(val_old) and pd.isna(val_new):
                    is_diff = False
                elif pd.isna(val_old) or pd.isna(val_new):
                    is_diff = True
                else:
                    # Tentar comparação numérica para evitar falsos positivos (ex: 0 vs 0.0)
                    try:
                        v1 = float(val_old)
                        v2 = float(val_new)
                        if not np.isclose(v1, v2):
                            is_diff = True
                    except:
                        # Comparação de texto (limpando espaços)
                        if str(val_old).strip() != str(val_new).strip():
                            is_diff = True

                if is_diff:
                    changes_count += 1
                    # Formatar a célula para mostrar a mudança
                    # Se era vazio/NaN, mostra "Vazio" para clareza, ou apenas o valor novo
                    str_old = str(val_old) if not pd.isna(val_old) else "Vazio"
                    str_new = str(val_new) if not pd.isna(val_new) else "Vazio"
                    
                    df_result.at[idx, col] = f"{str_old} ➡️ {str_new}"

        if changes_count > 0:
            st.success(f"Foram encontradas **{changes_count}** células com alterações.")
            
            # Mostrar tabela. Destacamos que é interativa.
            st.dataframe(df_result, use_container_width=True)
            
            # Opção de download do resultado
            csv = df_result.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Relatório de Alterações (CSV)",
                data=csv,
                file_name="relatorio_alteracoes.csv",
                mime="text/csv",
            )
        else:
            st.info("✅ Nenhuma alteração encontrada entre as planilhas.")

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os arquivos: {e}")
