import streamlit as st
import pandas as pd
import plotly.express as px

# Ler os dados
car_data = pd.read_csv('vehicles_us.csv')

# Cabeçalho
st.header('Dashboard de Vendas de Carros')

# Botão para histograma
hist_button = st.button('Criar histograma')

if hist_button:
    st.write('Criando um histograma...')
    fig = px.histogram(car_data, x="odometer")
    st.plotly_chart(fig, use_container_width=True)

<<<<<<< HEAD
# Botão para gráfico de dispersão
scatter_button = st.button('Criar gráfico de dispersão')

if scatter_button:
    st.write('Criando um gráfico de dispersão...')
    fig = px.scatter(car_data, x="odometer")
    st.plotly_chart(fig, use_container_width=True)


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
=======
>>>>>>> da0293210318cbdc97d4e89c9aef207c4b47e603
