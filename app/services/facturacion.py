# -*- coding: utf-8 -*-

"""
Servicio para la gestión de facturas.
Implementa la lógica de negocio relacionada con la facturación.
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional

from app.database.db_manager import DatabaseManager
from app.database.models import Factura
from app.services.exchange_rate import ExchangeRateService

class FacturacionService:
    """Servicio para la gestión de facturas"""
    
    def __init__(self):
        """Inicializa el servicio de facturación"""
        self.db = DatabaseManager()
        self.exchange_service = ExchangeRateService()
    
    def registrar_factura(self, orden_id: str, monto: float, moneda: str, 
                     pago_usd: float = 0, pago_eur: float = 0, pago_cup: float = 0, 
                     pago_transferencia: float = 0, transferencia_id: str = None,
                     mensajero: str = None) -> bool:
        """
        Registra una nueva factura en el sistema con pagos mixtos
        
        Args:
            orden_id: Identificador de la orden
            monto: Monto total de la factura
            moneda: Moneda principal de la factura ('USD', 'EUR' o 'CUP')
            pago_usd: Monto pagado en USD
            pago_eur: Monto pagado en EUR
            pago_cup: Monto pagado en CUP
            pago_transferencia: Monto pagado por transferencia
            transferencia_id: ID de la transferencia
            mensajero: Nombre del mensajero que entregó la factura (obligatorio)
            
        Returns:
            True si la factura se registró correctamente, False en caso contrario
        """
        try:
            # Validar datos
            if not orden_id or monto <= 0 or moneda not in ['USD', 'EUR', 'CUP']:
                return False
                
            # Validar mensajero (obligatorio)
            if not mensajero:
                print("Error: El nombre del mensajero es obligatorio")
                return False
            
            # Verificar si ya existe una factura con el mismo orden_id
            self.db.connect()
            factura_existente = self.db.fetch_one(
                "SELECT COUNT(*) FROM facturas WHERE orden_id = ?",
                (orden_id,)
            )
            
            if factura_existente and factura_existente[0] > 0:
                print(f"Ya existe una factura con el orden_id: {orden_id}")
                self.db.disconnect()
                return False
                
            # Convertir explícitamente todos los valores a float para garantizar el tipo correcto
            try:
                monto = float(monto)
                pago_usd = float(pago_usd) if pago_usd is not None else 0.0
                pago_eur = float(pago_eur) if pago_eur is not None else 0.0
                pago_cup = float(pago_cup) if pago_cup is not None else 0.0
                pago_transferencia = float(pago_transferencia) if pago_transferencia is not None else 0.0
            except (ValueError, TypeError) as e:
                print(f"Error al convertir valores a float: {e}")
                self.db.disconnect()
                return False
            
            # Obtener tasas de cambio
            tasas = self.exchange_service.obtener_tasas_actuales()
            tasa_usd = tasas['usd']
            tasa_eur = tasas['eur']
            
            # Calcular monto equivalente en USD (para estandarizar)
            if moneda == "USD":
                monto_equivalente = monto
                tasa_usada = tasa_usd
            elif moneda == "EUR":
                monto_equivalente = monto * (tasa_eur / tasa_usd)  # Convertir EUR a USD
                tasa_usada = tasa_eur
            else:  # CUP
                monto_equivalente = monto / tasa_usd
                tasa_usada = tasa_usd
            
            # Verificar que los pagos son válidos
            if pago_usd < 0 or pago_eur < 0 or pago_cup < 0 or pago_transferencia < 0:
                self.db.disconnect()
                return False
            
            # Si hay pago por transferencia, debe tener ID
            if pago_transferencia > 0 and not transferencia_id:
                self.db.disconnect()
                return False
            
            # Verificar que los pagos cubren el monto total
            total_en_moneda_principal = 0
            
            if moneda == "USD":
                total_en_moneda_principal = pago_usd + (pago_eur * tasa_eur / tasa_usd) + (pago_cup / tasa_usd) + (pago_transferencia / tasa_usd)
            elif moneda == "EUR":
                total_en_moneda_principal = pago_eur + (pago_usd * tasa_usd / tasa_eur) + (pago_cup / tasa_eur) + (pago_transferencia / tasa_eur)
            else:  # CUP
                total_en_moneda_principal = pago_cup + (pago_usd * tasa_usd) + (pago_eur * tasa_eur) + pago_transferencia
            
            # Permitir un pequeño margen de error por redondeo
            if total_en_moneda_principal < monto - 0.01:
                print(f"Pago insuficiente: {total_en_moneda_principal} vs {monto}")
                self.db.disconnect()
                return False
            
            # Imprimir valores para depuración
            print("Valores a insertar:")
            print(f"orden_id: {orden_id}")
            print(f"monto: {monto}")
            print(f"moneda: {moneda}")
            print(f"monto_equivalente: {monto_equivalente}")
            print(f"pago_usd: {pago_usd}")
            print(f"pago_eur: {pago_eur}")
            print(f"pago_cup: {pago_cup}")
            print(f"pago_transferencia: {pago_transferencia}")
            print(f"transferencia_id: {transferencia_id}")
            print(f"tasa_usada: {tasa_usada}")
            print(f"mensajero: {mensajero}")
            
            # Preparar parámetros explícitamente
            params = (
                str(orden_id),
                float(monto),
                str(moneda),
                float(monto_equivalente),
                float(pago_usd),
                float(pago_eur),
                float(pago_cup),
                float(pago_transferencia),
                transferencia_id,
                float(tasa_usada),
                str(mensajero)
            )
            
            # Verificar si la tabla tiene la columna mensajero
            tiene_columna_mensajero = False
            try:
                self.db.execute("SELECT mensajero FROM facturas LIMIT 1")
                tiene_columna_mensajero = True
            except:
                # Añadir la columna si no existe
                try:
                    self.db.execute("ALTER TABLE facturas ADD COLUMN mensajero TEXT NOT NULL DEFAULT 'No especificado'")
                    self.db.commit()
                    tiene_columna_mensajero = True
                    print("Columna 'mensajero' añadida a la tabla 'facturas'")
                except Exception as e:
                    print(f"Error al añadir columna 'mensajero': {e}")
                    self.db.disconnect()
                    return False
            
            # Insertar en la base de datos
            if tiene_columna_mensajero:
                cursor = self.db.execute(
                    "INSERT INTO facturas (orden_id, monto, moneda, monto_equivalente, pago_usd, pago_eur, pago_cup, pago_transferencia, transferencia_id, tasa_usada, fecha, mensajero) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)",
                    params
                )
            else:
                # Fallback sin mensajero (no debería ocurrir después de añadir la columna)
                cursor = self.db.execute(
                    "INSERT INTO facturas (orden_id, monto, moneda, monto_equivalente, pago_usd, pago_eur, pago_cup, pago_transferencia, transferencia_id, tasa_usada, fecha) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
                    params[:-1]  # Excluir mensajero
                )
            
            # Verificar la inserción
            if cursor:
                factura_id = cursor.lastrowid
                verificacion = self.db.fetch_one(
                    "SELECT pago_eur, pago_transferencia, mensajero FROM facturas WHERE id = ?",
                    (factura_id,)
                )
                
                if verificacion:
                    print(f"Verificación - pago_eur: {verificacion[0]}, pago_transferencia: {verificacion[1]}, mensajero: {verificacion[2] if len(verificacion) > 2 else 'N/A'}")
            
            self.db.commit()
            self.db.disconnect()
            
            return True
            
        except Exception as e:
            print(f"Error al registrar factura: {e}")
            # Imprimir traceback para más detalles
            import traceback
            traceback.print_exc()
            
            # Asegurar que la conexión se cierra en caso de error
            try:
                if self.db.connection:
                    self.db.disconnect()
            except:
                pass
                
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
            
            # Verificar si la tabla tiene las columnas necesarias
            tabla_actualizada = False
            tiene_mensajero = False
            try:
                self.db.execute("SELECT pago_usd, pago_eur, pago_cup, pago_transferencia FROM facturas LIMIT 1")
                tabla_actualizada = True
                
                try:
                    self.db.execute("SELECT mensajero FROM facturas LIMIT 1")
                    tiene_mensajero = True
                except:
                    tiene_mensajero = False
            except:
                tabla_actualizada = False
            
            # Realizar la consulta apropiada
            if tabla_actualizada and tiene_mensajero:
                resultado = self.db.fetch_all(
                    "SELECT id, orden_id, monto, moneda, monto_equivalente, pago_usd, pago_eur, pago_cup, pago_transferencia, fecha, mensajero "
                    "FROM facturas ORDER BY fecha DESC LIMIT ?",
                    (limite,)
                )
            elif tabla_actualizada:
                resultado = self.db.fetch_all(
                    "SELECT id, orden_id, monto, moneda, monto_equivalente, pago_usd, pago_eur, pago_cup, pago_transferencia, fecha "
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
                if tabla_actualizada and tiene_mensajero:
                    factura = Factura(
                        id=row[0],
                        orden_id=row[1],
                        monto=row[2],
                        moneda=row[3],
                        monto_equivalente=row[4],
                        pago_usd=row[5],
                        pago_eur=row[6],
                        pago_cup=row[7],
                        pago_transferencia=row[8],
                        fecha=datetime.fromisoformat(row[9].replace("Z", "+00:00")) 
                            if "Z" in row[9] else datetime.fromisoformat(row[9]),
                        mensajero=row[10]
                    )
                elif tabla_actualizada:
                    factura = Factura(
                        id=row[0],
                        orden_id=row[1],
                        monto=row[2],
                        moneda=row[3],
                        monto_equivalente=row[4],
                        pago_usd=row[5],
                        pago_eur=row[6],
                        pago_cup=row[7],
                        pago_transferencia=row[8],
                        fecha=datetime.fromisoformat(row[9].replace("Z", "+00:00")) 
                            if "Z" in row[9] else datetime.fromisoformat(row[9]),
                        mensajero="No especificado"  # Valor por defecto
                    )
                else:
                    factura = Factura.from_db_row(row)
                
                facturas.append(factura)
                    
            return facturas
                
        except Exception as e:
            print(f"Error al obtener facturas recientes: {e}")
            return []
        
    def obtener_facturas_por_orden_id(self, orden_id):
        """
        Obtiene facturas por ID de orden
        
        Args:
            orden_id: ID de orden a buscar
            
        Returns:
            Lista de objetos Factura
        """
        try:
            # Conectar a la base de datos
            self.db.connect()
            
            # Verificar si la tabla tiene la columna mensajero
            tiene_mensajero = False
            try:
                self.db.execute("SELECT mensajero FROM facturas LIMIT 1")
                tiene_mensajero = True
            except:
                tiene_mensajero = False
            
            # Consultar facturas
            if tiene_mensajero:
                query = """
                SELECT id, orden_id, monto, moneda, monto_equivalente, fecha, mensajero,
                    pago_usd, pago_eur, pago_cup, pago_transferencia, 
                    transferencia_id, tasa_usada, cerrada, dia_id
                FROM facturas 
                WHERE orden_id = ?
                ORDER BY fecha DESC
                """
            else:
                query = """
                SELECT id, orden_id, monto, moneda, monto_equivalente, fecha,
                    pago_usd, pago_eur, pago_cup, pago_transferencia, 
                    transferencia_id, tasa_usada, cerrada, dia_id
                FROM facturas 
                WHERE orden_id = ?
                ORDER BY fecha DESC
                """
            
            rows = self.db.fetch_all(query, (orden_id,))
            self.db.disconnect()
            
            # Convertir a objetos Factura
            facturas = []
            for row in rows:
                try:
                    # Procesar fecha
                    fecha_str = row[5]
                    try:
                        if "Z" in fecha_str:
                            fecha = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                        elif "T" in fecha_str:
                            fecha = datetime.fromisoformat(fecha_str)
                        else:
                            fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
                    except Exception as e:
                        print(f"Error al procesar fecha '{fecha_str}': {e}")
                        fecha = datetime.now()
                    
                    # Crear objeto Factura según las columnas disponibles
                    if tiene_mensajero:
                        factura = Factura(
                            id=row[0],
                            orden_id=row[1],
                            monto=row[2],
                            moneda=row[3],
                            monto_equivalente=row[4],
                            fecha=fecha,
                            mensajero=row[6],
                            pago_usd=row[7] if row[7] is not None else 0,
                            pago_eur=row[8] if row[8] is not None else 0,
                            pago_cup=row[9] if row[9] is not None else 0,
                            pago_transferencia=row[10] if row[10] is not None else 0,
                            transferencia_id=row[11],
                            tasa_usada=row[12],
                            cerrada=bool(row[13]) if row[13] is not None else False,
                            dia_id=row[14]
                        )
                    else:
                        factura = Factura(
                            id=row[0],
                            orden_id=row[1],
                            monto=row[2],
                            moneda=row[3],
                            monto_equivalente=row[4],
                            fecha=fecha,
                            # mensajero se usa con su valor por defecto
                            pago_usd=row[6] if row[6] is not None else 0,
                            pago_eur=row[7] if row[7] is not None else 0,
                            pago_cup=row[8] if row[8] is not None else 0,
                            pago_transferencia=row[9] if row[9] is not None else 0,
                            transferencia_id=row[10],
                            tasa_usada=row[11],
                            cerrada=bool(row[12]) if row[12] is not None else False,
                            dia_id=row[13]
                        )
                    
                    facturas.append(factura)
                except Exception as e:
                    print(f"Error al procesar factura: {e}")
                    import traceback
                    traceback.print_exc()
                    print(f"Datos de la fila: {row}")
            
            return facturas
        except Exception as e:
            print(f"Error al obtener facturas por orden ID: {e}")
            import traceback
            traceback.print_exc()
            try:
                if self.db.connection:
                    self.db.disconnect()
            except:
                pass
            return []
    
    def obtener_factura_por_id(self, factura_id):
        """
        Obtiene una factura por su ID
        
        Args:
            factura_id: ID de la factura a buscar
            
        Returns:
            Objeto Factura o None si no se encuentra
        """
        try:
            # Conectar a la base de datos
            self.db.connect()
            
            # Intentar obtener la columna mensajero
            tiene_mensajero = False
            try:
                self.db.execute("SELECT mensajero FROM facturas LIMIT 1")
                tiene_mensajero = True
            except:
                tiene_mensajero = False
            
            # Construir la consulta según las columnas disponibles
            if tiene_mensajero:
                query = """
                SELECT id, orden_id, monto, moneda, monto_equivalente, fecha, mensajero, 
                    pago_usd, pago_eur, pago_cup, pago_transferencia, 
                    transferencia_id, tasa_usada, cerrada, dia_id
                FROM facturas 
                WHERE id = ?
                """
            else:
                query = """
                SELECT id, orden_id, monto, moneda, monto_equivalente, fecha, 
                    pago_usd, pago_eur, pago_cup, pago_transferencia, 
                    transferencia_id, tasa_usada, cerrada, dia_id
                FROM facturas 
                WHERE id = ?
                """
            
            row = self.db.fetch_one(query, (factura_id,))
            self.db.disconnect()
            
            if not row:
                return None
            
            # Procesar la fecha correctamente
            fecha_str = row[5]
            try:
                if "Z" in fecha_str:
                    fecha = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                else:
                    # Determine el formato correcto
                    if "T" in fecha_str:
                        fecha = datetime.fromisoformat(fecha_str)
                    else:
                        fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            except Exception as e:
                print(f"Error al procesar fecha '{fecha_str}': {e}")
                fecha = datetime.now()  # Usar fecha actual como fallback
            
            # Crear objeto Factura con todos los campos, manejando la posición de mensajero
            if tiene_mensajero:
                factura = Factura(
                    id=row[0],
                    orden_id=row[1],
                    monto=row[2],
                    moneda=row[3],
                    monto_equivalente=row[4],
                    fecha=fecha,
                    mensajero=row[6],
                    pago_usd=row[7] if row[7] is not None else 0,
                    pago_eur=row[8] if row[8] is not None else 0,
                    pago_cup=row[9] if row[9] is not None else 0,
                    pago_transferencia=row[10] if row[10] is not None else 0,
                    transferencia_id=row[11],
                    tasa_usada=row[12],
                    cerrada=bool(row[13]) if row[13] is not None else False,
                    dia_id=row[14]
                )
            else:
                factura = Factura(
                    id=row[0],
                    orden_id=row[1],
                    monto=row[2],
                    moneda=row[3],
                    monto_equivalente=row[4],
                    fecha=fecha,
                    # mensajero usa el valor por defecto
                    pago_usd=row[6] if row[6] is not None else 0,
                    pago_eur=row[7] if row[7] is not None else 0,
                    pago_cup=row[8] if row[8] is not None else 0,
                    pago_transferencia=row[9] if row[9] is not None else 0,
                    transferencia_id=row[10],
                    tasa_usada=row[11],
                    cerrada=bool(row[12]) if row[12] is not None else False,
                    dia_id=row[13]
                )
            
            return factura
        except Exception as e:
            print(f"Error al obtener factura por ID: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.db.disconnect()
            except:
                pass
            return None
    
    def obtener_tasa_cambio(self) -> float:
        """
        Obtiene la tasa de cambio actual
        
        Returns:
            Tasa de cambio actual USD a CUP
        """
        return self.exchange_service.obtener_tasa_actual()
    
    

    def actualizar_pagos_factura(self, factura_id, pago_usd, pago_eur, pago_cup, pago_transferencia, transferencia_id=None):
        """
        Actualiza los medios de pago de una factura
        
        Args:
            factura_id: ID de la factura a actualizar
            pago_usd: Monto pagado en USD
            pago_eur: Monto pagado en EUR
            pago_cup: Monto pagado en CUP
            pago_transferencia: Monto pagado por transferencia
            transferencia_id: ID de la transferencia (opcional)
            
        Returns:
            True si la actualización fue exitosa, False en caso contrario
        """
        try:
            # Conectar a la base de datos
            self.db.connect()
            
            # Actualizar factura
            query = """
            UPDATE facturas
            SET pago_usd = ?, pago_eur = ?, pago_cup = ?, pago_transferencia = ?, transferencia_id = ?
            WHERE id = ? AND (cerrada = 0 OR cerrada IS NULL)
            """
            
            self.db.execute(query, (
                pago_usd, pago_eur, pago_cup, pago_transferencia, 
                transferencia_id, factura_id
            ))
            
            self.db.commit()
            self.db.disconnect()
            
            return True
        except Exception as e:
            print(f"Error al actualizar pagos de factura: {e}")
            try:
                self.db.disconnect()
            except:
                pass
            return False
    # En facturacion.py
    def cerrar_facturas_por_fecha(self, fecha):
        """
        Marca como cerradas todas las facturas hasta la fecha especificada
        """
        try:
            # Convertir fecha a objeto date si es string
            if isinstance(fecha, str):
                fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
            
            # Calcular fecha límite (fin del día)
            fecha_limite = datetime.combine(fecha, datetime.max.time())
            
            # Marcar facturas como cerradas
            self.db.session.query(Factura).filter(
                Factura.fecha <= fecha_limite,
                (Factura.cerrada == False) | (Factura.cerrada == None)
            ).update({"cerrada": True})
            
            self.db.session.commit()
            return True
        except Exception as e:
            print(f"Error al cerrar facturas: {e}")
            self.db.session.rollback()
            return False


    def obtener_facturas_sin_cerrar(self):
        """
        Obtiene todas las facturas que no han sido cerradas
        Returns:
            list: Lista de objetos Factura que no están cerradas
        """
        try:
            # Consultar facturas no cerradas
            query = """
            SELECT id, orden_id, monto, moneda, fecha, cerrada, pago_usd, pago_eur, pago_cup, 
                pago_transferencia, transferencia_id 
            FROM facturas 
            WHERE cerrada = 0 OR cerrada IS NULL
            ORDER BY fecha DESC
            """
            
            # Usar fetch_all en lugar de fetchall
            self.db.connect()
            facturas_rows = self.db.fetch_all(query)
            self.db.disconnect()
            
            # Convertir las filas en diccionarios para facilitar su uso
            facturas = []
            for row in facturas_rows:
                factura = {
                    'id': row[0],
                    'orden_id': row[1],
                    'monto': row[2],
                    'moneda': row[3],
                    'fecha': row[4],
                    'cerrada': bool(row[5]) if row[5] is not None else False,
                    'pago_usd': row[6] if row[6] is not None else 0,
                    'pago_eur': row[7] if row[7] is not None else 0,
                    'pago_cup': row[8] if row[8] is not None else 0,
                    'pago_transferencia': row[9] if row[9] is not None else 0,
                    'transferencia_id': row[10]
                }
                facturas.append(factura)
            
            return facturas
        except Exception as e:
            print(f"Error al obtener facturas sin cerrar: {e}")
            try:
                self.db.disconnect()
            except:
                pass
            return []
        
    def verificar_orden_id_existente(self, orden_id: str) -> bool:
        """
        Verifica si ya existe una factura con el orden_id proporcionado
        
        Args:
            orden_id: Identificador de la orden a verificar
            
        Returns:
            True si ya existe una factura con ese orden_id, False en caso contrario
        """
        try:
            self.db.connect()
            resultado = self.db.fetch_one(
                "SELECT COUNT(*) FROM facturas WHERE orden_id = ?",
                (orden_id,)
            )
            self.db.disconnect()
            
            # Si el resultado es mayor que 0, ya existe una factura con ese orden_id
            return resultado and resultado[0] > 0
            
        except Exception as e:
            print(f"Error al verificar orden_id existente: {e}")
            if self.db.connection:
                self.db.disconnect()
            return False
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
            
            # Verificar si la tabla tiene la columna mensajero
            self.db.connect()
            tiene_mensajero = False
            try:
                self.db.execute("SELECT mensajero FROM facturas LIMIT 1")
                tiene_mensajero = True
            except:
                tiene_mensajero = False
            
            # Construir la consulta según las columnas disponibles
            if tiene_mensajero:
                query = """
                SELECT id, orden_id, monto, moneda, monto_equivalente, fecha, mensajero,
                    pago_usd, pago_eur, pago_cup, pago_transferencia,
                    transferencia_id, tasa_usada, cerrada, dia_id
                FROM facturas 
                WHERE fecha BETWEEN ? AND ? 
                ORDER BY fecha
                """
            else:
                query = """
                SELECT id, orden_id, monto, moneda, monto_equivalente, fecha,
                    pago_usd, pago_eur, pago_cup, pago_transferencia,
                    transferencia_id, tasa_usada, cerrada, dia_id
                FROM facturas 
                WHERE fecha BETWEEN ? AND ? 
                ORDER BY fecha
                """
            
            resultado = self.db.fetch_all(query, (fecha_inicio, fecha_fin_ajustada))
            self.db.disconnect()
            
            print(f"Consultando facturas entre {fecha_inicio} y {fecha_fin_ajustada}")
            print(f"Resultados encontrados: {len(resultado) if resultado else 0}")
            
            facturas = []
            for row in resultado:
                try:
                    # Procesar fecha
                    fecha_str = row[5]
                    try:
                        if "Z" in fecha_str:
                            fecha = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
                        elif "T" in fecha_str:
                            fecha = datetime.fromisoformat(fecha_str)
                        else:
                            fecha = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
                    except Exception as e:
                        print(f"Error al procesar fecha '{fecha_str}': {e}")
                        fecha = datetime.now()
                    
                    # Crear objeto Factura según las columnas disponibles
                    if tiene_mensajero:
                        factura = Factura(
                            id=row[0],
                            orden_id=row[1],
                            monto=row[2],
                            moneda=row[3],
                            monto_equivalente=row[4],
                            fecha=fecha,
                            mensajero=row[6],
                            pago_usd=row[7] if row[7] is not None else 0,
                            pago_eur=row[8] if row[8] is not None else 0,
                            pago_cup=row[9] if row[9] is not None else 0,
                            pago_transferencia=row[10] if row[10] is not None else 0,
                            transferencia_id=row[11],
                            tasa_usada=row[12],
                            cerrada=bool(row[13]) if row[13] is not None else False,
                            dia_id=row[14]
                        )
                    else:
                        factura = Factura(
                            id=row[0],
                            orden_id=row[1],
                            monto=row[2],
                            moneda=row[3],
                            monto_equivalente=row[4],
                            fecha=fecha,
                            # mensajero usa valor predeterminado
                            pago_usd=row[6] if row[6] is not None else 0,
                            pago_eur=row[7] if row[7] is not None else 0,
                            pago_cup=row[8] if row[8] is not None else 0,
                            pago_transferencia=row[9] if row[9] is not None else 0,
                            transferencia_id=row[10],
                            tasa_usada=row[11],
                            cerrada=bool(row[12]) if row[12] is not None else False,
                            dia_id=row[13]
                        )
                    
                    facturas.append(factura)
                except Exception as e:
                    print(f"Error al procesar factura: {e}")
                    import traceback
                    traceback.print_exc()
                    print(f"Datos de la fila: {row}")
            
            return facturas
            
        except Exception as e:
            print(f"Error al obtener facturas por fecha: {e}")
            import traceback
            traceback.print_exc()
            if self.db.connection:
                self.db.disconnect()
            return []