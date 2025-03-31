#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Punto de entrada de la aplicación de facturación con escáner.
Este módulo inicia la aplicación y la interfaz gráfica.
"""

import sys
import os
from pathlib import Path

# Asegurar que los módulos de la aplicación se puedan importar
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.ui.dialogs.login_dialog import LoginDialog

def main():
    """Función principal que inicia la aplicación"""
    app = QApplication(sys.argv)
    app.setApplicationName("Sistema de Facturación")
    
    # Mostrar diálogo de inicio de sesión
    login_dialog = LoginDialog()
    if login_dialog.exec() != LoginDialog.DialogCode.Accepted:
        # Si el usuario cancela o ingresa clave incorrecta, salir
        print("Acceso denegado: clave incorrecta o cancelación.")
        return
    
    # Crear y mostrar la ventana principal solo si la clave es correcta
    window = MainWindow()
    window.show()
    
    # Ejecutar el bucle de eventos
    sys.exit(app.exec())

if __name__ == "__main__":
    main()