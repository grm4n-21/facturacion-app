# -*- coding: utf-8 -*-

"""
Pestaña de facturación de la aplicación.
Gestiona la interfaz para escaneo de códigos y registro de facturas.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLabel, QLineEdit, QPushButton, QComboBox, 
                             QTableWidget, QTableWidgetItem, QGroupBox,
                             QMessageBox, QInputDialog, QHeaderView, QCheckBox,
                             QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSlot, Qt
from datetime import datetime, date, timedelta

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

        titulo_label = QLabel(f"FACTURACIÓN - {fecha_actual}")
        titulo_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(titulo_label)
        
        # Sección 1: Tasas de Cambio
        tasa_group = QGroupBox("Tasas de Cambio")
        tasa_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        tasa_layout = QVBoxLayout()
        
        # Tasa USD
        tasa_usd_layout = QHBoxLayout()
        self.tasa_usd_label = QLabel("USD 1 = CUP --")
        self.tasa_usd_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        tasa_usd_btn = QPushButton("Actualizar")
        tasa_usd_btn.clicked.connect(lambda: self.mostrar_dialogo_tasa("usd"))
        
        tasa_usd_layout.addWidget(QLabel("Tasa USD:"))
        tasa_usd_layout.addWidget(self.tasa_usd_label)
        tasa_usd_layout.addStretch()
        tasa_usd_layout.addWidget(tasa_usd_btn)
        
        # Tasa EUR
        tasa_eur_layout = QHBoxLayout()
        self.tasa_eur_label = QLabel("EUR 1 = CUP --")
        self.tasa_eur_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        tasa_eur_btn = QPushButton("Actualizar")
        tasa_eur_btn.clicked.connect(lambda: self.mostrar_dialogo_tasa("eur"))
        
        tasa_eur_layout.addWidget(QLabel("Tasa EUR:"))
        tasa_eur_layout.addWidget(self.tasa_eur_label)
        tasa_eur_layout.addStretch()
        tasa_eur_layout.addWidget(tasa_eur_btn)
        
        tasa_layout.addLayout(tasa_usd_layout)
        tasa_layout.addLayout(tasa_eur_layout)
        
        tasa_group.setLayout(tasa_layout)
        container_layout.addWidget(tasa_group)
        
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
        
        # Añadir campo para Mensajero (obligatorio)
        mensajero_layout = QHBoxLayout()
        self.mensajero_input = QLineEdit()
        self.mensajero_input.setPlaceholderText("Nombre del mensajero (obligatorio)")
        self.mensajero_input.setMinimumWidth(200)
        # Estilo para indicar que es campo obligatorio
        self.mensajero_input.setStyleSheet("QLineEdit { border: 1px solid #FFA500; }")
        
        mensajero_layout.addWidget(self.mensajero_input)
        factura_layout.addRow("Mensajero:", mensajero_layout)
        
        # Monto y moneda
        monto_layout = QHBoxLayout()
        self.monto_input = QLineEdit()
        self.monto_input.setPlaceholderText("Ingrese el monto")
        self.monto_input.setMinimumWidth(120)
        self.monto_input.textChanged.connect(self.actualizar_monto_equivalente)
        
        self.moneda_combo = QComboBox()
        self.moneda_combo.addItems(["USD", "EUR", "CUP"])  # Añadido EUR
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
        container_layout.addWidget(factura_group)
        
        # Sección 3: Forma de Pago en efectivo
        pago_group = QGroupBox("Forma de Pago en Efectivo")
        pago_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        pago_layout = QFormLayout()
        
        # Pagos en efectivo
        self.pago_usd_input = QLineEdit()
        self.pago_usd_input.setPlaceholderText("0.00")
        self.pago_usd_input.textChanged.connect(self.verificar_balance)
        pago_layout.addRow("Efectivo USD:", self.pago_usd_input)
        
        self.pago_eur_input = QLineEdit()  # Añadido EUR
        self.pago_eur_input.setPlaceholderText("0.00")
        self.pago_eur_input.textChanged.connect(self.verificar_balance)
        pago_layout.addRow("Efectivo EUR:", self.pago_eur_input)
        
        self.pago_cup_input = QLineEdit()
        self.pago_cup_input.setPlaceholderText("0.00")
        self.pago_cup_input.textChanged.connect(self.verificar_balance)
        pago_layout.addRow("Efectivo CUP:", self.pago_cup_input)
        
        pago_group.setLayout(pago_layout)
        container_layout.addWidget(pago_group)  # Primero agregamos el grupo de pagos en efectivo
        
        # Sección 4: Transferencia
        transferencia_group = QGroupBox("Forma de Pago por Transferencia")
        transferencia_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        transferencia_layout = QFormLayout()

        # Campo para el monto de transferencia
        from PyQt6.QtCore import QRegularExpression
        from PyQt6.QtGui import QRegularExpressionValidator, QDoubleValidator
        
        self.pago_transferencia_input = QLineEdit()
        self.pago_transferencia_input.setPlaceholderText("0.00")
        
        # Usar expresión regular para permitir números muy grandes con hasta 2 decimales
        regex = QRegularExpression("^[0-9]*\\.?[0-9]{0,2}$")
        validator = QRegularExpressionValidator(regex)
        self.pago_transferencia_input.setValidator(validator)
        
        # Desconectar señales existentes si las hay
        try:
            self.pago_transferencia_input.textChanged.disconnect()
        except TypeError:
            pass  # Ignorar si no hay conexiones
        
        # Reconectar señales correctamente
        self.pago_transferencia_input.textChanged.connect(self.verificar_balance)
        self.pago_transferencia_input.editingFinished.connect(self.formatear_numero_transferencia)
        
        # Asegurarse de que esté habilitado
        self.pago_transferencia_input.setEnabled(True)

        # Campo para el ID de transferencia
        self.transferencia_id_input = QLineEdit()
        self.transferencia_id_input.setPlaceholderText("ID o referencia de la transferencia")
        
        # Usar editingFinished en lugar de textChanged para el ID
        self.pago_transferencia_input.editingFinished.connect(self.actualizar_campo_id_transferencia)

        # Agregar campos al layout
        transferencia_layout.addRow("Monto CUP:", self.pago_transferencia_input)
        transferencia_layout.addRow("ID Referencia:", self.transferencia_id_input)

        transferencia_group.setLayout(transferencia_layout)
        container_layout.addWidget(transferencia_group)  # Luego agregamos el grupo de transferencia
        
        # Sección 5: Balance de Pago
        balance_group = QGroupBox("Balance de Pago")
        balance_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        balance_layout = QVBoxLayout()
        
        # Balance
        self.balance_label = QLabel("Balance: --")
        self.balance_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.balance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        balance_layout.addWidget(self.balance_label)
        
        balance_group.setLayout(balance_layout)
        container_layout.addWidget(balance_group)  # Finalmente agregamos el grupo de balance
        
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
        container_layout.addWidget(registrar_btn)
        
        # Tabla de facturas recientes con área de desplazamiento propia
        facturas_group = QGroupBox("Facturas Recientes")
        facturas_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        facturas_layout = QVBoxLayout()
        
        # Configurar una altura mínima para la tabla
        self.facturas_table = QTableWidget()
        self.facturas_table.setMinimumHeight(250)  # Altura mínima para la tabla
        self.facturas_table.setColumnCount(10)  # Añadimos una columna para Mensajero
        self.facturas_table.setHorizontalHeaderLabels([
            "ID Orden", "Monto", "Moneda", "USD", "EUR", "CUP", "Transfer", 
            "Equivalente", "Fecha", "Mensajero"  # Añadido "Mensajero"
        ])
        
        # Mejorar la visualización de la tabla
        self.facturas_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.facturas_table.setAlternatingRowColors(True)
        self.facturas_table.setShowGrid(True)
        self.facturas_table.setGridStyle(Qt.PenStyle.SolidLine)
        
        facturas_layout.addWidget(self.facturas_table)
        facturas_group.setLayout(facturas_layout)
        container_layout.addWidget(facturas_group)
        
        # Configurar el scroll area
        scroll_area.setWidget(container_widget)
        main_layout.addWidget(scroll_area)
        
        # Dar foco al primer campo
        self.orden_id_input.setFocus()
    def cargar_tasa_actual(self):
        """Carga y muestra las tasas de cambio actuales"""
        tasas = self.exchange_service.obtener_tasas_actuales()
        self.tasa_usd_label.setText(f"USD 1 = CUP {tasas['usd']:.2f}")
        self.tasa_eur_label.setText(f"EUR 1 = CUP {tasas['eur']:.2f}")

    def formatear_numero_transferencia(self):
        """Formatea el número de la transferencia para mejor visualización"""
        texto = self.pago_transferencia_input.text().strip()
        if not texto:
            return
            
        try:
            # Convertir a número
            valor = float(texto)
            
            # Formatear con 2 decimales
            texto_formateado = f"{valor:.2f}"
            
            # Actualizar el campo solo si ha cambiado
            if texto != texto_formateado:
                self.pago_transferencia_input.blockSignals(True)
                self.pago_transferencia_input.setText(texto_formateado)
                self.pago_transferencia_input.blockSignals(False)
        except ValueError:
            pass  # Ignorar errores de conversión
    
    def habilitar_transferencia(self, state):
        """Habilita o deshabilita los campos de transferencia según el estado del checkbox"""
        is_checked = state == Qt.CheckState.Checked
        self.pago_transferencia_input.setEnabled(is_checked)
        self.transferencia_id_input.setEnabled(is_checked)
        
        if not is_checked:
            self.pago_transferencia_input.clear()
            self.transferencia_id_input.clear()
        else:
            self.pago_transferencia_input.setFocus()

    def verificar_balance(self):
        """Verifica si el balance de pago es correcto"""
        try:
            if not self.monto_input.text():
                self.balance_label.setText("Balance: --")
                return
                
            monto = float(self.monto_input.text())
            moneda = self.moneda_combo.currentText()
            
            # Obtener tasas de cambio
            tasas = self.exchange_service.obtener_tasas_actuales()
            tasa_usd = tasas['usd']
            tasa_eur = tasas['eur']
            
            # Obtener pagos - Usar try/except para cada conversión por seguridad
            try:
                pago_usd = float(self.pago_usd_input.text() or 0)
            except ValueError:
                pago_usd = 0
                self.pago_usd_input.setText("0")
                
            try:
                pago_eur = float(self.pago_eur_input.text() or 0)
            except ValueError:
                pago_eur = 0
                self.pago_eur_input.setText("0")
                
            try:
                pago_cup = float(self.pago_cup_input.text() or 0)
            except ValueError:
                pago_cup = 0
                self.pago_cup_input.setText("0")
            
            # Transferencia - Con manejo especial para números grandes
            try:
                pago_transferencia_texto = self.pago_transferencia_input.text().strip()
                pago_transferencia = float(pago_transferencia_texto or 0)
            except ValueError:
                pago_transferencia = 0
                self.pago_transferencia_input.setText("0")
            
            # Calcular total en la moneda de la factura
            if moneda == "USD":
                # Convertir todas las monedas a USD
                pago_eur_en_usd = pago_eur * (tasa_eur / tasa_usd)
                pago_cup_en_usd = pago_cup / tasa_usd
                pago_transferencia_en_usd = pago_transferencia / tasa_usd
                
                total_recibido = pago_usd + pago_eur_en_usd + pago_cup_en_usd + pago_transferencia_en_usd
                balance = total_recibido - monto
                moneda_balance = "USD"
                
            elif moneda == "EUR":
                # Convertir todas las monedas a EUR
                pago_usd_en_eur = pago_usd * (tasa_usd / tasa_eur)
                pago_cup_en_eur = pago_cup / tasa_eur
                pago_transferencia_en_eur = pago_transferencia / tasa_eur
                
                total_recibido = pago_eur + pago_usd_en_eur + pago_cup_en_eur + pago_transferencia_en_eur
                balance = total_recibido - monto
                moneda_balance = "EUR"
                
            else:  # CUP
                # Convertir todas las monedas a CUP
                pago_usd_en_cup = pago_usd * tasa_usd
                pago_eur_en_cup = pago_eur * tasa_eur
                
                total_recibido = pago_cup + pago_usd_en_cup + pago_eur_en_cup + pago_transferencia
                balance = total_recibido - monto
                moneda_balance = "CUP"
            
            # Mostrar balance
            if abs(balance) < 0.01:  # Si está cerca de cero (por redondeo)
                self.balance_label.setText("Balance: Correcto ✓")
                self.balance_label.setStyleSheet("color: green; font-weight: bold;")
            elif balance > 0:
                # Formatear el balance con separadores si es un número grande
                if abs(balance) >= 1000:
                    balance_formateado = f"{balance:,.2f}".replace(",", " ")
                    self.balance_label.setText(f"Balance: Cambio de {balance_formateado} {moneda_balance}")
                else:
                    self.balance_label.setText(f"Balance: Cambio de {balance:.2f} {moneda_balance}")
                self.balance_label.setStyleSheet("color: blue; font-weight: bold;")
            else:
                # Formatear el balance negativo con separadores si es un número grande
                if abs(balance) >= 1000:
                    balance_formateado = f"{abs(balance):,.2f}".replace(",", " ")
                    self.balance_label.setText(f"Balance: Faltan {balance_formateado} {moneda_balance}")
                else:
                    self.balance_label.setText(f"Balance: Faltan {abs(balance):.2f} {moneda_balance}")
                self.balance_label.setStyleSheet("color: red; font-weight: bold;")
                    
        except ValueError as e:
            print(f"Error al calcular balance: {e}")
            self.balance_label.setText("Balance: Error en valores")
            self.balance_label.setStyleSheet("color: red;")
        except Exception as e:
            print(f"Error inesperado: {e}")
            self.balance_label.setText("Balance: Error")
            self.balance_label.setStyleSheet("color: red;")

    def mostrar_dialogo_tasa(self, moneda="usd"):
        """Muestra un diálogo para actualizar la tasa de cambio"""
        tasas = self.exchange_service.obtener_tasas_actuales()
        tasa_actual = tasas[moneda.lower()]
        
        # Configurar título y mensaje según la moneda
        if moneda.lower() == "usd":
            titulo = "Actualizar Tasa USD"
            mensaje = "Ingrese la nueva tasa (USD 1 = CUP X):"
        else:
            titulo = "Actualizar Tasa EUR"
            mensaje = "Ingrese la nueva tasa (EUR 1 = CUP X):"
        
        nueva_tasa, ok = QInputDialog.getDouble(
            self, 
            titulo, 
            mensaje,
            tasa_actual,
            0.01, 1000.00, 2
        )
        
        if ok:
            self.exchange_service.actualizar_tasa(nueva_tasa, moneda)
            self.cargar_tasa_actual()
            self.actualizar_monto_equivalente()
            QMessageBox.information(self, "Tasa Actualizada", 
                                f"La tasa de cambio se ha actualizado: 1 {moneda.upper()} = {nueva_tasa:.2f} CUP")
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
            
            # Obtener tasas actuales
            tasas = self.exchange_service.obtener_tasas_actuales()
            tasa_usd = tasas['usd']
            tasa_eur = tasas['eur']
            
            if moneda == "USD":
                equivalente_cup = monto * tasa_usd
                self.equivalente_label.setText(f"Equivalente: {equivalente_cup:.2f} CUP")
            elif moneda == "EUR":
                equivalente_cup = monto * tasa_eur
                self.equivalente_label.setText(f"Equivalente: {equivalente_cup:.2f} CUP")
            else:  # CUP
                equivalente_usd = monto / tasa_usd
                equivalente_eur = monto / tasa_eur
                self.equivalente_label.setText(f"Equivalente: {equivalente_usd:.2f} USD | {equivalente_eur:.2f} EUR")
                    
        except ValueError:
            self.equivalente_label.setText("Equivalente: (valor inválido)")
    
    def registrar_factura(self):
        """Registra una nueva factura en el sistema"""
        # Validar campos
        if not self.orden_id_input.text():
            QMessageBox.warning(self, "Error", "Debe ingresar el ID de orden")
            return
        
        # Validar el campo mensajero (obligatorio)
        if not self.mensajero_input.text().strip():
            QMessageBox.warning(self, "Error", "Debe ingresar el nombre del mensajero")
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
            mensajero = self.mensajero_input.text().strip()  # Obtener el mensajero
            
            # Obtener pagos
            pago_usd = float(self.pago_usd_input.text() or 0)
            pago_eur = float(self.pago_eur_input.text() or 0)
            pago_cup = float(self.pago_cup_input.text() or 0)
            
            # Transferencia - Ya no usa checkbox
            pago_transferencia = float(self.pago_transferencia_input.text() or 0)
            transferencia_id = self.transferencia_id_input.text() if pago_transferencia > 0 else None
                
            # Validar ID de transferencia si hay monto
            if pago_transferencia > 0 and not transferencia_id:
                QMessageBox.warning(self, "Error", "Debe ingresar el ID de la transferencia")
                return
            
            # Obtener tasas de cambio
            tasas = self.exchange_service.obtener_tasas_actuales()
            tasa_usd = tasas['usd']
            tasa_eur = tasas['eur']
            
            # Verificar que los pagos sean suficientes (mismo cálculo que en verificar_balance)
            if moneda == "USD":
                pago_eur_en_usd = pago_eur * (tasa_eur / tasa_usd)
                pago_cup_en_usd = pago_cup / tasa_usd
                pago_transferencia_en_usd = pago_transferencia / tasa_usd
                
                total_recibido = pago_usd + pago_eur_en_usd + pago_cup_en_usd + pago_transferencia_en_usd
            elif moneda == "EUR":
                pago_usd_en_eur = pago_usd * (tasa_usd / tasa_eur)
                pago_cup_en_eur = pago_cup / tasa_eur
                pago_transferencia_en_eur = pago_transferencia / tasa_eur
                
                total_recibido = pago_eur + pago_usd_en_eur + pago_cup_en_eur + pago_transferencia_en_eur
            else:  # CUP
                pago_usd_en_cup = pago_usd * tasa_usd
                pago_eur_en_cup = pago_eur * tasa_eur
                
                total_recibido = pago_cup + pago_usd_en_cup + pago_eur_en_cup + pago_transferencia
            
            if total_recibido < monto - 0.01:  # Margen para redondeo
                QMessageBox.warning(self, "Error", "El pago recibido es insuficiente")
                return
            
            # Usar el servicio de facturación para registrar la factura
            resultado = self.facturacion_service.registrar_factura(
                orden_id, monto, moneda, pago_usd, pago_eur, pago_cup, 
                pago_transferencia, transferencia_id, mensajero  # Añadido mensajero como argumento
            )
            
            if resultado:
                # Limpiar campos
                self.orden_id_input.clear()
                self.monto_input.clear()
                self.mensajero_input.clear()  # Limpiar el campo mensajero
                self.pago_usd_input.clear()
                self.pago_eur_input.clear()
                self.pago_cup_input.clear()
                self.pago_transferencia_input.clear()
                self.transferencia_id_input.clear()
                # Ya no hay checkbox: self.pago_transferencia_check.setChecked(False)
                self.equivalente_label.setText("Equivalente: --")
                self.balance_label.setText("Balance: --")
                self.balance_label.setStyleSheet("")
                
                self.cargar_facturas_recientes()
                
                # Mensaje de éxito con información sobre cambio si corresponde
                mensaje = "Factura registrada correctamente"
                
                # Calcular cambio a devolver si hay sobrepago
                if total_recibido > monto + 0.01:  # Hay cambio a devolver
                    cambio = total_recibido - monto
                    mensaje += f"\n\nDar cambio: {cambio:.2f} {moneda}"
                    
                QMessageBox.information(self, "Éxito", mensaje)
            else:
                # Verificar si el error es por factura duplicada
                if self.facturacion_service.verificar_orden_id_existente(orden_id):
                    QMessageBox.warning(self, "Error", f"Ya existe una factura con el ID de orden '{orden_id}'")
                else:
                    QMessageBox.warning(self, "Error", "No se pudo registrar la factura")
                    
        except ValueError as e:
            QMessageBox.warning(self, "Error", f"Los valores ingresados no son válidos: {e}")
    
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
            
            # Para los diferentes tipos de pago
            pago_usd = getattr(factura, 'pago_usd', 0)
            pago_eur = getattr(factura, 'pago_eur', 0)
            pago_cup = getattr(factura, 'pago_cup', 0)
            pago_transferencia = getattr(factura, 'pago_transferencia', 0)
            
            pago_usd_item = QTableWidgetItem(f"{pago_usd:.2f}")
            pago_eur_item = QTableWidgetItem(f"{pago_eur:.2f}")
            pago_cup_item = QTableWidgetItem(f"{pago_cup:.2f}")
            pago_transferencia_item = QTableWidgetItem(f"{pago_transferencia:.2f}")
            
            equivalente_item = QTableWidgetItem(f"{factura.monto_equivalente:.2f}")
            fecha_item = QTableWidgetItem(factura.fecha.strftime("%Y-%m-%d %H:%M"))
            
            # Obtener el mensajero si existe el atributo, si no, mostrar "No especificado"
            mensajero = getattr(factura, 'mensajero', "No especificado")
            mensajero_item = QTableWidgetItem(mensajero)
            
            # Alinear números a la derecha
            for item in [monto_item, pago_usd_item, pago_eur_item, pago_cup_item, 
                        pago_transferencia_item, equivalente_item]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Añadir items a la tabla
            self.facturas_table.setItem(i, 0, orden_id_item)
            self.facturas_table.setItem(i, 1, monto_item)
            self.facturas_table.setItem(i, 2, moneda_item)
            self.facturas_table.setItem(i, 3, pago_usd_item)
            self.facturas_table.setItem(i, 4, pago_eur_item)
            self.facturas_table.setItem(i, 5, pago_cup_item)
            self.facturas_table.setItem(i, 6, pago_transferencia_item)
            self.facturas_table.setItem(i, 7, equivalente_item)
            self.facturas_table.setItem(i, 8, fecha_item)
            self.facturas_table.setItem(i, 9, mensajero_item)  # Añadir el mensajero

    def actualizar_campo_id_transferencia(self):
        """Habilita o deshabilita el campo de ID de transferencia según el monto"""
        try:
            monto_texto = self.pago_transferencia_input.text().strip()
            if not monto_texto:
                self.transferencia_id_input.setEnabled(False)
                self.transferencia_id_input.clear()
                return
                
            monto = float(monto_texto)
            habilitar = monto > 0
            
            # Actualizar estado del campo ID
            if self.transferencia_id_input.isEnabled() != habilitar:
                self.transferencia_id_input.setEnabled(habilitar)
                
                if not habilitar:
                    self.transferencia_id_input.clear()
                elif habilitar:
                    # Solo dar foco si se acaba de habilitar
                    self.transferencia_id_input.setFocus()
                    
        except ValueError as e:
            print(f"Error al convertir monto de transferencia: {e}")
            self.transferencia_id_input.setEnabled(False)
            self.transferencia_id_input.clear()