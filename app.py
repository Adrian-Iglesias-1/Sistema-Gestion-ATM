import streamlit as st

st.title("🚀 ATM System - Emergency Loader")
st.success("✅ Servidor funcionando correctamente!")

st.write("Si ves esta página, Streamlit Cloud está funcionando.")
st.write("El problema anterior era de configuración, no de código.")

if st.button("Mostrar información del sistema"):
    import sys
    import os
    
    st.write("**Python version:**", sys.version)
    st.write("**Working directory:**", os.getcwd())
    st.write("**Files in current dir:**", os.listdir("."))
    
    st.write("**Environment variables:**")
    for key, value in os.environ.items():
        if "STREAMLIT" in key or "PORT" in key:
            st.write(f"- {key}: {value}")

st.info("Una vez que esto funcione, podremos cargar tu app ATM real.")
