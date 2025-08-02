import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, time
import io
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 8080))
    st.run()

# Configuración de la página
st.set_page_config(page_title="Sistema de Gestión ATM",
                   page_icon="🏦",
                   layout="wide")

# CSS limpio y funcional
st.markdown("""
<style>
    :root {
        --primary-bg: #0d1117;
        --secondary-bg: #161b22;
        --primary-green: #39ff14;
        --text-green: #7cfc00;
    }
    .stApp {
        background: linear-gradient(135deg, var(--primary-bg) 0%, #0a0f1a 100%) !important;
        font-family: 'Courier New', Monaco, monospace !important;
    }
    h1 {
        color: var(--primary-green) !important;
        text-shadow: 0 0 10px var(--primary-green), 0 0 20px var(--primary-green) !important;
    }
    #MainMenu, footer, .stDeployButton, div[data-testid="stToolbar"] {
        display: none !important;
    }
    .st-emotion-cache-1bk6s9d {
        display: none !important;
    }
</style>
""",
            unsafe_allow_html=True)

# Inicializar estados de sesión
if 'processing' not in st.session_state:
    st.session_state.processing = False
if 'resultados' not in st.session_state:
    st.session_state.resultados = {}


# --- Funciones de Utilidad ---
def normalizar_id(series):
    return series.astype(str).str.extract(r"(\d+)\s*$",
                                          expand=False).str.lstrip('0')


def combinar_fecha_hora(f_val, h_val):
    try:
        fecha = pd.to_datetime(f_val, errors='coerce').date()
        if pd.isna(fecha):
            return None
        if pd.isna(h_val):
            return datetime.combine(fecha, time.min)
        hora = h_val if isinstance(h_val, time) else pd.to_datetime(
            h_val, errors='coerce').time()
        return datetime.combine(fecha, hora)
    except:
        return None


def limpiar_th_downtime(df_raw):
    header_idx = -1
    for i, row in df_raw.head(5).iterrows():
        texto = ' '.join(row.astype(str)).upper()
        if 'TICKET KEY' in texto and 'START TIME' in texto:
            header_idx = i
            break
    if header_idx < 0:
        return pd.DataFrame()
    df = df_raw.iloc[header_idx:].reset_index(drop=True)
    df.columns = df.iloc[0].astype(str).str.strip()
    df = df.drop(0).reset_index(drop=True)
    df.columns = df.columns.str.strip()
    return df.dropna(how='all').reset_index(drop=True)


def categoria_por_sbif(codigo):
    try:
        c = str(int(float(codigo))).strip()
    except:
        c = str(codigo).strip()
    return {
        '2': 'Exigidos por SBIF',
        '6': 'Exigidos por SBIF',
        '7': 'Exigidos por SBIF',
        '5': 'Remodelación',
        '3': 'Vandalismo'
    }.get(c, 'Comunicaciones')


# --- Funciones de Lógica de Negocio ---
def procesar_exclusiones_cmm(df_cmm, df_th, tol):
    try:
        atm_col = 'ATM'
        fini = next(c for c in df_cmm
                    if 'FECHA' in c.upper() and 'INICIO' in c.upper())
        hini = next(c for c in df_cmm
                    if 'HORA' in c.upper() and 'INICIO' in c.upper())
        ffin = next(c for c in df_cmm if 'FECHA' in c.upper() and any(
            k in c.upper() for k in ['TERMINO', 'CIERRE', 'FIN']))
        hfin = next(c for c in df_cmm if 'HORA' in c.upper() and any(
            k in c.upper() for k in ['TERMINO', 'CIERRE', 'FIN']))
        sbif = next(c for c in df_cmm
                    if 'SBIF' in c.upper() or 'CODIGO' in c.upper())
    except StopIteration as e:
        st.error(
            f"Columna no encontrada en el archivo de Exclusiones-CMM: {e}")
        return pd.DataFrame()

    df_cmm['_ini'] = df_cmm.apply(
        lambda r: combinar_fecha_hora(r[fini], r[hini]), axis=1)
    df_cmm['_fin'] = df_cmm.apply(
        lambda r: combinar_fecha_hora(r[ffin], r[hfin]), axis=1)

    df_th['id_norm'] = normalizar_id(df_th['ID'])
    df_th['ini_th'] = pd.to_datetime(df_th['START TIME'], errors='coerce')
    df_th['fin_th'] = pd.to_datetime(df_th['END TIME'], errors='coerce')

    out = []
    for _, r in df_cmm.iterrows():
        atm, ini = r[atm_col], r['_ini']
        if pd.isna(ini): continue
        orig = categoria_por_sbif(r[sbif])
        norm = normalizar_id(pd.Series(str(atm))).iloc[0]
        sub = df_th[df_th['id_norm'] == norm].copy()

        if sub.empty:
            out.append({
                'ATM': atm,
                'Status Orig': orig,
                'Estado': 'No Encontrado',
                'TK TH': 'N/A',
                'Ini Orig': ini,
                'Fin Orig': r['_fin'],
                'Ini TH': pd.NaT,
                'Fin TH': pd.NaT
            })
        else:
            sub['diff'] = (sub['ini_th'] - ini).abs().dt.total_seconds() / 60
            best = sub.loc[sub['diff'].idxmin()]
            est = 'Encontrado' if best['diff'] <= tol else 'Diferencia'
            out.append({
                'ATM': atm,
                'Status Orig': orig,
                'Estado': est,
                'TK TH': best['TICKET KEY'],
                'Ini Orig': ini,
                'Fin Orig': r['_fin'],
                'Ini TH': best['ini_th'],
                'Fin TH': best['fin_th']
            })

    return pd.DataFrame(out)


# --- Interfaz Principal ---
def main():
    st.title("🏦 Sistema de Gestión ATM")
    st.markdown("**💻 Terminal de Procesamiento de Datos v2.0**")

    with st.sidebar:
        st.header("🔧 Panel de Control")
        st.subheader("📂 Carga de Archivos")
        file_dat = st.file_uploader("📊 Datos ATM (Excel)",
                                    type=['xlsx', 'xls'])
        file_th = st.file_uploader("📉 TH Downtime (Excel)",
                                   type=['xlsx', 'xls'])

        hojas = []
        excel = None
        if file_dat:
            st.success("✅ Archivo de datos cargado")
            excel = pd.ExcelFile(file_dat)
            hojas = excel.sheet_names
        else:
            st.warning("⚠️ Archivo de datos requerido")

        if file_th:
            st.success("✅ Archivo TH cargado")
        else:
            st.warning("⚠️ Archivo TH requerido")

    tab1, tab2, tab3 = st.tabs(["⚙️ Configuración", "📊 Resultados", "📋 Ayuda"])

    with tab1:
        st.subheader("⚙️ Configuración de Procesamiento")
        if not all([file_dat, file_th]):
            st.error(
                "Carga ambos archivos en el panel lateral para continuar.")
            return

        excl = st.selectbox("🔄 Exclusiones-CMM", ["No procesar"] + hojas,
                            key='excl')
        tol = st.slider("⏱️ Tolerancia (minutos)", 0, 120, 30, key='tol')

        if st.button("🚀 INICIAR PROCESAMIENTO", use_container_width=True):
            st.session_state.processing = True
            with st.spinner("🔄 Procesando datos..."):
                try:
                    df_th_raw = pd.read_excel(file_th, header=None)
                    df_th = limpiar_th_downtime(df_th_raw)
                    if df_th.empty:
                        st.error("No se pudo procesar el archivo TH Downtime.")
                        return

                    resultados = {}
                    if excl != "No procesar":
                        df_exclusiones = excel.parse(excl)
                        resultados[
                            'Exclusiones-CMM'] = procesar_exclusiones_cmm(
                                df_exclusiones, df_th, tol)

                    st.session_state.resultados = resultados
                    st.success("¡Procesamiento completado!")
                except Exception as e:
                    st.error(f"Ocurrió un error: {e}")
                finally:
                    st.session_state.processing = False
    with tab2:
        st.subheader("📊 Resultados del Procesamiento")
        if st.session_state.resultados:
            for name, df_out in st.session_state.resultados.items():
                st.markdown(f"### {name}")
                st.dataframe(df_out)
        else:
            st.info("No hay resultados para mostrar.")

    with tab3:
        st.subheader("📋 Ayuda")
        st.info("Guía de uso y solución de problemas.")


if __name__ == "__main__":
    main()
