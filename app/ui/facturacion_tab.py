# -*- coding: utf-8 -*-

"""
Pestaña de facturación de la aplicación.
Gestiona la interfaz para escaneo de códigos y registro de facturas.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, 
                             QTableWidget, QTableWidgetItem, QGroupBox,
                             QMessageBox, QInputDialog, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSlot
import datetime

from app.ui.components.scanner import ScannerWidget
from app.ui.components.invoice_table import InvoiceTableWidget
from app.services.facturacion import FacturacionService
from app.services.scanner_service import ScannerService

class FacturacionTab(QWidget):
    """Pestaña para la facturación y escaneo de códigos"""
    
    def __init__(self, exchange_service):
        super().__init__()
        
        # Inicializar servicios
        self.exchange_service = exchange_service
        self.facturacion_service = FacturacionService()
        self.scanner_service = ScannerService()
        
        # Configurar la interfaz
        self.init_ui()
        
        # Cargar datos iniciales
        self.cargar_tasa_actual()
        self.cargar_facturas_recientes()
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Título/Fecha
        fecha_actual = datetime.date.today().strftime("%d/%m/%Y")
        titulo_label = QLabel(f"FACTURACIÓN - {fecha_actual}")
        titulo_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo_label)
        
        # Sección 1: Tasa de cambio
        tasa_group = QGroupBox("Tasa de Cambio")
        tasa_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        tasa_layout = QHBoxLayout()
        
        self.tasa_label = QLabel("USD 1 = CUP --")
        self.tasa_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        tasa_actualizar_btn = QPushButton("Actualizar Tasa")
        tasa_actualizar_btn.clicked.connect(self.mostrar_dialogo_tasa)
        
        tasa_layout.addWidget(QLabel("Tasa actual:"))
        tasa_layout.addWidget(self.tasa_label)
        tasa_layout.addStretch()
        tasa_layout.addWidget(tasa_actualizar_btn)
        
        tasa_group.setLayout(tasa_layout)
        main_layout.addWidget(tasa_group)
                # Sección 2: Datos de la factura
        factura_group = QGroupBox("Datos de Factura")
        factura_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        factura_layout = QFormLayout()
        
        # ID de Orden con botón de escaneo
        orden_layout = QHBoxLayout()
        self.orden_id_input = QLineEdit()
        self.orden_id_input.setPlaceholderText("Escanee o ingrese ID de orden")
        self.orden_id_input.setMinimumWidth(200)
        
        escanear_btn = QPushButton("Escanear")
        escanear_btn.clicked.connect(self.iniciar_escaneo)
        
        orden_layout.addWidget(self.orden_id_input)
        orden_layout.addWidget(escanear_btn)
        
        factura_layout.addRow("ID de Orden:", orden_layout)
        
        # Monto y moneda
        monto_layout = QHBoxLayout()
        self.monto_input = QLineEdit()
        self.monto_input.setPlaceholderText("Ingrese el monto")
        self.monto_input.setMinimumWidth(120)
        self.monto_input.textChanged.connect(self.actualizar_monto_equivalente)
        
        self.moneda_combo = QComboBox()
        self.moneda_combo.addItems(["USD", "CUP"])
        self.moneda_combo.currentTextChanged.connect(self.actualizar_monto_equivalente)
        
        monto_layout.addWidget(self.monto_input)
        monto_layout.addWidget(QLabel("en"))
        monto_layout.addWidget(self.moneda_combo)
        
        factura_layout.addRow("Monto:", monto_layout)
        
        # Equivalente
        self.equivalente_label = QLabel("Equivalente: --")
        self.equivalente_label.setStyleSheet("font-style: italic;")
        factura_layout.addRow("", self.equivalente_label)
        
        factura_group.setLayout(factura_layout)
        main_layout.addWidget(factura_group)

            # Sección 3: Forma de Pago
        pago_group = QGroupBox("Forma de Pago")
        pago_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        pago_layout = QFormLayout()
        
        self.pago_usd_input = QLineEdit()
        self.pago_usd_input.setPlaceholderText("0.00")
        self.pago_usd_input.textChanged.connect(self.verificar_balance)
        pago_layout.addRow("Recibido en USD:", self.pago_usd_input)
        
        self.pago_cup_input = QLineEdit()
        self.pago_cup_input.setPlaceholderText("0.00")
        self.pago_cup_input.textChanged.connect(self.verificar_balance)
        pago_layout.addRow("Recibido en CUP:", self.pago_cup_input)
        
        self.balance_label = QLabel("Balance: --")
        self.balance_label.setStyleSheet("font-weight: bold;")
        pago_layout.addRow("", self.balance_label)
        
        pago_group.setLayout(pago_layout)
        main_layout.addWidget(pago_group)
        
        # Botón de registrar
        registrar_btn = QPushButton("REGISTRAR FACTURA")
        registrar_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        registrar_btn.clicked.connect(self.registrar_factura)
        main_layout.addWidget(registrar_btn)

                # Tabla de facturas recientes
        facturas_group = QGroupBox("Facturas Recientes")
        facturas_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        facturas_layout = QVBoxLayout()
        
        self.facturas_table = QTableWidget()
        self.facturas_table.setColumnCount(7)
        self.facturas_table.setHorizontalHeaderLabels([
            "ID Orden", "Monto", "Moneda", "Pago USD", "Pago CUP", 
            "Equivalente (USD)", "Fecha"
        ])
        self.facturas_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.facturas_table.setAlternatingRowColors(True)
        
        facturas_layout.addWidget(self.facturas_table)
        facturas_group.setLayout(facturas_layout)
        main_layout.addWidget(facturas_group)
        
        # Dar foco al primer campo
        self.orden_id_input.setFocus()

    def cargar_tasa_actual(self):
        """Carga y muestra la tasa de cambio actual"""
        tasa = self.exchange_service.obtener_tasa_actual()
        self.tasa_label.setText(f"USD 1 = CUP {tasa:.2f}")
    
    def verificar_balance(self):
        """Verifica si el balance de pago es correcto"""
        try:
            if not self.monto_input.text():
                self.balance_label.setText("Balance: --")
                return
                
            monto = float(self.monto_input.text())
            moneda = self.moneda_combo.currentText()
            tasa = self.exchange_service.obtener_tasa_actual()
            
            pago_usd = float(self.pago_usd_input.text() or 0)
            pago_cup = float(self.pago_cup_input.text() or 0)
            
            # Calcular total en la moneda de la factura
            if moneda == "USD":
                # Convertir CUP a USD
                pago_cup_en_usd = pago_cup / tasa
                total_recibido = pago_usd + pago_cup_en_usd
                balance = total_recibido - monto
                moneda_balance = "USD"
            else:  # CUP
                # Convertir USD a CUP
                pago_usd_en_cup = pago_usd * tasa
                total_recibido = pago_cup + pago_usd_en_cup
                balance = total_recibido - monto
                moneda_balance = "CUP"
            
            # Mostrar balance
            if abs(balance) < 0.01:  # Si está cerca de cero (por redondeo)
                self.balance_label.setText("Balance: Correcto")
                self.balance_label.setStyleSheet("color: green;")
            elif balance > 0:
                self.balance_label.setText(f"Balance: Cambio de {balance:.2f} {moneda_balance}")
                self.balance_label.setStyleSheet("color: blue;")
            else:
                self.balance_label.setText(f"Balance: Faltan {-balance:.2f} {moneda_balance}")
                self.balance_label.setStyleSheet("color: red;")
                
        except ValueError:
            self.balance_label.setText("Balance: Error en valores")
            self.balance_label.setStyleSheet("color: red;")

    def mostrar_dialogo_tasa(self):
        """Muestra un diálogo para actualizar la tasa de cambio"""
        tasa_actual = self.exchange_service.obtener_tasa_actual()
        nueva_tasa, ok = QInputDialog.getDouble(
            self, 
            "Actualizar Tasa de Cambio", 
            "Ingrese la nueva tasa (USD 1 = CUP X):",
            tasa_actual,
            0.01, 1000.00, 2
        )
        
        if ok:
            self.exchange_service.actualizar_tasa(nueva_tasa)
            self.cargar_tasa_actual()
            self.actualizar_monto_equivalente()
            QMessageBox.information(self, "Tasa Actualizada", 
                                f"La tasa de cambio se ha actualizado a: USD 1 = CUP {nueva_tasa:.2f}")
    
    def iniciar_escaneo(self):
        """Inicia el proceso de escaneo de código de barras"""
        codigo = self.scanner_service.escanear()
        if codigo:
            self.orden_id_input.setText(codigo)
            QMessageBox.information(self, "Escaneo Exitoso", 
                                f"Código escaneado: {codigo}")

    def actualizar_monto_equivalente(self):
        """Actualiza el monto equivalente basado en la moneda seleccionada y la tasa de cambio"""
        try:
            if not self.monto_input.text():
                self.equivalente_label.setText("Equivalente: --")
                return
                
            monto = float(self.monto_input.text())
            moneda = self.moneda_combo.currentText()
            tasa = self.exchange_service.obtener_tasa_actual()
            
            if moneda == "USD":
                equivalente = monto * tasa
                self.equivalente_label.setText(f"Equivalente: {equivalente:.2f} CUP")
            else:  # CUP
                equivalente = monto / tasa
                self.equivalente_label.setText(f"Equivalente: {equivalente:.2f} USD")
                
        except ValueError:
            self.equivalente_label.setText("Equivalente: (valor inválido)")
    
    def registrar_factura(self):
        """Registra una nueva factura en el sistema"""
        # Validar campos
        if not self.orden_id_input.text():
            QMessageBox.warning(self, "Error", "Debe ingresar el ID de orden")
            return
            
        try:
            if not self.monto_input.text():
                QMessageBox.warning(self, "Error", "Debe ingresar el monto")
                return
                
            monto = float(self.monto_input.text())
            if monto <= 0:
                QMessageBox.warning(self, "Error", "El monto debe ser mayor que cero")
                return
                
            # Obtener valores
            orden_id = self.orden_id_input.text()
            moneda = self.moneda_combo.currentText()
            pago_usd = float(self.pago_usd_input.text() or 0)
            pago_cup = float(self.pago_cup_input.text() or 0)
            tasa = self.exchange_service.obtener_tasa_actual()
            
            # Verificar que los pagos sean suficientes
            if moneda == "USD":
                pago_cup_en_usd = pago_cup / tasa
                total_recibido = pago_usd + pago_cup_en_usd
            else:  # CUP
                pago_usd_en_cup = pago_usd * tasa
                total_recibido = pago_cup + pago_usd_en_cup
            
            if total_recibido < monto - 0.01:  # Margen para redondeo
                QMessageBox.warning(self, "Error", "El pago recibido es insuficiente")
                return
            
            # Usar el servicio de facturación para registrar la factura
            resultado = self.facturacion_service.registrar_factura(
                orden_id, monto, moneda, pago_usd, pago_cup
            )
            
            if resultado:
                # Limpiar campos
                self.orden_id_input.clear()
                self.monto_input.clear()
                self.pago_usd_input.clear()
                self.pago_cup_input.clear()
                self.equivalente_label.setText("Equivalente: --")
                self.balance_label.setText("Balance: --")
                self.balance_label.setStyleSheet("")
                
                # Actualizar tabla de facturas recientes
                self.cargar_facturas_recientes()
                
                # Mensaje de éxito con información sobre cambio si corresponde
                mensaje = "Factura registrada correctamente"
                if total_recibido > monto + 0.01:  # Hay cambio a devolver
                    cambio = total_recibido - monto
                    if moneda == "USD":
                        mensaje += f"\n\nDar cambio: ${cambio:.2f} USD"
                    else:
                        mensaje += f"\n\nDar cambio: ${cambio:.2f} CUP"
                    
                QMessageBox.information(self, "Éxito", mensaje)
            else:
                QMessageBox.warning(self, "Error", "No se pudo registrar la factura")
                
        except ValueError:
            QMessageBox.warning(self, "Error", "Los valores ingresados no son válidos")
    
    def cargar_facturas_recientes(self):
        """Carga las facturas recientes en la tabla"""
        # Usar el servicio de facturación para obtener los datos
        facturas = self.facturacion_service.obtener_facturas_recientes(10)
        
        # Limpiar tabla
        self.facturas_table.setRowCount(0)
        
        # Llenar tabla con datos
        for i, factura in enumerate(facturas):
            self.facturas_table.insertRow(i)
            
            # Crear items para cada columna
            orden_id_item = QTableWidgetItem(factura.orden_id)
            monto_item = QTableWidgetItem(f"{factura.monto:.2f}")
            moneda_item = QTableWidgetItem(factura.moneda)
            
            # Para los pagos en USD y CUP, necesitamos verificar si esos atributos existen
            pago_usd = getattr(factura, 'pago_usd', 0)
            pago_cup = getattr(factura, 'pago_cup', 0)
            
            pago_usd_item = QTableWidgetItem(f"{pago_usd:.2f}")
            pago_cup_item = QTableWidgetItem(f"{pago_cup:.2f}")
            equivalente_item = QTableWidgetItem(f"{factura.monto_equivalente:.2f}")
            fecha_item = QTableWidgetItem(factura.fecha.strftime("%Y-%m-%d %H:%M"))
            
            # Añadir items a la tabla
            self.facturas_table.setItem(i, 0, orden_id_item)
            self.facturas_table.setItem(i, 1, monto_item)
            self.facturas_table.setItem(i, 2, moneda_item)
            self.facturas_table.setItem(i, 3, pago_usd_item)
            self.facturas_table.setItem(i, 4, pago_cup_item)
            self.facturas_table.setItem(i, 5, equivalente_item)
            self.facturas_table.setItem(i, 6, fecha_item)