import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Tablero de Cartera Vendedores", layout="wide")

st.title("📊 Tablero de Cartera para Vendedores")

# Cargar datos
carpeta = os.path.dirname(__file__)
archivo = os.path.join(carpeta, "Cartera.xlsx")
if not os.path.exists(archivo):
    st.error("No se encontró el archivo Cartera.xlsx en la carpeta actual.")
    st.stop()

cartera = pd.read_excel(archivo)
cartera.columns = [c.lower() for c in cartera.columns]

# Filtros
vendedores = cartera['nomvendedor'].dropna().unique()
vendedor_sel = st.selectbox("Selecciona un vendedor", sorted(vendedores))
cartera_vend = cartera[cartera['nomvendedor'] == vendedor_sel]

# KPIs
total_cartera = cartera_vend['importe'].replace({'[$,]': ''}, regex=True).astype(float).sum()
cartera_vencida = cartera_vend[cartera_vend['dias_vencido'] > 0]['importe'].replace({'[$,]': ''}, regex=True).astype(float).sum()
cartera_sana = cartera_vend[cartera_vend['dias_vencido'] <= 0]['importe'].replace({'[$,]': ''}, regex=True).astype(float).sum()

col1, col2, col3 = st.columns(3)
col1.metric("Total Cartera", f"${total_cartera:,.0f}")
col2.metric("Cartera Vencida", f"${cartera_vencida:,.0f}")
col3.metric("Cartera Sana", f"${cartera_sana:,.0f}")

# Gráfico de barras: Cartera por cliente
cartera_vend['importe'] = cartera_vend['importe'].replace({'[$,]': ''}, regex=True).astype(float)
grafico = px.bar(
    cartera_vend.groupby('nombrecliente')['importe'].sum().sort_values(ascending=False).head(10).reset_index(),
    x='nombrecliente', y='importe',
    title='Top 10 Clientes por Cartera',
    labels={'importe': 'Valor', 'nombrecliente': 'Cliente'},
    text_auto='.2s',
)
st.plotly_chart(grafico, use_container_width=True)

# Tabla de facturas vencidas
st.subheader("Facturas Vencidas")
df_vencidas = cartera_vend[cartera_vend['dias_vencido'] > 0][['nombrecliente', 'numero', 'fecha_vencimiento', 'importe', 'dias_vencido']]
st.dataframe(df_vencidas, use_container_width=True)

# Botón para copiar el enlace del tablero
st.markdown("""
<div style='text-align:center;'>
    <a href='https://tu-enlace-del-tablero' target='_blank' style='background:#25D366;color:white;padding:12px 24px;border-radius:8px;text-decoration:none;font-size:18px;'>
        📱 Abrir este tablero desde WhatsApp
    </a>
</div>
""", unsafe_allow_html=True)

st.info("Puedes compartir este enlace por WhatsApp para que los vendedores lo abran como una app móvil.")
