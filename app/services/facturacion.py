# -*- coding: utf-8 -*-

"""
Servicio para la gestión de facturas.
Implementa la lógica de negocio relacionada con la facturación.
"""

import datetime
from typing import List, Optional

from app.database.db_manager import DatabaseManager
from app.database.models import Factura
from app.services.exchange_rate import ExchangeRateService

class FacturacionService:
    """Servicio para la gestión de facturas"""
    
    def __init__(self):
        """Inicializa el servicio de facturación"""
        self.db = DatabaseManager()
        self.exchange_service = ExchangeRateService()
    
    def registrar_factura(self, orden_id: str, monto: float, moneda: str, pago_usd: float = 0, pago_cup: float = 0) -> bool:
        """
        Registra una nueva factura en el sistema con pagos mixtos
        
        Args:
            orden_id: Identificador de la orden
            monto: Monto total de la factura
            moneda: Moneda principal de la factura ('USD' o 'CUP')
            pago_usd: Monto pagado en USD
            pago_cup: Monto pagado en CUP
            
        Returns:
            True si la factura se registró correctamente, False en caso contrario
        """
        try:
            # Validar datos
            if not orden_id or monto <= 0 or moneda not in ['USD', 'CUP']:
                return False
            
            # Obtener tasa de cambio
            tasa = self.exchange_service.obtener_tasa_actual()
            
            # Calcular monto equivalente en USD (para estandarizar)
            if moneda == "USD":
                monto_equivalente = monto
            else:  # CUP
                monto_equivalente = monto / tasa
            
            # Verificar que los pagos son válidos
            if pago_usd < 0 or pago_cup < 0:
                return False
            
            # Verificar que los pagos cubren el monto total
            if moneda == "USD":
                total_pagado = pago_usd + (pago_cup / tasa)
            else:  # CUP
                total_pagado = pago_cup + (pago_usd * tasa)
            
            # Permitir un pequeño margen de error por redondeo
            if total_pagado < monto - 0.01:
                print(f"Pago insuficiente: {total_pagado} vs {monto}")
                return False
            
            # Insertar en la base de datos
            self.db.connect()
            self.db.execute(
                "INSERT INTO facturas (orden_id, monto, moneda, monto_equivalente, pago_usd, pago_cup) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (orden_id, monto, moneda, monto_equivalente, pago_usd, pago_cup)
            )
            self.db.commit()
            self.db.disconnect()
            
            return True
            
        except Exception as e:
            print(f"Error al registrar factura: {e}")
            return False
    
    def obtener_facturas_recientes(self, limite: int = 10) -> List[Factura]:
        """
        Obtiene las facturas más recientes
        
        Args:
            limite: Número máximo de facturas a devolver
            
        Returns:
            Lista de objetos Factura
        """
        try:
            self.db.connect()
            
            # Verificar si la tabla tiene las columnas de pagos
            tabla_actualizada = False
            try:
                self.db.execute("SELECT pago_usd, pago_cup FROM facturas LIMIT 1")
                tabla_actualizada = True
            except:
                tabla_actualizada = False
                
            # Realizar la consulta apropiada
            if tabla_actualizada:
                resultado = self.db.fetch_all(
                    "SELECT id, orden_id, monto, moneda, monto_equivalente, pago_usd, pago_cup, fecha "
                    "FROM facturas ORDER BY fecha DESC LIMIT ?",
                    (limite,)
                )
            else:
                resultado = self.db.fetch_all(
                    "SELECT id, orden_id, monto, moneda, monto_equivalente, fecha "
                    "FROM facturas ORDER BY fecha DESC LIMIT ?",
                    (limite,)
                )
            
            self.db.disconnect()
            
            facturas = []
            for row in resultado:
                if tabla_actualizada:
                    factura = Factura(
                        id=row[0],
                        orden_id=row[1],
                        monto=row[2],
                        moneda=row[3],
                        monto_equivalente=row[4],
                        fecha=datetime.datetime.fromisoformat(row[7].replace("Z", "+00:00")) 
                            if "Z" in row[7] else datetime.datetime.fromisoformat(row[7])
                    )
                    factura.pago_usd = row[5]
                    factura.pago_cup = row[6]
                else:
                    factura = Factura.from_db_row(row)
                
                facturas.append(factura)
                    
            return facturas
                
        except Exception as e:
            print(f"Error al obtener facturas recientes: {e}")
            return []
    
    def obtener_facturas_por_fecha(self, fecha_inicio: str, fecha_fin: str) -> List[Factura]:
        """
        Obtiene las facturas en un rango de fechas
        
        Args:
            fecha_inicio: Fecha de inicio en formato 'YYYY-MM-DD'
            fecha_fin: Fecha de fin en formato 'YYYY-MM-DD'
            
        Returns:
            Lista de objetos Factura
        """
        try:
            # Ajustar fecha_fin para incluir todo el día
            fecha_fin_ajustada = f"{fecha_fin} 23:59:59"
            
            self.db.connect()
            resultado = self.db.fetch_all(
                "SELECT id, orden_id, monto, moneda, monto_equivalente, fecha "
                "FROM facturas "
                "WHERE fecha BETWEEN ? AND ? "
                "ORDER BY fecha",
                (fecha_inicio, fecha_fin_ajustada)
            )
            self.db.disconnect()
            
            facturas = []
            for row in resultado:
                facturas.append(Factura.from_db_row(row))
                
            return facturas
            
        except Exception as e:
            print(f"Error al obtener facturas por fecha: {e}")
            return []
    
    def obtener_factura_por_id(self, factura_id: int) -> Optional[Factura]:
        """
        Obtiene una factura por su ID
        
        Args:
            factura_id: ID de la factura
            
        Returns:
            Objeto Factura o None si no se encuentra
        """
        try:
            self.db.connect()
            resultado = self.db.fetch_one(
                "SELECT id, orden_id, monto, moneda, monto_equivalente, fecha "
                "FROM facturas WHERE id = ?",
                (factura_id,)
            )
            self.db.disconnect()
            
            if resultado:
                return Factura.from_db_row(resultado)
            return None
            
        except Exception as e:
            print(f"Error al obtener factura por ID: {e}")
            return None
    
    def obtener_tasa_cambio(self) -> float:
        """
        Obtiene la tasa de cambio actual
        
        Returns:
            Tasa de cambio actual USD a CUP
        """
        return self.exchange_service.obtener_tasa_actual()