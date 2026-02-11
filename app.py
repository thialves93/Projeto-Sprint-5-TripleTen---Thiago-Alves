import pandas as pd
import plotly.express as px
import streamlit as st


# --- Configuração da página (precisa ser o primeiro comando de UI) ---
import streamlit as st
st.set_page_config(page_title="Carros US - EDA", layout="wide")

# --- Imports ---
import pandas as pd
import plotly.express as px

# --- Cache de leitura ---
@st.cache_data(show_spinner=False)
def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

# --- Saneamento dos dados ---
def sanitize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Numéricos
    for col in ["price", "odometer", "model_year", "days_listed"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # Boolean (is_4wd como 0/1 → bool)
    if "is_4wd" in df.columns:
        df["is_4wd"] = df["is_4wd"].fillna(0).astype(int).astype(bool)
    # Datas
    if "date_posted" in df.columns:
        df["date_posted"] = pd.to_datetime(df["date_posted"], errors="coerce")
    # Strings padronizadas
    for col in ["model", "condition", "transmission", "type", "paint_color", "fuel", "title_status"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip().str.lower()
    # Regras de negócio (faixas válidas)
    if "odometer" in df.columns:
        df.loc[df["odometer"] < 0, "odometer"] = pd.NA
    if "price" in df.columns:
        df.loc[df["price"] <= 0, "price"] = pd.NA
    if "model_year" in df.columns:
        df.loc[~df["model_year"].between(1980, 2025), "model_year"] = pd.NA
    return df

# --- UI: Título ---
st.title("Exploração de anúncios de carros (vehicles_us.csv)")

# --- Carregamento robusto (Render/GitHub) ---
try:
    raw = load_data("vehicles_us.csv")
except FileNotFoundError:
    st.error("Arquivo vehicles_us.csv não encontrado no contêiner.")
    uploaded = st.file_uploader("Envie o CSV vehicles_us.csv")
    if uploaded:
        raw = load_data(uploaded)
    else:
        st.stop()

car_data = sanitize(raw)

# --- Relatório simples de qualidade ---
def warn_missing(df: pd.DataFrame, col: str, thresh=0.3):
    if col in df.columns:
        pct = df[col].isna().mean()
        if pct > thresh:
            st.warning(f"Atenção: {pct:.0%} de '{col}' ausente(s). Os gráficos podem não refletir o mercado real.")

with st.expander("Qualidade dos dados"):
    na_pct = (car_data.isna().mean() * 100).round(1)
    st.write(na_pct.sort_values(ascending=False))

# --- Filtros (barra lateral) ---
with st.sidebar:
    st.header("Filtros")
    # Filtros numéricos dinâmicos
    if "price" in car_data.columns:
        pr_min = float(car_data["price"].min(skipna=True) or 0)
        pr_max = float(car_data["price"].max(skipna=True) or 1)
        price_range = st.slider("Faixa de preço", min_value=0.0, max_value=pr_max, value=(pr_min, pr_max), step=100.0)
    else:
        price_range = None

    if "odometer" in car_data.columns:
        od_min = float(car_data["odometer"].min(skipna=True) or 0)
        od_max = float(car_data["odometer"].max(skipna=True) or 1)
        odo_range = st.slider("Faixa de odômetro", min_value=0.0, max_value=od_max, value=(od_min, od_max), step=1000.0)
    else:
        odo_range = None

    cond_sel = st.multiselect("Condição", sorted(car_data["condition"].dropna().unique().tolist()) if "condition" in car_data.columns else [])
    trn_sel  = st.multiselect("Transmissão", sorted(car_data["transmission"].dropna().unique().tolist()) if "transmission" in car_data.columns else [])

# --- Aplicação dos filtros ---
dfv = car_data.copy()
if price_range and "price" in dfv.columns:
    dfv = dfv[dfv["price"].between(*price_range)]
if odo_range and "odometer" in dfv.columns:
    dfv = dfv[dfv["odometer"].between(*odo_range)]
if cond_sel and "condition" in dfv.columns:
    dfv = dfv[dfv["condition"].isin(cond_sel)]
if trn_sel and "transmission" in dfv.columns:
    dfv = dfv[dfv["transmission"].isin(trn_sel)]

# --- Alertas de dados problemáticos no dataset filtrado ---
for c in ["model_year","odometer","price","date_posted"]:
    warn_missing(dfv, c)

# --- Métricas de contexto ---
st.metric("Registros filtrados", len(dfv))
if "price" in dfv.columns:
    st.metric("Preço médio (filtrado)", f"${dfv['price'].mean(skipna=True):,.0f}")

# --- Histograma dinâmico ---
num_cols = [c for c in dfv.columns if pd.api.types.is_numeric_dtype(dfv[c])]
st.subheader("Histograma")
if not num_cols:
    st.info("Não há colunas numéricas disponíveis após os filtros.")
else:
    colh1, colh2, colh3 = st.columns([2,1,1])
    with colh1:
        default_hist = num_cols.index("odometer") if "odometer" in num_cols else 0
        hist_col = st.selectbox("Coluna numérica", num_cols, index=default_hist)
    with colh2:
        bins = st.number_input("Bins", min_value=5, max_value=200, value=50, step=5)
    with colh3:
        log_y = st.checkbox("Escala log em Y", value=False)

    if st.button("Criar histograma"):
        st.write(f"Histograma de {hist_col}")
        fig = px.histogram(dfv, x=hist_col, nbins=int(bins))
        if log_y:
            fig.update_yaxes(type="log")
        st.plotly_chart(fig, use_container_width=True)

# --- Dispersão com validação e cor opcional ---
st.subheader("Gráfico de dispersão")
if len(num_cols) < 2:
    st.info("São necessárias pelo menos duas colunas numéricas para criar dispersão.")
else:
    x_default = num_cols.index("odometer") if "odometer" in num_cols else 0
    y_default = num_cols.index("price") if "price" in num_cols else (1 if len(num_cols) > 1 else 0)
    x_var = st.selectbox("X", num_cols, index=x_default, key="x_var")
    y_var = st.selectbox("Y", num_cols, index=y_default, key="y_var")
    cat_opts = [c for c in ["condition","type","transmission","paint_color"] if c in dfv.columns]
    color_col = st.selectbox("Cor (opcional)", ["(nenhum)"] + cat_opts)
    trend = st.checkbox("Adicionar linha de tendência (OLS)", value=False, help="Requer statsmodels instalado.")

    if st.button("Criar dispersão"):
        if x_var == y_var:
            st.warning("Escolha variáveis diferentes para X e Y!")
        else:
            fig = px.scatter(
                dfv, x=x_var, y=y_var,
                color=None if color_col == "(nenhum)" else color_col,
                trendline="ols" if trend else None,
                hover_data=[c for c in ["model","model_year","condition"] if c in dfv.columns]
            )
            st.plotly_chart(fig, use_container_width=True)

# --- Top 3 modelos com menor odômetro (após filtros) ---
st.subheader("Top 3 modelos com menor odômetro (após filtros)")
if st.button("Buscar Top 3"):
    needed = {"model","odometer"}
    if not needed.issubset(dfv.columns):
        st.warning("Colunas necessárias ausentes para esta análise.")
    else:
        df_filtered = dfv.dropna(subset=list(needed))
        if df_filtered.empty:
            st.warning("Nenhum veículo encontrado nessa combinação de filtros.")
        else:
            # menor odômetro por modelo
            min_odos = df_filtered.groupby("model", as_index=False)["odometer"].min().rename(columns={"odometer":"min_odometer"})
            joined = df_filtered.merge(min_odos, on="model")
            candidates = joined[joined["odometer"] == joined["min_odometer"]]
            # critérios de desempate: ano mais novo e preço mais baixo (se existirem)
            sort_cols, sort_asc = ["min_odometer"], [True]
            if "model_year" in candidates.columns:
                sort_cols.append("model_year"); sort_asc.append(False)
            if "price" in candidates.columns:
                sort_cols.append("price"); sort_asc.append(True)
            candidates = candidates.sort_values(by=sort_cols, ascending=sort_asc)
            top3 = candidates.drop_duplicates(subset=["model"]).head(3)

            st.caption("Critérios: menor odômetro; desempate por ano mais novo e menor preço (quando disponíveis).")
            show_cols_pref = ["price","model_year","model","condition","odometer","transmission","type","paint_color"]
            show_cols = [c for c in show_cols_pref if c in candidates.columns]
            st.dataframe(top3[show_cols].reset_index(drop=True))








breakpoint()

        
car_data = pd.read_csv('vehicles_us.csv') # lendo os dados
hist_button = st.button('Criar histograma') # criar um botão
        
if hist_button: # se o botão for clicado
# escrever uma mensagem
    st.write('Criando um histograma para o conjunto de dados de anúncios de vendas de carros')
            
# criar um histograma
    fig = px.histogram(car_data, x="odometer")
        
# exibir um gráfico Plotly interativo
    st.plotly_chart(fig, use_container_width=True)

    #############################################################################################################################

# Botão para gráfico de dispersão
# Selectboxes para escolher variáveis
col1, col2 = st.columns(2)
with col1:
    x_var = st.selectbox('Escolha variável X:', ['odometer', 'model_year', 'price'])
with col2:
    y_var = st.selectbox('Escolha variável Y:', ['price', 'odometer', 'model_year'])

if st.button('Criar gráfico de dispersão'):
    if x_var != y_var:
        fig = px.scatter(car_data, x=x_var, y=y_var)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning('Escolha variáveis diferentes para X e Y!')

#############################################################################################################################

# Botão para buscar top 3 modelos por menor odômetro dentro de uma faixa de preço
cols = ['price','model_year','model','condition','odometer','transmission','type','paint_color']

# Preparar colunas numéricas
car_data['price'] = pd.to_numeric(car_data['price'], errors='coerce')
car_data['odometer'] = pd.to_numeric(car_data['odometer'], errors='coerce')

# Inputs para faixa de preço
price_min_default = int(car_data['price'].min(skipna=True) or 0)
price_max_default = int(car_data['price'].max(skipna=True) or 100000)

st.subheader('Filtrar por faixa de preço')
col1, col2 = st.columns(2)
with col1:
    min_price_input = st.number_input('Preço mínimo', value=price_min_default, min_value=0, step=100)
with col2:
    max_price_input = st.number_input('Preço máximo', value=price_max_default, min_value=0, step=100)

search_button = st.button('Buscar Top 3 por menor odômetro')

if search_button:
    df = car_data.copy()
    df_filtered = df[df['price'].between(min_price_input, max_price_input)]

    if df_filtered.empty:
        st.warning('Nenhum veículo encontrado nessa faixa de preço.')
    else:
        # Para cada modelo, pegar o menor odômetro dentro da faixa; ordenar e selecionar top 3 modelos
        model_min_odo = (
            df_filtered
            .dropna(subset=['model','odometer'])
            .groupby('model', as_index=False)
            .agg(min_odometer=('odometer','min'))
            .sort_values('min_odometer', ascending=True)
            .head(3)
        )

        # Selecionar a linha representativa (preenchida com as colunas solicitadas) para cada modelo
        rows = []
        for _, r in model_min_odo.iterrows():
            model_name = r['model']
            min_odo = r['min_odometer']
            candidates = df_filtered[(df_filtered['model'] == model_name) & (df_filtered['odometer'] == min_odo)]
            # se houver múltiplos candidatos, escolher o com maior ano do modelo
            chosen = candidates.sort_values('model_year', ascending=False).iloc[0]
            rows.append(chosen[cols])

        result_df = pd.DataFrame(rows)
        st.write('Top 3 modelos com menor odômetro na faixa de preço')
        st.dataframe(result_df.reset_index(drop=True))

