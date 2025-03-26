# -*- coding: utf-8 -*-

"""
Pestaña de cierre de día de la aplicación.
Muestra entradas y salidas, y permite contar billetes por denominación.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLabel, QLineEdit, QPushButton, QComboBox, 
                            QTableWidget, QTableWidgetItem, QGroupBox,
                            QMessageBox, QHeaderView, QTextEdit, QDateEdit,
                            QScrollArea, QSizePolicy, QGridLayout, QSpinBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, date, timedelta

from app.services.facturacion import FacturacionService
from app.services.salidas_service import SalidasService
from app.services.cierre_dia import CierreDiaService
from app.services.exchange_rate import ExchangeRateService

class CierreDiaTab(QWidget):
    """Pestaña para visualizar y realizar cierres de día"""
    
    def __init__(self, exchange_service):
        super().__init__()
        
        # Inicializar servicios
        self.exchange_service = exchange_service
        self.facturacion_service = FacturacionService()
        self.salidas_service = SalidasService()
        self.cierre_service = CierreDiaService()
        
        # Denominaciones de billetes
        self.denominaciones_usd = [1, 2, 5, 10, 20, 50, 100]
        self.denominaciones_eur = [5, 10, 20, 50, 100, 200, 500]
        self.denominaciones_cup = [1, 3, 5, 10, 20, 50, 100, 200, 500, 1000]
        
        # Contadores de billetes
        self.contadores_usd = {}
        self.contadores_eur = {}
        self.contadores_cup = {}
        
        # Configurar la interfaz
        self.init_ui()
        
        # Cargar datos iniciales
        self.actualizar_resumen()
    
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
        fecha_actual = datetime.date.today().strftime("%d/%m/%Y")
        titulo_label = QLabel(f"CIERRE DE CAJA - {fecha_actual}")
        titulo_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(titulo_label)
        
        # Sección: Selección de fecha
        fecha_layout = QHBoxLayout()
        fecha_layout.addWidget(QLabel("Fecha de cierre:"))
        
        self.fecha_selector = QDateEdit()
        self.fecha_selector.setDate(QDate.currentDate())
        self.fecha_selector.setCalendarPopup(True)
        self.fecha_selector.dateChanged.connect(self.actualizar_resumen)
        
        fecha_layout.addWidget(self.fecha_selector)
        fecha_layout.addStretch()
        
        actualizar_btn = QPushButton("Actualizar")
        actualizar_btn.clicked.connect(self.actualizar_resumen)
        fecha_layout.addWidget(actualizar_btn)
        
        container_layout.addLayout(fecha_layout)
        
        # Sección: Resumen de movimientos
        resumen_group = QGroupBox("Resumen de Movimientos")
        resumen_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        resumen_layout = QGridLayout()
        
        # Encabezados
        resumen_layout.addWidget(QLabel(""), 0, 0)
        resumen_layout.addWidget(QLabel("USD"), 0, 1, Qt.AlignmentFlag.AlignCenter)
        resumen_layout.addWidget(QLabel("EUR"), 0, 2, Qt.AlignmentFlag.AlignCenter)
        resumen_layout.addWidget(QLabel("CUP"), 0, 3, Qt.AlignmentFlag.AlignCenter)
        resumen_layout.addWidget(QLabel("Transferencia"), 0, 4, Qt.AlignmentFlag.AlignCenter)
        
        # Fila 1: Entradas
        resumen_layout.addWidget(QLabel("Entradas:"), 1, 0)
        self.entradas_usd_label = QLabel("0.00")
        self.entradas_eur_label = QLabel("0.00")
        self.entradas_cup_label = QLabel("0.00")
        self.entradas_transfer_label = QLabel("0.00")
        
        resumen_layout.addWidget(self.entradas_usd_label, 1, 1, Qt.AlignmentFlag.AlignRight)
        resumen_layout.addWidget(self.entradas_eur_label, 1, 2, Qt.AlignmentFlag.AlignRight)
        resumen_layout.addWidget(self.entradas_cup_label, 1, 3, Qt.AlignmentFlag.AlignRight)
        resumen_layout.addWidget(self.entradas_transfer_label, 1, 4, Qt.AlignmentFlag.AlignRight)
        
        # Fila 2: Salidas
        resumen_layout.addWidget(QLabel("Salidas:"), 2, 0)
        self.salidas_usd_label = QLabel("0.00")
        self.salidas_eur_label = QLabel("0.00")
        self.salidas_cup_label = QLabel("0.00")
        self.salidas_transfer_label = QLabel("0.00")
        
        resumen_layout.addWidget(self.salidas_usd_label, 2, 1, Qt.AlignmentFlag.AlignRight)
        resumen_layout.addWidget(self.salidas_eur_label, 2, 2, Qt.AlignmentFlag.AlignRight)
        resumen_layout.addWidget(self.salidas_cup_label, 2, 3, Qt.AlignmentFlag.AlignRight)
        resumen_layout.addWidget(self.salidas_transfer_label, 2, 4, Qt.AlignmentFlag.AlignRight)
        
        # Fila 3: Balance
        resumen_layout.addWidget(QLabel("Balance:"), 3, 0)
        self.balance_usd_label = QLabel("0.00")
        self.balance_eur_label = QLabel("0.00")
        self.balance_cup_label = QLabel("0.00")
        self.balance_transfer_label = QLabel("0.00")
        
        for label in [self.balance_usd_label, self.balance_eur_label, self.balance_cup_label, self.balance_transfer_label]:
            label.setStyleSheet("font-weight: bold;")
        
        resumen_layout.addWidget(self.balance_usd_label, 3, 1, Qt.AlignmentFlag.AlignRight)
        resumen_layout.addWidget(self.balance_eur_label, 3, 2, Qt.AlignmentFlag.AlignRight)
        resumen_layout.addWidget(self.balance_cup_label, 3, 3, Qt.AlignmentFlag.AlignRight)
        resumen_layout.addWidget(self.balance_transfer_label, 3, 4, Qt.AlignmentFlag.AlignRight)
        
        resumen_group.setLayout(resumen_layout)
        container_layout.addWidget(resumen_group)
        
        # Sección: Conteo de billetes USD
        billetes_usd_group = QGroupBox("Conteo de Billetes USD")
        billetes_usd_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        billetes_usd_layout = QGridLayout()
        
        # Encabezados
        billetes_usd_layout.addWidget(QLabel("Denominación"), 0, 0)
        billetes_usd_layout.addWidget(QLabel("Cantidad"), 0, 1)
        billetes_usd_layout.addWidget(QLabel("Total"), 0, 2)
        
        # Filas para cada denominación
        for i, denom in enumerate(self.denominaciones_usd):
            billetes_usd_layout.addWidget(QLabel(f"${denom}"), i+1, 0)
            
            # Spinner para cantidad
            spinner = QSpinBox()
            spinner.setMinimum(0)
            spinner.setMaximum(9999)
            spinner.valueChanged.connect(self.calcular_totales)
            self.contadores_usd[denom] = spinner
            billetes_usd_layout.addWidget(spinner, i+1, 1)
            
            # Label para total
            total_label = QLabel("0.00")
            billetes_usd_layout.addWidget(total_label, i+1, 2, Qt.AlignmentFlag.AlignRight)
            spinner.setProperty("total_label", total_label)
            spinner.setProperty("denominacion", denom)
            spinner.setProperty("moneda", "usd")
        
        # Total USD
        billetes_usd_layout.addWidget(QLabel("Total USD:"), len(self.denominaciones_usd)+1, 0, 1, 2, Qt.AlignmentFlag.AlignRight)
        self.total_usd_label = QLabel("0.00")
        self.total_usd_label.setStyleSheet("font-weight: bold; color: blue;")
        billetes_usd_layout.addWidget(self.total_usd_label, len(self.denominaciones_usd)+1, 2, Qt.AlignmentFlag.AlignRight)
        
        billetes_usd_group.setLayout(billetes_usd_layout)
        container_layout.addWidget(billetes_usd_group)
        
        # Sección: Conteo de billetes EUR
        billetes_eur_group = QGroupBox("Conteo de Billetes EUR")
        billetes_eur_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        billetes_eur_layout = QGridLayout()
        
        # Encabezados
        billetes_eur_layout.addWidget(QLabel("Denominación"), 0, 0)
        billetes_eur_layout.addWidget(QLabel("Cantidad"), 0, 1)
        billetes_eur_layout.addWidget(QLabel("Total"), 0, 2)
        
        # Filas para cada denominación
        for i, denom in enumerate(self.denominaciones_eur):
            billetes_eur_layout.addWidget(QLabel(f"{denom}€"), i+1, 0)
            
            # Spinner para cantidad
            spinner = QSpinBox()
            spinner.setMinimum(0)
            spinner.setMaximum(9999)
            spinner.valueChanged.connect(self.calcular_totales)
            self.contadores_eur[denom] = spinner
            billetes_eur_layout.addWidget(spinner, i+1, 1)
            
            # Label para total
            total_label = QLabel("0.00")
            billetes_eur_layout.addWidget(total_label, i+1, 2, Qt.AlignmentFlag.AlignRight)
            spinner.setProperty("total_label", total_label)
            spinner.setProperty("denominacion", denom)
            spinner.setProperty("moneda", "eur")
        
        # Total EUR
        billetes_eur_layout.addWidget(QLabel("Total EUR:"), len(self.denominaciones_eur)+1, 0, 1, 2, Qt.AlignmentFlag.AlignRight)
        self.total_eur_label = QLabel("0.00")
        self.total_eur_label.setStyleSheet("font-weight: bold; color: blue;")
        billetes_eur_layout.addWidget(self.total_eur_label, len(self.denominaciones_eur)+1, 2, Qt.AlignmentFlag.AlignRight)
        
        billetes_eur_group.setLayout(billetes_eur_layout)
        container_layout.addWidget(billetes_eur_group)
        
        # Sección: Conteo de billetes CUP
        billetes_cup_group = QGroupBox("Conteo de Billetes CUP")
        billetes_cup_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        billetes_cup_layout = QGridLayout()
        
        # Encabezados
        billetes_cup_layout.addWidget(QLabel("Denominación"), 0, 0)
        billetes_cup_layout.addWidget(QLabel("Cantidad"), 0, 1)
        billetes_cup_layout.addWidget(QLabel("Total"), 0, 2)
        
        # Filas para cada denominación
        for i, denom in enumerate(self.denominaciones_cup):
            billetes_cup_layout.addWidget(QLabel(f"{denom} CUP"), i+1, 0)
            
            # Spinner para cantidad
            spinner = QSpinBox()
            spinner.setMinimum(0)
            spinner.setMaximum(9999)
            spinner.valueChanged.connect(self.calcular_totales)
            self.contadores_cup[denom] = spinner
            billetes_cup_layout.addWidget(spinner, i+1, 1)
            
            # Label para total
            total_label = QLabel("0.00")
            billetes_cup_layout.addWidget(total_label, i+1, 2, Qt.AlignmentFlag.AlignRight)
            spinner.setProperty("total_label", total_label)
            spinner.setProperty("denominacion", denom)
            spinner.setProperty("moneda", "cup")
        
        # Total CUP
        billetes_cup_layout.addWidget(QLabel("Total CUP:"), len(self.denominaciones_cup)+1, 0, 1, 2, Qt.AlignmentFlag.AlignRight)
        self.total_cup_label = QLabel("0.00")
        self.total_cup_label.setStyleSheet("font-weight: bold; color: blue;")
        billetes_cup_layout.addWidget(self.total_cup_label, len(self.denominaciones_cup)+1, 2, Qt.AlignmentFlag.AlignRight)
        
        billetes_cup_group.setLayout(billetes_cup_layout)
        container_layout.addWidget(billetes_cup_group)
        
        # Sección: Diferencias
        diferencias_group = QGroupBox("Diferencias")
        diferencias_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        diferencias_layout = QGridLayout()
        
        # Encabezados
        diferencias_layout.addWidget(QLabel("Moneda"), 0, 0)
        diferencias_layout.addWidget(QLabel("En Caja"), 0, 1, Qt.AlignmentFlag.AlignCenter)
        diferencias_layout.addWidget(QLabel("Contado"), 0, 2, Qt.AlignmentFlag.AlignCenter)
        diferencias_layout.addWidget(QLabel("Diferencia"), 0, 3, Qt.AlignmentFlag.AlignCenter)
        
        # Crear duplicados de etiquetas para usar en la sección de diferencias
        balance_usd_value = QLabel(self.balance_usd_label.text())
        balance_eur_value = QLabel(self.balance_eur_label.text())
        balance_cup_value = QLabel(self.balance_cup_label.text())
        
        total_usd_value = QLabel(self.total_usd_label.text())
        total_eur_value = QLabel(self.total_eur_label.text())
        total_cup_value = QLabel(self.total_cup_label.text())
        
        # Fila USD
        diferencias_layout.addWidget(QLabel("USD"), 1, 0)
        diferencias_layout.addWidget(balance_usd_value, 1, 1, Qt.AlignmentFlag.AlignRight)
        diferencias_layout.addWidget(total_usd_value, 1, 2, Qt.AlignmentFlag.AlignRight)
        self.diferencia_usd_label = QLabel("0.00")
        diferencias_layout.addWidget(self.diferencia_usd_label, 1, 3, Qt.AlignmentFlag.AlignRight)
        
            # Fila EUR
        diferencias_layout.addWidget(QLabel("EUR"), 2, 0)
        diferencias_layout.addWidget(balance_eur_value, 2, 1, Qt.AlignmentFlag.AlignRight)
        diferencias_layout.addWidget(total_eur_value, 2, 2, Qt.AlignmentFlag.AlignRight)
        self.diferencia_eur_label = QLabel("0.00")
        diferencias_layout.addWidget(self.diferencia_eur_label, 2, 3, Qt.AlignmentFlag.AlignRight)
        
        # Fila CUP
        diferencias_layout.addWidget(QLabel("CUP"), 3, 0)
        diferencias_layout.addWidget(balance_cup_value, 3, 1, Qt.AlignmentFlag.AlignRight)
        diferencias_layout.addWidget(total_cup_value, 3, 2, Qt.AlignmentFlag.AlignRight)
        self.diferencia_cup_label = QLabel("0.00")
        diferencias_layout.addWidget(self.diferencia_cup_label, 3, 3, Qt.AlignmentFlag.AlignRight)
        
        diferencias_group.setLayout(diferencias_layout)
        container_layout.addWidget(diferencias_group)
        
        # Botón de realizar cierre
        cierre_layout = QHBoxLayout()
        
        limpiar_btn = QPushButton("Limpiar Conteo")
        limpiar_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFA726;
                color: white;
                font-weight: bold;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #FB8C00;
            }
        """)
        limpiar_btn.clicked.connect(self.limpiar_conteo)
        cierre_layout.addWidget(limpiar_btn)
        
        # Agregar botón para sugerir conteo
        sugerir_btn = QPushButton("Sugerir Conteo")
        sugerir_btn.setStyleSheet("""
            QPushButton {
                background-color: #42A5F5;
                color: white;
                font-weight: bold;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2196F3;
            }
        """)
        sugerir_btn.clicked.connect(self.sugerir_conteo)
        cierre_layout.addWidget(sugerir_btn)
        
        cierre_layout.addStretch()
        
        realizar_cierre_btn = QPushButton("REALIZAR CIERRE DE DÍA")
        realizar_cierre_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                font-weight: bold;
                padding: 10px;
                font-size: 16px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
        """)
        realizar_cierre_btn.clicked.connect(self.realizar_cierre)
        cierre_layout.addWidget(realizar_cierre_btn)
        
        container_layout.addLayout(cierre_layout)
        
        # Configurar el scroll area
        scroll_area.setWidget(container_widget)
        main_layout.addWidget(scroll_area)
    
    def actualizar_resumen(self):
        """Actualiza el resumen de entradas y salidas del día"""
        fecha = self.fecha_selector.date().toString("yyyy-MM-dd")
        
        # Obtener facturas sin cerrar para esta fecha
        self.db_facturas = self.facturacion_service.obtener_facturas_por_fecha(fecha, fecha)
        
        # Calcular totales de entradas
        total_entradas_usd = 0
        total_entradas_eur = 0
        total_entradas_cup = 0
        total_entradas_transfer = 0
        
        for factura in self.db_facturas:
            # Usar getattr para manejar casos donde el atributo podría no existir
            # y proporcionar un valor predeterminado de 0
            pago_usd = getattr(factura, 'pago_usd', 0) 
            if pago_usd is None: pago_usd = 0
            
            pago_eur = getattr(factura, 'pago_eur', 0)
            if pago_eur is None: pago_eur = 0
            
            pago_cup = getattr(factura, 'pago_cup', 0)
            if pago_cup is None: pago_cup = 0
            
            pago_transferencia = getattr(factura, 'pago_transferencia', 0)
            if pago_transferencia is None: pago_transferencia = 0
            
            total_entradas_usd += pago_usd
            total_entradas_eur += pago_eur
            total_entradas_cup += pago_cup
            total_entradas_transfer += pago_transferencia
        
        # Obtener salidas para esta fecha
        salidas = self.salidas_service.obtener_salidas_por_fecha(fecha, fecha)
        
        # Calcular totales de salidas
        total_salidas_usd = 0
        total_salidas_eur = 0
        total_salidas_cup = 0
        total_salidas_transfer = 0
        
        for salida in salidas:
            # Asegurarse de que los valores None se manejen como 0
            monto_usd = salida.get('monto_usd', 0) or 0
            monto_eur = salida.get('monto_eur', 0) or 0
            monto_cup = salida.get('monto_cup', 0) or 0
            monto_transferencia = salida.get('monto_transferencia', 0) or 0
            
            total_salidas_usd += monto_usd
            total_salidas_eur += monto_eur
            total_salidas_cup += monto_cup
            total_salidas_transfer += monto_transferencia
        
        # Calcular balances
        balance_usd = total_entradas_usd - total_salidas_usd
        balance_eur = total_entradas_eur - total_salidas_eur
        balance_cup = total_entradas_cup - total_salidas_cup
        balance_transfer = total_entradas_transfer - total_salidas_transfer
        
        # Imprimir valores para depuración
        print(f"Entradas - USD: {total_entradas_usd}, EUR: {total_entradas_eur}, CUP: {total_entradas_cup}, Transfer: {total_entradas_transfer}")
        print(f"Salidas - USD: {total_salidas_usd}, EUR: {total_salidas_eur}, CUP: {total_salidas_cup}, Transfer: {total_salidas_transfer}")
        print(f"Balance - USD: {balance_usd}, EUR: {balance_eur}, CUP: {balance_cup}, Transfer: {balance_transfer}")
        
        # Actualizar etiquetas de entradas
        self.entradas_usd_label.setText(f"{total_entradas_usd:.2f}")
        self.entradas_eur_label.setText(f"{total_entradas_eur:.2f}")
        self.entradas_cup_label.setText(f"{total_entradas_cup:.2f}")
        self.entradas_transfer_label.setText(f"{total_entradas_transfer:.2f}")
        
        # Actualizar etiquetas de salidas
        self.salidas_usd_label.setText(f"{total_salidas_usd:.2f}")
        self.salidas_eur_label.setText(f"{total_salidas_eur:.2f}")
        self.salidas_cup_label.setText(f"{total_salidas_cup:.2f}")
        self.salidas_transfer_label.setText(f"{total_salidas_transfer:.2f}")
        
        # Actualizar etiquetas de balance
        self.balance_usd_label.setText(f"{balance_usd:.2f}")
        self.balance_eur_label.setText(f"{balance_eur:.2f}")
        self.balance_cup_label.setText(f"{balance_cup:.2f}")
        self.balance_transfer_label.setText(f"{balance_transfer:.2f}")
        
        # Colorear balances según valor
        for label, valor in [
            (self.balance_usd_label, balance_usd),
            (self.balance_eur_label, balance_eur),
            (self.balance_cup_label, balance_cup),
            (self.balance_transfer_label, balance_transfer)
        ]:
            if valor < 0:
                label.setStyleSheet("font-weight: bold; color: red;")
            elif valor > 0:
                label.setStyleSheet("font-weight: bold; color: green;")
            else:
                label.setStyleSheet("font-weight: bold; color: black;")
        
        # Calcular diferencias
        self.calcular_totales()
    
    def calcular_totales(self):
        """Calcula los totales de billetes contados y las diferencias"""
        # Calcular total USD
        total_usd = 0
        for denom, spinner in self.contadores_usd.items():
            cantidad = spinner.value()
            total_denom = denom * cantidad
            total_usd += total_denom
            
            # Actualizar etiqueta de total por denominación
            total_label = spinner.property("total_label")
            total_label.setText(f"{total_denom:.2f}")
        
        # Actualizar etiqueta de total USD
        self.total_usd_label.setText(f"{total_usd:.2f}")
        
        # Calcular total EUR
        total_eur = 0
        for denom, spinner in self.contadores_eur.items():
            cantidad = spinner.value()
            total_denom = denom * cantidad
            total_eur += total_denom
            
            # Actualizar etiqueta de total por denominación
            total_label = spinner.property("total_label")
            total_label.setText(f"{total_denom:.2f}")
        
        # Actualizar etiqueta de total EUR
        self.total_eur_label.setText(f"{total_eur:.2f}")
        
        # Calcular total CUP
        total_cup = 0
        for denom, spinner in self.contadores_cup.items():
            cantidad = spinner.value()
            total_denom = denom * cantidad
            total_cup += total_denom
            
            # Actualizar etiqueta de total por denominación
            total_label = spinner.property("total_label")
            total_label.setText(f"{total_denom:.2f}")
        
        # Actualizar etiqueta de total CUP
        self.total_cup_label.setText(f"{total_cup:.2f}")
        
        # Calcular diferencias
        try:
            balance_usd = float(self.balance_usd_label.text())
            diferencia_usd = total_usd - balance_usd
            self.diferencia_usd_label.setText(f"{diferencia_usd:.2f}")
            
            if diferencia_usd < 0:
                self.diferencia_usd_label.setStyleSheet("color: red; font-weight: bold;")
            elif diferencia_usd > 0:
                self.diferencia_usd_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.diferencia_usd_label.setStyleSheet("color: black; font-weight: bold;")
        except ValueError:
            self.diferencia_usd_label.setText("Error")
        
        try:
            balance_eur = float(self.balance_eur_label.text())
            diferencia_eur = total_eur - balance_eur
            self.diferencia_eur_label.setText(f"{diferencia_eur:.2f}")
            
            if diferencia_eur < 0:
                self.diferencia_eur_label.setStyleSheet("color: red; font-weight: bold;")
            elif diferencia_eur > 0:
                self.diferencia_eur_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.diferencia_eur_label.setStyleSheet("color: black; font-weight: bold;")
        except ValueError:
            self.diferencia_eur_label.setText("Error")
        
        try:
            balance_cup = float(self.balance_cup_label.text())
            diferencia_cup = total_cup - balance_cup
            self.diferencia_cup_label.setText(f"{diferencia_cup:.2f}")
            
            if diferencia_cup < 0:
                self.diferencia_cup_label.setStyleSheet("color: red; font-weight: bold;")
            elif diferencia_cup > 0:
                self.diferencia_cup_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.diferencia_cup_label.setStyleSheet("color: black; font-weight: bold;")
        except ValueError:
            self.diferencia_cup_label.setText("Error")
        
        # Actualizar los valores en la sección de diferencias
        # Buscar el GroupBox de diferencias
        for widget in self.findChildren(QGroupBox):
            if widget.title() == "Diferencias":
                # Actualizar etiquetas de balance (En Caja)
                balance_widgets = []
                for i in range(1, 4):  # Filas 1, 2, 3 (USD, EUR, CUP)
                    item = widget.layout().itemAtPosition(i, 1)
                    if item and item.widget():
                        balance_widgets.append(item.widget())
                
                if balance_widgets and len(balance_widgets) >= 3:
                    balance_widgets[0].setText(self.balance_usd_label.text())
                    balance_widgets[1].setText(self.balance_eur_label.text())
                    balance_widgets[2].setText(self.balance_cup_label.text())
                
                # Actualizar etiquetas de total contado
                total_widgets = []
                for i in range(1, 4):  # Filas 1, 2, 3 (USD, EUR, CUP)
                    item = widget.layout().itemAtPosition(i, 2)
                    if item and item.widget():
                        total_widgets.append(item.widget())
                
                if total_widgets and len(total_widgets) >= 3:
                    total_widgets[0].setText(self.total_usd_label.text())
                    total_widgets[1].setText(self.total_eur_label.text())
                    total_widgets[2].setText(self.total_cup_label.text())
                
                break
    
    def limpiar_conteo(self):
        """Limpia todos los contadores de billetes"""
        for spinner in list(self.contadores_usd.values()) + list(self.contadores_eur.values()) + list(self.contadores_cup.values()):
            spinner.setValue(0)
    
    def realizar_cierre(self):
        """Realiza el cierre del día con los montos contados"""
        # Primero verificar que todas las diferencias sean cero
        try:
            diferencia_usd = float(self.diferencia_usd_label.text())
            diferencia_eur = float(self.diferencia_eur_label.text())
            diferencia_cup = float(self.diferencia_cup_label.text())
            
            # Verificar si hay alguna diferencia (usando un pequeño margen para manejar errores de redondeo)
            epsilon = 0.01  # margen de error aceptable
            if abs(diferencia_usd) > epsilon or abs(diferencia_eur) > epsilon or abs(diferencia_cup) > epsilon:
                QMessageBox.warning(
                    self,
                    "Diferencias en el conteo",
                    "No se puede realizar el cierre con diferencias en el conteo.\n\n"
                    f"Diferencia USD: {diferencia_usd:.2f}\n"
                    f"Diferencia EUR: {diferencia_eur:.2f}\n"
                    f"Diferencia CUP: {diferencia_cup:.2f}\n\n"
                    "Por favor, ajuste el conteo de billetes para que coincida con el balance esperado."
                )
                return
        except ValueError:
            QMessageBox.warning(
                self,
                "Error en los valores",
                "Ha ocurrido un error al calcular las diferencias. Por favor actualice los valores e intente nuevamente."
            )
            return
            
        fecha_str = self.fecha_selector.date().toString("yyyy-MM-dd")
        
        # Verificar si es la fecha de hoy
        if fecha_str != datetime.date.today().isoformat():
            respuesta = QMessageBox.question(
                self,
                "Confirmar cierre para otra fecha",
                f"Está realizando un cierre para el día {fecha_str}, que no es el día actual.\n\n"
                "¿Está seguro de continuar con esta operación?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if respuesta == QMessageBox.StandardButton.No:
                return
        
        # Obtener montos contados
        efectivo_usd = float(self.total_usd_label.text())
        efectivo_eur = float(self.total_eur_label.text())
        efectivo_cup = float(self.total_cup_label.text())
        
        # Confirmar cierre
        mensaje = (
            f"Se realizará el cierre del día {fecha_str} con los siguientes montos:\n\n"
            f"USD en caja según movimientos: {self.balance_usd_label.text()}\n"
            f"USD contado: {efectivo_usd:.2f}\n"
            f"Diferencia USD: {self.diferencia_usd_label.text()}\n\n"
            f"EUR en caja según movimientos: {self.balance_eur_label.text()}\n"
            f"EUR contado: {efectivo_eur:.2f}\n"
            f"Diferencia EUR: {self.diferencia_eur_label.text()}\n\n"
            f"CUP en caja según movimientos: {self.balance_cup_label.text()}\n"
            f"CUP contado: {efectivo_cup:.2f}\n"
            f"Diferencia CUP: {self.diferencia_cup_label.text()}\n\n"
            f"¿Está seguro de realizar el cierre?"
        )
        
        respuesta = QMessageBox.question(
            self,
            "Confirmar cierre de día",
            mensaje,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.No:
            return
        
        # Realizar cierre
        resultado = self.cierre_service.realizar_cierre_dia(
            efectivo_contado_usd=efectivo_usd,
            efectivo_contado_eur=efectivo_eur,
            efectivo_contado_cup=efectivo_cup
        )
        
        if resultado['success']:
            # Mostrar mensaje de éxito
            mensaje_exito = (
                f"Cierre del día realizado con éxito.\n\n"
                f"Resumen:\n"
                f"- Facturas procesadas: {resultado.get('num_facturas', 0)}\n"
                f"- USD: {resultado.get('total_usd', 0):.2f}\n"
                f"- EUR: {resultado.get('total_eur', 0):.2f}\n"
                f"- CUP: {resultado.get('total_cup', 0):.2f}\n"
                f"- Transferencias: {resultado.get('total_transferencia', 0):.2f}\n\n"
                f"El cierre ha sido registrado en el sistema."
            )
            
            QMessageBox.information(self, "Cierre exitoso", mensaje_exito)
            
            # Actualizar la interfaz
            self.fecha_selector.setDate(self.fecha_selector.date())  # Forzar actualización
            self.limpiar_conteo()
        else:
            # Mostrar mensaje de error
            QMessageBox.warning(
                self, 
                "Error al realizar cierre", 
                f"No se pudo realizar el cierre: {resultado.get('message', 'Error desconocido')}"
            )
    
    def sugerir_conteo(self):
        """Sugiere el conteo de billetes basado en el balance esperado"""
        try:
            # Obtener balances
            balance_usd = float(self.balance_usd_label.text())
            balance_eur = float(self.balance_eur_label.text())
            balance_cup = float(self.balance_cup_label.text())
            
            # Limpiar conteo actual
            self.limpiar_conteo()
            
            # Algoritmo para sugerir conteo de USD
            restante_usd = balance_usd
            for denom in sorted(self.denominaciones_usd, reverse=True):
                if restante_usd >= denom:
                    cantidad = int(restante_usd / denom)
                    self.contadores_usd[denom].setValue(cantidad)
                    restante_usd -= cantidad * denom
            
            # Algoritmo para sugerir conteo de EUR
            restante_eur = balance_eur
            for denom in sorted(self.denominaciones_eur, reverse=True):
                if restante_eur >= denom:
                    cantidad = int(restante_eur / denom)
                    self.contadores_eur[denom].setValue(cantidad)
                    restante_eur -= cantidad * denom
            
            # Algoritmo para sugerir conteo de CUP
            restante_cup = balance_cup
            for denom in sorted(self.denominaciones_cup, reverse=True):
                if restante_cup >= denom:
                    cantidad = int(restante_cup / denom)
                    self.contadores_cup[denom].setValue(cantidad)
                    restante_cup -= cantidad * denom
            
            # Actualizar totales
            self.calcular_totales()
            
            QMessageBox.information(
                self,
                "Sugerencia de conteo",
                "Se ha sugerido un conteo de billetes basado en el balance esperado.\n"
                "Por favor verifique y ajuste según sea necesario."
            )
        
        except ValueError:
            QMessageBox.warning(
                self,
                "Error",
                "No se pudo calcular la sugerencia de conteo debido a valores inválidos."
            )