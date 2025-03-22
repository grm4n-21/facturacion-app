# -*- coding: utf-8 -*-

"""
Servicio para la gestión de tasas de cambio.
"""

import datetime
from app.database.db_manager import DatabaseManager

class ExchangeRateService:
    """Servicio para gestionar las tasas de cambio entre monedas"""
    
    def __init__(self):
        """Inicializa el servicio de tasas de cambio"""
        self.db = DatabaseManager()
        self.tasa_predeterminada = 350.0  # Valor predeterminado
    
    def obtener_tasa_actual(self) -> float:
        """
        Obtiene la tasa de cambio actual (USD a CUP)
        
        Returns:
            Tasa de cambio actual o valor predeterminado si no hay datos
        """
        try:
            # Obtener la fecha actual
            fecha_hoy = datetime.date.today().isoformat()
            
            # Conectar a la base de datos
            self.db.connect()
            
            # Intentar obtener la tasa para la fecha actual
            resultado = self.db.fetch_one(
                "SELECT valor FROM tasa_cambio WHERE fecha = ?",
                (fecha_hoy,)
            )
            
            # Si no hay tasa para hoy, obtener la más reciente
            if not resultado:
                resultado = self.db.fetch_one(
                    "SELECT valor FROM tasa_cambio ORDER BY fecha DESC LIMIT 1"
                )
            
            self.db.disconnect()
            
            # Devolver el valor o el predeterminado
            if resultado:
                return resultado[0]
            
            return self.tasa_predeterminada
            
        except Exception as e:
            print(f"Error al obtener tasa de cambio: {e}")
            return self.tasa_predeterminada
    
    def actualizar_tasa(self, nueva_tasa: float) -> bool:
        """
        Actualiza la tasa de cambio para la fecha actual
        
        Args:
            nueva_tasa: Nuevo valor de la tasa de cambio
            
        Returns:
            True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Validar tasa
            if nueva_tasa <= 0:
                return False
                
            # Obtener la fecha actual
            fecha_hoy = datetime.date.today().isoformat()
            
            # Insertar o actualizar en la base de datos
            self.db.connect()
            self.db.execute(
                "INSERT OR REPLACE INTO tasa_cambio (fecha, valor) VALUES (?, ?)",
                (fecha_hoy, nueva_tasa)
            )
            self.db.commit()
            self.db.disconnect()
            
            return True
            
        except Exception as e:
            print(f"Error al actualizar tasa de cambio: {e}")
            return False
    
    def obtener_historial_tasas(self, limite: int = 30) -> list:
        """
        Obtiene el historial de tasas de cambio
        
        Args:
            limite: Número máximo de registros a devolver
            
        Returns:
            Lista de tuplas (fecha, valor) ordenadas por fecha descendente
        """
        try:
            self.db.connect()
            resultado = self.db.fetch_all(
                "SELECT fecha, valor FROM tasa_cambio ORDER BY fecha DESC LIMIT ?",
                (limite,)
            )
            self.db.disconnect()
            
            return resultado
            
        except Exception as e:
            print(f"Error al obtener historial de tasas: {e}")
            return []
    
    def obtener_tasa_por_fecha(self, fecha: str) -> float:
        """
        Obtiene la tasa de cambio para una fecha específica
        
        Args:
            fecha: Fecha en formato 'YYYY-MM-DD'
            
        Returns:
            Tasa de cambio para la fecha especificada o la tasa actual si no hay datos
        """
        try:
            self.db.connect()
            resultado = self.db.fetch_one(
                "SELECT valor FROM tasa_cambio WHERE fecha = ?",
                (fecha,)
            )
            self.db.disconnect()
            
            if resultado:
                return resultado[0]
            
            # Si no hay tasa para esa fecha, devolver la tasa actual
            return self.obtener_tasa_actual()
            
        except Exception as e:
            print(f"Error al obtener tasa por fecha: {e}")
            return self.tasa_predeterminada