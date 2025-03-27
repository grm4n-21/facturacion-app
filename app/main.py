#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Punto de entrada de la aplicación de facturación con escáner.
Este módulo inicia la aplicación y la interfaz gráfica.
"""

import sys
import os
from pathlib import Path

def main():
    """Función principal que inicia la aplicación"""
    # Determinar si es un exe o script
    if getattr(sys, 'frozen', False):
        # Ejecutando como archivo congelado (exe)
        app_path = Path(sys.executable).parent
        # Añadir la carpeta scripts al path para poder importar setup.py
        scripts_path = app_path / "scripts"
        if scripts_path.exists():
            sys.path.append(str(scripts_path))
    else:
        # Ejecutando como script
        # Asegurar que los módulos de la aplicación se puedan importar
        app_path = Path(__file__).parent.parent
        sys.path.insert(0, str(app_path))
    
    # Verificar si la base de datos existe
    db_path = app_path / "data" / "facturacion.db"
    if not db_path.exists():
        print(f"Base de datos no encontrada en {db_path}")
        print("Ejecutando configuración inicial...")
        
        try:
            # Importar y ejecutar setup
            from scripts.setup import run_setup
            success = run_setup(force=False, db_path=str(db_path))
            if not success:
                print("Error en la configuración inicial. Continuando con precaución...")
        except Exception as e:
            print(f"Error al ejecutar configuración inicial: {e}")
            import traceback
            traceback.print_exc()
    
    # Importar PyQt y otros módulos después de la configuración inicial
    from PyQt6.QtWidgets import QApplication
    from app.ui.main_window import MainWindow
    
    app = QApplication(sys.argv)
    app.setApplicationName("Sistema de Facturación")
    
    # Crear y mostrar la ventana principal
    window = MainWindow()
    window.show()
    
    # Ejecutar el bucle de eventos
    sys.exit(app.exec())

if __name__ == "__main__":
    main()