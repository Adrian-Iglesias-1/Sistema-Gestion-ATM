import pandas as pd
import numpy as np
from datetime import timedelta

class WorkOrderMatcher:
    """
    Clase para encontrar coincidencias entre órdenes de trabajo y registros de downtime
    """
    
    def __init__(self, tolerance_minutes=30):
        """
        Inicializa el matcher con tolerancia en minutos
        
        Args:
            tolerance_minutes (int): Tolerancia en minutos para considerar una coincidencia
        """
        self.tolerance_minutes = tolerance_minutes
        self.tolerance_delta = timedelta(minutes=tolerance_minutes)
    
    def find_matches(self, work_orders_df, downtime_df):
        """
        Encuentra coincidencias entre órdenes de trabajo y downtime
        
        Args:
            work_orders_df (pd.DataFrame): DataFrame con órdenes de trabajo
            downtime_df (pd.DataFrame): DataFrame con registros de downtime
            
        Returns:
            pd.DataFrame: DataFrame con las coincidencias encontradas
        """
        matches = []
        
        # Obtener ATMs comunes entre ambos datasets
        common_atms = set(work_orders_df['ATM_ID']) & set(downtime_df['ATM_ID'])
        
        if not common_atms:
            # Retornar DataFrame vacío con la estructura esperada
            return self._create_empty_matches_df()
        
        # Procesar cada ATM común
        for atm_id in common_atms:
            atm_matches = self._find_atm_matches(
                work_orders_df[work_orders_df['ATM_ID'] == atm_id],
                downtime_df[downtime_df['ATM_ID'] == atm_id],
                atm_id
            )
            matches.extend(atm_matches)
        
        # Convertir a DataFrame
        if matches:
            matches_df = pd.DataFrame(matches)
            # Ordenar por ATM_ID y fecha de orden
            matches_df = matches_df.sort_values(['ATM_ID', 'Fecha_Orden'])
            matches_df = matches_df.reset_index(drop=True)
        else:
            matches_df = self._create_empty_matches_df()
        
        return matches_df
    
    def _find_atm_matches(self, work_orders, downtime_records, atm_id):
        """
        Encuentra coincidencias para un ATM específico
        
        Args:
            work_orders (pd.DataFrame): Órdenes de trabajo del ATM
            downtime_records (pd.DataFrame): Registros de downtime del ATM
            atm_id (str): ID del ATM
            
        Returns:
            list: Lista de coincidencias encontradas
        """
        matches = []
        
        for _, order in work_orders.iterrows():
            order_datetime = order['Fecha_Hora']
            
            # Buscar registros de downtime que coincidan temporalmente
            for _, downtime in downtime_records.iterrows():
                if self._is_temporal_match(order_datetime, downtime):
                    match = self._create_match_record(order, downtime, atm_id)
                    matches.append(match)
        
        return matches
    
    def _is_temporal_match(self, order_datetime, downtime_record):
        """
        Verifica si hay coincidencia temporal entre una orden y un downtime
        
        Args:
            order_datetime (pd.Timestamp): Fecha y hora de la orden
            downtime_record (pd.Series): Registro de downtime
            
        Returns:
            bool: True si hay coincidencia temporal
        """
        downtime_start = downtime_record['Fecha_Inicio']
        downtime_end = downtime_record['Fecha_Fin']
        
        # Calcular ventana de tolerancia alrededor del inicio del downtime
        tolerance_start = downtime_start - self.tolerance_delta
        tolerance_end = downtime_start + self.tolerance_delta
        
        # Verificar si la orden está dentro de la ventana de tolerancia
        # o si la orden está entre el inicio y fin del downtime
        return (tolerance_start <= order_datetime <= tolerance_end) or \
               (downtime_start <= order_datetime <= downtime_end)
    
    def _create_match_record(self, order, downtime, atm_id):
        """
        Crea un registro de coincidencia
        
        Args:
            order (pd.Series): Registro de orden de trabajo
            downtime (pd.Series): Registro de downtime
            atm_id (str): ID del ATM
            
        Returns:
            dict: Registro de coincidencia
        """
        # Calcular diferencia de tiempo en minutos
        time_diff_minutes = abs((order['Fecha_Hora'] - downtime['Fecha_Inicio']).total_seconds() / 60)
        
        match_record = {
            'ATM_ID': atm_id,
            'Fecha_Orden': order['Fecha_Hora'],
            'Descripcion_Orden': order['Descripcion'],
            'Inicio_Downtime': downtime['Fecha_Inicio'],
            'Fin_Downtime': downtime['Fecha_Fin'],
            'Causa_Downtime': downtime['Causa'],
            'Duracion_Downtime_Horas': downtime['Duracion_Horas'],
            'Diferencia_Tiempo_Minutos': time_diff_minutes,
            'Tolerancia_Minutos': self.tolerance_minutes
        }
        
        return match_record
    
    def _create_empty_matches_df(self):
        """
        Crea un DataFrame vacío con la estructura de coincidencias
        
        Returns:
            pd.DataFrame: DataFrame vacío con columnas de coincidencias
        """
        columns = [
            'ATM_ID', 'Fecha_Orden', 'Descripcion_Orden',
            'Inicio_Downtime', 'Fin_Downtime', 'Causa_Downtime',
            'Duracion_Downtime_Horas', 'Diferencia_Tiempo_Minutos',
            'Tolerancia_Minutos'
        ]
        
        return pd.DataFrame(columns=columns)
    
    def get_match_statistics(self, matches_df):
        """
        Calcula estadísticas de las coincidencias encontradas
        
        Args:
            matches_df (pd.DataFrame): DataFrame con coincidencias
            
        Returns:
            dict: Estadísticas de las coincidencias
        """
        if len(matches_df) == 0:
            return {
                'total_matches': 0,
                'unique_atms': 0,
                'avg_duration_hours': 0,
                'avg_time_diff_minutes': 0,
                'duration_stats': {},
                'time_diff_stats': {}
            }
        
        stats = {
            'total_matches': len(matches_df),
            'unique_atms': matches_df['ATM_ID'].nunique(),
            'avg_duration_hours': matches_df['Duracion_Downtime_Horas'].mean(),
            'avg_time_diff_minutes': matches_df['Diferencia_Tiempo_Minutos'].mean(),
            'duration_stats': {
                'min': matches_df['Duracion_Downtime_Horas'].min(),
                'max': matches_df['Duracion_Downtime_Horas'].max(),
                'median': matches_df['Duracion_Downtime_Horas'].median(),
                'std': matches_df['Duracion_Downtime_Horas'].std()
            },
            'time_diff_stats': {
                'min': matches_df['Diferencia_Tiempo_Minutos'].min(),
                'max': matches_df['Diferencia_Tiempo_Minutos'].max(),
                'median': matches_df['Diferencia_Tiempo_Minutos'].median(),
                'std': matches_df['Diferencia_Tiempo_Minutos'].std()
            }
        }
        
        return stats
    
    def filter_matches_by_criteria(self, matches_df, criteria):
        """
        Filtra coincidencias basándose en criterios específicos
        
        Args:
            matches_df (pd.DataFrame): DataFrame con coincidencias
            criteria (dict): Criterios de filtrado
            
        Returns:
            pd.DataFrame: DataFrame filtrado
        """
        filtered_df = matches_df.copy()
        
        # Filtrar por ATMs específicos
        if 'atm_ids' in criteria and criteria['atm_ids']:
            filtered_df = filtered_df[filtered_df['ATM_ID'].isin(criteria['atm_ids'])]
        
        # Filtrar por duración mínima
        if 'min_duration_hours' in criteria:
            filtered_df = filtered_df[
                filtered_df['Duracion_Downtime_Horas'] >= criteria['min_duration_hours']
            ]
        
        # Filtrar por duración máxima
        if 'max_duration_hours' in criteria:
            filtered_df = filtered_df[
                filtered_df['Duracion_Downtime_Horas'] <= criteria['max_duration_hours']
            ]
        
        # Filtrar por rango de fechas
        if 'start_date' in criteria and 'end_date' in criteria:
            start_date = pd.to_datetime(criteria['start_date'])
            end_date = pd.to_datetime(criteria['end_date'])
            
            filtered_df = filtered_df[
                (filtered_df['Fecha_Orden'] >= start_date) &
                (filtered_df['Fecha_Orden'] <= end_date)
            ]
        
        # Filtrar por diferencia de tiempo máxima
        if 'max_time_diff_minutes' in criteria:
            filtered_df = filtered_df[
                filtered_df['Diferencia_Tiempo_Minutos'] <= criteria['max_time_diff_minutes']
            ]
        
        # Filtrar por causa de downtime
        if 'downtime_causes' in criteria and criteria['downtime_causes']:
            filtered_df = filtered_df[
                filtered_df['Causa_Downtime'].isin(criteria['downtime_causes'])
            ]
        
        return filtered_df.reset_index(drop=True)
    
    def update_tolerance(self, new_tolerance_minutes):
        """
        Actualiza la tolerancia del matcher
        
        Args:
            new_tolerance_minutes (int): Nueva tolerancia en minutos
        """
        self.tolerance_minutes = new_tolerance_minutes
        self.tolerance_delta = timedelta(minutes=new_tolerance_minutes)
