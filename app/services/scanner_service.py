# -*- coding: utf-8 -*-

"""
Servicio para el escaneo de códigos de barras.
"""

from app.ui.components.scanner import ScannerWidget
from PyQt6.QtWidgets import QApplication

class ScannerService:
    """Servicio para gestionar el escaneo de códigos de barras"""
    
    def __init__(self):
        """Inicializa el servicio de escaneo"""
        pass
    
    def escanear(self) -> str:
        """
        Inicia el proceso de escaneo de código de barras
        
        Returns:
            Código escaneado o cadena vacía si se cancela
        """
        # Crear un nuevo diálogo de escaneo
        scanner_dialog = ScannerWidget()
        
        # Código escaneado
        codigo_escaneado = ""
        
        # Conectar la señal de código escaneado
        scanner_dialog.codigo_escaneado.connect(lambda codigo: setattr(scanner_dialog, "codigo", codigo))
        
        # Mostrar el diálogo y esperar a que se cierre
        if scanner_dialog.exec():
            # Si se aceptó, obtener el código escaneado
            codigo_escaneado = getattr(scanner_dialog, "codigo", "")
        
        return codigo_escaneado
    
    def simular_escaneo(self, codigo: str) -> str:
        """
        Simula un escaneo de código de barras (para pruebas)
        
        Args:
            codigo: Código a simular
            
        Returns:
            El mismo código ingresado
        """
        return codigo