import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import timedelta

# Configuración de la página
st.set_page_config(page_title="Gestión de Riesgo Meteorológico - Medellín", page_icon="🌤️", layout="wide")

# ==========================================
# 1. PERSONALIZACIÓN DEL PANEL IZQUIERDO Y SEGURIDAD
# ==========================================
st.sidebar.markdown("### 🎓 EAFIT 2026")
st.sidebar.markdown("**📚 Ciencia de Datos**")
st.sidebar.markdown("**👤 Jeronimo Acosta**")
st.sidebar.markdown("**📅 Julio de 2026**")
st.sidebar.divider()

# Clave de acceso
st.sidebar.header("🔒 Autenticación")
password = st.sidebar.text_input("Ingrese el código de acceso:", type="password")

if password != "4650":
    st.warning("⚠️ Acceso denegado. Por favor, introduzca el código de acceso en el panel lateral para operar el dashboard.")
    st.stop()
else:
    st.sidebar.success("✅ Acceso concedido")

# ==========================================
# 2. SIMULACIÓN DE DATOS SINTÉTICOS (METEOROLOGÍA MEDELLÍN)
# ==========================================
@st.cache_data
def generar_datos_meteorologicos(n_registros=500):
    np.random.seed(42)
    
    # 1. Serie de tiempo (Frecuencia diaria)
    fechas = pd.date_range(start='2026-01-01', periods=n_registros, freq='D')
    
    comunas = ['Popular', 'Santa Cruz', 'Manrique', 'Aranjuez', 'Castilla', 
               'Doce de Octubre', 'Robledo', 'Villa Hermosa', 'Buenos Aires', 
               'La Candelaria', 'Laureles-Estadio', 'La América', 'San Javier', 
               'El Poblado', 'Guayabal', 'Belén']
    
    df = pd.DataFrame({
        'Fecha': fechas,                                                                # 1. Fecha (Serie de tiempo)
        'Comuna': np.random.choice(comunas, n_registros),                               # 2. Comuna (Categórica)
        'Temperatura_C': np.round(np.random.normal(23, 4, n_registros), 1),             # 3. Temperatura
        'Humedad_Pct': np.round(np.random.uniform(40, 100, n_registros), 1),            # 4. Humedad
        'Velocidad_Viento_kmh': np.round(np.random.exponential(12, n_registros), 1),    # 5. Viento
        'Precipitacion_mm': np.round(np.random.exponential(15, n_registros), 1),        # 6. Lluvia
        'Poblacion_Afectable': np.random.randint(5000, 150000, n_registros),            # 7. Población en riesgo
        'Indice_Calidad_Aire': np.random.randint(20, 180, n_registros)                  # 8. ICA
    })
    
    # 9. Nivel de Riesgo (Categórica Ordinal)
    def calcular_riesgo(row):
        if row['Precipitacion_mm'] > 50 or row['Velocidad_Viento_kmh'] > 40: return 'Crítico'
        elif row['Precipitacion_mm'] > 30 or row['Indice_Calidad_Aire'] > 120: return 'Alto'
        elif row['Precipitacion_mm'] > 10: return 'Medio'
        return 'Bajo'
        
    df['Nivel_Riesgo'] = df.apply(calcular_riesgo, axis=1)
    
    # 10. Alerta Deslizamiento (Booleana/Categórica)
    condicion_deslizamiento = (df['Precipitacion_mm'] > 40) & (df['Humedad_Pct'] > 85)
    df['Alerta_Deslizamiento'] = np.where(condicion_deslizamiento, 'Sí', 'No')
    
    return df

df = generar_datos_meteorologicos()

# ==========================================
# INTERFAZ Y FILTROS LATERALES
# ==========================================
st.title("🌦️ Dashboard de Riesgo Meteorológico - Medellín")
st.markdown("Herramienta de análisis de condiciones climáticas y riesgos para la toma de decisiones de la Alcaldía.")

st.sidebar.header("⚙️ Filtros de Análisis")
comuna_sel = st.sidebar.multiselect("Filtrar por Comuna:", options=df['Comuna'].unique(), default=df['Comuna'].unique()[:5])
riesgo_sel = st.sidebar.multiselect("Nivel de Riesgo:", options=df['Nivel_Riesgo'].unique(), default=df['Nivel_Riesgo'].unique())

df_filtrado = df[(df['Comuna'].isin(comuna_sel)) & (df['Nivel_Riesgo'].isin(riesgo_sel))]

# ==========================================
# 3. ESQUEMA DE MÉTRICAS 
# ==========================================
st.markdown("### 📊 Panel de Alertas y Métricas")

col1, col2, col3, col4 = st.columns(4)

alertas_activas = len(df_filtrado[df_filtrado['Alerta_Deslizamiento'] == 'Sí'])
precipitacion_max = df_filtrado['Precipitacion_mm'].max() if not df_filtrado.empty else 0
temp_promedio = df_filtrado['Temperatura_C'].mean() if not df_filtrado.empty else 0
pob_riesgo = df_filtrado[df_filtrado['Nivel_Riesgo'].isin(['Alto', 'Crítico'])]['Poblacion_Afectable'].sum()

with col1:
    st.metric(label="Alertas de Deslizamiento (Sí)", value=alertas_activas)
with col2:
    st.metric(label="Precipitación Máxima", value=f"{precipitacion_max} mm")
with col3:
    st.metric(label="Temperatura Promedio", value=f"{temp_promedio:.1f} °C")
with col4:
    st.metric(label="Población en Alto Riesgo", value=f"{pob_riesgo:,}")

st.divider()

# ==========================================
# 4. GRÁFICOS DINÁMICOS E INTERACCIÓN
# ==========================================
st.markdown("### 📈 Análisis Visual de Variables")

tab1, tab2, tab3 = st.tabs(["Serie de Tiempo", "Análisis por Comuna y Umbrales", "Dispersión Multivariable"])

with tab1:
    st.subheader("Comportamiento Meteorológico en el Tiempo")
    var_tiempo = st.selectbox("Seleccione la variable a visualizar en el tiempo:", 
                              ['Precipitacion_mm', 'Temperatura_C', 'Indice_Calidad_Aire', 'Velocidad_Viento_kmh'])
    
    # Agrupar por fecha promedio en base a filtros
    df_tiempo = df_filtrado.groupby('Fecha')[var_tiempo].mean().reset_index()
    
    fig_line = px.line(df_tiempo, x='Fecha', y=var_tiempo, 
                       title=f"Evolución Diaria Promedio de {var_tiempo}",
                       color_discrete_sequence=['#1E88E5'])
    st.plotly_chart(fig_line, use_container_width=True)

with tab2:
    st.subheader("Comparativa por Comunas y Control de Umbrales")
    col_var, col_umbral = st.columns([1, 2])
    
    with col_var:
        variable_bar = st.selectbox("Variable para agrupar por Comuna:", 
                                    ['Precipitacion_mm', 'Poblacion_Afectable', 'Indice_Calidad_Aire'])
    
    # Promedio o Suma dependiendo de la variable
    if variable_bar == 'Poblacion_Afectable':
        df_bar = df_filtrado.groupby('Comuna')[variable_bar].sum().reset_index()
    else:
        df_bar = df_filtrado.groupby('Comuna')[variable_bar].mean().reset_index()
        
    with col_umbral:
        max_val = float(df_bar[variable_bar].max()) if not df_bar.empty else 100.0
        umbral_riesgo = st.slider(f"Definir Umbral Crítico para {variable_bar}:", 
                                  min_value=0.0, max_value=max_val * 1.2, value=max_val * 0.7, step=max_val/20)

    fig_bar = px.bar(df_bar, x='Comuna', y=variable_bar, text_auto='.2f',
                     title=f"{variable_bar} por Comuna",
                     color=variable_bar, color_continuous_scale='Reds')
    
    fig_bar.add_hline(y=umbral_riesgo, line_dash="dash", line_color="black",
                      annotation_text=f"Umbral: {umbral_riesgo:.1f}", annotation_position="top left")
    
    st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    st.subheader("Relación entre Variables y Riesgo")
    var_x = st.selectbox("Variable Eje X:", ['Temperatura_C', 'Velocidad_Viento_kmh'], index=0)
    var_y = st.selectbox("Variable Eje Y:", ['Humedad_Pct', 'Precipitacion_mm'], index=1)
    
    fig_scatter = px.scatter(df_filtrado, x=var_x, y=var_y, color='Nivel_Riesgo', 
                             size='Poblacion_Afectable', hover_data=['Comuna', 'Fecha'],
                             title=f"Dispersión: {var_x} vs {var_y} (Tamaño = Población)",
                             color_discrete_map={'Bajo': 'green', 'Medio': 'yellow', 'Alto': 'orange', 'Crítico': 'red'})
    
    st.plotly_chart(fig_scatter, use_container_width=True)

with st.expander("Ver Datos Crudos Simulados (Medellín)"):
    st.dataframe(df_filtrado.head(150), use_container_width=True)
