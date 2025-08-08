import streamlit as st
import os
import importlib.util
import traceback

st.set_page_config(page_title="ATM System", page_icon="💳", layout="wide")

st.title("💳 Sistema de Gestión ATM")
st.caption("Entrypoint para Streamlit Cloud: inicia en modo seguro y permite cargar la app bajo demanda")


def _load_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo crear el spec para: {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

base_dir = os.path.dirname(__file__)

# Candidatos bien explícitos (ajusta si tu estructura cambia en el repo):
REAL_MAIN = os.path.join(base_dir, "Sistema-gestion-ATM", "Sistema-Gestion-ATM", "main.py")
TEST_APP = os.path.join(base_dir, "Sistema-gestion-ATM", "Sistema-Gestion-ATM", "test_app.py")

st.success("Servidor iniciado. El health check debería pasar.")
st.write("Elige qué cargar:")

col1, col2 = st.columns(2)
with col1:
    if st.button("Cargar app REAL", type="primary"):
        try:
            if not os.path.exists(REAL_MAIN):
                raise FileNotFoundError(f"No existe: {os.path.relpath(REAL_MAIN, base_dir)}")
            st.info(f"Cargando {os.path.relpath(REAL_MAIN, base_dir)} …")
            mod = _load_module_from_path("atm_real", REAL_MAIN)
            if hasattr(mod, "main") and callable(mod.main):
                mod.main()
            elif hasattr(mod, "app") and callable(mod.app):
                mod.app()
            else:
                st.warning("El módulo no tiene 'main()' ni 'app()' callable.")
        except Exception as e:
            st.error("Error al cargar la app REAL:")
            st.exception(e)
            st.code("\n".join(traceback.format_exc().splitlines()[-40:]), language="text")

with col2:
    if st.button("Cargar app de PRUEBA"):
        try:
            if not os.path.exists(TEST_APP):
                raise FileNotFoundError(f"No existe: {os.path.relpath(TEST_APP, base_dir)}")
            st.info(f"Cargando {os.path.relpath(TEST_APP, base_dir)} …")
            mod = _load_module_from_path("atm_test", TEST_APP)
            if hasattr(mod, "main") and callable(mod.main):
                mod.main()
            elif hasattr(mod, "app") and callable(mod.app):
                mod.app()
            else:
                st.warning("El módulo de prueba no tiene 'main()' ni 'app()' callable.")
        except Exception as e:
            st.error("Error al cargar la app de PRUEBA:")
            st.exception(e)
            st.code("\n".join(traceback.format_exc().splitlines()[-40:]), language="text")

st.divider()
with st.expander("Rutas detectadas"):
    st.code(f"REAL_MAIN = {os.path.relpath(REAL_MAIN, base_dir)}\nTEST_APP = {os.path.relpath(TEST_APP, base_dir)}")

