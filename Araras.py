import streamlit as st
import pandas as pd
import plotly.express as px
import textwrap

# --- Constantes e Configurações Iniciais ---

# Constante para o nome do arquivo, facilita a manutenção
ARQUIVO_DADOS = "Araras.xlsx"
# Paleta de cores centralizada para os gráficos
CORES_GRAFICOS = ["#A8D5BA", "#AFCBFF", "#87CEFA", "#FFDAB9", "#E6E6FA", "#F08080", "#98FB98"]

# Configuração da página (deve ser o primeiro comando do Streamlit)
st.set_page_config(page_title="Dashboard Araras", layout="wide")

# --- Funções ---

@st.cache_data
def carregar_dados(caminho_arquivo):
    """
    Carrega os dados de um arquivo Excel, realiza a limpeza e valida as colunas.
    Retorna um DataFrame do Pandas.
    """
    try:
        df = pd.read_excel(caminho_arquivo, sheet_name="Página1")
    except FileNotFoundError:
        st.error(f"Erro: O arquivo '{caminho_arquivo}' não foi encontrado. Verifique se o arquivo está na mesma pasta que o script.")
        st.stop() 

    # Validação para garantir que as colunas essenciais existem no arquivo
    colunas_necessarias = ["Tipo", "Subtipo", "Locais", "Quantidade"]
    if not all(coluna in df.columns for coluna in colunas_necessarias):
        st.error("Erro: O arquivo Excel deve conter as colunas: 'Tipo', 'Subtipo', 'Locais', 'Quantidade'.")
        st.stop()

    # Limpeza e conversão de tipo
    df["Quantidade"] = pd.to_numeric(df["Quantidade"], errors="coerce")
    df = df.dropna(subset=["Quantidade", "Subtipo", "Locais"])
    df["Quantidade"] = df["Quantidade"].astype(int)
    return df

# --- Carregamento dos Dados ---
df = carregar_dados(ARQUIVO_DADOS)

# --- Layout do Cabeçalho ---
top_col1, top_col2 = st.columns([0.1, 0.9])
with top_col1:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3c/Coat_of_arms_of_Araras.svg/800px-Coat_of_arms_of_Araras.svg.png", width=80)
with top_col2:
    st.title("🏢 Dashboard - Município de Araras")
    st.markdown("<h6>Dados de câmeras de segurança, categorizados por Tipo e Subtipo</h6>", unsafe_allow_html=True)

# --- Barra Lateral de Filtros ---
with st.sidebar:
    st.header("🔍 Filtros")
    
    tipo_unico = sorted(df["Tipo"].dropna().unique())
    tipo_opcao = st.selectbox("Tipo", ["Todos"] + tipo_unico)

    if tipo_opcao != "Todos":
        subtipo_lista = sorted(df[df["Tipo"] == tipo_opcao]["Subtipo"].dropna().unique())
    else:
        subtipo_lista = sorted(df["Subtipo"].dropna().unique())
    subtipo_opcao = st.selectbox("Subtipo", ["Todos"] + subtipo_lista)
    
    busca_local = st.text_input("Buscar por nome do local")

# --- Lógica de Filtragem ---
df_filtrado = df.copy()
if tipo_opcao != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Tipo"] == tipo_opcao]
if subtipo_opcao != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Subtipo"] == subtipo_opcao]
if busca_local:
    df_filtrado = df_filtrado[df_filtrado["Locais"].str.contains(busca_local, case=False, na=False)]

# --- Exibição do Dashboard ---
st.subheader("📊 Indicadores Gerais")

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os filtros aplicados.")
else:
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="Total de Câmeras", value=int(df_filtrado["Quantidade"].sum()))
    kpi2.metric(label="Total de Locais", value=df_filtrado["Locais"].nunique())
    with kpi3:
        st.markdown("<p style='font-size: 14px; font-weight: bold;'>Local com Mais Câmeras</p>", unsafe_allow_html=True)
        maior_linha = df_filtrado.loc[df_filtrado["Quantidade"].idxmax()]
        maior_nome = maior_linha["Locais"]
        maior_qtd = int(maior_linha["Quantidade"])
        st.markdown(f"<div style='font-size:18px; font-weight: bold;'>{maior_nome}</div>"
                    f"<span style='font-size:14px;'>{maior_qtd} câmeras</span>", unsafe_allow_html=True)

    st.markdown("---")

    # --- Gráficos (COM LÓGICA DE LAYOUT DINÂMICO) ---
    
    if subtipo_opcao != "Todos":
        # --- VISTA DETALHADA COM "TOP 10" ---
        st.subheader(f"Top 10 Principais Locais em '{subtipo_opcao}'")
        df_locais = df_filtrado.groupby("Locais", as_index=False)["Quantidade"].sum().sort_values("Quantidade", ascending=False)
        top_n = 10
        df_para_plotar = df_locais.head(top_n)
        fig = px.bar(
            df_para_plotar,
            x='Locais',
            y='Quantidade',
            text_auto=True,
            color='Locais',
        )
        fig.update_layout(
            showlegend=False,
            title_text=f"Exibindo os {len(df_para_plotar)} Principais Locais"
        )
        fig.update_xaxes(title_text="Local", tickangle=0)
        st.plotly_chart(fig, use_container_width=True)

    else:
        # --- VISTA GERAL ---
        col1, col2 = st.columns(2)
        with col1:
            if tipo_opcao == "Todos":
                df_tipo = df_filtrado.groupby("Tipo")["Quantidade"].sum().reset_index()
                fig = px.bar(
                    df_tipo, x="Tipo", y="Quantidade", text_auto=True,
                    title="Distribuição por Categoria (Tipo)", color_discrete_sequence=CORES_GRAFICOS
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                df_subtipo_bar = df_filtrado.groupby("Subtipo")["Quantidade"].sum().reset_index()
                fig = px.bar(
                    df_subtipo_bar, x="Subtipo", y="Quantidade", text_auto=True,
                    title=f"Distribuição por Subcategorias em '{tipo_opcao}'",
                    color="Subtipo"
                )
                fig.update_xaxes(tickvals=df_subtipo_bar['Subtipo'], ticktext=['<br>'.join(textwrap.wrap(l, 20)) for l in df_subtipo_bar['Subtipo']])
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            df_subtipo_pie = df_filtrado.groupby("Subtipo")["Quantidade"].sum().reset_index()
            fig_pie = px.pie(
                df_subtipo_pie, names="Subtipo", values="Quantidade",
                title="Distribuição Percentual por Subcategoria"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # --- Tabela Detalhada ---
    st.subheader("🔍 Tabela Detalhada")
    for subtipo, grupo in df_filtrado.groupby("Subtipo"):
        # Usando expander para uma UI mais limpa
        with st.expander(f"**{subtipo}** ({grupo['Quantidade'].sum()} câmeras no total)"):
            # Ordena os locais pela quantidade de câmeras dentro de cada grupo
            grupo_ordenado = grupo.sort_values(by="Quantidade", ascending=False)
            
            # --- TABELA COM O ESTILO ORIGINAL PADRÃO SOLICITADO ---
            st.dataframe(
                grupo_ordenado[["Locais", "Quantidade"]],
                use_container_width=True,
                hide_index=True
            )