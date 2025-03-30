# -*- coding: utf-8 -*-

"""
Servicio para gestionar los cierres de día.
"""

from datetime import datetime, date, timedelta
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
            "SELECT id, orden_id, monto, moneda, monto_equivalente, pago_usd, pago_eur, pago_cup, pago_transferencia, fecha "
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
                'pago_eur': row[6],  # Añadido soporte para EUR
                'pago_cup': row[7],
                'pago_transferencia': row[8],  # Añadido soporte para transferencias
                'fecha': row[9]
            })
        
        return facturas
    
    def obtener_salidas_sin_cerrar(self) -> List[Dict]:
        """
        Obtiene todas las salidas de caja que no han sido cerradas
        
        Returns:
            Lista de salidas sin cerrar
        """
        self.db.connect()
        resultado = self.db.fetch_all(
            "SELECT id, fecha, monto_usd, monto_eur, monto_cup, monto_transferencia, destinatario, autorizado_por, motivo "
            "FROM salidas_caja WHERE cerrada = 0 ORDER BY fecha"
        )
        self.db.disconnect()
    
        salidas = []
        for row in resultado:
            salidas.append({
                'id': row[0],
                'fecha': row[1],
                'monto_usd': row[2],
                'monto_eur': row[3],
                'monto_cup': row[4],
                'monto_transferencia': row[5],
                'destinatario': row[6],
                'autorizado_por': row[7],
                'motivo': row[8]
            })
        
        return salidas

    def realizar_cierre_dia(self, efectivo_contado_usd=0, efectivo_contado_eur=0, efectivo_contado_cup=0) -> Dict:
        """
        Realiza el cierre del día actual
        
        Args:
            efectivo_contado_usd: Efectivo físico contado en USD
            efectivo_contado_eur: Efectivo físico contado en EUR
            efectivo_contado_cup: Efectivo físico contado en CUP
        
        Returns:
            Diccionario con resultados del cierre incluyendo diferencias
        """
        try:
            # Obtener fecha actual
            fecha_hoy = date.today().isoformat()
            
            # Verificar si ya hay un cierre para hoy
            hay_cierre, _ = self.verificar_dia_actual()
            if hay_cierre:
                return {
                    'success': False,
                    'message': f"Ya existe un cierre para el día {fecha_hoy}"
                }
            
            # Obtener facturas sin cerrar
            facturas = self.obtener_facturas_sin_cerrar()
            
            # Obtener salidas sin cerrar
            salidas = self.obtener_salidas_sin_cerrar()
            
            if not facturas and not salidas:
                return {
                    'success': False,
                    'message': "No hay facturas ni salidas para cerrar"
                }
            
            # Calcular totales según los pagos realizados en cada moneda
            total_usd_caja = 0.0
            total_eur_caja = 0.0
            total_cup_caja = 0.0
            total_transferencia = 0.0
            ids_facturas = []
            
            for factura in facturas:
                ids_facturas.append(factura['id'])
                
                # Sumar pagos directamente por cada moneda
                total_usd_caja += factura.get('pago_usd', 0) or 0
                total_eur_caja += factura.get('pago_eur', 0) or 0
                total_cup_caja += factura.get('pago_cup', 0) or 0
                total_transferencia += factura.get('pago_transferencia', 0) or 0
            
            # Restar las salidas de caja
            ids_salidas = []
            for salida in salidas:
                ids_salidas.append(salida['id'])
                
                # Restar montos de salidas
                total_usd_caja -= salida.get('monto_usd', 0) or 0
                total_eur_caja -= salida.get('monto_eur', 0) or 0
                total_cup_caja -= salida.get('monto_cup', 0) or 0
                total_transferencia -= salida.get('monto_transferencia', 0) or 0
            
            # Calcular diferencias con el efectivo contado
            diferencia_usd = efectivo_contado_usd - total_usd_caja
            diferencia_eur = efectivo_contado_eur - total_eur_caja
            diferencia_cup = efectivo_contado_cup - total_cup_caja
            
            # Crear registro de cierre
            self.db.connect()
            
            # Insertar cierre
            self.db.execute(
                "INSERT INTO cierres_dia (fecha, total_usd, total_eur, total_cup, total_transferencia, num_facturas, "
                "efectivo_contado_usd, efectivo_contado_eur, efectivo_contado_cup, diferencia_usd, diferencia_eur, diferencia_cup) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (fecha_hoy, total_usd_caja, total_eur_caja, total_cup_caja, total_transferencia, len(facturas), 
                efectivo_contado_usd, efectivo_contado_eur, efectivo_contado_cup, diferencia_usd, diferencia_eur, diferencia_cup)
            )
            
            # Obtener ID del cierre
            cierre_id = self.db.cursor.lastrowid
            
            # Marcar facturas como cerradas
            for factura_id in ids_facturas:
                self.db.execute(
                    "UPDATE facturas SET cerrada = 1, dia_id = ? WHERE id = ?",
                    (cierre_id, factura_id)
                )
            
            # Marcar salidas como cerradas
            for salida_id in ids_salidas:
                self.db.execute(
                    "UPDATE salidas_caja SET cerrada = 1, dia_id = ? WHERE id = ?",
                    (cierre_id, salida_id)
                )
            
            self.db.commit()
            self.db.disconnect()
            
            # Preparar resultados
            return {
                'success': True,
                'fecha': fecha_hoy,
                'total_usd': total_usd_caja,
                'total_eur': total_eur_caja,
                'total_cup': total_cup_caja,
                'total_transferencia': total_transferencia,
                'num_facturas': len(facturas),
                'num_salidas': len(salidas),
                'efectivo_contado_usd': efectivo_contado_usd,
                'efectivo_contado_eur': efectivo_contado_eur,
                'efectivo_contado_cup': efectivo_contado_cup,
                'diferencia_usd': diferencia_usd,
                'diferencia_eur': diferencia_eur,
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
            "SELECT id, fecha, total_usd, total_eur, total_cup, total_transferencia, num_facturas, "
            "efectivo_contado_usd, efectivo_contado_eur, efectivo_contado_cup, "
            "diferencia_usd, diferencia_eur, diferencia_cup, fecha_cierre "
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
                'total_eur': row[3],
                'total_cup': row[4],
                'total_transferencia': row[5],
                'num_facturas': row[6],
                'efectivo_contado_usd': row[7],
                'efectivo_contado_eur': row[8],
                'efectivo_contado_cup': row[9],
                'diferencia_usd': row[10],
                'diferencia_eur': row[11],
                'diferencia_cup': row[12],
                'fecha_cierre': row[13]
            })
        
        return cierres

    def obtener_detalles_cierre(self, cierre_id: int) -> Dict:
        """
        Obtiene los detalles de un cierre específico, incluyendo las facturas y salidas asociadas
        
        Args:
            cierre_id: ID del cierre a consultar
            
        Returns:
            Diccionario con detalles del cierre, facturas y salidas
        """
        try:
            # Obtener información del cierre
            self.db.connect()
            cierre = self.db.fetch_one(
                "SELECT id, fecha, total_usd, total_eur, total_cup, total_transferencia, num_facturas, "
                "efectivo_contado_usd, efectivo_contado_eur, efectivo_contado_cup, "
                "diferencia_usd, diferencia_eur, diferencia_cup, fecha_cierre "
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
                "SELECT id, orden_id, monto, moneda, monto_equivalente, pago_usd, pago_eur, pago_cup, pago_transferencia, fecha "
                "FROM facturas WHERE dia_id = ? ORDER BY fecha",
                (cierre_id,)
            )
            
            # Obtener salidas asociadas al cierre
            salidas = self.db.fetch_all(
                "SELECT id, fecha, monto_usd, monto_eur, monto_cup, monto_transferencia, destinatario, autorizado_por, motivo "
                "FROM salidas_caja WHERE dia_id = ? ORDER BY fecha",
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
                    'pago_eur': factura[6],
                    'pago_cup': factura[7],
                    'pago_transferencia': factura[8],
                    'fecha': factura[9]
                })
            
            salidas_formateadas = []
            for salida in salidas:
                salidas_formateadas.append({
                    'id': salida[0],
                    'fecha': salida[1],
                    'monto_usd': salida[2],
                    'monto_eur': salida[3],
                    'monto_cup': salida[4],
                    'monto_transferencia': salida[5],
                    'destinatario': salida[6],
                    'autorizado_por': salida[7],
                    'motivo': salida[8]
                })
            
            return {
                'success': True,
                'cierre': {
                    'id': cierre[0],
                    'fecha': cierre[1],
                    'total_usd': cierre[2],
                    'total_eur': cierre[3],
                    'total_cup': cierre[4],
                    'total_transferencia': cierre[5],
                    'num_facturas': cierre[6],
                    'efectivo_contado_usd': cierre[7],
                    'efectivo_contado_eur': cierre[8],
                    'efectivo_contado_cup': cierre[9],
                    'diferencia_usd': cierre[10],
                    'diferencia_eur': cierre[11],
                    'diferencia_cup': cierre[12],
                    'fecha_cierre': cierre[13]
                },
                'facturas': facturas_formateadas,
                'salidas': salidas_formateadas
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
                fecha_limite = (date.today() - timedelta(days=dias)).isoformat()
                
                self.db.connect()
                resultado = self.db.fetch_all(
                    "SELECT SUM(total_usd), SUM(total_eur), SUM(total_cup), SUM(total_transferencia), SUM(num_facturas), COUNT(*) "
                    "FROM cierres_dia WHERE fecha >= ?",
                    (fecha_limite,)
                )
                self.db.disconnect()
                
                if resultado and resultado[0][0] is not None:
                    return {
                        'success': True,
                        'total_usd': resultado[0][0],
                        'total_eur': resultado[0][1],
                        'total_cup': resultado[0][2],
                        'total_transferencia': resultado[0][3],
                        'num_facturas': resultado[0][4],
                        'num_cierres': resultado[0][5],
                        'periodo_dias': dias
                    }
                else:
                    return {
                        'success': True,
                        'total_usd': 0,
                        'total_eur': 0,
                        'total_cup': 0,
                        'total_transferencia': 0,
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
            fecha_hoy = date.today().isoformat()
            
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