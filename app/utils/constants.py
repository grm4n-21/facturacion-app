# -*- coding: utf-8 -*-

"""
Constantes utilizadas en la aplicación.
"""

# Versión de la aplicación
APP_VERSION = "1.0.0"
APP_NAME = "Sistema de Facturación"

# Monedas soportadas
CURRENCIES = ["USD", "CUP"]

# Formatos de fecha y hora
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DISPLAY_DATE_FORMAT = "%d/%m/%Y"
DISPLAY_DATETIME_FORMAT = "%d/%m/%Y %H:%M"

# Mensajes
MESSAGES = {
    "scan_success": "Código escaneado con éxito",
    "scan_error": "Error al escanear código",
    "scan_cancel": "Escaneo cancelado",
    "invoice_success": "Factura registrada correctamente",
    "invoice_error": "Error al registrar factura",
    "rate_success": "Tasa de cambio actualizada correctamente",
    "rate_error": "Error al actualizar tasa de cambio",
    "export_success": "Reporte exportado correctamente",
    "export_error": "Error al exportar reporte",
    "no_data": "No hay datos para mostrar",
}

# Colores para la interfaz
COLORS = {
    "usd_row": "#F0FFF0",  # Verde claro para filas USD
    "cup_row": "#F0F0FF",  # Azul claro para filas CUP
    "header": "#E0E0E0",    # Gris claro para encabezados
    "total": "#FFF0F0",     # Rojo claro para totales
}