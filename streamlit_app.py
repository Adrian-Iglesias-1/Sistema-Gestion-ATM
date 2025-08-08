import streamlit as st
import os
import importlib.util
import traceback
import glob

def _load_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo crear el spec para: {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def find_main_app():
    """Busca automáticamente main.py en cualquier estructura de repo"""
    base_dir = os.path.dirname(__file__)
    main_candidates = glob.glob(os.path.join(base_dir, "**/main.py"), recursive=True)
    return main_candidates[0] if main_candidates else None

# Buscar y cargar la app principal automáticamente
main_file = find_main_app()

if main_file:
    try:
        # Cargar y ejecutar la app principal directamente
        mod = _load_module_from_path("atm_main", main_file)
        
        if hasattr(mod, "main") and callable(mod.main):
            mod.main()
        elif hasattr(mod, "app") and callable(mod.app):
            mod.app()
        else:
            st.error("El módulo main.py no tiene función 'main()' ni 'app()' ejecutable.")
            
    except Exception as e:
        st.error("❌ Error al cargar la aplicación ATM:")
        st.exception(e)
        st.code(traceback.format_exc(), language="text")
else:
    st.error("❌ No se encontró main.py en el repositorio.")
    st.write("Estructura del repo:")
    base_dir = os.path.dirname(__file__)
    for root, dirs, files in os.walk(base_dir):
        level = root.replace(base_dir, '').count(os.sep)
        indent = ' ' * 2 * level
        st.text(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files[:5]:
            st.text(f"{subindent}{file}")
