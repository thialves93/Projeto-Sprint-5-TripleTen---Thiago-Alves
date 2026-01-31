import streamlit as st
import pandas as pd
import plotly.express as px

# Ler os dados
car_data = pd.read_csv('vehicles.csv')

# Cabeçalho
st.header('Dashboard de Vendas de Carros')

# Botão para histograma
hist_button = st.button('Criar histograma')

if hist_button:
    st.write('Criando um histograma...')
    fig = px.histogram(car_data, x="odometer")
    st.plotly_chart(fig, use_container_width=True)
