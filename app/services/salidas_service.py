# -*- coding: utf-8 -*-

"""
Servicio para la gestión de salidas de caja.
Implementa la lógica de negocio relacionada con las salidas de dinero.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict

from app.database.db_manager import DatabaseManager
from app.database.models import SalidaCaja

class SalidasService:
    """Servicio para la gestión de salidas de caja"""
    
    def __init__(self):
        """Inicializa el servicio de salidas de caja"""
        self.db = DatabaseManager()
    
    def calcular_saldo_disponible(self) -> Dict[str, float]:
        """
        Calcula el saldo disponible en caja para cada moneda
        
        Returns:
            Diccionario con los saldos disponibles por moneda
        """
        try:
            self.db.connect()
            
            # Obtener pagos de facturas sin cerrar
            pagos = self.db.fetch_one(
                "SELECT SUM(pago_usd), SUM(pago_eur), SUM(pago_cup), SUM(pago_transferencia) "
                "FROM facturas WHERE cerrada = 0"
            )
            
            total_usd = pagos[0] or 0 if pagos else 0
            total_eur = pagos[1] or 0 if pagos else 0
            total_cup = pagos[2] or 0 if pagos else 0
            total_transferencia = pagos[3] or 0 if pagos else 0
            
            # Restar salidas sin cerrar
            salidas = self.db.fetch_one(
                "SELECT SUM(monto_usd), SUM(monto_eur), SUM(monto_cup), SUM(monto_transferencia) "
                "FROM salidas_caja WHERE cerrada = 0"
            )
            
            if salidas and salidas[0] is not None:
                total_usd -= salidas[0] or 0
                total_eur -= salidas[1] or 0
                total_cup -= salidas[2] or 0
                total_transferencia -= salidas[3] or 0
            
            self.db.disconnect()
            
            return {
                'usd': total_usd,
                'eur': total_eur,
                'cup': total_cup,
                'transferencia': total_transferencia
            }
            
        except Exception as e:
            print(f"Error al calcular saldo disponible: {e}")
            if self.db.connection:
                self.db.disconnect()
            return {'usd': 0, 'eur': 0, 'cup': 0, 'transferencia': 0}
    
    def registrar_salida(self, monto_usd: float = 0, monto_eur: float = 0, 
                        monto_cup: float = 0, monto_transferencia: float = 0,
                        destinatario: str = "", autorizado_por: str = "",
                        motivo: str = "", validar_saldo: bool = True) -> Dict:
        """
        Registra una nueva salida de caja
        
        Args:
            monto_usd: Monto en USD a retirar
            monto_eur: Monto en EUR a retirar
            monto_cup: Monto en CUP a retirar
            monto_transferencia: Monto en transferencia a retirar
            destinatario: Persona que recibe el dinero
            autorizado_por: Persona que autoriza la salida
            motivo: Motivo de la salida
            validar_saldo: Si True, valida que haya suficiente saldo
            
        Returns:
            Diccionario con resultado de la operación
        """
        try:
            # Validar datos
            if not destinatario or not autorizado_por:
                return {
                    'success': False,
                    'message': "Debe especificar destinatario y quien autoriza la salida"
                }
                
            # Validar que al menos un monto sea mayor que cero
            if monto_usd <= 0 and monto_eur <= 0 and monto_cup <= 0 and monto_transferencia <= 0:
                return {
                    'success': False,
                    'message': "Debe especificar al menos un monto mayor que cero"
                }
            
            # Validar que hay suficiente saldo
            if validar_saldo:
                saldo = self.calcular_saldo_disponible()
                
                errores = []
                if monto_usd > 0 and monto_usd > saldo['usd']:
                    errores.append(f"No hay suficiente USD en caja. Disponible: {saldo['usd']:.2f}")
                
                if monto_eur > 0 and monto_eur > saldo['eur']:
                    errores.append(f"No hay suficiente EUR en caja. Disponible: {saldo['eur']:.2f}")
                
                if monto_cup > 0 and monto_cup > saldo['cup']:
                    errores.append(f"No hay suficiente CUP en caja. Disponible: {saldo['cup']:.2f}")
                
                if monto_transferencia > 0 and monto_transferencia > saldo['transferencia']:
                    errores.append(f"No hay suficiente saldo de transferencia. Disponible: {saldo['transferencia']:.2f}")
                
                if errores:
                    return {
                        'success': False,
                        'message': "\n".join(errores)
                    }
            
            # Insertar en la base de datos
            self.db.connect()
            self.db.execute(
                "INSERT INTO salidas_caja (monto_usd, monto_eur, monto_cup, monto_transferencia, destinatario, autorizado_por, motivo, fecha) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                (monto_usd, monto_eur, monto_cup, monto_transferencia, destinatario, autorizado_por, motivo)
            )
            
            salida_id = self.db.cursor.lastrowid
            self.db.commit()
            self.db.disconnect()
            
            return {
                'success': True,
                'message': "Salida registrada correctamente",
                'id': salida_id
            }
                
        except Exception as e:
            print(f"Error al registrar salida de caja: {e}")
            if self.db.connection:
                self.db.disconnect()
            return {
                'success': False,
                'message': f"Error: {str(e)}"
            }
    
    def obtener_salidas_recientes(self, limite: int = 10) -> List[Dict]:
        """
        Obtiene las salidas de caja más recientes
        
        Args:
            limite: Número máximo de salidas a devolver
            
        Returns:
            Lista de salidas de caja
        """
        try:
            self.db.connect()
            resultado = self.db.fetch_all(
                "SELECT id, fecha, monto_usd, monto_eur, monto_cup, monto_transferencia, "
                "destinatario, autorizado_por, motivo FROM salidas_caja "
                "ORDER BY fecha DESC LIMIT ?",
                (limite,)
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
                
        except Exception as e:
            print(f"Error al obtener salidas recientes: {e}")
            if self.db.connection:
                self.db.disconnect()
            return []
    
    def obtener_salidas_por_fecha(self, fecha_inicio: str, fecha_fin: str, destinatario=None, autorizado_por=None):
        """
        Obtiene las salidas en un rango de fechas con filtros opcionales
        
        Args:
            fecha_inicio: Fecha de inicio en formato 'YYYY-MM-DD'
            fecha_fin: Fecha de fin en formato 'YYYY-MM-DD'
            destinatario: Opcional - Filtrar por destinatario
            autorizado_por: Opcional - Filtrar por quien autorizó
            
        Returns:
            Lista de salidas de caja
        """
        try:
            # Ajustar fecha_fin para incluir todo el día
            fecha_fin_ajustada = f"{fecha_fin} 23:59:59"
            
            # Construir query base
            query = """
            SELECT id, fecha, monto_usd, monto_eur, monto_cup, monto_transferencia, 
                destinatario, autorizado_por, motivo
            FROM salidas_caja 
            WHERE fecha BETWEEN ? AND ?
            """
            
            params = [fecha_inicio, fecha_fin_ajustada]
            
            # Agregar filtros adicionales si se proporcionan
            if destinatario:
                query += " AND destinatario LIKE ?"
                params.append(f"%{destinatario}%")
            
            if autorizado_por:
                query += " AND autorizado_por LIKE ?"
                params.append(f"%{autorizado_por}%")
            
            # Finalizar query con orden
            query += " ORDER BY fecha DESC"
            
            print(f"Query salidas: {query}")
            print(f"Params: {params}")
            
            self.db.connect()
            cursor = self.db.connection.cursor()
            cursor.execute(query, params)
            resultado = cursor.fetchall()
            self.db.disconnect()
            
            print(f"Resultados encontrados: {len(resultado)}")
            
            salidas = []
            for row in resultado:
                salida = {
                    'id': row[0],
                    'fecha': row[1],
                    'monto_usd': row[2] or 0,
                    'monto_eur': row[3] or 0,
                    'monto_cup': row[4] or 0,
                    'monto_transferencia': row[5] or 0,
                    'destinatario': row[6] or '',
                    'autorizado_por': row[7] or '',
                    'motivo': row[8] or ''
                }
                salidas.append(salida)
                    
            return salidas
                
        except Exception as e:
            print(f"Error al obtener salidas por fecha: {e}")
            import traceback
            traceback.print_exc()
            if hasattr(self, 'db') and hasattr(self.db, 'connection') and self.db.connection:
                self.db.disconnect()
            return []
    
    def exportar_salidas_a_csv(self, fecha_inicio: str, fecha_fin: str, ruta_archivo: str) -> bool:
        """
        Exporta las salidas de un período a un archivo CSV
        
        Args:
            fecha_inicio: Fecha de inicio en formato 'YYYY-MM-DD'
            fecha_fin: Fecha de fin en formato 'YYYY-MM-DD'
            ruta_archivo: Ruta donde guardar el archivo CSV
            
        Returns:
            True si la exportación fue exitosa, False en caso contrario
        """
        try:
            import csv
            
            # Obtener salidas
            salidas = self.obtener_salidas_por_fecha(fecha_inicio, fecha_fin)
            
            if not salidas:
                return False
                
            # Exportar a CSV
            with open(ruta_archivo, 'w', newline='', encoding='utf-8') as archivo:
                writer = csv.writer(archivo)
                
                # Escribir encabezados
                writer.writerow([
                    'ID', 'Fecha', 'Monto USD', 'Monto EUR', 'Monto CUP', 'Monto Transferencia',
                    'Destinatario', 'Autorizado Por', 'Motivo'
                ])
                
                # Escribir datos
                for salida in salidas:
                    writer.writerow([
                        salida['id'],
                        salida['fecha'],
                        salida['monto_usd'],
                        salida['monto_eur'],
                        salida['monto_cup'],
                        salida['monto_transferencia'],
                        salida['destinatario'],
                        salida['autorizado_por'],
                        salida['motivo']
                    ])
                    
            return True
                
        except Exception as e:
            print(f"Error al exportar salidas a CSV: {e}")
            return False