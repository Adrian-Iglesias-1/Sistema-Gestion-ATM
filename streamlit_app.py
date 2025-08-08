import streamlit as st
import os
import importlib.util
import traceback
import glob

st.set_page_config(page_title="ATM System", page_icon="💳", layout="wide")

st.title("💳 Sistema de Gestión ATM")
st.caption("Entrypoint universal para Streamlit Cloud - detecta automáticamente la estructura del repo")

# SIEMPRE mostrar una UI mínima para pasar el health check
st.success("✅ Servidor iniciado correctamente. Health check OK.")

def _load_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo crear el spec para: {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def find_app_files():
    """Busca automáticamente main.py y test_app.py en cualquier estructura de repo"""
    base_dir = os.path.dirname(__file__)
    
    # Buscar main.py en cualquier subcarpeta
    main_candidates = glob.glob(os.path.join(base_dir, "**/main.py"), recursive=True)
    test_candidates = glob.glob(os.path.join(base_dir, "**/test_app.py"), recursive=True)
    
    return main_candidates, test_candidates

# Detectar archivos automáticamente
main_files, test_files = find_app_files()
base_dir = os.path.dirname(__file__)

st.write("**Archivos detectados:**")
if main_files:
    st.write("📁 main.py encontrado en:")
    for f in main_files:
        st.code(os.path.relpath(f, base_dir))
else:
    st.warning("❌ No se encontró main.py")

if test_files:
    st.write("📁 test_app.py encontrado en:")
    for f in test_files:
        st.code(os.path.relpath(f, base_dir))
else:
    st.warning("❌ No se encontró test_app.py")

st.divider()
st.write("**Cargar aplicación:**")

col1, col2 = st.columns(2)

with col1:
    if st.button("🚀 Cargar APP PRINCIPAL", type="primary", disabled=not main_files):
        if main_files:
            main_file = main_files[0]  # Usar el primero encontrado
            try:
                st.info(f"Cargando {os.path.relpath(main_file, base_dir)}...")
                with st.spinner("Importando módulo..."):
                    mod = _load_module_from_path("atm_main", main_file)
                
                if hasattr(mod, "main") and callable(mod.main):
                    st.success("Ejecutando main()...")
                    mod.main()
                elif hasattr(mod, "app") and callable(mod.app):
                    st.success("Ejecutando app()...")
                    mod.app()
                else:
                    st.error("El módulo no tiene función 'main()' ni 'app()' ejecutable.")
                    
            except Exception as e:
                st.error("❌ Error al cargar la aplicación principal:")
                st.exception(e)
                with st.expander("Ver traceback completo"):
                    st.code(traceback.format_exc(), language="text")

with col2:
    if st.button("🧪 Cargar APP DE PRUEBA", disabled=not test_files):
        if test_files:
            test_file = test_files[0]  # Usar el primero encontrado
            try:
                st.info(f"Cargando {os.path.relpath(test_file, base_dir)}...")
                with st.spinner("Importando módulo de prueba..."):
                    mod = _load_module_from_path("atm_test", test_file)
                
                if hasattr(mod, "main") and callable(mod.main):
                    st.success("Ejecutando main() de prueba...")
                    mod.main()
                elif hasattr(mod, "app") and callable(mod.app):
                    st.success("Ejecutando app() de prueba...")
                    mod.app()
                else:
                    st.error("El módulo de prueba no tiene función 'main()' ni 'app()' ejecutable.")
                    
            except Exception as e:
                st.error("❌ Error al cargar la aplicación de prueba:")
                st.exception(e)
                with st.expander("Ver traceback completo"):
                    st.code(traceback.format_exc(), language="text")

with st.expander("ℹ️ Información de debug"):
    st.write(f"**Directorio base:** `{base_dir}`")
    st.write(f"**Archivos en raíz:** {os.listdir(base_dir)}")
    
    # Mostrar estructura de carpetas
    st.write("**Estructura del repo:**")
    for root, dirs, files in os.walk(base_dir):
        level = root.replace(base_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        st.text(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files[:10]:  # Limitar a 10 archivos por carpeta
            st.text(f"{subindent}{file}")
        if len(files) > 10:
            st.text(f"{subindent}... y {len(files) - 10} archivos más")
