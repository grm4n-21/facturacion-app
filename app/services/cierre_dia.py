# -*- coding: utf-8 -*-

"""
Servicio para gestionar los cierres de día.
"""

import datetime
from typing import Dict, List, Optional, Tuple

from app.database.db_manager import DatabaseManager
from app.services.facturacion import FacturacionService

class CierreDiaService:
    """Servicio para gestionar los cierres de día"""
    
    def __init__(self):
        """Inicializa el servicio de cierres de día"""
        self.db = DatabaseManager()
        self.facturacion_service = FacturacionService()
    
    def obtener_facturas_sin_cerrar(self) -> List[Dict]:
        """
        Obtiene todas las facturas que no han sido cerradas
        
        Returns:
            Lista de facturas sin cerrar
        """
        self.db.connect()
        resultado = self.db.fetch_all(
            "SELECT id, orden_id, monto, moneda, monto_equivalente, pago_usd, pago_cup, fecha "
            "FROM facturas WHERE cerrada = 0 ORDER BY fecha"
        )
        self.db.disconnect()
    
        facturas = []
        for row in resultado:
            facturas.append({
                'id': row[0],
                'orden_id': row[1],
                'monto': row[2],
                'moneda': row[3],
                'monto_equivalente': row[4],
                'pago_usd': row[5],
                'pago_cup': row[6],
                'fecha': row[7]
            })
        
        return facturas

    def realizar_cierre_dia(self, efectivo_contado_usd=0, efectivo_contado_cup=0) -> Dict:
        """
        Realiza el cierre del día actual
        
        Args:
            efectivo_contado_usd: Efectivo físico contado en USD
            efectivo_contado_cup: Efectivo físico contado en CUP
        
        Returns:
            Diccionario con resultados del cierre incluyendo diferencias
        """
        try:
            # Obtener fecha actual
            fecha_hoy = datetime.date.today().isoformat()
            
            # Verificar si ya hay un cierre para hoy
            hay_cierre, _ = self.verificar_dia_actual()
            if hay_cierre:
                return {
                    'success': False,
                    'message': f"Ya existe un cierre para el día {fecha_hoy}"
                }
            
            # Obtener facturas sin cerrar
            facturas = self.obtener_facturas_sin_cerrar()
            
            if not facturas:
                return {
                    'success': False,
                    'message': "No hay facturas para cerrar"
                }
            
            # Calcular totales según los pagos realizados en cada moneda
            total_usd_caja = 0.0
            total_cup_caja = 0.0
            ids_facturas = []
            
            for factura in facturas:
                ids_facturas.append(factura['id'])
                
                # Sumar pagos directamente por cada moneda
                total_usd_caja += factura['pago_usd']
                total_cup_caja += factura['pago_cup']
            
            # Calcular diferencias con el efectivo contado
            diferencia_usd = efectivo_contado_usd - total_usd_caja
            diferencia_cup = efectivo_contado_cup - total_cup_caja
            
            # Crear registro de cierre
            self.db.connect()
            
            # Insertar cierre
            self.db.execute(
                "INSERT INTO cierres_dia (fecha, total_usd, total_cup, num_facturas, "
                "efectivo_contado_usd, efectivo_contado_cup, diferencia_usd, diferencia_cup) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (fecha_hoy, total_usd_caja, total_cup_caja, len(facturas), 
                efectivo_contado_usd, efectivo_contado_cup, diferencia_usd, diferencia_cup)
            )
            
            # Obtener ID del cierre
            cierre_id = self.db.cursor.lastrowid
            
            # Marcar facturas como cerradas
            for factura_id in ids_facturas:
                self.db.execute(
                    "UPDATE facturas SET cerrada = 1, dia_id = ? WHERE id = ?",
                    (cierre_id, factura_id)
                )
            
            self.db.commit()
            self.db.disconnect()
            
            # Preparar resultados
            return {
                'success': True,
                'fecha': fecha_hoy,
                'total_usd': total_usd_caja,
                'total_cup': total_cup_caja,
                'num_facturas': len(facturas),
                'efectivo_contado_usd': efectivo_contado_usd,
                'efectivo_contado_cup': efectivo_contado_cup,
                'diferencia_usd': diferencia_usd,
                'diferencia_cup': diferencia_cup,
                'cierre_id': cierre_id
            }
                
        except Exception as e:
            print(f"Error al realizar cierre de día: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def obtener_historial_cierres(self, limite: int = 30) -> List[Dict]:
        """
        Obtiene el historial de cierres de día
        
        Args:
            limite: Número máximo de registros a devolver
                
        Returns:
            Lista de cierres de día
        """
        self.db.connect()
        resultado = self.db.fetch_all(
            "SELECT id, fecha, total_usd, total_cup, num_facturas, "
            "efectivo_contado_usd, efectivo_contado_cup, diferencia_usd, diferencia_cup, fecha_cierre "
            "FROM cierres_dia ORDER BY fecha DESC LIMIT ?",
            (limite,)
        )
        self.db.disconnect()
        
        cierres = []
        for row in resultado:
            cierres.append({
                'id': row[0],
                'fecha': row[1],
                'total_usd': row[2],
                'total_cup': row[3],
                'num_facturas': row[4],
                'efectivo_contado_usd': row[5],
                'efectivo_contado_cup': row[6],
                'diferencia_usd': row[7],
                'diferencia_cup': row[8],
                'fecha_cierre': row[9]
            })
        
        return cierres

    def obtener_detalles_cierre(self, cierre_id: int) -> Dict:
        """
        Obtiene los detalles de un cierre específico, incluyendo las facturas asociadas
        
        Args:
            cierre_id: ID del cierre a consultar
            
        Returns:
            Diccionario con detalles del cierre y sus facturas
        """
        try:
            # Obtener información del cierre
            self.db.connect()
            cierre = self.db.fetch_one(
                "SELECT id, fecha, total_usd, total_cup, num_facturas, "
                "efectivo_contado_usd, efectivo_contado_cup, diferencia_usd, diferencia_cup, fecha_cierre "
                "FROM cierres_dia WHERE id = ?",
                (cierre_id,)
            )
            
            if not cierre:
                return {
                    'success': False,
                    'message': f"No se encontró el cierre con ID {cierre_id}"
                }
            
            # Obtener facturas asociadas al cierre
            facturas = self.db.fetch_all(
                "SELECT id, orden_id, monto, moneda, monto_equivalente, pago_usd, pago_cup, fecha "
                "FROM facturas WHERE dia_id = ? ORDER BY fecha",
                (cierre_id,)
            )
            
            self.db.disconnect()
            
            # Formatear resultados
            facturas_formateadas = []
            for factura in facturas:
                facturas_formateadas.append({
                    'id': factura[0],
                    'orden_id': factura[1],
                    'monto': factura[2],
                    'moneda': factura[3],
                    'monto_equivalente': factura[4],
                    'pago_usd': factura[5],
                    'pago_cup': factura[6],
                    'fecha': factura[7]
                })
            
            return {
                'success': True,
                'cierre': {
                    'id': cierre[0],
                    'fecha': cierre[1],
                    'total_usd': cierre[2],
                    'total_cup': cierre[3],
                    'num_facturas': cierre[4],
                    'efectivo_contado_usd': cierre[5],
                    'efectivo_contado_cup': cierre[6],
                    'diferencia_usd': cierre[7],
                    'diferencia_cup': cierre[8],
                    'fecha_cierre': cierre[9]
                },
                'facturas': facturas_formateadas
            }
                
        except Exception as e:
            print(f"Error al obtener detalles del cierre: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }

    def calcular_resumen_periodo(self, dias: int = 30) -> Dict:
        """
        Calcula un resumen de los cierres en un período específico
        
        Args:
            dias: Número de días anteriores a considerar
            
        Returns:
            Diccionario con resumen del período
        """
        try:
            fecha_limite = (datetime.date.today() - datetime.timedelta(days=dias)).isoformat()
            
            self.db.connect()
            resultado = self.db.fetch_all(
                "SELECT SUM(total_usd), SUM(total_cup), SUM(num_facturas), COUNT(*) "
                "FROM cierres_dia WHERE fecha >= ?",
                (fecha_limite,)
            )
            self.db.disconnect()
            
            if resultado and resultado[0][0] is not None:
                return {
                    'success': True,
                    'total_usd': resultado[0][0],
                    'total_cup': resultado[0][1],
                    'num_facturas': resultado[0][2],
                    'num_cierres': resultado[0][3],
                    'periodo_dias': dias
                }
            else:
                return {
                    'success': True,
                    'total_usd': 0,
                    'total_cup': 0,
                    'num_facturas': 0,
                    'num_cierres': 0,
                    'periodo_dias': dias
                }
                
        except Exception as e:
            print(f"Error al calcular resumen de período: {e}")
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }
    def verificar_dia_actual(self) -> Tuple[bool, Optional[str]]:
        """
        Verifica si hay un cierre para el día actual
        
        Returns:
            Tupla (hay_cierre, fecha_ultimo_cierre)
        """
        fecha_hoy = datetime.date.today().isoformat()
        
        self.db.connect()
        resultado = self.db.fetch_one(
            "SELECT fecha FROM cierres_dia WHERE fecha = ?",
            (fecha_hoy,)
        )
        self.db.disconnect()
        
        if resultado:
            return True, fecha_hoy
        
        # Verificar último cierre
        self.db.connect()
        resultado = self.db.fetch_one(
            "SELECT fecha FROM cierres_dia ORDER BY fecha DESC LIMIT 1"
        )
        self.db.disconnect()
        
        if resultado:
            return False, resultado[0]
        
        return False, None