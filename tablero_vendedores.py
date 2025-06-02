import streamlit as st
import pandas as pd
import plotly.express as px

# --- Configuración de la Página ---
st.set_page_config(page_title="Tablero Vendedores", layout="wide", initial_sidebar_state="expanded")

# --- Lector de Archivos Directo ---
# Se asume que 'resumen_vendedores.xlsx' está en el mismo directorio que este script
# en el repositorio de GitHub.
file_path = "resumen_vendedores.xlsx"

try:
    df = pd.read_excel(file_path)
    st.success(f"Archivo '{file_path}' cargado exitosamente desde el repositorio.")
except FileNotFoundError:
    st.error(f"¡Error! El archivo '{file_path}' no se encontró en el repositorio. Asegúrate de que esté subido en la misma carpeta que tu script de Streamlit en GitHub.")
    st.stop()
except Exception as e:
    st.error(f"Error al leer el archivo Excel. Asegúrate de que es un archivo .xlsx válido y no está corrupto: {e}")
    st.stop()

if df.empty:
    st.error("El archivo cargado está vacío o no contiene datos válidos. Por favor, asegúrate de que el Excel tenga datos.")
    st.stop()

# --- Validar Columnas Esenciales ---
# Lista de columnas que son absolutamente necesarias para que la aplicación funcione
required_cols = [
    'nomvendedor', 'ventas_totales', 'presupuesto',
    'cobros_totales', 'presupuestocartera', 'marquilla',
    'codigo_vendedor', 'impactos', 'clientes_total' # Añadidas para la tabla resumen
]

missing_cols = [col for col in required_cols if col not in df.columns]

if missing_cols:
    st.error(f"¡Error en el archivo! Faltan las siguientes columnas esenciales: {', '.join(missing_cols)}.")
    st.info("Por favor, verifica que tu archivo Excel contenga todas estas columnas con los nombres correctos.")
    st.stop()

# --- FILTRO POR VENDEDOR ---
# Asegúrate de que 'nomvendedor' exista y limpia NaN antes de crear la lista de filtros
vendedores = sorted(df['nomvendedor'].dropna().unique())
st.sidebar.header("Filtros de Vendedores")
vendedores_sel = st.sidebar.multiselect(
    "Selecciona Vendedor(es)",
    vendedores,
    default=vendedores # Selecciona todos por defecto
)

# Filtrar DF según selección de vendedores
if vendedores_sel: # Si se seleccionaron vendedores
    dff = df[df['nomvendedor'].isin(vendedores_sel)].copy() # Usa .copy() para evitar SettingWithCopyWarning
else: # Si no se selecciona ninguno (o se desmarcan todos), muestra todos los datos
    dff = df.copy()

if dff.empty:
    st.warning("No hay datos para los vendedores seleccionados. Ajusta los filtros en la barra lateral.")
    st.stop()

# --- KPIs SOLO DEL FILTRO ---
# Aseguramos que las columnas sean numéricas y rellenamos NaN para sumas seguras
for col in ['ventas_totales', 'presupuesto', 'cobros_totales', 'presupuestocartera', 'marquilla']:
    dff[col] = pd.to_numeric(dff[col], errors='coerce').fillna(0)


ventas_total = dff['ventas_totales'].sum()
ventas_meta = dff['presupuesto'].sum()
# Evitar división por cero para avance de ventas
ventas_avance = (ventas_total / ventas_meta) * 100 if ventas_meta > 0 else (100 if ventas_total > 0 else 0)

cobros_total = dff['cobros_totales'].sum()
cobros_meta = dff['presupuestocartera'].sum()
# Evitar división por cero para avance de cobros
cobros_avance = (cobros_total / cobros_meta) * 100 if cobros_meta > 0 else (100 if cobros_total > 0 else 0)

# Calcular promedio de marquilla solo si hay datos para evitar NaN o errores
marquilla_prom = dff['marquilla'].mean() if len(dff) > 0 and dff['marquilla'].sum() > 0 else 0

# --- TABLERO ---
st.title("Tablero Estadístico de Vendedores (Acumulado Total)")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Ventas Totales", f"${ventas_total:,.0f}", f"Meta: ${ventas_meta:,.0f}")
    st.progress(min(ventas_avance/100, 1.0), text=f"{ventas_avance:.1f}% de avance")
with col2:
    st.metric("Cobros Totales", f"${cobros_total:,.0f}", f"Meta: ${cobros_meta:,.0f}")
    st.progress(min(cobros_avance/100, 1.0), text=f"{cobros_avance:.1f}% de avance")
with col3:
    st.metric("Promedio Marquillas", f"{marquilla_prom:.2f}", "Meta: 2.4")
    st.write("✔️ **Meta alcanzada**" if marquilla_prom >= 2.4 else "❌ **Meta no alcanzada**")

st.subheader("Tabla Resumen (por Vendedor)")
# Asegúrate de que solo se muestren las columnas que existen y están en la lista de requeridas
cols_to_display_in_table = [c for c in required_cols if c in dff.columns]
st.dataframe(dff[cols_to_display_in_table], use_container_width=True)

st.subheader("Gráficos de Rendimiento")

# --- Gráfico de Avance de Ventas ---
# Solo intenta graficar si hay datos y las columnas necesarias
if 'ventas_totales' in dff.columns and 'presupuesto' in dff.columns and not dff.empty and not dff['nomvendedor'].isnull().all():
    # Calcula el porcentaje de avance de ventas, manejando divisiones por cero o infinitos
    dff['% Avance Ventas'] = (dff['ventas_totales'] / dff['presupuesto']) * 100
    dff['% Avance Ventas'] = dff['% Avance Ventas'].replace([float('inf'), float('-inf')], 0).fillna(0) # Reemplaza inf/-inf con 0 y NaN con 0

    # Si todos los valores de '% Avance Ventas' son 0 después de la limpieza, el gráfico podría fallar o ser inútil.
    # También asegurar que haya suficientes datos para que Plotly cree un gráfico significativo.
    if dff['% Avance Ventas'].sum() > 0 or len(dff['nomvendedor'].unique()) > 1: # Evita gráficos de una sola barra o todo cero
        fig_ventas = px.bar(
            dff.sort_values(by='% Avance Ventas', ascending=False), # Ordena para mejor visualización
            x='nomvendedor',
            y='% Avance Ventas',
            color='% Avance Ventas',
            color_continuous_scale=["#e53935", "#ffb347", "#43a047"], # Rojo (bajo) a Verde (alto)
            title="Porcentaje de Avance de Ventas vs Presupuesto por Vendedor",
            labels={"nomvendedor": "Vendedor", "% Avance Ventas": "% Avance Avance (%)"}
        )
        fig_ventas.update_layout(xaxis_title="Vendedor", yaxis_title="Avance (%)")
        st.plotly_chart(fig_ventas, use_container_width=True)
    else:
        st.info("No hay datos significativos de avance de ventas para mostrar en el gráfico.")
else:
    st.warning("No se pueden generar los gráficos de ventas. Verifica que las columnas 'ventas_totales', 'presupuesto' y 'nomvendedor' existan y contengan datos válidos después del filtro.")

# --- Gráfico de Avance de Cobros ---
if 'cobros_totales' in dff.columns and 'presupuestocartera' in dff.columns and not dff.empty and not dff['nomvendedor'].isnull().all():
    dff['% Avance Cobros'] = (dff['cobros_totales'] / dff['presupuestocartera']) * 100
    dff['% Avance Cobros'] = dff['% Avance Cobros'].replace([float('inf'), float('-inf')], 0).fillna(0)

    if dff['% Avance Cobros'].sum() > 0 or len(dff['nomvendedor'].unique()) > 1:
        fig_cobros = px.bar(
            dff.sort_values(by='% Avance Cobros', ascending=False),
            x='nomvendedor',
            y='% Avance Cobros',
            color='% Avance Cobros',
            color_continuous_scale=["#e53935", "#ffb347", "#43a047"],
            title="Porcentaje de Avance de Cobros vs Presupuesto Cartera por Vendedor",
            labels={"nomvendedor": "Vendedor", "% Avance Cobros": "% Avance Cobros (%)"}
        )
        fig_cobros.update_layout(xaxis_title="Vendedor", yaxis_title="Avance (%)")
        st.plotly_chart(fig_cobros, use_container_width=True)
    else:
        st.info("No hay datos significativos de avance de cobros para mostrar en el gráfico.")
else:
    st.warning("No se pueden generar los gráficos de cobros. Verifica que las columnas 'cobros_totales', 'presupuestocartera' y 'nomvendedor' existan y contengan datos válidos después del filtro.")

# --- Gráfico de Promedio de Marquillas ---
if 'marquilla' in dff.columns and not dff.empty and not dff['nomvendedor'].isnull().all():
    if dff['marquilla'].sum() > 0 or len(dff['nomvendedor'].unique()) > 1:
        fig_marquilla = px.bar(
            dff.sort_values(by='marquilla', ascending=False),
            x='nomvendedor',
            y='marquilla',
            color='marquilla',
            color_continuous_scale=["#e53935", "#ffb347", "#43a047"],
            title="Promedio de Marquillas por Vendedor",
            labels={"nomvendedor": "Vendedor", "marquilla": "Promedio de Marquillas"}
        )
        fig_marquilla.update_layout(xaxis_title="Vendedor", yaxis_title="Promedio Marquillas")
        st.plotly_chart(fig_marquilla, use_container_width=True)
    else:
        st.info("No hay datos significativos de marquillas para mostrar en el gráfico.")
else:
    st.warning("No se pueden generar los gráficos de marquilla. Verifica que la columna 'marquilla' y 'nomvendedor' existan y contengan datos válidos después del filtro.")
