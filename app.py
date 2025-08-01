import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime, time
import io
from openpyxl.styles import Font, PatternFill

# --- Configuración de la página ---
st.set_page_config(page_title="Sistema de Gestión ATM",
                   page_icon="🏧",
                   layout="wide")

# --- CSS Mejorado para un look profesional y cohesivo ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

    /* --- TEMA OSCURO GLOBAL --- */
    html, body, [class*="st-"], [data-testid="stSidebarNavLink"] {
        font-family: 'Roboto', sans-serif;
    }
    .stApp {
        background-color: #1E1E1E; /* Fondo principal */
    }

    /* BARRA LATERAL */
    [data-testid="stSidebar"] {
        background-color: #252526;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #00A550; /* Verde NCR para títulos en sidebar */
    }
    [data-testid="stSidebar"] .st-emotion-cache-16txtl3 {
        color: #FAFAFA; /* Texto de labels en sidebar */
    }
    /* Estilo del File Uploader */
    [data-testid="stFileUploader"] {
        background-color: #2D2D30;
        border-radius: 8px;
        padding: 10px;
    }

    /* PANEL PRINCIPAL */
    .main {
        background-color: #1E1E1E;
        color: #FAFAFA;
    }

    /* Ocultar elementos de Streamlit */
    #MainMenu, footer, header {
        visibility: hidden;
    }

    /* --- COMPONENTES --- */
    .stButton>button {
        background-color: #00A550;
        color: #FFFFFF;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: bold;
        transition: background-color 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #008741;
    }

    h1, h2 { color: #FAFAFA; }
    h3 { color: #00A550; }

    [data-testid="stMetric"] {
        background-color: #2D2D30;
        border: 1px solid #444444;
        border-radius: 8px;
        padding: 15px;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #444444;
    }

    /* Pantalla de Bienvenida */
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 60vh;
        text-align: center;
        color: #A0A0A0;
    }
    .welcome-icon {
        font-size: 6rem;
        margin-bottom: 1rem;
    }
</style>
""",
            unsafe_allow_html=True)


# --- (Las funciones de utilidad y procesamiento se mantienen igual) ---
def normalizar_id(series):
    return series.astype(str).str.extract(r"(\d+)\s*$",
                                          expand=False).str.lstrip('0')


def combinar_fecha_hora(f_val, h_val):
    try:
        fecha = pd.to_datetime(f_val, errors='coerce').date()
        if pd.isna(fecha): return pd.NaT
        if pd.isna(h_val): return datetime.combine(fecha, time.min)
        hora = h_val if isinstance(h_val, time) else pd.to_datetime(
            h_val, errors='coerce').time()
        return datetime.combine(fecha, hora)
    except:
        return pd.NaT


def limpiar_th_downtime(df_raw):
    header_idx = -1
    for i, row in df_raw.head(10).iterrows():
        texto = ' '.join(row.astype(str)).upper()
        if 'TICKET KEY' in texto and 'START TIME' in texto:
            header_idx = i
            break
    if header_idx < 0: return pd.DataFrame()
    df = df_raw.iloc[header_idx:].copy().reset_index(drop=True)
    df.columns = df.iloc[0].astype(str).str.strip().str.upper()
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


def categoria_por_resumen_falla(falla):
    m = str(falla).lower()
    mapping = {
        'dispensador con falla': 'Dispenser No Paga FLMG',
        'impresora de recibos': 'Impresora Recibos FLMG',
        'bna con falla': 'BNA/SDM/Deposito FLMG',
        '4 gavetas': '4 Gavetas Indisponibles',
        'host down': 'Aplicacion Fuera de Servicio',
        'comunicación con falla': 'Comunicaciones',
        'lector de tarjeta con falla': 'Lector de Tarjeta FLMG',
        'impresora sin papel': 'Sin Papel Recibos',
        'modo supervisor': 'Supervisor',
        'cash out': 'Cash Out'
    }
    for k, v in mapping.items():
        if k in m: return v
    return 'Comunicaciones'


def categoria_por_falla_ncr(falla):
    m = str(falla).lower()
    mapping = {
        'falla de configuración': 'Falla de HW / Servicio Técnico',
        'hardware': 'Falla de HW / Servicio Técnico',
        'pantalla con fallas': 'Falla de HW / Servicio Técnico',
        'lector de tarjeta con falla': 'Lector de Tarjeta SLMG',
        'impresora con falla': 'Impresora de recibos SLMG',
        'dispensador con falla': 'Dispenser no paga SLMG',
        'bna con falla': 'BNA/SDM/Deposito SLMG'
    }
    for k, v in mapping.items():
        if k in m: return v
    return 'Falla de HW / Servicio Técnico'


def procesar_exclusiones_cmm(df_cmm, df_th, tol):
    st.info("🔍 Procesando Exclusiones-CMM…")
    col_atm = 'ATM'
    col_fini = next((c for c in df_cmm.columns
                     if 'FECHA' in c.upper() and 'INICIO' in c.upper()), None)
    col_hini = next((c for c in df_cmm.columns
                     if 'HORA' in c.upper() and 'INICIO' in c.upper()), None)
    col_ffin = next((c for c in df_cmm.columns if 'FECHA' in c.upper() and any(
        k in c.upper() for k in ['TERMINO', 'CIERRE', 'FIN'])), None)
    col_hfin = next((c for c in df_cmm.columns if 'HORA' in c.upper() and any(
        k in c.upper() for k in ['TERMINO', 'CIERRE', 'FIN'])), None)
    col_sbif = next((c for c in df_cmm.columns
                     if 'SBIF' in c.upper() or 'CODIGO' in c.upper()), None)

    if not all([col_atm, col_fini, col_hini, col_ffin, col_hfin, col_sbif]):
        st.error("Columnas requeridas para CMM no encontradas.")
        return pd.DataFrame()

    df_cmm['_ini'] = df_cmm.apply(
        lambda r: combinar_fecha_hora(r[col_fini], r[col_hini]), axis=1)
    df_cmm['_fin'] = df_cmm.apply(
        lambda r: combinar_fecha_hora(r[col_ffin], r[col_hfin]), axis=1)
    df_th['id_norm'] = normalizar_id(df_th['ID'])
    df_th['ini_th'] = pd.to_datetime(df_th['START TIME'], errors='coerce')
    df_th['fin_th'] = pd.to_datetime(df_th['END TIME'], errors='coerce')
    result = []
    for _, r in df_cmm.iterrows():
        atm, ini, fin = r[col_atm], r['_ini'], r['_fin']
        if pd.isna(ini): continue
        orig_cat = categoria_por_sbif(r[col_sbif])
        norm = normalizar_id(pd.Series(str(atm))).iloc[0]
        subset = df_th[df_th['id_norm'] == norm]
        if subset.empty:
            result.append({
                'ATM': atm,
                'Status Orig': orig_cat,
                'Estado': 'No Encontrado',
                'TK TH': 'N/A',
                'Cat TH': 'N/A',
                'Ini Orig': ini,
                'Fin Orig': fin,
                'Ini TH': pd.NaT,
                'Fin TH': pd.NaT
            })
        else:
            subset['diff'] = (subset['ini_th'] -
                              ini).abs().dt.total_seconds() / 60
            best = subset.loc[subset['diff'].idxmin()]
            estado = 'Encontrado' if best[
                'diff'] <= tol else 'Diferencia de Tiempo'
            result.append({
                'ATM': atm,
                'Status Orig': orig_cat,
                'Estado': estado,
                'TK TH': best['TICKET KEY'],
                'Cat TH': best['CATEGORY'],
                'Ini Orig': ini,
                'Fin Orig': fin,
                'Ini TH': best['ini_th'],
                'Fin TH': best['fin_th']
            })
    return pd.DataFrame(result)


def procesar_base_fallas(df_base, df_th):
    st.info("🔍 Procesando Base Fallas…")
    df_base['id_norm'] = normalizar_id(df_base['ATM'])
    df_base['Status'] = df_base['RESUMEN FALLA'].apply(
        categoria_por_resumen_falla)
    df_th2 = df_th.copy()
    df_th2['id_norm'] = normalizar_id(df_th2['ID'])
    df_th2['sd'] = pd.to_datetime(df_th2['START TIME'], errors='coerce')
    idx = df_th2.dropna(subset=['sd']).groupby('id_norm')['sd'].idxmax()
    df_latest = df_th2.loc[idx]
    df_latest['Inicio TH'] = df_latest['sd']
    df_latest['Fin TH'] = pd.to_datetime(df_latest['END TIME'],
                                         errors='coerce')
    merged = pd.merge(
        df_base,
        df_latest[['id_norm', 'TICKET KEY', 'Inicio TH', 'Fin TH']],
        on='id_norm',
        how='left')
    merged['Estado'] = np.where(merged['TICKET KEY'].notna(),
                                'Encontrado en TH', 'No Encontrado')
    merged['TK TH'] = merged['TICKET KEY'].fillna('N/A')
    return merged[['ATM', 'TK TH', 'Status', 'Estado', 'Inicio TH', 'Fin TH']]


def procesar_base_fallas_ncr(df_ncr, df_th, tol=30):
    st.info("🔍 Procesando Base Fallas NCR…")
    df_ncr['inicio'] = df_ncr.apply(
        lambda r: combinar_fecha_hora(r['FECHA INICIAL'], r['HORA INICIAL']),
        axis=1) if 'FECHA INICIAL' in df_ncr else pd.NaT
    df_th['id_norm'] = normalizar_id(df_th['ID'])
    df_th['inicio_th'] = pd.to_datetime(df_th['START TIME'], errors='coerce')
    df_th['fin_th'] = pd.to_datetime(df_th['END TIME'], errors='coerce')
    df_th['REFERENCE'] = df_th['REFERENCE'].astype(str).str.strip()
    rows = []
    for _, r in df_ncr.iterrows():
        atm, wo, falla, inicio = r['ATM'], str(
            r['WO']).strip(), r['FALLA NCR'], r['inicio']
        cat = categoria_por_falla_ncr(falla)
        estado, tk, i_th, f_th = 'No Encontrado', 'N/A', pd.NaT, pd.NaT
        if wo and wo.lower() != 'nan':
            ref = df_th[df_th['REFERENCE'] == wo]
            if not ref.empty:
                m = ref.iloc[0]
                estado, tk, i_th, f_th = 'Encontrado por WO', m[
                    'TICKET KEY'], m['inicio_th'], m['fin_th']
        if estado == 'No Encontrado' and pd.notna(inicio):
            norm = normalizar_id(pd.Series(str(atm))).iloc[0]
            subset = df_th[df_th['id_norm'] == norm].copy()
            if not subset.empty:
                subset['diff'] = (subset['inicio_th'] -
                                  inicio).abs().dt.total_seconds() / 60
                filt = subset[subset['diff'] <= tol]
                if not filt.empty:
                    best = filt.loc[filt['diff'].idxmin()]
                    estado, tk, i_th, f_th = 'Encontrado (ID+Tiempo)', best[
                        'TICKET KEY'], best['inicio_th'], best['fin_th']
                else:
                    best = subset.loc[subset['diff'].idxmin()]
                    estado, tk, i_th, f_th = 'Diferencia de Tiempo', best[
                        'TICKET KEY'], best['inicio_th'], best['fin_th']

        rows.append({
            'ATM': atm,
            'TK TH': tk,
            'Status (Categoría)': cat,
            'Inicio TH': i_th,
            'Fin TH': f_th,
            'Estado Búsqueda': estado
        })
    return pd.DataFrame(rows)


# --- Interfaz Principal ---
def main():
    # --- BARRA LATERAL PARA TODOS LOS CONTROLES ---
    with st.sidebar:
        st.header("1. Cargar Archivos")
        file_dat = st.file_uploader("Archivo de Datos (CMM, Fallas, NCR)",
                                    type=['xlsx', 'xls'])
        file_th = st.file_uploader("Archivo TH Downtime", type=['xlsx', 'xls'])

        st.divider()

        hojas = []
        if file_dat:
            try:
                st.session_state.excel_file = pd.ExcelFile(file_dat)
                hojas = st.session_state.excel_file.sheet_names
            except Exception as e:
                st.error(f"No se pudo leer el archivo.")

        with st.container(border=True):
            st.header("2. Configurar Hojas")
            excl = st.selectbox("Hoja Exclusiones-CMM",
                                ['No procesar'] + hojas)
            base = st.selectbox("Hoja Base Fallas", ['No procesar'] + hojas)
            ncr = st.selectbox("Hoja Base Fallas NCR", ['No procesar'] + hojas)
            tol = st.slider("Tolerancia de tiempo (minutos)", 0, 120, 30)

        procesar_btn = st.button("🚀 Procesar Archivos",
                                 use_container_width=True,
                                 type="primary")

    # --- ÁREA PRINCIPAL PARA TÍTULO Y RESULTADOS ---
    c1, c2 = st.columns([1, 10])
    with c1:
        st.write("🏧")
    with c2:
        st.title("Sistema de Gestión de Fallas ATM")
        st.write(
            "Herramienta para la unificación y análisis de datos de fallas.")

    st.divider()

    # Manejo del estado inicial y de los resultados
    if 'resultados' not in st.session_state:
        st.session_state.resultados = None

    if procesar_btn:
        if not file_dat or not file_th:
            st.error(
                "⚠️ Por favor, carga ambos archivos en la barra lateral antes de procesar."
            )
        else:
            with st.spinner("Procesando datos... por favor espera."):
                try:
                    excel = st.session_state.excel_file
                    df_th_raw = pd.read_excel(file_th, header=None)
                    df_th = limpiar_th_downtime(df_th_raw)

                    if df_th.empty:
                        st.warning(
                            "El archivo TH Downtime no pudo ser procesado o está vacío."
                        )
                        return

                    res = {}
                    if excl != 'No procesar':
                        res['Exclusiones-CMM'] = procesar_exclusiones_cmm(
                            excel.parse(excl), df_th.copy(), tol)
                    if base != 'No procesar':
                        res['Base Fallas'] = procesar_base_fallas(
                            excel.parse(base), df_th.copy())
                    if ncr != 'No procesar':
                        res['Base Fallas NCR'] = procesar_base_fallas_ncr(
                            excel.parse(ncr), df_th.copy(), tol)

                    st.session_state.resultados = res
                    if not res:
                        st.warning(
                            "No se seleccionó ninguna hoja para procesar.")
                    else:
                        st.success("✅ ¡Procesamiento completado con éxito!")

                except Exception as e:
                    st.error(f"❌ Ocurrió un error durante el procesamiento.")
                    st.exception(e)

    # Visualización de la pantalla de bienvenida o los resultados
    if st.session_state.resultados is None:
        st.markdown("""
        <div class="welcome-container">
            <div class="welcome-icon">👈</div>
            <h2>Comienza por cargar tus archivos</h2>
            <p>Una vez cargados, selecciona las hojas correspondientes en la barra lateral y haz clic en "Procesar".</p>
        </div>
        """,
                    unsafe_allow_html=True)
    elif st.session_state.resultados:
        st.header("3. Resultados del Análisis")
        res = st.session_state.resultados

        tabs = st.tabs(list(res.keys()))
        for tab, (name, df_out) in zip(tabs, res.items()):
            with tab:
                with st.container(border=True):
                    total_filas = len(df_out)
                    col_estado = next(
                        (c for c in df_out.columns if 'Estado' in c), None)
                    if col_estado:
                        encontrados = df_out[df_out[col_estado].str.contains(
                            'Encontrado', na=False)].shape[0]
                        porc_encontrado = (encontrados / total_filas *
                                           100) if total_filas > 0 else 0
                    else:
                        encontrados, porc_encontrado = "N/A", 0

                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Registros", f"{total_filas}")
                    c2.metric("Coincidencias", f"{encontrados}")
                    c3.metric("% Coincidencia", f"{porc_encontrado:.1f}%")

                st.dataframe(df_out, use_container_width=True)

            # --- Lógica de Descarga (aún necesita ser creada/refinada) ---
            # st.download_button(...)


if __name__ == '__main__':
    main()
