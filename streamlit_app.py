import streamlit as st
import os
import importlib.util
import traceback

st.set_page_config(page_title="ATM System", page_icon="💳", layout="wide")

st.title("💳 Sistema de Gestión ATM")
st.caption("Loader de la app para Streamlit Cloud (auto-import por ruta de archivo)")


def _load_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"No se pudo crear el spec para: {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_app():
    base_dir = os.path.dirname(__file__)

    # Candidatos: main real y test de respaldo
    candidates = [
        os.path.join(base_dir, "Sistema-gestion-ATM", "Sistema-Gestion-ATM", "main.py"),
        os.path.join(base_dir, "Sistema-gestion-ATM", "Sistema-Gestion-ATM", "test_app.py"),
    ]

    last_error = None
    for idx, path in enumerate(candidates, start=1):
        if not os.path.exists(path):
            continue
        try:
            st.info(f"Intentando cargar: {os.path.relpath(path, base_dir)}")
            module = _load_module_from_path(f"atm_app_{idx}", path)
            # Ejecutar main() si existe; si no, intentar app()
            if hasattr(module, "main") and callable(module.main):
                module.main()
                return
            if hasattr(module, "app") and callable(module.app):
                module.app()
                return
            st.warning(
                "El módulo se cargó, pero no tiene una función callable 'main()' ni 'app()'."
            )
        except Exception as e:
            last_error = e
            st.error(f"Fallo al cargar {os.path.relpath(path, base_dir)}")
            st.exception(e)
            st.code("\n".join(traceback.format_exc().splitlines()[-20:]), language="text")

    # Si nada funcionó, mostrar guía
    st.error("No se pudo iniciar la aplicación.")
    st.write(
        "Verifica que exista alguno de estos archivos y que contenga una función 'main()' o 'app()':"
    )
    for p in candidates:
        st.code(os.path.relpath(p, base_dir))
    st.write(
        "Si estás en Streamlit Cloud, pon el Main file path en 'streamlit_app.py'."
    )


if __name__ == "__main__":
    # Ejecutar cuando se corre localmente con 'python streamlit_app.py'
    run_app()
else:
    # Streamlit importa el módulo: ejecutamos al import
    run_app()
