import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
from utils.data_processor import DataProcessor
from utils.matcher import WorkOrderMatcher

def main():
    st.set_page_config(
        page_title="Sistema de Gestión ATM",
        page_icon="🏧",
        layout="wide"
    )
    
    st.title("🏧 Sistema de Gestión ATM")
    st.markdown("### Procesamiento de Órdenes de Trabajo y Registros de Downtime")
    
    # Initialize session state
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'matches' not in st.session_state:
        st.session_state.matches = None
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        # Time tolerance configuration
        tolerance_minutes = st.number_input(
            "Tolerancia de tiempo (minutos)",
            min_value=1,
            max_value=180,
            value=30,
            help="Diferencia máxima de tiempo permitida para considerar una coincidencia"
        )
        
        st.markdown("---")
        st.markdown("**Formatos soportados:**")
        st.markdown("- Excel (.xlsx, .xls)")
        st.markdown("- Archivos con órdenes de trabajo y downtime")
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📁 Cargar Archivo de Órdenes de Trabajo")
        work_orders_file = st.file_uploader(
            "Seleccione el archivo Excel con órdenes de trabajo",
            type=['xlsx', 'xls'],
            key="work_orders",
            help="Archivo debe contener columnas: ATM_ID, Fecha_Hora, Descripcion"
        )
    
    with col2:
        st.subheader("📁 Cargar Archivo de Downtime")
        downtime_file = st.file_uploader(
            "Seleccione el archivo Excel con registros de downtime",
            type=['xlsx', 'xls'],
            key="downtime",
            help="Archivo debe contener columnas: ATM_ID, Fecha_Inicio, Fecha_Fin, Causa"
        )
    
    # Process files when both are uploaded
    if work_orders_file and downtime_file:
        if st.button("🔄 Procesar Archivos", type="primary"):
            with st.spinner("Procesando archivos..."):
                try:
                    # Initialize data processor
                    processor = DataProcessor()
                    
                    # Process work orders
                    work_orders_df = processor.process_work_orders(work_orders_file)
                    
                    # Process downtime records
                    downtime_df = processor.process_downtime(downtime_file)
                    
                    # Initialize matcher and find matches
                    matcher = WorkOrderMatcher(tolerance_minutes)
                    matches_df = matcher.find_matches(work_orders_df, downtime_df)
                    
                    # Store in session state
                    st.session_state.processed_data = {
                        'work_orders': work_orders_df,
                        'downtime': downtime_df
                    }
                    st.session_state.matches = matches_df
                    
                    st.success(f"✅ Procesamiento completado. Se encontraron {len(matches_df)} coincidencias.")
                    
                except Exception as e:
                    st.error(f"❌ Error al procesar los archivos: {str(e)}")
                    st.info("Verifique que los archivos tengan el formato correcto y las columnas requeridas.")
    
    # Display results if available
    if st.session_state.matches is not None:
        st.markdown("---")
        st.subheader("📊 Resultados de Coincidencias")
        
        matches_df = st.session_state.matches
        
        if len(matches_df) > 0:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Coincidencias", len(matches_df))
            
            with col2:
                unique_atms = matches_df['ATM_ID'].nunique()
                st.metric("ATMs Afectados", unique_atms)
            
            with col3:
                avg_duration = matches_df['Duracion_Downtime_Horas'].mean()
                st.metric("Duración Promedio (hrs)", f"{float(avg_duration):.1f}")
            
            with col4:
                if st.session_state.processed_data:
                    total_orders = len(st.session_state.processed_data['work_orders'])
                    match_rate = (len(matches_df) / total_orders) * 100
                    st.metric("Tasa de Coincidencia", f"{match_rate:.1f}%")
                else:
                    st.metric("Tasa de Coincidencia", "0.0%")
            
            # Filter options
            st.markdown("### 🔍 Filtros")
            filter_col1, filter_col2, filter_col3 = st.columns(3)
            
            with filter_col1:
                selected_atms = st.multiselect(
                    "Filtrar por ATM ID",
                    options=sorted(matches_df['ATM_ID'].unique()),
                    default=[]
                )
            
            with filter_col2:
                min_duration = st.number_input(
                    "Duración mínima (horas)",
                    min_value=0.0,
                    value=0.0,
                    step=0.5
                )
            
            with filter_col3:
                date_range = st.date_input(
                    "Rango de fechas",
                    value=[],
                    help="Seleccione rango de fechas para filtrar"
                )
            
            # Apply filters
            filtered_df = matches_df.copy()
            
            if selected_atms:
                filtered_df = filtered_df[filtered_df['ATM_ID'].isin(selected_atms)]
            
            if min_duration > 0:
                filtered_df = filtered_df[filtered_df['Duracion_Downtime_Horas'] >= min_duration]
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                filtered_df = filtered_df[
                    (pd.to_datetime(filtered_df['Fecha_Orden']).dt.date >= start_date) &
                    (pd.to_datetime(filtered_df['Fecha_Orden']).dt.date <= end_date)
                ]
            
            # Display filtered results
            st.markdown(f"### 📋 Tabla de Resultados ({len(filtered_df)} registros)")
            
            if len(filtered_df) > 0:
                # Format datetime columns for display
                display_df = filtered_df.copy()
                display_df['Fecha_Orden'] = pd.to_datetime(display_df['Fecha_Orden']).dt.strftime('%Y-%m-%d %H:%M')
                display_df['Inicio_Downtime'] = pd.to_datetime(display_df['Inicio_Downtime']).dt.strftime('%Y-%m-%d %H:%M')
                display_df['Fin_Downtime'] = pd.to_datetime(display_df['Fin_Downtime']).dt.strftime('%Y-%m-%d %H:%M')
                display_df['Duracion_Downtime_Horas'] = pd.to_numeric(display_df['Duracion_Downtime_Horas']).round(2)
                display_df['Diferencia_Tiempo_Minutos'] = pd.to_numeric(display_df['Diferencia_Tiempo_Minutos']).round(1)
                
                # Reorder columns for better display
                column_order = [
                    'ATM_ID', 'Fecha_Orden', 'Descripcion_Orden', 
                    'Inicio_Downtime', 'Fin_Downtime', 'Causa_Downtime',
                    'Duracion_Downtime_Horas', 'Diferencia_Tiempo_Minutos'
                ]
                display_df = display_df[column_order]
                
                # Rename columns for Spanish display
                display_df.columns = [
                    'ID ATM', 'Fecha Orden', 'Descripción Orden',
                    'Inicio Downtime', 'Fin Downtime', 'Causa Downtime',
                    'Duración (hrs)', 'Diferencia (min)'
                ]
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
                
                # Export functionality
                st.markdown("### 💾 Exportar Resultados")
                
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if st.button("📥 Descargar CSV", type="secondary"):
                        # Convert to CSV
                        csv_buffer = io.StringIO()
                        # Ensure filtered_df is a pandas DataFrame
                        if isinstance(filtered_df, pd.DataFrame):
                            filtered_df.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                        else:
                            pd.DataFrame(filtered_df).to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                        csv_data = csv_buffer.getvalue()
                        
                        # Generate filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"coincidencias_atm_{timestamp}.csv"
                        
                        st.download_button(
                            label="💾 Confirmar Descarga",
                            data=csv_data,
                            file_name=filename,
                            mime='text/csv',
                            help="Haga clic para descargar el archivo CSV"
                        )
                
                with col2:
                    st.info(f"📊 Se exportarán {len(filtered_df)} registros con los filtros aplicados")
            
            else:
                st.warning("⚠️ No hay registros que coincidan con los filtros aplicados.")
        
        else:
            st.warning("⚠️ No se encontraron coincidencias entre los archivos procesados.")
            st.info("Intente aumentar la tolerancia de tiempo o verifique que los datos contengan ATMs en común.")
    
    # Instructions section
    if st.session_state.matches is None:
        st.markdown("---")
        st.subheader("📖 Instrucciones de Uso")
        
        with st.expander("Formato requerido para archivos Excel", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Archivo de Órdenes de Trabajo:**")
                st.markdown("""
                - `ATM_ID`: Identificador del ATM
                - `Fecha_Hora`: Fecha y hora de la orden
                - `Descripcion`: Descripción de la orden de trabajo
                """)
            
            with col2:
                st.markdown("**Archivo de Downtime:**")
                st.markdown("""
                - `ATM_ID`: Identificador del ATM
                - `Fecha_Inicio`: Fecha y hora de inicio del downtime
                - `Fecha_Fin`: Fecha y hora de fin del downtime
                - `Causa`: Causa del downtime
                """)
        
        with st.expander("Cómo funciona la coincidencia"):
            st.markdown("""
            El sistema busca coincidencias entre órdenes de trabajo y registros de downtime basándose en:
            
            1. **Mismo ATM ID**: La orden y el downtime deben ser del mismo ATM
            2. **Proximidad temporal**: La fecha de la orden debe estar dentro de la tolerancia configurada respecto al inicio del downtime
            3. **Tolerancia configurable**: Puede ajustar la tolerancia en minutos desde la barra lateral
            
            Los resultados muestran todas las coincidencias encontradas con métricas de duración y diferencia temporal.
            """)

if __name__ == "__main__":
    main()