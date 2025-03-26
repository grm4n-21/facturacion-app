# -*- coding: utf-8 -*-

"""
Servicio para la gestión de tasas de cambio.
"""

from datetime import datetime, date, timedelta
from app.database.db_manager import DatabaseManager

class ExchangeRateService:
    """Servicio para gestionar las tasas de cambio entre monedas"""
    
    def __init__(self):
        """Inicializa el servicio de tasas de cambio"""
        self.db = DatabaseManager()
        self.tasa_predeterminada_usd = 350.0  # Valor predeterminado
        self.tasa_predeterminada_eur = 350.0  # Valor predeterminado
    
    def obtener_tasas_actuales(self):
        """
        Obtiene las tasas de cambio actuales (USD y EUR a CUP)
        
        Returns:
            Diccionario con las tasas actuales
        """
        try:
            # Obtener la fecha actual
            fecha_hoy = datetime.date.today().isoformat()
            
            # Conectar a la base de datos
            self.db.connect()
            
            # Intentar obtener las tasas para la fecha actual
            resultado = self.db.fetch_one(
                "SELECT usd_valor, eur_valor FROM tasa_cambio WHERE fecha = ?",
                (fecha_hoy,)
            )
            
            # Si no hay tasas para hoy, obtener las más recientes
            if not resultado:
                resultado = self.db.fetch_one(
                    "SELECT usd_valor, eur_valor FROM tasa_cambio ORDER BY fecha DESC LIMIT 1"
                )
            
            self.db.disconnect()
            
            # Devolver los valores o los predeterminados
            if resultado:
                return {
                    'usd': resultado[0],
                    'eur': resultado[1]
                }
            
            return {
                'usd': self.tasa_predeterminada_usd,
                'eur': self.tasa_predeterminada_eur
            }
            
        except Exception as e:
            print(f"Error al obtener tasas de cambio: {e}")
            return {
                'usd': self.tasa_predeterminada_usd,
                'eur': self.tasa_predeterminada_eur
            }
    
    def obtener_tasa_actual(self, moneda="usd"):
        """
        Obtiene la tasa de cambio actual para una moneda específica
        
        Args:
            moneda: 'usd' o 'eur'
            
        Returns:
            Tasa de cambio actual
        """
        tasas = self.obtener_tasas_actuales()
        return tasas.get(moneda.lower(), self.tasa_predeterminada_usd)
    
    def actualizar_tasas(self, tasa_usd, tasa_eur):
        """
        Actualiza las tasas de cambio para la fecha actual
        
        Args:
            tasa_usd: Nuevo valor de la tasa USD a CUP
            tasa_eur: Nuevo valor de la tasa EUR a CUP
            
        Returns:
            True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Validar tasas
            if tasa_usd <= 0 or tasa_eur <= 0:
                return False
                
            # Obtener la fecha actual
            fecha_hoy = datetime.date.today().isoformat()
            
            # Insertar o actualizar en la base de datos
            self.db.connect()
            self.db.execute(
                "INSERT OR REPLACE INTO tasa_cambio (fecha, usd_valor, eur_valor) VALUES (?, ?, ?)",
                (fecha_hoy, tasa_usd, tasa_eur)
            )
            self.db.commit()
            self.db.disconnect()
            
            return True
            
        except Exception as e:
            print(f"Error al actualizar tasas de cambio: {e}")
            return False
    
    def actualizar_tasa(self, nueva_tasa, moneda="usd"):
        """
        Actualiza la tasa de cambio para una moneda específica
        
        Args:
            nueva_tasa: Nuevo valor de la tasa
            moneda: 'usd' o 'eur'
            
        Returns:
            True si la actualización fue exitosa, False en caso contrario
        """
        tasas = self.obtener_tasas_actuales()
        
        if moneda.lower() == "usd":
            return self.actualizar_tasas(nueva_tasa, tasas['eur'])
        elif moneda.lower() == "eur":
            return self.actualizar_tasas(tasas['usd'], nueva_tasa)
        else:
            return False