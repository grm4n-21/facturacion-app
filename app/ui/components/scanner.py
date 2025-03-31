# -*- coding: utf-8 -*-

"""
Componente para el escaneo de códigos de barras.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton,
                            QDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import cv2

class ScannerWidget(QDialog):
    """Widget para escanear códigos de barras utilizando la cámara"""
    
    codigo_escaneado = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Escáner de Códigos")
        self.setMinimumSize(640, 480)
        
        # Inicializar cámara
        self.camara = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.actualizar_frame)
        
        # Configurar interfaz
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        layout = QVBoxLayout(self)
        
        # Label para mostrar el video
        self.imagen_label = QLabel()
        self.imagen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.imagen_label)
        
        # Etiqueta de instrucciones
        instrucciones = QLabel("Coloque el código de barras frente a la cámara.")
        instrucciones.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(instrucciones)
        
        # Botón para cancelar
        cancelar_btn = QPushButton("Cancelar")
        cancelar_btn.clicked.connect(self.reject)
        layout.addWidget(cancelar_btn)
    
    def showEvent(self, event):
        """Evento que se dispara cuando el diálogo se muestra"""
        super().showEvent(event)
        self.iniciar_camara()
    
    def closeEvent(self, event):
        """Evento que se dispara cuando el diálogo se cierra"""
        self.detener_camara()
        super().closeEvent(event)
    
    def iniciar_camara(self):
        """Inicia la captura de video desde la cámara"""
        self.camara = cv2.VideoCapture(0)
        
        if not self.camara.isOpened():
            QMessageBox.critical(self, "Error", "No se pudo acceder a la cámara.")
            self.reject()
            return
        
        self.timer.start(30)  # Actualizar cada 30ms (aprox. 33fps)
    
    def detener_camara(self):
        """Detiene la captura de video"""
        if self.timer.isActive():
            self.timer.stop()
        
        if self.camara is not None and self.camara.isOpened():
            self.camara.release()
            self.camara = None
    
    