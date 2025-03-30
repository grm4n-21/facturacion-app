# -*- coding: utf-8 -*-

"""
Pestaña de salidas de caja de la aplicación.
Gestiona la interfaz para registrar y visualizar salidas de dinero.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLabel, QLineEdit, QPushButton, QComboBox, 
                            QTableWidget, QTableWidgetItem, QGroupBox,
                            QMessageBox, QHeaderView, QTextEdit,
                            QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QRegularExpressionValidator, QColor
from datetime import date, timedelta
import os
from pathlib import Path
import datetime
from app.services.salidas_service import SalidasService

class SalidasTab(QWidget):
    """Pestaña para registrar y visualizar salidas de caja"""
    
    def __init__(self, exchange_service):
        super().__init__()
        
        # Inicializar servicios
        self.exchange_service = exchange_service
        self.salidas_service = SalidasService()
        
        # Configurar la interfaz
        self.init_ui()
        
        # Cargar datos iniciales
        self.cargar_salidas_recientes()
        self.actualizar_saldo_disponible()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Crear un área de desplazamiento
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Crear un widget contenedor para poner dentro del área de desplazamiento
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        
        # Título/Fecha
        fecha_actual = date.today().strftime("%d/%m/%Y")        
        titulo_label = QLabel(f"SALIDAS DE CAJA - {fecha_actual}")
        titulo_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(titulo_label)
        
        # Sección: Saldo disponible
        saldo_group = QGroupBox("Saldo Disponible")
        saldo_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        saldo_layout = QFormLayout()
        
        self.saldo_usd_label = QLabel("0.00")
        self.saldo_eur_label = QLabel("0.00")
        self.saldo_cup_label = QLabel("0.00")
        self.saldo_transferencia_label = QLabel("0.00")
        
        actualizar_saldo_btn = QPushButton("Actualizar")
        actualizar_saldo_btn.clicked.connect(self.actualizar_saldo_disponible)
        
        saldo_layout.addRow("USD:", self.saldo_usd_label)
        saldo_layout.addRow("EUR:", self.saldo_eur_label)
        saldo_layout.addRow("CUP:", self.saldo_cup_label)
        saldo_layout.addRow("Transferencia:", self.saldo_transferencia_label)
        saldo_layout.addRow("", actualizar_saldo_btn)
        
        saldo_group.setLayout(saldo_layout)
        container_layout.addWidget(saldo_group)
        
        # Sección 1: Datos de la Salida
        salida_group = QGroupBox("Datos de la Salida")
        salida_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        salida_layout = QFormLayout()
        
        # Destinatario
        self.destinatario_input = QLineEdit()
        self.destinatario_input.setPlaceholderText("Persona que recibe el dinero")
        salida_layout.addRow("Destinatario:", self.destinatario_input)
        
        # Autorizado por
        self.autorizado_por_input = QLineEdit()
        self.autorizado_por_input.setPlaceholderText("Persona que autoriza la salida")
        salida_layout.addRow("Autorizado por:", self.autorizado_por_input)
        
        # Motivo (área de texto)
        self.motivo_input = QTextEdit()
        self.motivo_input.setPlaceholderText("Motivo de la salida")
        self.motivo_input.setMaximumHeight(80)
        salida_layout.addRow("Motivo:", self.motivo_input)
        
        salida_group.setLayout(salida_layout)
        container_layout.addWidget(salida_group)
        
        # Sección 2: Montos a Retirar
        montos_group = QGroupBox("Montos a Retirar")
        montos_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        montos_layout = QFormLayout()
        
        # Monto USD
        self.monto_usd_input = QLineEdit()
        self.monto_usd_input.setPlaceholderText("0.00")
        self.monto_usd_input.setValidator(QDoubleValidator(0, 9999999.99, 2))
        montos_layout.addRow("USD:", self.monto_usd_input)
        
        # Monto EUR
        self.monto_eur_input = QLineEdit()
        self.monto_eur_input.setPlaceholderText("0.00")
        self.monto_eur_input.setValidator(QDoubleValidator(0, 9999999.99, 2))
        montos_layout.addRow("EUR:", self.monto_eur_input)
        
        # Monto CUP
        self.monto_cup_input = QLineEdit()
        self.monto_cup_input.setPlaceholderText("0.00")
        self.monto_cup_input.setValidator(QDoubleValidator(0, 9999999.99, 2))
        montos_layout.addRow("CUP:", self.monto_cup_input)
        
        # Monto Transferencia
        from PyQt6.QtCore import QRegularExpression
        
        self.monto_transferencia_input = QLineEdit()
        self.monto_transferencia_input.setPlaceholderText("0.00")
        
        # Usar expresión regular para permitir números grandes con hasta 2 decimales
        regex = QRegularExpression("^[0-9]*\\.?[0-9]{0,2}$")
        validator = QRegularExpressionValidator(regex)
        self.monto_transferencia_input.setValidator(validator)
        
        montos_layout.addRow("Transferencia:", self.monto_transferencia_input)
        
        montos_group.setLayout(montos_layout)
        container_layout.addWidget(montos_group)
        
        # Botón de registrar
        registrar_btn = QPushButton("REGISTRAR SALIDA")
        registrar_btn.setStyleSheet("""
            QPushButton {
                background-color: #E57373;
                color: white;
                font-weight: bold;
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #EF5350;
            }
        """)
        registrar_btn.clicked.connect(self.registrar_salida)
        container_layout.addWidget(registrar_btn)
        
        # Tabla de salidas recientes
        salidas_group = QGroupBox("Salidas Recientes")
        salidas_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        salidas_layout = QVBoxLayout()
        
        # Configurar tabla
        self.salidas_table = QTableWidget()
        self.salidas_table.setMinimumHeight(250)
        self.salidas_table.setColumnCount(9)
        self.salidas_table.setHorizontalHeaderLabels([
            "ID", "Fecha", "USD", "EUR", "CUP", "Transferencia", 
            "Destinatario", "Autorizado Por", "Motivo"
        ])
        
        # Mejorar la visualización de la tabla
        self.salidas_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.salidas_table.setAlternatingRowColors(True)
        self.salidas_table.setShowGrid(True)
        self.salidas_table.setGridStyle(Qt.PenStyle.SolidLine)
        
        salidas_layout.addWidget(self.salidas_table)
        salidas_group.setLayout(salidas_layout)
        container_layout.addWidget(salidas_group)
        
        # Configurar el scroll area
        scroll_area.setWidget(container_widget)
        main_layout.addWidget(scroll_area)
        
        # Dar foco al primer campo
        self.destinatario_input.setFocus()
    
    def actualizar_saldo_disponible(self):
        """Actualiza las etiquetas de saldo disponible"""
        saldo = self.salidas_service.calcular_saldo_disponible()
        
        # Actualizar etiquetas
        self.saldo_usd_label.setText(f"{saldo['usd']:.2f}")
        self.saldo_eur_label.setText(f"{saldo['eur']:.2f}")
        self.saldo_cup_label.setText(f"{saldo['cup']:.2f}")
        self.saldo_transferencia_label.setText(f"{saldo['transferencia']:.2f}")
        
        # Aplicar colores según el saldo
        for label, valor in [
            (self.saldo_usd_label, saldo['usd']),
            (self.saldo_eur_label, saldo['eur']),
            (self.saldo_cup_label, saldo['cup']),
            (self.saldo_transferencia_label, saldo['transferencia'])
        ]:
            if valor <= 0:
                label.setStyleSheet("color: red; font-weight: bold;")
            else:
                label.setStyleSheet("color: green; font-weight: bold;")
    
    def registrar_salida(self):
        """Registra una nueva salida de caja"""
        # Validar campos obligatorios
        if not self.destinatario_input.text():
            QMessageBox.warning(self, "Error", "Debe ingresar el destinatario")
            self.destinatario_input.setFocus()
            return
            
        if not self.autorizado_por_input.text():
            QMessageBox.warning(self, "Error", "Debe ingresar quién autoriza la salida")
            self.autorizado_por_input.setFocus()
            return
            
        # Obtener valores de los campos
        try:
            # Obtener montos
            monto_usd = float(self.monto_usd_input.text() or 0)
            monto_eur = float(self.monto_eur_input.text() or 0)
            monto_cup = float(self.monto_cup_input.text() or 0)
            monto_transferencia = float(self.monto_transferencia_input.text() or 0)
            
            # Verificar que al menos un monto sea mayor que cero
            if monto_usd <= 0 and monto_eur <= 0 and monto_cup <= 0 and monto_transferencia <= 0:
                QMessageBox.warning(self, "Error", "Debe ingresar al menos un monto mayor que cero")
                self.monto_usd_input.setFocus()
                return
                
            # Obtener otros campos
            destinatario = self.destinatario_input.text()
            autorizado_por = self.autorizado_por_input.text()
            motivo = self.motivo_input.toPlainText()
            
            # Verificar si hay suficiente saldo disponible
            saldo = self.salidas_service.calcular_saldo_disponible()
            
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
                QMessageBox.warning(self, "Saldo insuficiente", "\n".join(errores))
                return
            
            # Confirmar la operación
            respuesta = QMessageBox.question(
                self,
                "Confirmar Salida",
                f"¿Está seguro de registrar esta salida?\n\n"
                f"Destinatario: {destinatario}\n"
                f"Autorizado por: {autorizado_por}\n"
                f"Montos:\n"
                f"  USD: {monto_usd:.2f}\n"
                f"  EUR: {monto_eur:.2f}\n"
                f"  CUP: {monto_cup:.2f}\n"
                f"  Transferencia: {monto_transferencia:.2f}\n\n"
                f"Motivo: {motivo}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if respuesta == QMessageBox.StandardButton.No:
                return
            
            # Registrar salida
            resultado = self.salidas_service.registrar_salida(
                monto_usd=monto_usd,
                monto_eur=monto_eur,
                monto_cup=monto_cup,
                monto_transferencia=monto_transferencia,
                destinatario=destinatario,
                autorizado_por=autorizado_por,
                motivo=motivo,
                validar_saldo=True  # Ya validamos arriba, pero por seguridad
            )
            
            if resultado['success']:
                # Limpiar campos
                self.destinatario_input.clear()
                self.autorizado_por_input.clear()
                self.motivo_input.clear()
                self.monto_usd_input.clear()
                self.monto_eur_input.clear()
                self.monto_cup_input.clear()
                self.monto_transferencia_input.clear()
                
                # Actualizar tabla de salidas recientes
                self.cargar_salidas_recientes()
                
                # Actualizar saldo disponible
                self.actualizar_saldo_disponible()
                
                # Mensaje de éxito
                QMessageBox.information(self, "Éxito", "Salida registrada correctamente")
            else:
                QMessageBox.warning(self, "Error", resultado['message'])
                
        except ValueError:
            QMessageBox.warning(self, "Error", "Los valores monetarios deben ser números válidos")
            return
    
    def cargar_salidas_recientes(self):
        """Carga las salidas recientes en la tabla"""
        # Obtener salidas recientes
        salidas = self.salidas_service.obtener_salidas_recientes(20)
        
        # Limpiar tabla
        self.salidas_table.setRowCount(0)
        
        # Llenar tabla con datos
        for i, salida in enumerate(salidas):
            self.salidas_table.insertRow(i)
            
            # Crear items para cada columna
            id_item = QTableWidgetItem(str(salida['id']))
            fecha_item = QTableWidgetItem(str(salida['fecha']))
            usd_item = QTableWidgetItem(f"{salida['monto_usd']:.2f}")
            eur_item = QTableWidgetItem(f"{salida['monto_eur']:.2f}")
            cup_item = QTableWidgetItem(f"{salida['monto_cup']:.2f}")
            transferencia_item = QTableWidgetItem(f"{salida['monto_transferencia']:.2f}")
            destinatario_item = QTableWidgetItem(salida['destinatario'])
            autorizado_item = QTableWidgetItem(salida['autorizado_por'])
            motivo_item = QTableWidgetItem(salida['motivo'])
            
            # Configurar alineación para valores numéricos
            for item in [usd_item, eur_item, cup_item, transferencia_item]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
            # Colorear filas según montos
            if salida['monto_usd'] > 0:
                usd_item.setBackground(QColor(220, 255, 220))  # Verde claro
            if salida['monto_eur'] > 0:
                eur_item.setBackground(QColor(220, 220, 255))  # Azul claro
            if salida['monto_cup'] > 0:
                cup_item.setBackground(QColor(255, 220, 220))  # Rosa claro
            if salida['monto_transferencia'] > 0:
                transferencia_item.setBackground(QColor(255, 255, 220))  # Amarillo claro
            
                        # Añadir items a la tabla
            self.salidas_table.setItem(i, 0, id_item)
            self.salidas_table.setItem(i, 1, fecha_item)
            self.salidas_table.setItem(i, 2, usd_item)
            self.salidas_table.setItem(i, 3, eur_item)
            self.salidas_table.setItem(i, 4, cup_item)
            self.salidas_table.setItem(i, 5, transferencia_item)
            self.salidas_table.setItem(i, 6, destinatario_item)
            self.salidas_table.setItem(i, 7, autorizado_item)
            self.salidas_table.setItem(i, 8, motivo_item)
    
    def exportar_salidas(self, fecha_inicio, fecha_fin):
        """
        Exporta las salidas en un rango de fechas a un archivo CSV
        
        Args:
            fecha_inicio: Fecha de inicio en formato 'YYYY-MM-DD'
            fecha_fin: Fecha de fin en formato 'YYYY-MM-DD'
            
        Returns:
            Ruta al archivo generado o None si hay error
        """
        try:
            # Crear directorio de reportes si no existe
            reportes_dir = Path.home() / "Reportes_Caja"
            os.makedirs(reportes_dir, exist_ok=True)
            
            # Nombre del archivo
            nombre_archivo = f"Salidas_{fecha_inicio}_{fecha_fin}.csv"
            ruta_archivo = reportes_dir / nombre_archivo
            
            # Exportar
            exito = self.salidas_service.exportar_salidas_a_csv(
                fecha_inicio, fecha_fin, str(ruta_archivo)
            )
            
            if exito:
                return str(ruta_archivo)
            return None
            
        except Exception as e:
            print(f"Error al exportar salidas: {e}")
            return None
    
    def mostrar_dialogo_salida_rapida(self):
        """
        Muestra un diálogo para registrar una salida rápida
        """
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        
        # Crear diálogo
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Salida Rápida")
        dialogo.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Mostrar saldo disponible
        saldo = self.salidas_service.calcular_saldo_disponible()
        saldo_label = QLabel(f"Saldo disponible:\n"
                             f"USD: {saldo['usd']:.2f}\n"
                             f"EUR: {saldo['eur']:.2f}\n"
                             f"CUP: {saldo['cup']:.2f}\n"
                             f"Transferencia: {saldo['transferencia']:.2f}")
        layout.addWidget(saldo_label)
        
        # Botones de acciones comunes
        if saldo['usd'] > 0:
            btn_usd = QPushButton(f"Retirar todo USD ({saldo['usd']:.2f})")
            btn_usd.clicked.connect(lambda: self.pre_rellenar_salida("usd", saldo['usd']))
            layout.addWidget(btn_usd)
        
        if saldo['eur'] > 0:
            btn_eur = QPushButton(f"Retirar todo EUR ({saldo['eur']:.2f})")
            btn_eur.clicked.connect(lambda: self.pre_rellenar_salida("eur", saldo['eur']))
            layout.addWidget(btn_eur)
        
        if saldo['cup'] > 0:
            btn_cup = QPushButton(f"Retirar todo CUP ({saldo['cup']:.2f})")
            btn_cup.clicked.connect(lambda: self.pre_rellenar_salida("cup", saldo['cup']))
            layout.addWidget(btn_cup)
        
        if saldo['transferencia'] > 0:
            btn_transfer = QPushButton(f"Retirar toda Transferencia ({saldo['transferencia']:.2f})")
            btn_transfer.clicked.connect(lambda: self.pre_rellenar_salida("transferencia", saldo['transferencia']))
            layout.addWidget(btn_transfer)
        
        # Botón para cancelar
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dialogo.reject)
        layout.addWidget(btn_cancelar)
        
        dialogo.setLayout(layout)
        dialogo.exec()
    
    def pre_rellenar_salida(self, tipo, monto):
        """
        Pre-rellena los campos de salida con un monto específico
        
        Args:
            tipo: Tipo de moneda ('usd', 'eur', 'cup', 'transferencia')
            monto: Monto a pre-rellenar
        """
        # Limpiar todos los campos de monto primero
        self.monto_usd_input.clear()
        self.monto_eur_input.clear()
        self.monto_cup_input.clear()
        self.monto_transferencia_input.clear()
        
        # Rellenar el campo correspondiente
        if tipo == "usd":
            self.monto_usd_input.setText(f"{monto:.2f}")
        elif tipo == "eur":
            self.monto_eur_input.setText(f"{monto:.2f}")
        elif tipo == "cup":
            self.monto_cup_input.setText(f"{monto:.2f}")
        elif tipo == "transferencia":
            self.monto_transferencia_input.setText(f"{monto:.2f}")
        
        # Dar foco al campo de destinatario si está vacío
        if not self.destinatario_input.text():
            self.destinatario_input.setFocus()
        else:
            # Si el destinatario ya está rellenado, dar foco al motivo
            self.motivo_input.setFocus()