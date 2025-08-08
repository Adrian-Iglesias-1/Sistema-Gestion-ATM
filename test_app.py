import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Configuración básica
st.set_page_config(
    page_title="Test ATM System",
    page_icon="🏧",
    layout="wide"
)

# CSS mínimo
st.markdown("""
<style>
.stApp {
    background-color: #0d1117;
    color: #39ff14;
}
</style>
""", unsafe_allow_html=True)

# Aplicación mínima
st.title("🏧 Sistema de Gestión ATM - Test")
st.write("Esta es una versión de prueba para verificar que funciona en Streamlit Cloud")

# Sidebar básico
with st.sidebar:
    st.header("Panel de Control")
    test_file = st.file_uploader("Subir archivo de prueba", type=['xlsx', 'csv'])
    
    if test_file:
        st.success("Archivo cargado correctamente")
    else:
        st.warning("No hay archivo cargado")

# Contenido principal
tab1, tab2 = st.tabs(["Prueba", "Info"])

with tab1:
    st.subheader("Prueba de Funcionalidad")
    
    if st.button("Probar Funcionalidad"):
        st.success("✅ La aplicación funciona correctamente!")
        
        # Crear datos de prueba
        data = {
            'ATM': ['ATM001', 'ATM002', 'ATM003'],
            'Estado': ['Activo', 'Inactivo', 'Mantenimiento'],
            'Fecha': [datetime.now().strftime('%Y-%m-%d')] * 3
        }
        df = pd.DataFrame(data)
        st.dataframe(df)

with tab2:
    st.subheader("Información del Sistema")
    st.write("- Streamlit funcionando ✅")
    st.write("- Pandas funcionando ✅") 
    st.write("- NumPy funcionando ✅")
    st.write(f"- Fecha actual: {datetime.now()}")

st.info("Si ves este mensaje, la aplicación está funcionando correctamente en Streamlit Cloud")
