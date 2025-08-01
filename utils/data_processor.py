import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st

class DataProcessor:
    """
    Clase para procesar archivos Excel de órdenes de trabajo y downtime
    """
    
    def __init__(self):
        self.required_work_order_columns = ['ATM_ID', 'Fecha_Hora', 'Descripcion']
        self.required_downtime_columns = ['ATM_ID', 'Fecha_Inicio', 'Fecha_Fin', 'Causa']
    
    def process_work_orders(self, file):
        """
        Procesa el archivo de órdenes de trabajo
        
        Args:
            file: Archivo Excel cargado
            
        Returns:
            pandas.DataFrame: DataFrame procesado con órdenes de trabajo
        """
        try:
            # Leer archivo Excel
            df = pd.read_excel(file)
            
            # Verificar columnas requeridas
            self._validate_columns(df, self.required_work_order_columns, "órdenes de trabajo")
            
            # Limpiar y procesar datos
            df = self._clean_work_orders_data(df)
            
            # Validar datos procesados
            self._validate_work_orders_data(df)
            
            return df
            
        except Exception as e:
            raise Exception(f"Error procesando archivo de órdenes de trabajo: {str(e)}")
    
    def process_downtime(self, file):
        """
        Procesa el archivo de registros de downtime
        
        Args:
            file: Archivo Excel cargado
            
        Returns:
            pandas.DataFrame: DataFrame procesado con registros de downtime
        """
        try:
            # Leer archivo Excel
            df = pd.read_excel(file)
            
            # Verificar columnas requeridas
            self._validate_columns(df, self.required_downtime_columns, "downtime")
            
            # Limpiar y procesar datos
            df = self._clean_downtime_data(df)
            
            # Validar datos procesados
            self._validate_downtime_data(df)
            
            return df
            
        except Exception as e:
            raise Exception(f"Error procesando archivo de downtime: {str(e)}")
    
    def _validate_columns(self, df, required_columns, file_type):
        """
        Valida que el DataFrame contenga las columnas requeridas
        """
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            available_columns = list(df.columns)
            raise Exception(
                f"Columnas faltantes en archivo de {file_type}: {missing_columns}. "
                f"Columnas disponibles: {available_columns}"
            )
    
    def _clean_work_orders_data(self, df):
        """
        Limpia y procesa los datos de órdenes de trabajo
        """
        # Crear una copia para no modificar el original
        df = df.copy()
        
        # Limpiar ATM_ID
        df['ATM_ID'] = df['ATM_ID'].astype(str).str.strip().str.upper()
        
        # Convertir fecha_hora a datetime
        df['Fecha_Hora'] = pd.to_datetime(df['Fecha_Hora'], errors='coerce')
        
        # Limpiar descripción
        df['Descripcion'] = df['Descripcion'].astype(str).str.strip()
        
        # Eliminar filas con datos críticos faltantes
        df = df.dropna(subset=['ATM_ID', 'Fecha_Hora'])
        
        # Eliminar duplicados
        df = df.drop_duplicates(subset=['ATM_ID', 'Fecha_Hora', 'Descripcion'])
        
        return df
    
    def _clean_downtime_data(self, df):
        """
        Limpia y procesa los datos de downtime
        """
        # Crear una copia para no modificar el original
        df = df.copy()
        
        # Limpiar ATM_ID
        df['ATM_ID'] = df['ATM_ID'].astype(str).str.strip().str.upper()
        
        # Convertir fechas a datetime
        df['Fecha_Inicio'] = pd.to_datetime(df['Fecha_Inicio'], errors='coerce')
        df['Fecha_Fin'] = pd.to_datetime(df['Fecha_Fin'], errors='coerce')
        
        # Limpiar causa
        df['Causa'] = df['Causa'].astype(str).str.strip()
        
        # Eliminar filas con datos críticos faltantes
        df = df.dropna(subset=['ATM_ID', 'Fecha_Inicio', 'Fecha_Fin'])
        
        # Calcular duración del downtime en horas
        df['Duracion_Horas'] = (df['Fecha_Fin'] - df['Fecha_Inicio']).dt.total_seconds() / 3600
        
        # Eliminar registros con duración negativa o cero
        df = df[df['Duracion_Horas'] > 0]
        
        # Eliminar duplicados
        df = df.drop_duplicates(subset=['ATM_ID', 'Fecha_Inicio', 'Fecha_Fin'])
        
        return df
    
    def _validate_work_orders_data(self, df):
        """
        Valida los datos procesados de órdenes de trabajo
        """
        if len(df) == 0:
            raise Exception("No hay datos válidos en el archivo de órdenes de trabajo después del procesamiento")
        
        # Verificar que hay fechas válidas
        invalid_dates = df['Fecha_Hora'].isna().sum()
        if invalid_dates > 0:
            st.warning(f"Se encontraron {invalid_dates} órdenes con fechas inválidas que fueron excluidas")
        
        # Verificar rango de fechas razonable
        min_date = df['Fecha_Hora'].min()
        max_date = df['Fecha_Hora'].max()
        
        if min_date < pd.Timestamp('2000-01-01'):
            st.warning("Se encontraron fechas muy antiguas en las órdenes de trabajo")
        
        if max_date > pd.Timestamp.now() + pd.Timedelta(days=365):
            st.warning("Se encontraron fechas futuras en las órdenes de trabajo")
    
    def _validate_downtime_data(self, df):
        """
        Valida los datos procesados de downtime
        """
        if len(df) == 0:
            raise Exception("No hay datos válidos en el archivo de downtime después del procesamiento")
        
        # Verificar que hay fechas válidas
        invalid_start_dates = df['Fecha_Inicio'].isna().sum()
        invalid_end_dates = df['Fecha_Fin'].isna().sum()
        
        if invalid_start_dates > 0 or invalid_end_dates > 0:
            st.warning(f"Se encontraron registros con fechas inválidas que fueron excluidos")
        
        # Verificar duraciones razonables
        max_duration = df['Duracion_Horas'].max()
        if max_duration > 24 * 30:  # Más de 30 días
            st.warning("Se encontraron registros de downtime con duración muy larga (>30 días)")
        
        # Verificar que fecha_fin > fecha_inicio
        invalid_ranges = df[df['Fecha_Fin'] <= df['Fecha_Inicio']]
        if len(invalid_ranges) > 0:
            st.warning(f"Se encontraron {len(invalid_ranges)} registros con rangos de fecha inválidos que fueron excluidos")
    
    def get_data_summary(self, work_orders_df, downtime_df):
        """
        Genera un resumen de los datos procesados
        
        Returns:
            dict: Resumen de estadísticas de los datos
        """
        summary = {
            'work_orders': {
                'total_records': len(work_orders_df),
                'unique_atms': work_orders_df['ATM_ID'].nunique(),
                'date_range': {
                    'min': work_orders_df['Fecha_Hora'].min(),
                    'max': work_orders_df['Fecha_Hora'].max()
                }
            },
            'downtime': {
                'total_records': len(downtime_df),
                'unique_atms': downtime_df['ATM_ID'].nunique(),
                'date_range': {
                    'min': downtime_df['Fecha_Inicio'].min(),
                    'max': downtime_df['Fecha_Fin'].max()
                },
                'avg_duration_hours': downtime_df['Duracion_Horas'].mean()
            },
            'common_atms': len(set(work_orders_df['ATM_ID']) & set(downtime_df['ATM_ID']))
        }
        
        return summary
