# -*- coding: utf-8 -*-

"""
Diálogo simple de inicio de sesión.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtCore import Qt

from app.services.auth_service import AuthService

class LoginDialog(QDialog):
    """Diálogo simple para ingresar clave de acceso"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configuración de la ventana
        self.setWindowTitle("Acceso al Sistema")
        self.setFixedSize(350, 150)
        
        # Eliminar el botón de ayuda contextual (usando un método más compatible)
        flags = self.windowFlags()
        try:
            # Intentar con la nueva sintaxis
            flags = flags & ~Qt.WindowType.WindowContextHelpButtonHint
        except AttributeError:
            try:
                # Intentar con sintaxis alternativa
                flags = flags & ~Qt.WindowContextHelpButtonHint
            except:
                # Si falla, simplemente ignorar
                pass
        
        try:
            self.setWindowFlags(flags)
        except:
            # Si todo falla, no modificar los flags de la ventana
            pass
        
        # Inicializar servicio de autenticación
        self.auth_service = AuthService()
        
        # Inicializar la interfaz
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Mensaje
        mensaje = QLabel("Ingrese la clave de acceso:")
        mensaje.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(mensaje)
        
        # Campo de clave
        self.clave_input = QLineEdit()
        self.clave_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.clave_input.setPlaceholderText("Clave de acceso")
        self.clave_input.returnPressed.connect(self.verificar_clave)
        layout.addWidget(self.clave_input)
        
        # Botones
        botones_layout = QHBoxLayout()
        
        self.cancelar_btn = QPushButton("Cancelar")
        self.cancelar_btn.clicked.connect(self.reject)
        
        self.acceder_btn = QPushButton("Acceder")
        self.acceder_btn.clicked.connect(self.verificar_clave)
        self.acceder_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        botones_layout.addWidget(self.cancelar_btn)
        botones_layout.addWidget(self.acceder_btn)
        
        layout.addLayout(botones_layout)
    
    def verificar_clave(self):
        """Verifica si la clave ingresada es correcta"""
        clave = self.clave_input.text()
        
        if not clave:
            QMessageBox.warning(self, "Error", "Por favor, ingrese la clave de acceso.")
            return
        
        if self.auth_service.verificar_clave(clave):
            # Clave correcta
            self.accept()
        else:
            # Clave incorrecta
            QMessageBox.warning(self, "Error", "Clave de acceso incorrecta.")
            self.clave_input.clear()
            self.clave_input.setFocus()