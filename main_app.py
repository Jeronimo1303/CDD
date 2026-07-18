import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta

# Configuración de la página
st.set_page_config(page_title="COVID-19 Dashboard Analítico", page_icon="🦠", layout="wide")

# ==========================================
# 1. SIMULACIÓN DE DATOS SINTÉTICOS
# ==========================================
@st.cache_data
def generar_datos_sinteticos(n_registros=10000):
    """
    Genera 10,000 registros con 8 columnas de diferentes tipos de datos.
    Se usa caché para evitar regenerar los datos con cada interacción en la UI.
    """
    np.random.seed(42)  # Para reproducibilidad
    
    # Rango de fechas (últimos 365 días)
    fecha_inicio = pd.to_datetime('2023-01-01')
    fechas = [fecha_inicio + timedelta(days=np.random.randint(0, 365)) for _ in range(n_registros)]
    
    # Construcción del DataFrame
    df = pd.DataFrame({
        'ID_Paciente': np.arange(1, n_registros + 1),                      # Entero (Identificador)
        'Fecha_Reporte': fechas,                                           # Fecha
        'Edad': np.random.randint(1, 95, n_registros),                     # Entero (Cuantitativa discreta)
        'Genero': np.random.choice(['Masculino', 'Femenino'], n_registros),# Categórica nominal
        'Region': np.random.choice(['Norte', 'Sur', 'Centro', 'Este', 'Oeste'], n_registros), # Categórica
        'Estado': np.random.choice(['Recuperado', 'Activo', 'Fallecido'], n_registros, p=[0.75, 0.20, 0.05]), 
        'Severidad': np.random.choice(['Leve', 'Moderada', 'Grave'], n_registros, p=[0.6, 0.3, 0.1]), # Ordinal
        'Carga_Viral': np.round(np.random.uniform(10.5, 999.9, n_registros), 2) # Float (Cuantitativa continua)
    })
    
    return df

df = generar_datos_sinteticos()

# ==========================================
# INTERFAZ Y BARRA LATERAL (CONTROLES)
# ==========================================
st.title("🦠 Dashboard Analítico: Simulación COVID-19")
st.markdown("Plataforma interactiva para el análisis descriptivo y exploratorio de datos epidemiológicos.")

st.sidebar.header("⚙️ Panel de Control")

# Filtros Globales
region_sel = st.sidebar.multiselect("Filtrar por Región:", options=df['Region'].unique(), default=df['Region'].unique())
estado_sel = st.sidebar.multiselect("Filtrar por Estado:", options=df['Estado'].unique(), default=df['Estado'].unique())

# Filtrar el dataframe según la selección
df_filtrado = df[(df['Region'].isin(region_sel)) & (df['Estado'].isin(estado_sel))]

# ==========================================
# 2. ESQUEMA DE MÉTRICAS (ESTADÍSTICA)
# ==========================================
st.markdown("### 📊 Indicadores Principales (KPIs)")

col1, col2, col3, col4 = st.columns(4)

# Métricas Cuantitativas
total_casos = len(df_filtrado)
edad_promedio = df_filtrado['Edad'].mean()
carga_viral_max = df_filtrado['Carga_Viral'].max()

# Métricas Cualitativas (Modas/Frecuencias)
if total_casos > 0:
    region_afectada = df_filtrado['Region'].mode()[0]
else:
    region_afectada = "N/A"

with col1:
    st.metric(label="Total Casos Registrados", value=f"{total_casos:,}")
with col2:
    st.metric(label="Edad Promedio", value=f"{edad_promedio:.1f} años")
with col3:
    st.metric(label="Región más afectada", value=str(region_afectada))
with col4:
    st.metric(label="Pico Carga Viral", value=f"{carga_viral_max:.1f} copias/mL")

st.divider()

# ==========================================
# 3. GRÁFICOS DINÁMICOS Y PERSONALIZABLES
# ==========================================

st.markdown("### 📈 Análisis Exploratorio Visual")

tab1, tab2, tab3 = st.tabs(["Tendencias Temporales", "Análisis Categórico (Umbrales)", "Distribución Cuantitativa"])

with tab1:
    st.subheader("Evolución de Casos en el Tiempo")
    # Agrupar por fecha
    df_tiempo = df_filtrado.groupby(df_filtrado['Fecha_Reporte'].dt.to_period('M')).size().reset_index(name='Casos')
    df_tiempo['Fecha_Reporte'] = df_tiempo['Fecha_Reporte'].dt.to_timestamp()
    
    fig_line = px.line(df_tiempo, x='Fecha_Reporte', y='Casos', markers=True, 
                       title="Volumen de Casos por Mes", 
                       line_shape='spline', color_discrete_sequence=['#FF4B4B'])
    st.plotly_chart(fig_line, use_container_width=True)

with tab2:
    st.subheader("Comparativa Categórica con Umbral Crítico")
    
    # Opciones de usuario para personalizar la gráfica
    col_var, col_umbral = st.columns([1, 2])
    with col_var:
        variable_cat = st.selectbox("Selecciona Variable a analizar:", ['Region', 'Severidad', 'Genero', 'Estado'])
    
    # Preparar datos de barras
    df_bar = df_filtrado[variable_cat].value_counts().reset_index()
    df_bar.columns = [variable_cat, 'Cantidad']
    
    with col_umbral:
        # Slider dinámico según la cantidad máxima de la variable elegida
        max_val = int(df_bar['Cantidad'].max()) if not df_bar.empty else 100
        umbral_alerta = st.slider("Define el Umbral de Alerta (Línea de referencia):", 
                                  min_value=0, max_value=max_val + 500, value=int(max_val*0.8), step=100)

    # Construir gráfica de barras
    fig_bar = px.bar(df_bar, x=variable_cat, y='Cantidad', text_auto=True,
                     title=f"Distribución por {variable_cat}",
                     color='Cantidad', color_continuous_scale='Blues')
    
    # Añadir línea de umbral dinámico (Interacción solicitada)
    fig_bar.add_hline(y=umbral_alerta, line_dash="dot", 
                      annotation_text=f"Umbral: {umbral_alerta}", 
                      annotation_position="top right", line_color="red")
    
    fig_bar.update_layout(xaxis_title=variable_cat, yaxis_title="Cantidad de Pacientes")
    st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    st.subheader("Dispersión: Edad vs Carga Viral")
    
    # Para no saturar el navegador con 10,000 puntos, tomamos una muestra si es muy grande
    muestra_dispersion = df_filtrado.sample(n=min(1000, len(df_filtrado)), random_state=1)
    
    color_disp = st.radio("Colorear puntos por:", ['Severidad', 'Estado', 'Genero'], horizontal=True)
    
    fig_scatter = px.scatter(muestra_dispersion, x='Edad', y='Carga_Viral', color=color_disp,
                             opacity=0.7, title=f"Relación Carga Viral vs Edad (Muestra representativa) - Agrupado por {color_disp}",
                             size_max=10, hover_data=['ID_Paciente'])
    
    st.plotly_chart(fig_scatter, use_container_width=True)

# Sección de datos crudos (opcional para el usuario)
with st.expander("Ver Base de Datos Simulada"):
    st.dataframe(df_filtrado.head(100), use_container_width=True)
    st.caption("Mostrando los primeros 100 registros aplicados a los filtros actuales.")
