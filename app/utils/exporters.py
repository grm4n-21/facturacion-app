# -*- coding: utf-8 -*-

"""
Utilidades para exportar datos a diferentes formatos.
"""

import os
import csv
from datetime import datetime, date, timedelta
import json
from typing import List, Dict, Any

class CSVExporter:
    """Clase para exportar datos a formato CSV"""
    
    @staticmethod
    def export(data: List[Dict[str, Any]], filepath: str, headers: List[str] = None) -> bool:
        """
        Exporta datos a un archivo CSV
        
        Args:
            data: Lista de diccionarios con los datos a exportar
            filepath: Ruta del archivo de destino
            headers: Encabezados a utilizar (si es None, se usan las claves del primer diccionario)
            
        Returns:
            True si la exportación fue exitosa, False en caso contrario
        """
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Si no hay datos, no hay nada que exportar
            if not data:
                return False
            
            # Si no se proporcionan encabezados, usar las claves del primer diccionario
            if headers is None:
                headers = list(data[0].keys())
            
            # Escribir archivo CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=headers)
                writer.writeheader()
                
                for row in data:
                    # Filtrar sólo las claves que están en los encabezados
                    filtered_row = {key: row.get(key, '') for key in headers}
                    writer.writerow(filtered_row)
            
            return True
            
        except Exception as e:
            print(f"Error al exportar a CSV: {e}")
            return False

class JSONExporter:
    """Clase para exportar datos a formato JSON"""
    
    @staticmethod
    def export(data: Any, filepath: str, indent: int = 4) -> bool:
        """
        Exporta datos a un archivo JSON
        
        Args:
            data: Datos a exportar (debe ser serializable a JSON)
            filepath: Ruta del archivo de destino
            indent: Indentación a utilizar
            
        Returns:
            True si la exportación fue exitosa, False en caso contrario
        """
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Convertir datetime a strings
            def json_serial(obj):
                if isinstance(obj, (datetime.datetime, datetime.date)):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")
            
            # Escribir archivo JSON
            with open(filepath, 'w', encoding='utf-8') as json_file:
                json.dump(data, json_file, indent=indent, default=json_serial)
            
            return True
            
        except Exception as e:
            print(f"Error al exportar a JSON: {e}")
            return False

class ReportExporter:
    """Clase para exportar reportes de facturación"""
    
    @staticmethod
    def export_invoice_report(
        facturas: List[Dict],
        filepath: str,
        formato: str = 'csv',
        include_summary: bool = True
    ) -> bool:
        """
        Exporta un reporte de facturas
        
        Args:
            facturas: Lista de diccionarios con los datos de facturas
            filepath: Ruta del archivo de destino
            formato: Formato de exportación ('csv' o 'json')
            include_summary: Incluir resumen al final del reporte
            
        Returns:
            True si la exportación fue exitosa, False en caso contrario
        """
        try:
            # Si no hay facturas, no hay nada que exportar
            if not facturas:
                return False
            
            # Calcular totales para el resumen
            total_usd = 0.0
            total_cup = 0.0
            
            for factura in facturas:
                if factura['moneda'] == 'USD':
                    total_usd += factura['monto']
                else:  # CUP
                    total_cup += factura['monto']
            
            # Exportar según formato
            if formato.lower() == 'csv':
                # Definir encabezados
                headers = ['id', 'orden_id', 'monto', 'moneda', 'monto_equivalente', 'fecha']
                
                # Exportar datos
                result = CSVExporter.export(facturas, filepath, headers)
                
                # Añadir resumen si se solicita
                if result and include_summary:
                    with open(filepath, 'a', encoding='utf-8') as f:
                        f.write('\n')
                        f.write('RESUMEN\n')
                        f.write(f'Total de facturas,{len(facturas)}\n')
                        f.write(f'Total USD,${total_usd:.2f}\n')
                        f.write(f'Total CUP,${total_cup:.2f}\n')
                
                return result
                
            elif formato.lower() == 'json':
                # Preparar datos con resumen
                data = {
                    'facturas': facturas,
                    'resumen': {
                        'total_facturas': len(facturas),
                        'total_usd': total_usd,
                        'total_cup': total_cup
                    }
                }
                
                # Exportar datos
                return JSONExporter.export(data, filepath)
                
            else:
                print(f"Formato de exportación no soportado: {formato}")
                return False
                
        except Exception as e:
            print(f"Error al exportar reporte de facturas: {e}")
            return False
    
    @staticmethod
    def export_exchange_rate_history(
        tasas: List[Dict],
        filepath: str,
        formato: str = 'csv'
    ) -> bool:
        """
        Exporta el historial de tasas de cambio
        
        Args:
            tasas: Lista de diccionarios con los datos de tasas de cambio
            filepath: Ruta del archivo de destino
            formato: Formato de exportación ('csv' o 'json')
            
        Returns:
            True si la exportación fue exitosa, False en caso contrario
        """
        try:
            # Si no hay tasas, no hay nada que exportar
            if not tasas:
                return False
            
            # Exportar según formato
            if formato.lower() == 'csv':
                # Definir encabezados
                headers = ['fecha', 'valor']
                
                # Exportar datos
                return CSVExporter.export(tasas, filepath, headers)
                
            elif formato.lower() == 'json':
                # Preparar datos
                data = {
                    'tasas_cambio': tasas,
                    'metadata': {
                        'fecha_exportacion': datetime.datetime.now().isoformat(),
                        'total_registros': len(tasas)
                    }
                }
                
                # Exportar datos
                return JSONExporter.export(data, filepath)
                
            else:
                print(f"Formato de exportación no soportado: {formato}")
                return False
                
        except Exception as e:
            print(f"Error al exportar historial de tasas de cambio: {e}")
            return False