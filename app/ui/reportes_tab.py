# -*- coding: utf-8 -*-

"""
Pestaña de reportes de la aplicación.
Gestiona la visualización y exportación de reportes de facturación y cierres de día.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QPushButton, QDateEdit,
                            QTableWidget, QTableWidgetItem, QGroupBox,
                            QMessageBox, QFileDialog, QHeaderView, QTabWidget,
                            QComboBox, QSplitter,QCheckBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor
from datetime import datetime, date, timedelta
import csv
import os

from app.services.facturacion import FacturacionService
from app.services.cierre_dia import CierreDiaService
from app.services.salidas_service import SalidasService

class ReportesTab(QWidget):
    """Pestaña para la visualización y exportación de reportes"""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar servicios
        self.facturacion_service = FacturacionService()
        self.cierre_service = CierreDiaService()
        self.salidas_service = SalidasService()
        
        # Configurar la interfaz
        self.init_ui()
        
        # Cargar datos iniciales
        self.cargar_datos_iniciales()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Pestañas de reportes
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)  # Estilo de pestañas más compacto
        
        # Pestaña 1: Reporte de Facturas
        self.facturas_tab = QWidget()
        self.setup_facturas_tab()
        self.tabs.addTab(self.facturas_tab, "Facturas")
        
        # Pestaña 2: Salidas de Caja
        self.salidas_tab = QWidget()
        self.setup_salidas_tab()
        self.tabs.addTab(self.salidas_tab, "Salidas de Caja")
        
        # Pestaña 3: Cierres de Día
        self.cierres_tab = QWidget()
        self.setup_cierres_tab()
        self.tabs.addTab(self.cierres_tab, "Cierres de Día")
        
        # Pestaña 4: Resumen Consolidado
        self.resumen_tab = QWidget()
        self.setup_resumen_tab()
        self.tabs.addTab(self.resumen_tab, "Resumen Consolidado")
        
        # Añadir pestañas al layout principal
        main_layout.addWidget(self.tabs)
        
    def setup_facturas_tab(self):
        """Configura la pestaña de reportes de facturas"""
        layout = QVBoxLayout(self.facturas_tab)
        
        # Grupo: Filtros de reporte
        filtros_group = QGroupBox("Filtros de Reporte")
        filtros_layout = QVBoxLayout()  # Cambiado a vertical para mejor organización
        
        # Sección superior con fechas y filtros básicos
        fecha_filtros_layout = QHBoxLayout()
        
        # Fechas
        fecha_layout = QFormLayout()
        
        hoy = QDate.currentDate()
        
        self.factura_fecha_inicio = QDateEdit()
        self.factura_fecha_inicio.setDate(hoy.addDays(-30))  # Último mes por defecto
        self.factura_fecha_inicio.setCalendarPopup(True)
        fecha_layout.addRow("Desde:", self.factura_fecha_inicio)
        
        self.factura_fecha_fin = QDateEdit()
        self.factura_fecha_fin.setDate(hoy)
        self.factura_fecha_fin.setCalendarPopup(True)
        fecha_layout.addRow("Hasta:", self.factura_fecha_fin)
        
        fecha_filtros_layout.addLayout(fecha_layout)
        
        # Filtros adicionales
        filtros_extra_layout = QFormLayout()
        
        self.filtro_moneda = QComboBox()
        self.filtro_moneda.addItems(["Todas", "USD", "EUR", "CUP"])
        filtros_extra_layout.addRow("Moneda:", self.filtro_moneda)
        
        self.filtro_min_monto = QLineEdit()
        self.filtro_min_monto.setPlaceholderText("Monto mínimo")
        filtros_extra_layout.addRow("Monto mín:", self.filtro_min_monto)
        
        fecha_filtros_layout.addLayout(filtros_extra_layout)
        
        # Botones
        botones_layout = QVBoxLayout()
        
        self.generar_facturas_btn = QPushButton("Generar Reporte")
        self.generar_facturas_btn.clicked.connect(self.generar_reporte_facturas)
        botones_layout.addWidget(self.generar_facturas_btn)
        
        self.exportar_facturas_btn = QPushButton("Exportar a CSV")
        self.exportar_facturas_btn.clicked.connect(self.exportar_facturas_csv)
        botones_layout.addWidget(self.exportar_facturas_btn)
        
        fecha_filtros_layout.addLayout(botones_layout)
        
        # Añadir la sección superior al layout de filtros
        filtros_layout.addLayout(fecha_filtros_layout)
        
        # Sección de filtros de tipo de pago
        tipo_pago_layout = QHBoxLayout()
        
        # Crear checkboxes para filtrar por tipo de pago
        self.filtro_incluir_usd = QCheckBox("Incluir pagos en USD")
        self.filtro_incluir_eur = QCheckBox("Incluir pagos en EUR")
        self.filtro_incluir_cup = QCheckBox("Incluir pagos en CUP")
        self.filtro_incluir_transferencia = QCheckBox("Incluir pagos por transferencia")
        
        # Por defecto todos marcados
        self.filtro_incluir_usd.setChecked(True)
        self.filtro_incluir_eur.setChecked(True)
        self.filtro_incluir_cup.setChecked(True)
        self.filtro_incluir_transferencia.setChecked(True)
        
        tipo_pago_layout.addWidget(self.filtro_incluir_usd)
        tipo_pago_layout.addWidget(self.filtro_incluir_eur)
        tipo_pago_layout.addWidget(self.filtro_incluir_cup)
        tipo_pago_layout.addWidget(self.filtro_incluir_transferencia)
            
            # Añadir la sección de filtros de tipo de pago al layout de filtros
        filtros_layout.addLayout(tipo_pago_layout)
            
            # Establecer el layout para el grupo de filtros
        filtros_group.setLayout(filtros_layout)
            
            # Tabla de reporte
        self.facturas_table = QTableWidget()
        self.facturas_table.setColumnCount(9)
        self.facturas_table.setHorizontalHeaderLabels([
                "ID Orden", "Monto", "Moneda", "USD", "EUR", "CUP", "Transfer", 
                "Equivalente", "Fecha"
            ])
        self.facturas_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            
            # Panel de totales
        totales_group = QGroupBox("Resumen")
        totales_layout = QHBoxLayout()
            
        self.total_facturas = QLabel("Facturas: 0")
        self.total_usd = QLabel("Total USD: $0.00")
        self.total_eur = QLabel("Total EUR: €0.00")
        self.total_cup = QLabel("Total CUP: $0.00")
        self.total_transferencia = QLabel("Total Transferencia: $0.00")
            
        totales_layout.addWidget(self.total_facturas)
        totales_layout.addWidget(self.total_usd)
        totales_layout.addWidget(self.total_eur)
        totales_layout.addWidget(self.total_cup)
        totales_layout.addWidget(self.total_transferencia)
            
        totales_group.setLayout(totales_layout)
            
            # Añadir todo al layout principal
        layout.addWidget(filtros_group)
        layout.addWidget(self.facturas_table)
        layout.addWidget(totales_group)
    
    def setup_cierres_tab(self):
        """Configura la pestaña de cierres de día"""
        layout = QVBoxLayout(self.cierres_tab)
        
        # Filtros para cierres
        filtros_group = QGroupBox("Filtros")
        filtros_layout = QHBoxLayout()
        
        # Periodo
        periodo_layout = QFormLayout()
        
        self.cierre_periodo_combo = QComboBox()
        self.cierre_periodo_combo.addItems(["Último mes", "Últimos 3 meses", "Último año", "Todo"])
        self.cierre_periodo_combo.currentIndexChanged.connect(self.filtrar_cierres)
        
        periodo_layout.addRow("Periodo:", self.cierre_periodo_combo)
        filtros_layout.addLayout(periodo_layout)
        
        # Fechas específicas
        fechas_layout = QFormLayout()
        
        hoy = QDate.currentDate()
        
        self.cierre_fecha_inicio = QDateEdit()
        self.cierre_fecha_inicio.setDate(hoy.addDays(-30))  # Último mes por defecto
        self.cierre_fecha_inicio.setCalendarPopup(True)
        fechas_layout.addRow("Desde:", self.cierre_fecha_inicio)
        
        self.cierre_fecha_fin = QDateEdit()
        self.cierre_fecha_fin.setDate(hoy)
        self.cierre_fecha_fin.setCalendarPopup(True)
        fechas_layout.addRow("Hasta:", self.cierre_fecha_fin)
        
        filtros_layout.addLayout(fechas_layout)
        
        # Botones
        botones_layout = QVBoxLayout()
        
        self.cargar_cierres_recientes_btn = QPushButton("Cargar Cierres Recientes")
        self.cargar_cierres_recientes_btn.clicked.connect(self.cargar_cierres_recientes)
        botones_layout.addWidget(self.cargar_cierres_recientes_btn)
        
        self.cargar_cierres_por_fechas_btn = QPushButton("Cargar por Fechas")
        self.cargar_cierres_por_fechas_btn.clicked.connect(self.cargar_cierres_por_fechas)
        botones_layout.addWidget(self.cargar_cierres_por_fechas_btn)
        
        self.exportar_cierres_btn = QPushButton("Exportar Cierres a CSV")
        self.exportar_cierres_btn.clicked.connect(self.exportar_cierres_csv)
        botones_layout.addWidget(self.exportar_cierres_btn)
        
        filtros_layout.addStretch()
        filtros_layout.addLayout(botones_layout)
        
        filtros_group.setLayout(filtros_layout)
        
        # Crear un splitter para dividir la vista
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Tabla de cierres
        cierres_group = QGroupBox("Cierres de Día")
        cierres_layout = QVBoxLayout()
        
        self.cierres_table = QTableWidget()
        self.cierres_table.setColumnCount(10)
        self.cierres_table.setHorizontalHeaderLabels([
            "ID", "Fecha", "USD", "EUR", "CUP", "Transferencia", 
            "Facturas", "Dif. USD", "Dif. EUR", "Dif. CUP"
        ])
        self.cierres_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.cierres_table.selectionModel().selectionChanged.connect(self.mostrar_detalle_cierre)
        
        cierres_layout.addWidget(self.cierres_table)
        cierres_group.setLayout(cierres_layout)
        
        splitter.addWidget(cierres_group)
        
        # Detalles del cierre seleccionado
        detalles_group = QGroupBox("Detalles del Cierre")
        detalles_layout = QVBoxLayout()
        
        # Tabla de facturas del cierre
        self.cierre_facturas_table = QTableWidget()
        self.cierre_facturas_table.setColumnCount(7)
        self.cierre_facturas_table.setHorizontalHeaderLabels([
            "ID Orden", "Monto", "Moneda", "Pagos", "Equivalente", "Fecha", "Estado"
        ])
        
        # Tabla de salidas del cierre
        self.cierre_salidas_table = QTableWidget()
        self.cierre_salidas_table.setColumnCount(7)
        self.cierre_salidas_table.setHorizontalHeaderLabels([
            "ID", "Monto USD", "Monto EUR", "Monto CUP", "Transfer", "Destinatario", "Motivo"
        ])
        
        detalles_tabs = QTabWidget()
        
        facturas_widget = QWidget()
        facturas_layout = QVBoxLayout(facturas_widget)
        facturas_layout.addWidget(self.cierre_facturas_table)
        
        salidas_widget = QWidget()
        salidas_layout = QVBoxLayout(salidas_widget)
        salidas_layout.addWidget(self.cierre_salidas_table)
        
        detalles_tabs.addTab(facturas_widget, "Facturas")
        detalles_tabs.addTab(salidas_widget, "Salidas")
        
        detalles_layout.addWidget(detalles_tabs)
        detalles_group.setLayout(detalles_layout)
        
        splitter.addWidget(detalles_group)
        
        # Añadir todo al layout principal
        layout.addWidget(filtros_group)
        layout.addWidget(splitter)
    
    def limpiar_filtros_salidas(self):
        """Limpia todos los filtros de la pestaña de salidas"""
        hoy = QDate.currentDate()
        
        # Restablecer fechas a los valores por defecto
        self.salida_fecha_inicio.setDate(hoy.addDays(-30))
        self.salida_fecha_fin.setDate(hoy)
        
        # Limpiar los campos de texto
        self.filtro_destinatario.clear()
        self.filtro_autorizado.clear()
        self.filtro_motivo.clear()
        
        # Regenerar el reporte con los filtros limpios
        self.generar_reporte_salidas()

    def cargar_cierres_recientes(self):
        """Carga los cierres más recientes (último mes)"""
        self.cierre_periodo_combo.setCurrentIndex(0)  # Selecciona "Último mes"
        self.cargar_cierres_dia()
    
    def cargar_cierres_por_fechas(self):
        """Carga los cierres según el rango de fechas seleccionado"""
        try:
            fecha_inicio = self.cierre_fecha_inicio.date().toString("yyyy-MM-dd")
            fecha_fin = self.cierre_fecha_fin.date().toString("yyyy-MM-dd")
            
            # Validar fechas
            if self.cierre_fecha_inicio.date() > self.cierre_fecha_fin.date():
                QMessageBox.warning(self, "Error", "La fecha de inicio debe ser anterior a la fecha final")
                return
            
            print(f"Consultando cierres desde {fecha_inicio} hasta {fecha_fin}")
            
            # Llamar al servicio de cierres con el rango de fechas
            cierres = self.cierre_service.obtener_cierres_por_fecha(fecha_inicio, fecha_fin)
            
            print(f"Se encontraron {len(cierres)} cierres en el período seleccionado")
            
            # Limpiar tabla y mostrar los resultados
            self.cierres_table.setRowCount(0)
            
            # Llenar tabla con datos
            for i, cierre in enumerate(cierres):
                self.cierres_table.insertRow(i)
                # (Código para llenar la tabla, similar al del método cargar_cierres_dia)
                # ...
                
            if len(cierres) == 0:
                QMessageBox.information(self, "Sin resultados", 
                                        "No se encontraron cierres para el período seleccionado.")
                
        except Exception as e:
            print(f"ERROR al cargar cierres por fechas: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Ocurrió un error al cargar los cierres:\n{str(e)}")
    
    def setup_salidas_tab(self):
        """Configura la pestaña de salidas de caja"""
        layout = QVBoxLayout(self.salidas_tab)
        
        # Grupo: Filtros de reporte
        filtros_group = QGroupBox("Filtros de Salidas")
        filtros_layout = QHBoxLayout()
        
        # Fechas
        fecha_layout = QFormLayout()
        
        hoy = QDate.currentDate()
        
        self.salida_fecha_inicio = QDateEdit()
        self.salida_fecha_inicio.setDate(hoy.addDays(-30))  # Último mes por defecto
        self.salida_fecha_inicio.setCalendarPopup(True)
        fecha_layout.addRow("Desde:", self.salida_fecha_inicio)
        
        self.salida_fecha_fin = QDateEdit()
        self.salida_fecha_fin.setDate(hoy)
        self.salida_fecha_fin.setCalendarPopup(True)
        fecha_layout.addRow("Hasta:", self.salida_fecha_fin)
        
        filtros_layout.addLayout(fecha_layout)
        
        # Filtros adicionales
        filtros_extra_layout = QFormLayout()
        
        self.filtro_destinatario = QLineEdit()
        self.filtro_destinatario.setPlaceholderText("Filtrar por destinatario")
        filtros_extra_layout.addRow("Destinatario:", self.filtro_destinatario)
        
        # Nuevo filtro para Autorizado por
        self.filtro_autorizado = QLineEdit()
        self.filtro_autorizado.setPlaceholderText("Filtrar por quien autorizó")
        filtros_extra_layout.addRow("Autorizado por:", self.filtro_autorizado)
        
        # Agregamos filtro por motivo también para mayor flexibilidad
        self.filtro_motivo = QLineEdit()
        self.filtro_motivo.setPlaceholderText("Filtrar por motivo o descripción")
        filtros_extra_layout.addRow("Motivo:", self.filtro_motivo)
        
        filtros_layout.addLayout(filtros_extra_layout)
        
        # Botones
        botones_layout = QVBoxLayout()
        
        self.generar_salidas_btn = QPushButton("Generar Reporte")
        self.generar_salidas_btn.clicked.connect(self.generar_reporte_salidas)
        botones_layout.addWidget(self.generar_salidas_btn)
        
        self.exportar_salidas_btn = QPushButton("Exportar a CSV")
        self.exportar_salidas_btn.clicked.connect(self.exportar_salidas_csv)
        botones_layout.addWidget(self.exportar_salidas_btn)
        
        # Agregar botón para limpiar filtros
        self.limpiar_filtros_btn = QPushButton("Limpiar Filtros")
        self.limpiar_filtros_btn.clicked.connect(self.limpiar_filtros_salidas)
        botones_layout.addWidget(self.limpiar_filtros_btn)
        
        filtros_layout.addLayout(botones_layout)
        filtros_group.setLayout(filtros_layout)
        
        # Tabla de salidas
        self.salidas_table = QTableWidget()
        self.salidas_table.setColumnCount(9)
        self.salidas_table.setHorizontalHeaderLabels([
            "ID", "Fecha", "USD", "EUR", "CUP", "Transferencia", 
            "Destinatario", "Autorizado Por", "Motivo"
        ])
        self.salidas_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Panel de totales
        totales_group = QGroupBox("Resumen de Salidas")
        totales_layout = QHBoxLayout()
        
        self.total_salidas = QLabel("Salidas: 0")
        self.salidas_total_usd = QLabel("Total USD: $0.00")
        self.salidas_total_eur = QLabel("Total EUR: €0.00")
        self.salidas_total_cup = QLabel("Total CUP: $0.00")
        self.salidas_total_transf = QLabel("Total Transf.: $0.00")
        
        totales_layout.addWidget(self.total_salidas)
        totales_layout.addWidget(self.salidas_total_usd)
        totales_layout.addWidget(self.salidas_total_eur)
        totales_layout.addWidget(self.salidas_total_cup)
        totales_layout.addWidget(self.salidas_total_transf)
        
        totales_group.setLayout(totales_layout)
        
        # Añadir todo al layout principal
        layout.addWidget(filtros_group)
        layout.addWidget(self.salidas_table)
        layout.addWidget(totales_group)
    
    def setup_resumen_tab(self):
        """Configura la pestaña de resumen consolidado"""
        layout = QVBoxLayout(self.resumen_tab)
        
        # Grupo: Periodo de consolidación
        periodo_group = QGroupBox("Periodo de Consolidación")
        periodo_layout = QHBoxLayout()
        
        fecha_layout = QFormLayout()
        
        hoy = QDate.currentDate()
        primer_dia_mes = QDate(hoy.year(), hoy.month(), 1)
        
        self.consolidado_fecha_inicio = QDateEdit()
        self.consolidado_fecha_inicio.setDate(primer_dia_mes)  # Primer día del mes actual
        self.consolidado_fecha_inicio.setCalendarPopup(True)
        fecha_layout.addRow("Desde:", self.consolidado_fecha_inicio)
        
        self.consolidado_fecha_fin = QDateEdit()
        self.consolidado_fecha_fin.setDate(hoy)  # Hoy
        self.consolidado_fecha_fin.setCalendarPopup(True)
        fecha_layout.addRow("Hasta:", self.consolidado_fecha_fin)
        
        periodo_layout.addLayout(fecha_layout)
        
        # Botones
        botones_layout = QVBoxLayout()
        
        self.consolidar_btn = QPushButton("Consolidar Periodo")
        self.consolidar_btn.clicked.connect(self.generar_consolidado)
        botones_layout.addWidget(self.consolidar_btn)
        
        self.exportar_consolidado_btn = QPushButton("Exportar Consolidado")
        self.exportar_consolidado_btn.clicked.connect(self.exportar_consolidado)
        botones_layout.addWidget(self.exportar_consolidado_btn)
        
        periodo_layout.addStretch()
        periodo_layout.addLayout(botones_layout)
        
        periodo_group.setLayout(periodo_layout)
        layout.addWidget(periodo_group)
        
        # Contenedor para múltiples paneles de resumen
        resumen_layout = QHBoxLayout()
        
        # Panel: Resumen de Facturas
        facturas_group = QGroupBox("Resumen de Facturas")
        facturas_layout = QVBoxLayout()
        
        self.consolidado_num_facturas = QLabel("Facturas: 0")
        self.consolidado_total_facturado = QLabel("Total Facturado (USD): $0.00")
        self.consolidado_promedio_factura = QLabel("Promedio por Factura: $0.00")
        
        # Añadir etiqueta para desglose detallado de facturas por moneda
        self.consolidado_facturas_detalle = QLabel("")
        self.consolidado_facturas_detalle.setStyleSheet("font-size: 11px; color: #666;")
        self.consolidado_facturas_detalle.setWordWrap(True)
        
        facturas_layout.addWidget(self.consolidado_num_facturas)
        facturas_layout.addWidget(self.consolidado_total_facturado)
        facturas_layout.addWidget(self.consolidado_promedio_factura)
        facturas_layout.addWidget(self.consolidado_facturas_detalle)
        facturas_layout.addStretch()
        
        facturas_group.setLayout(facturas_layout)
        resumen_layout.addWidget(facturas_group)
        
        # Panel: Resumen de Salidas
        salidas_group = QGroupBox("Resumen de Salidas")
        salidas_layout = QVBoxLayout()
        
        self.consolidado_num_salidas = QLabel("Salidas: 0")
        self.consolidado_total_salidas = QLabel("Total Salidas (USD): $0.00")
        self.consolidado_promedio_salida = QLabel("Promedio por Salida: $0.00")
        
        salidas_layout.addWidget(self.consolidado_num_salidas)
        salidas_layout.addWidget(self.consolidado_total_salidas)
        salidas_layout.addWidget(self.consolidado_promedio_salida)
        salidas_layout.addStretch()
        
        salidas_group.setLayout(salidas_layout)
        resumen_layout.addWidget(salidas_group)
        
        # Panel: Balance Final
        balance_group = QGroupBox("Balance Final")
        balance_layout = QVBoxLayout()
        
        self.consolidado_balance_usd = QLabel("Balance USD: $0.00")
        self.consolidado_balance_eur = QLabel("Balance EUR: €0.00")
        self.consolidado_balance_cup = QLabel("Balance CUP: $0.00")
        self.consolidado_balance_transf = QLabel("Balance Transferencia: $0.00")
        
        balance_layout.addWidget(self.consolidado_balance_usd)
        balance_layout.addWidget(self.consolidado_balance_eur)
        balance_layout.addWidget(self.consolidado_balance_cup)
        balance_layout.addWidget(self.consolidado_balance_transf)
        balance_layout.addStretch()
        
        balance_group.setLayout(balance_layout)
        resumen_layout.addWidget(balance_group)
        
        layout.addLayout(resumen_layout)
        
        # Tabla de resumen por día
        resumen_dias_group = QGroupBox("Resumen por Día")
        resumen_dias_layout = QVBoxLayout()
        
        self.consolidado_dias_table = QTableWidget()
        self.consolidado_dias_table.setColumnCount(8)
        self.consolidado_dias_table.setHorizontalHeaderLabels([
            "Fecha", "Facturas", "Monto USD", "Monto EUR", "Monto CUP", 
            "Salidas USD", "Salidas EUR", "Salidas CUP"
        ])
        self.consolidado_dias_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        resumen_dias_layout.addWidget(self.consolidado_dias_table)
        resumen_dias_group.setLayout(resumen_dias_layout)
        
        layout.addWidget(resumen_dias_group)
        
    def cargar_datos_iniciales(self):
        """Carga los datos iniciales para todas las pestañas"""
        # Generar reporte de facturas inicial
        self.generar_reporte_facturas()
        
        # Cargar cierres de día
        self.cargar_cierres_dia()
        
        # Generar reporte de salidas inicial
        self.generar_reporte_salidas()
        
        # Generar consolidado inicial
        self.generar_consolidado()
    
    def generar_reporte_facturas(self):
       
        """Genera un reporte de facturas según los filtros seleccionados"""
        try:
            print("\n--- INICIANDO GENERACIÓN DE REPORTE DE FACTURAS ---")
            
            # Obtener fechas
            fecha_inicio = self.factura_fecha_inicio.date().toString("yyyy-MM-dd")
            fecha_fin = self.factura_fecha_fin.date().toString("yyyy-MM-dd")
            print(f"Periodo seleccionado: {fecha_inicio} a {fecha_fin}")
            
            # Validar fechas
            if self.factura_fecha_inicio.date() > self.factura_fecha_fin.date():
                QMessageBox.warning(self, "Error", "La fecha de inicio debe ser anterior a la fecha final")
                return
            
            # Obtener facturas filtradas
            print("Consultando facturas en la base de datos...")
            facturas = self.facturacion_service.obtener_facturas_por_fecha(fecha_inicio, fecha_fin)
            print(f"Se encontraron {len(facturas)} facturas en la base de datos")
            
            # Aplicar filtros adicionales
            moneda_filtro = self.filtro_moneda.currentText()
            if moneda_filtro != "Todas":
                print(f"Aplicando filtro de moneda: {moneda_filtro}")
                facturas = [f for f in facturas if f.moneda == moneda_filtro]
                print(f"Quedan {len(facturas)} facturas después del filtro de moneda")
            
            min_monto_texto = self.filtro_min_monto.text()
            if min_monto_texto:
                try:
                    min_monto = float(min_monto_texto)
                    print(f"Aplicando filtro de monto mínimo: {min_monto}")
                    facturas = [f for f in facturas if f.monto >= min_monto]
                    print(f"Quedan {len(facturas)} facturas después del filtro de monto")
                except ValueError:
                    print(f"Error: el monto '{min_monto_texto}' no es un número válido")
                    pass  # Ignorar si no es un número válido
            
            # Limpiar tabla
            print("Limpiando tabla de resultados...")
            self.facturas_table.setRowCount(0)
            
            # Variables para totales
            total_usd = 0.0
            total_eur = 0.0
            total_cup = 0.0
            total_transferencia = 0.0
            
            # Llenar tabla con datos
            print(f"Llenando tabla con {len(facturas)} facturas...")
            for i, factura in enumerate(facturas):
                try:
                    self.facturas_table.insertRow(i)
                    
                    # Crear items para cada columna
                    orden_id_item = QTableWidgetItem(str(factura.orden_id))
                    monto_item = QTableWidgetItem(f"{factura.monto:.2f}")
                    moneda_item = QTableWidgetItem(factura.moneda)
                    
                    # Pagos en diferentes monedas
                    pago_usd = getattr(factura, 'pago_usd', 0) or 0
                    pago_eur = getattr(factura, 'pago_eur', 0) or 0
                    pago_cup = getattr(factura, 'pago_cup', 0) or 0
                    pago_transferencia = getattr(factura, 'pago_transferencia', 0) or 0
                    
                    usd_item = QTableWidgetItem(f"{pago_usd:.2f}")
                    eur_item = QTableWidgetItem(f"{pago_eur:.2f}")
                    cup_item = QTableWidgetItem(f"{pago_cup:.2f}")
                    transferencia_item = QTableWidgetItem(f"{pago_transferencia:.2f}")
                    
                    equivalente_item = QTableWidgetItem(f"{factura.monto_equivalente:.2f}")
                    fecha_item = QTableWidgetItem(factura.fecha.strftime("%Y-%m-%d %H:%M"))
                    
                    # Alinear números a la derecha
                    for item in [monto_item, usd_item, eur_item, cup_item, transferencia_item, equivalente_item]:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    
                    # Añadir items a la tabla
                    self.facturas_table.setItem(i, 0, orden_id_item)
                    self.facturas_table.setItem(i, 1, monto_item)
                    self.facturas_table.setItem(i, 2, moneda_item)
                    self.facturas_table.setItem(i, 3, usd_item)
                    self.facturas_table.setItem(i, 4, eur_item)
                    self.facturas_table.setItem(i, 5, cup_item)
                    self.facturas_table.setItem(i, 6, transferencia_item)
                    self.facturas_table.setItem(i, 7, equivalente_item)
                    self.facturas_table.setItem(i, 8, fecha_item)
                    
                    # Actualizar totales
                    total_usd += pago_usd
                    total_eur += pago_eur
                    total_cup += pago_cup
                    total_transferencia += pago_transferencia
                    
                except Exception as e:
                    print(f"Error procesando factura #{i+1}: {e}")
            
            # IMPORTANTE: Este código debe estar FUERA del bucle for y del bloque except
            # Actualizar etiquetas de totales - FUERA DEL BUCLE
            print("Actualizando etiquetas de totales...")
            self.total_facturas.setText(f"Facturas: {len(facturas)}")
            self.total_usd.setText(f"Total USD: ${total_usd:.2f}")
            self.total_eur.setText(f"Total EUR: €{total_eur:.2f}")
            self.total_cup.setText(f"Total CUP: ${total_cup:.2f}")
            self.total_transferencia.setText(f"Total Transferencia: ${total_transferencia:.2f}")
            
            # Forzar actualización de la interfaz - FUERA DEL BUCLE
            self.facturas_table.update()
            
            print(f"Reporte generado exitosamente: {len(facturas)} facturas mostradas.")
            
            # Si no hay resultados, mostrar mensaje - FUERA DEL BUCLE
            if len(facturas) == 0:
                QMessageBox.information(self, "Sin resultados", 
                                        "No se encontraron facturas que coincidan con los filtros seleccionados.")
                                            
        except Exception as e:
            print(f"ERROR GENERAL al generar reporte: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Ocurrió un error al generar el reporte:\n{str(e)}")
    def exportar_facturas_csv(self):
        """Exporta el reporte de facturas actual a un archivo CSV"""
        # Verificar si hay datos para exportar
        if self.facturas_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "No hay datos para exportar. Genere un reporte primero.")
            return
        
        # Solicitar ubicación para guardar el archivo
        fecha_inicio = self.factura_fecha_inicio.date().toString("yyyyMMdd")
        fecha_fin = self.factura_fecha_fin.date().toString("yyyyMMdd")
        nombre_default = f"reporte_facturas_{fecha_inicio}_{fecha_fin}.csv"
        
        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte CSV",
            nombre_default,
            "Archivos CSV (*.csv);;Todos los archivos (*)"
        )
        
        if not ruta_archivo:  # El usuario canceló
            return
        
        try:
            with open(ruta_archivo, 'w', newline='', encoding='utf-8') as archivo_csv:
                writer = csv.writer(archivo_csv)
                
                # Escribir encabezados
                encabezados = []
                for i in range(self.facturas_table.columnCount()):
                    encabezados.append(self.facturas_table.horizontalHeaderItem(i).text())
                writer.writerow(encabezados)
                
                # Escribir datos
                for fila in range(self.facturas_table.rowCount()):
                    datos_fila = []
                    for columna in range(self.facturas_table.columnCount()):
                        item = self.facturas_table.item(fila, columna)
                        if item is not None:
                            datos_fila.append(item.text())
                        else:
                            datos_fila.append("")
                    writer.writerow(datos_fila)
                
                # Escribir totales
                writer.writerow([])  # Línea en blanco
                writer.writerow(["Resumen", "", "", "", "", "", "", "", ""])
                writer.writerow(["Total Facturas", self.total_facturas.text().replace("Facturas: ", ""), "", "", "", "", "", "", ""])
                writer.writerow(["Total USD", self.total_usd.text().replace("Total USD: $", ""), "", "", "", "", "", "", ""])
                writer.writerow(["Total EUR", self.total_eur.text().replace("Total EUR: €", ""), "", "", "", "", "", "", ""])
                writer.writerow(["Total CUP", self.total_cup.text().replace("Total CUP: $", ""), "", "", "", "", "", "", ""])
                writer.writerow(["Total Transferencia", self.total_transferencia.text().replace("Total Transferencia: $", ""), "", "", "", "", "", "", ""])
                
            QMessageBox.information(self, "Exportación Exitosa", 
                                  f"El reporte se ha exportado correctamente a:\n{ruta_archivo}")
                                  
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", 
                               f"No se pudo exportar el reporte:\n{str(e)}")
    
    def cargar_cierres_dia(self):
        """Carga la lista de cierres de día"""
        try:
            print("\n--- INICIANDO CARGA DE CIERRES DE DÍA ---")
            
            # Determinar el límite según el periodo seleccionado
            limite = 30  # Por defecto: último mes
            periodo_idx = self.cierre_periodo_combo.currentIndex()
            if periodo_idx == 1:  # Últimos 3 meses
                limite = 90
            elif periodo_idx == 2:  # Último año
                limite = 365
            elif periodo_idx == 3:  # Todo
                limite = None
            
            print(f"Consultando cierres con límite: {limite} días")
            
            # Obtener cierres de día
            cierres = self.cierre_service.obtener_historial_cierres(limite)
            print(f"Se encontraron {len(cierres)} cierres de día")
            
            if not cierres:
                print("No se encontraron cierres en este periodo")
                # Podríamos añadir aquí código para diagnosticar si hay cierres en la base de datos
            
            # Limpiar tabla
            print("Limpiando tabla de resultados...")
            self.cierres_table.setRowCount(0)
            
            # Llenar tabla con datos
            print(f"Llenando tabla con {len(cierres)} cierres...")
            for i, cierre in enumerate(cierres):
                try:
                    self.cierres_table.insertRow(i)
                    
                    # Verificar que el cierre tenga los campos esperados
                    if 'id' not in cierre or 'fecha' not in cierre:
                        print(f"Cierre #{i+1} incompleto. Campos disponibles: {cierre.keys()}")
                    
                    # Crear items para cada columna
                    id_item = QTableWidgetItem(str(cierre.get('id', 'N/A')))
                    fecha_item = QTableWidgetItem(str(cierre.get('fecha', 'N/A')))
                    
                    # Datos numéricos con manejo de errores
                    try:
                        total_usd = cierre.get('total_usd', 0) or 0
                        total_eur = cierre.get('total_eur', 0) or 0
                        total_cup = cierre.get('total_cup', 0) or 0
                        total_transf = cierre.get('total_transferencia', 0) or 0
                        
                        print(f"Cierre #{i+1}: USD={total_usd}, EUR={total_eur}, CUP={total_cup}, Transf={total_transf}")
                        
                        total_usd_item = QTableWidgetItem(f"{total_usd:.2f}")
                        total_eur_item = QTableWidgetItem(f"{total_eur:.2f}")
                        total_cup_item = QTableWidgetItem(f"{total_cup:.2f}")
                        total_transferencia_item = QTableWidgetItem(f"{total_transf:.2f}")
                    except Exception as e:
                        print(f"Error al procesar montos del cierre #{i+1}: {e}")
                        total_usd_item = QTableWidgetItem("0.00")
                        total_eur_item = QTableWidgetItem("0.00")
                        total_cup_item = QTableWidgetItem("0.00")
                        total_transferencia_item = QTableWidgetItem("0.00")
                    
                    # Facturas
                                    # Facturas
                    num_facturas_item = QTableWidgetItem(str(cierre.get('num_facturas', 0)))
                    
                    # Diferencias
                    try:
                        dif_usd = cierre.get('diferencia_usd', 0) or 0
                        dif_eur = cierre.get('diferencia_eur', 0) or 0
                        dif_cup = cierre.get('diferencia_cup', 0) or 0
                        
                        diferencia_usd_item = QTableWidgetItem(f"{dif_usd:.2f}")
                        diferencia_eur_item = QTableWidgetItem(f"{dif_eur:.2f}")
                        diferencia_cup_item = QTableWidgetItem(f"{dif_cup:.2f}")
                    except Exception as e:
                        print(f"Error al procesar diferencias del cierre #{i+1}: {e}")
                        diferencia_usd_item = QTableWidgetItem("0.00")
                        diferencia_eur_item = QTableWidgetItem("0.00")
                        diferencia_cup_item = QTableWidgetItem("0.00")
                    
                    # Alinear números a la derecha
                    for item in [total_usd_item, total_eur_item, total_cup_item, total_transferencia_item, 
                                diferencia_usd_item, diferencia_eur_item, diferencia_cup_item]:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    
                    # Colorear diferencias según si son positivas o negativas
                    dif_usd = cierre.get('diferencia_usd', 0) or 0
                    if dif_usd < 0:
                        diferencia_usd_item.setForeground(QColor(255, 0, 0))  # Rojo para negativo
                    elif dif_usd > 0:
                        diferencia_usd_item.setForeground(QColor(0, 128, 0))  # Verde para positivo
                        
                    dif_eur = cierre.get('diferencia_eur', 0) or 0
                    if dif_eur < 0:
                        diferencia_eur_item.setForeground(QColor(255, 0, 0))
                    elif dif_eur > 0:
                        diferencia_eur_item.setForeground(QColor(0, 128, 0))
                        
                    dif_cup = cierre.get('diferencia_cup', 0) or 0
                    if dif_cup < 0:
                        diferencia_cup_item.setForeground(QColor(255, 0, 0))
                    elif dif_cup > 0:
                        diferencia_cup_item.setForeground(QColor(0, 128, 0))
                    
                    # Añadir items a la tabla
                    self.cierres_table.setItem(i, 0, id_item)
                    self.cierres_table.setItem(i, 1, fecha_item)
                    self.cierres_table.setItem(i, 2, total_usd_item)
                    self.cierres_table.setItem(i, 3, total_eur_item)
                    self.cierres_table.setItem(i, 4, total_cup_item)
                    self.cierres_table.setItem(i, 5, total_transferencia_item)
                    self.cierres_table.setItem(i, 6, num_facturas_item)
                    self.cierres_table.setItem(i, 7, diferencia_usd_item)
                    self.cierres_table.setItem(i, 8, diferencia_eur_item)
                    self.cierres_table.setItem(i, 9, diferencia_cup_item)
            
                except Exception as e:
                    print(f"Error al procesar cierre #{i+1}: {e}")
                    import traceback
                    traceback.print_exc()
        
            # Forzar actualización de la tabla después de cargar todos los datos
            self.cierres_table.update()
            
            # Mostrar mensajes informativos
            if len(cierres) > 0:
                print(f"Se cargaron {len(cierres)} cierres en la tabla")
                # Opcional: Mostrar mensaje en la barra de estado
                # self.parent().statusBar().showMessage(f"Se cargaron {len(cierres)} cierres", 3000)
            else:
                print("No se encontraron cierres de día para mostrar")
                # Mostrar mensaje informativo al usuario
                QMessageBox.information(self, "Sin resultados", 
                                    "No se encontraron cierres de día para el período seleccionado.")
        
        except Exception as e:
            print(f"ERROR GENERAL al cargar cierres de día: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Ocurrió un error al cargar los cierres de día:\n{str(e)}")
        
    def filtrar_cierres(self):
        """Filtra la lista de cierres según el periodo seleccionado"""
        self.cargar_cierres_dia()
    
    def mostrar_detalle_cierre(self):
        """Muestra los detalles del cierre seleccionado"""
        try:
            # Obtener fila seleccionada
            filas_seleccionadas = self.cierres_table.selectedItems()
            if not filas_seleccionadas:
                print("No hay filas seleccionadas en la tabla de cierres")
                return
            
            # Obtener ID del cierre seleccionado
            fila = filas_seleccionadas[0].row()
            cierre_id_item = self.cierres_table.item(fila, 0)
            if not cierre_id_item:
                print("No se pudo obtener el ítem de ID")
                return
                
            cierre_id_text = cierre_id_item.text().strip()
            if not cierre_id_text:
                print("El texto del ID está vacío")
                return
                
            try:
                cierre_id = int(cierre_id_text)
                print(f"Mostrando detalles del cierre #{cierre_id}")
            except ValueError:
                print(f"No se pudo convertir '{cierre_id_text}' a entero")
                return
            
            # Actualizar la información del cierre seleccionado
            fecha_item = self.cierres_table.item(fila, 1)
            usd_item = self.cierres_table.item(fila, 2)
            eur_item = self.cierres_table.item(fila, 3)
            cup_item = self.cierres_table.item(fila, 4)
            
            if fecha_item and usd_item and eur_item and cup_item:
                fecha_cierre = fecha_item.text()
                total_usd = float(usd_item.text() or 0)
                total_eur = float(eur_item.text() or 0)
                total_cup = float(cup_item.text() or 0)
                
                # Actualizar el título del grupo de detalles
                parent = self.cierre_facturas_table.parent()
                while parent:
                    if isinstance(parent, QGroupBox):
                        parent.setTitle(f"Detalles del Cierre #{cierre_id} - {fecha_cierre} - USD: {total_usd:.2f}, EUR: {total_eur:.2f}, CUP: {total_cup:.2f}")
                        break
                    parent = parent.parent()
            
            # Obtener detalles del cierre desde el servicio
            print(f"Solicitando detalles del cierre #{cierre_id} al servicio...")
            detalles = self.cierre_service.obtener_detalles_cierre(cierre_id)
            
            if not detalles or not detalles.get('success', False):
                error_msg = detalles.get('message', 'Error desconocido') if detalles else 'No se obtuvo respuesta del servicio'
                print(f"Error al obtener detalles: {error_msg}")
                QMessageBox.warning(self, "Error", f"No se pudieron obtener los detalles del cierre: {error_msg}")
                
                # Intentar consulta directa a la base de datos como alternativa
                print("Intentando consulta directa a la base de datos...")
                from app.database.db_manager import DBManager
                db = DBManager()
                try:
                    db.connect()
                    cursor = db.connection.cursor()
                    
                    # Verificar si el cierre existe
                    cursor.execute("SELECT id, fecha FROM cierres_dia WHERE id = ?", (cierre_id,))
                    cierre = cursor.fetchone()
                    if not cierre:
                        print(f"No se encontró el cierre #{cierre_id} en la base de datos")
                        db.disconnect()
                        return
                    
                    # Consultar facturas asociadas al cierre
                    cursor.execute("""
                        SELECT orden_id, monto, moneda, pago_usd, pago_eur, pago_cup, 
                            pago_transferencia, monto_equivalente, fecha, cerrada
                        FROM facturas 
                        WHERE cierre_id = ?
                    """, (cierre_id,))
                    facturas_data = cursor.fetchall()
                    
                    # Consultar salidas asociadas al cierre
                    cursor.execute("""
                        SELECT id, monto_usd, monto_eur, monto_cup, monto_transferencia, 
                            destinatario, autorizado_por, motivo
                        FROM salidas_caja 
                        WHERE cierre_id = ?
                    """, (cierre_id,))
                    salidas_data = cursor.fetchall()
                    
                    db.disconnect()
                    
                    # Convertir resultados a lista de diccionarios para procesar
                    facturas = []
                    for f in facturas_data:
                        facturas.append({
                            'orden_id': str(f[0]),
                            'monto': float(f[1] or 0),
                            'moneda': f[2],
                            'pago_usd': float(f[3] or 0),
                            'pago_eur': float(f[4] or 0),
                            'pago_cup': float(f[5] or 0),
                            'pago_transferencia': float(f[6] or 0),
                            'monto_equivalente': float(f[7] or 0),
                            'fecha': f[8],
                            'cerrada': bool(f[9])
                        })
                    
                    salidas = []
                    for s in salidas_data:
                        salidas.append({
                            'id': s[0],
                            'monto_usd': float(s[1] or 0),
                            'monto_eur': float(s[2] or 0),
                            'monto_cup': float(s[3] or 0),
                            'monto_transferencia': float(s[4] or 0),
                            'destinatario': s[5],
                            'autorizado_por': s[6],
                            'motivo': s[7] if len(s) > 7 else ''
                        })
                    
                    print(f"Consulta directa - Facturas: {len(facturas)}, Salidas: {len(salidas)}")
                    
                except Exception as e:
                    print(f"Error en consulta directa: {e}")
                    import traceback
                    traceback.print_exc()
                    if db.connection:
                        db.disconnect()
                    return
            else:
                # Obtener facturas y salidas de la respuesta del servicio
                facturas = detalles.get('facturas', [])
                salidas = detalles.get('salidas', [])
                print(f"Detalles obtenidos del servicio - Facturas: {len(facturas)}, Salidas: {len(salidas)}")
            
            # Limpiar tablas de detalles
            self.cierre_facturas_table.setRowCount(0)
            self.cierre_salidas_table.setRowCount(0)
            
            # Llenar tabla de facturas
            for i, factura in enumerate(facturas):
                try:
                    self.cierre_facturas_table.insertRow(i)
                    
                    # Simplificar la presentación de los pagos
                    pagos = []
                    if factura.get('pago_usd', 0) > 0:
                        pagos.append(f"USD: {factura['pago_usd']:.2f}")
                    if factura.get('pago_eur', 0) > 0:
                        pagos.append(f"EUR: {factura['pago_eur']:.2f}")
                    if factura.get('pago_cup', 0) > 0:
                        pagos.append(f"CUP: {factura['pago_cup']:.2f}")
                    if factura.get('pago_transferencia', 0) > 0:
                        pagos.append(f"Trans: {factura['pago_transferencia']:.2f}")
                    
                    pagos_texto = ", ".join(pagos)
                    
                    # Crear items para cada columna
                    orden_id_item = QTableWidgetItem(str(factura.get('orden_id', '')))
                    monto_item = QTableWidgetItem(f"{factura.get('monto', 0):.2f}")
                    moneda_item = QTableWidgetItem(factura.get('moneda', ''))
                    pagos_item = QTableWidgetItem(pagos_texto)
                    equivalente_item = QTableWidgetItem(f"{factura.get('monto_equivalente', 0):.2f}")
                    fecha_item = QTableWidgetItem(str(factura.get('fecha', '')))
                    estado_item = QTableWidgetItem("Cerrada" if factura.get('cerrada', False) else "Abierta")
                    
                    # Añadir items a la tabla
                    self.cierre_facturas_table.setItem(i, 0, orden_id_item)
                    self.cierre_facturas_table.setItem(i, 1, monto_item)
                    self.cierre_facturas_table.setItem(i, 2, moneda_item)
                    self.cierre_facturas_table.setItem(i, 3, pagos_item)
                    self.cierre_facturas_table.setItem(i, 4, equivalente_item)
                    self.cierre_facturas_table.setItem(i, 5, fecha_item)
                    self.cierre_facturas_table.setItem(i, 6, estado_item)
                except Exception as e:
                    print(f"Error al procesar factura: {e}")
            
            # Llenar tabla de salidas
            for i, salida in enumerate(salidas):
                try:
                    self.cierre_salidas_table.insertRow(i)
                    
                    # Crear items para cada columna
                    id_item = QTableWidgetItem(str(salida.get('id', '')))
                    usd_item = QTableWidgetItem(f"{salida.get('monto_usd', 0):.2f}")
                    eur_item = QTableWidgetItem(f"{salida.get('monto_eur', 0):.2f}")
                    cup_item = QTableWidgetItem(f"{salida.get('monto_cup', 0):.2f}")
                    transferencia_item = QTableWidgetItem(f"{salida.get('monto_transferencia', 0):.2f}")
                    destinatario_item = QTableWidgetItem(salida.get('destinatario', ''))
                    motivo_item = QTableWidgetItem(salida.get('motivo', ''))
                    
                    # Añadir items a la tabla
                    self.cierre_salidas_table.setItem(i, 0, id_item)
                    self.cierre_salidas_table.setItem(i, 1, usd_item)
                    self.cierre_salidas_table.setItem(i, 2, eur_item)
                    self.cierre_salidas_table.setItem(i, 3, cup_item)
                    self.cierre_salidas_table.setItem(i, 4, transferencia_item)
                    self.cierre_salidas_table.setItem(i, 5, destinatario_item)
                    self.cierre_salidas_table.setItem(i, 6, motivo_item)
                except Exception as e:
                    print(f"Error al procesar salida: {e}")
            
            # Mostrar mensaje si no hay datos
            if len(facturas) == 0 and len(salidas) == 0:
                print("No se encontraron facturas ni salidas para este cierre")
                QMessageBox.information(self, "Sin datos", 
                                    "Este cierre no tiene facturas ni salidas asociadas.")
        
        except Exception as e:
            print(f"ERROR GENERAL al mostrar detalles: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error al mostrar detalles del cierre: {str(e)}")
        
    def exportar_cierres_csv(self):
        """Exporta los cierres de día a un archivo CSV"""
        # Verificar si hay datos para exportar
        if self.cierres_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "No hay datos para exportar.")
            return
        
        # Solicitar ubicación para guardar el archivo
        nombre_default = f"cierres_dia_{date.today().strftime('%Y%m%d')}.csv"
        
        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Cierres CSV",
            nombre_default,
            "Archivos CSV (*.csv);;Todos los archivos (*)"
        )
        
        if not ruta_archivo:  
            return
        
        try:
            with open(ruta_archivo, 'w', newline='', encoding='utf-8') as archivo_csv:
                writer = csv.writer(archivo_csv)
                
                # Escribir encabezados
                encabezados = []
                for i in range(self.cierres_table.columnCount()):
                    encabezados.append(self.cierres_table.horizontalHeaderItem(i).text())
                writer.writerow(encabezados)
                
                # Escribir datos
                for fila in range(self.cierres_table.rowCount()):
                    datos_fila = []
                    for columna in range(self.cierres_table.columnCount()):
                        item = self.cierres_table.item(fila, columna)
                        if item is not None:
                            datos_fila.append(item.text())
                        else:
                            datos_fila.append("")
                    writer.writerow(datos_fila)
                
            QMessageBox.information(self, "Exportación Exitosa", 
                                  f"Los cierres se han exportado correctamente a:\n{ruta_archivo}")
                                  
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", 
                               f"No se pudo exportar el reporte:\n{str(e)}")
    
    def generar_reporte_salidas(self):
        """Genera un reporte de salidas según los filtros seleccionados"""
        try:
            print("\n--- INICIANDO GENERACIÓN DE REPORTE DE SALIDAS ---")
            
            # Obtener fechas
            fecha_inicio = self.salida_fecha_inicio.date().toString("yyyy-MM-dd")
            fecha_fin = self.salida_fecha_fin.date().toString("yyyy-MM-dd")
            print(f"Periodo seleccionado: {fecha_inicio} a {fecha_fin}")
            
            # Validar fechas
            if self.salida_fecha_inicio.date() > self.salida_fecha_fin.date():
                QMessageBox.warning(self, "Error", "La fecha de inicio debe ser anterior a la fecha final")
                return
            
            # Obtener valores de los filtros
            destinatario = self.filtro_destinatario.text().strip() if self.filtro_destinatario.text().strip() else None
            autorizado_por = self.filtro_autorizado.text().strip() if self.filtro_autorizado.text().strip() else None
            motivo = self.filtro_motivo.text().strip() if self.filtro_motivo.text().strip() else None
            
            # Obtener salidas filtradas
            print("Consultando salidas en la base de datos...")
            salidas = self.salidas_service.obtener_salidas_por_fecha(fecha_inicio, fecha_fin)
            print(f"Se encontraron {len(salidas)} salidas en la base de datos")
            
            # Aplicar filtro de destinatario
            if destinatario:
                print(f"Filtrando por destinatario: '{destinatario}'")
                salidas = [s for s in salidas if destinatario.lower() in s['destinatario'].lower()]
                print(f"Quedan {len(salidas)} salidas después del filtro de destinatario")
            
            # Aplicar filtro de autorizado por
            if autorizado_por:
                print(f"Filtrando por autorizado por: '{autorizado_por}'")
                salidas = [s for s in salidas if autorizado_por.lower() in s['autorizado_por'].lower()]
                print(f"Quedan {len(salidas)} salidas después del filtro de autorizado por")
            
            # Aplicar filtro de motivo
            if motivo:
                print(f"Filtrando por motivo: '{motivo}'")
                salidas = [s for s in salidas if motivo.lower() in (s.get('motivo', '').lower() or '')]
                print(f"Quedan {len(salidas)} salidas después del filtro de motivo")
            
            # Limpiar tabla
            print("Limpiando tabla de resultados...")
            self.salidas_table.setRowCount(0)
            
            # Variables para totales
            total_usd = 0.0
            total_eur = 0.0
            total_cup = 0.0
            total_transferencia = 0.0
            
            # Llenar tabla con datos
            print(f"Llenando tabla con {len(salidas)} salidas...")
            for i, salida in enumerate(salidas):
                try:
                    self.salidas_table.insertRow(i)
                    
                    # Crear items para cada columna
                    id_item = QTableWidgetItem(str(salida['id']))
                    fecha_item = QTableWidgetItem(str(salida['fecha']))
                    
                    monto_usd = salida.get('monto_usd', 0) or 0
                    monto_eur = salida.get('monto_eur', 0) or 0
                    monto_cup = salida.get('monto_cup', 0) or 0
                    monto_transferencia = salida.get('monto_transferencia', 0) or 0
                    
                    print(f"Salida #{i+1}: USD={monto_usd}, EUR={monto_eur}, CUP={monto_cup}, Transf={monto_transferencia}")
                    
                    usd_item = QTableWidgetItem(f"{monto_usd:.2f}")
                    eur_item = QTableWidgetItem(f"{monto_eur:.2f}")
                    cup_item = QTableWidgetItem(f"{monto_cup:.2f}")
                    transferencia_item = QTableWidgetItem(f"{monto_transferencia:.2f}")
                    
                    destinatario_item = QTableWidgetItem(salida.get('destinatario', ''))
                    autorizado_item = QTableWidgetItem(salida.get('autorizado_por', ''))
                    motivo_item = QTableWidgetItem(salida.get('motivo', ''))
                
                    # Alinear números a la derecha
                    for item in [usd_item, eur_item, cup_item, transferencia_item]:
                        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                    
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
                    
                    # Actualizar totales
                    total_usd += monto_usd
                    total_eur += monto_eur
                    total_cup += monto_cup
                    total_transferencia += monto_transferencia
                    
                except Exception as e:
                    print(f"Error al procesar salida #{i+1}: {e}")
        
            # Actualizar etiquetas de totales
            print("Actualizando etiquetas de totales...")
            self.total_salidas.setText(f"Salidas: {len(salidas)}")
            self.salidas_total_usd.setText(f"Total USD: ${total_usd:.2f}")
            self.salidas_total_eur.setText(f"Total EUR: €{total_eur:.2f}")
            self.salidas_total_cup.setText(f"Total CUP: ${total_cup:.2f}")
            self.salidas_total_transf.setText(f"Total Transf.: ${total_transferencia:.2f}")
            
            # Forzar actualización de la interfaz
            self.salidas_table.update()
            
            print(f"Reporte de salidas generado exitosamente: {len(salidas)} salidas mostradas.")
            
            # Si no hay resultados, mostrar mensaje
            if len(salidas) == 0:
                QMessageBox.information(self, "Sin resultados", 
                                    "No se encontraron salidas que coincidan con los filtros seleccionados.")
        
        except Exception as e:
            print(f"ERROR GENERAL al generar reporte de salidas: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Ocurrió un error al generar el reporte de salidas:\n{str(e)}")
            
    def exportar_salidas_csv(self):
        """Exporta el reporte de salidas a un archivo CSV"""
        # Verificar si hay datos para exportar
        if self.salidas_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "No hay datos para exportar. Genere un reporte primero.")
            return
        
        # Solicitar ubicación para guardar el archivo
        fecha_inicio = self.salida_fecha_inicio.date().toString("yyyyMMdd")
        fecha_fin = self.salida_fecha_fin.date().toString("yyyyMMdd")
        nombre_default = f"reporte_salidas_{fecha_inicio}_{fecha_fin}.csv"
        
        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte CSV",
            nombre_default,
            "Archivos CSV (*.csv);;Todos los archivos (*)"
        )
        
        if not ruta_archivo:  # El usuario canceló
            return
        
        try:
            with open(ruta_archivo, 'w', newline='', encoding='utf-8') as archivo_csv:
                writer = csv.writer(archivo_csv)
                
                # Escribir encabezados
                encabezados = []
                for i in range(self.salidas_table.columnCount()):
                    encabezados.append(self.salidas_table.horizontalHeaderItem(i).text())
                writer.writerow(encabezados)
                
                # Escribir datos
                for fila in range(self.salidas_table.rowCount()):
                    datos_fila = []
                    for columna in range(self.salidas_table.columnCount()):
                        item = self.salidas_table.item(fila, columna)
                        if item is not None:
                            datos_fila.append(item.text())
                        else:
                            datos_fila.append("")
                    writer.writerow(datos_fila)
                
                # Escribir totales
                writer.writerow([])  # Línea en blanco
                writer.writerow(["Resumen", "", "", "", "", "", "", "", ""])
                writer.writerow(["Total Salidas", self.total_salidas.text().replace("Salidas: ", ""), "", "", "", "", "", "", ""])
                writer.writerow(["Total USD", self.salidas_total_usd.text().replace("Total USD: $", ""), "", "", "", "", "", "", ""])
                writer.writerow(["Total EUR", self.salidas_total_eur.text().replace("Total EUR: €", ""), "", "", "", "", "", "", ""])
                writer.writerow(["Total CUP", self.salidas_total_cup.text().replace("Total CUP: $", ""), "", "", "", "", "", "", ""])
                writer.writerow(["Total Transferencia", self.salidas_total_transf.text().replace("Total Transf.: $", ""), "", "", "", "", "", "", ""])
                
            QMessageBox.information(self, "Exportación Exitosa", 
                                  f"El reporte se ha exportado correctamente a:\n{ruta_archivo}")
                                  
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", 
                               f"No se pudo exportar el reporte:\n{str(e)}")
    
    def generar_consolidado(self):
        """Genera un reporte consolidado para el período seleccionado"""
        try:
            print("\n--- INICIANDO GENERACIÓN DE REPORTE CONSOLIDADO ---")
            
            # Obtener fechas
            fecha_inicio = self.consolidado_fecha_inicio.date().toString("yyyy-MM-dd")
            fecha_fin = self.consolidado_fecha_fin.date().toString("yyyy-MM-dd")
            print(f"Periodo seleccionado: {fecha_inicio} a {fecha_fin}")
            
            # Validar fechas
            if self.consolidado_fecha_inicio.date() > self.consolidado_fecha_fin.date():
                QMessageBox.warning(self, "Error", "La fecha de inicio debe ser anterior a la fecha final")
                return
            
            # Obtener estadísticas detalladas de facturas para totales y promedios
            estadisticas = self.facturacion_service.obtener_estadisticas_facturas_por_fecha(fecha_inicio, fecha_fin)
            
            # Obtener facturas y salidas para el período
            print("Consultando facturas...")
            facturas = self.facturacion_service.obtener_facturas_por_fecha(fecha_inicio, fecha_fin)
            print(f"Se encontraron {len(facturas)} facturas")
            
            print("Consultando salidas...")
            salidas = self.salidas_service.obtener_salidas_por_fecha(fecha_inicio, fecha_fin)
            print(f"Se encontraron {len(salidas)} salidas")
            
            # Variables para totales generales
            total_facturas = estadisticas["cantidad_total"]
            total_salidas = len(salidas)
            
            # Calcular totales de pagos recibidos (por forma de pago)
            pagos_recibidos_usd = sum(getattr(f, 'pago_usd', 0) or 0 for f in facturas)
            pagos_recibidos_eur = sum(getattr(f, 'pago_eur', 0) or 0 for f in facturas)
            pagos_recibidos_cup = sum(getattr(f, 'pago_cup', 0) or 0 for f in facturas)
            pagos_recibidos_transf = sum(getattr(f, 'pago_transferencia', 0) or 0 for f in facturas)
            
            print(f"Pagos recibidos - USD: {pagos_recibidos_usd}, EUR: {pagos_recibidos_eur}, " +
                f"CUP: {pagos_recibidos_cup}, Transf: {pagos_recibidos_transf}")
            
            # Calcular totales de salidas
            try:
                total_salidas_usd = sum(s.get('monto_usd', 0) or 0 for s in salidas)
                total_salidas_eur = sum(s.get('monto_eur', 0) or 0 for s in salidas)
                total_salidas_cup = sum(s.get('monto_cup', 0) or 0 for s in salidas)
                total_salidas_transf = sum(s.get('monto_transferencia', 0) or 0 for s in salidas)
                
                print(f"Total salidas - USD: {total_salidas_usd}, EUR: {total_salidas_eur}, " +
                    f"CUP: {total_salidas_cup}, Transf: {total_salidas_transf}")
            except Exception as e:
                print(f"Error al calcular totales de salidas: {e}")
                total_salidas_usd = 0
                total_salidas_eur = 0
                total_salidas_cup = 0
                total_salidas_transf = 0
            
            # Calcular balances finales basados en formas de pago
            try:
                balance_usd = pagos_recibidos_usd - total_salidas_usd
                balance_eur = pagos_recibidos_eur - total_salidas_eur
                balance_cup = pagos_recibidos_cup - total_salidas_cup
                balance_transf = pagos_recibidos_transf - total_salidas_transf
                
                print(f"Balance - USD: {balance_usd}, EUR: {balance_eur}, " +
                    f"CUP: {balance_cup}, Transf: {balance_transf}")
            except Exception as e:
                print(f"Error al calcular balances: {e}")
                balance_usd = 0
                balance_eur = 0
                balance_cup = 0
                balance_transf = 0
            
            # Actualizar etiquetas del panel de facturas con estadísticas
            print("Actualizando etiquetas de facturas...")
            self.consolidado_num_facturas.setText(f"Facturas: {total_facturas}")
            
            # Usar el total equivalente en USD de las estadísticas
            self.consolidado_total_facturado.setText(f"Total Facturado (USD): ${estadisticas['total_equivalente_usd']:.2f}")
            
            # Usar el promedio general en USD de las estadísticas
            self.consolidado_promedio_factura.setText(f"Promedio por Factura: ${estadisticas['promedio_general_usd']:.2f}")
            
            # Actualizar desglose de facturas por moneda
            desglose = ""
            if estadisticas["cantidad_usd"] > 0:
                desglose += f"USD: {estadisticas['cantidad_usd']} fact, Total: ${estadisticas['total_usd']:.2f}, Prom: ${estadisticas['promedio_usd']:.2f}\n"
            if estadisticas["cantidad_eur"] > 0:
                desglose += f"EUR: {estadisticas['cantidad_eur']} fact, Total: €{estadisticas['total_eur']:.2f}, Prom: €{estadisticas['promedio_eur']:.2f}\n"
            if estadisticas["cantidad_cup"] > 0:
                desglose += f"CUP: {estadisticas['cantidad_cup']} fact, Total: ${estadisticas['total_cup']:.2f}, Prom: ${estadisticas['promedio_cup']:.2f}"
            
            self.consolidado_facturas_detalle.setText(desglose)
            
            # Actualizar etiquetas del panel de salidas
            print("Actualizando etiquetas de salidas...")
            self.consolidado_num_salidas.setText(f"Salidas: {total_salidas}")
            
            # Convertir salidas a USD (aproximación)
            try:
                tasa_actual = self.facturacion_service.obtener_tasa_cambio()
                print(f"Tasa de cambio actual: {tasa_actual}")
                
                if tasa_actual > 0:
                    total_salidas_usd_equiv = total_salidas_usd + (total_salidas_eur * 1.1) + (total_salidas_cup / tasa_actual)
                else:
                    print("Advertencia: Tasa de cambio es cero o negativa. Usando solo USD para el total.")
                    total_salidas_usd_equiv = total_salidas_usd
                    
                self.consolidado_total_salidas.setText(f"Total Salidas (USD): ${total_salidas_usd_equiv:.2f}")
                
                promedio_salida = total_salidas_usd_equiv / total_salidas if total_salidas > 0 else 0
                self.consolidado_promedio_salida.setText(f"Promedio por Salida: ${promedio_salida:.2f}")
                
            except Exception as e:
                print(f"Error al convertir salidas a USD: {e}")
                self.consolidado_total_salidas.setText(f"Total Salidas (USD): ${total_salidas_usd:.2f}")
                promedio_salida = total_salidas_usd / total_salidas if total_salidas > 0 else 0
                self.consolidado_promedio_salida.setText(f"Promedio por Salida: ${promedio_salida:.2f}")
            
            # Actualizar etiquetas de balance según los pagos recibidos vs. salidas
            print("Actualizando etiquetas de balance...")
            self.consolidado_balance_usd.setText(f"Balance USD: ${balance_usd:.2f}")
            self.consolidado_balance_eur.setText(f"Balance EUR: €{balance_eur:.2f}")
            self.consolidado_balance_cup.setText(f"Balance CUP: ${balance_cup:.2f}")
            self.consolidado_balance_transf.setText(f"Balance Transferencia: ${balance_transf:.2f}")
            
            # Colorear balances según si son positivos o negativos
            for label, valor in [
                (self.consolidado_balance_usd, balance_usd),
                (self.consolidado_balance_eur, balance_eur),
                (self.consolidado_balance_cup, balance_cup),
                (self.consolidado_balance_transf, balance_transf)
            ]:
                if valor < 0:
                    label.setStyleSheet("color: red;")
                elif valor > 0:
                    label.setStyleSheet("color: green;")
                else:
                    label.setStyleSheet("color: black;")
            
            # Generar resumen por día
            print("Generando resumen por día...")
            self.generar_resumen_por_dia(fecha_inicio, fecha_fin, facturas, salidas)
            
            # Forzar actualización de la interfaz
            self.consolidado_dias_table.update()
            
            # Mostrar resumen
            print(f"Reporte consolidado generado exitosamente para el período {fecha_inicio} a {fecha_fin}")
            print(f"- Facturas: {total_facturas}, Total facturado: {estadisticas['total_equivalente_usd']:.2f} USD, Promedio: {estadisticas['promedio_general_usd']:.2f} USD")
            print(f"- Pagos recibidos: USD ${pagos_recibidos_usd:.2f}, EUR €{pagos_recibidos_eur:.2f}, CUP ${pagos_recibidos_cup:.2f}, Transf ${pagos_recibidos_transf:.2f}")
            print(f"- Salidas: {total_salidas}, Total salidas: USD ${total_salidas_usd:.2f}, EUR €{total_salidas_eur:.2f}, CUP ${total_salidas_cup:.2f}, Transf ${total_salidas_transf:.2f}")
            print(f"- Balance: USD ${balance_usd:.2f}, EUR €{balance_eur:.2f}, CUP ${balance_cup:.2f}, Transf ${balance_transf:.2f}")
            
            # Si no hay datos, mostrar un mensaje al usuario
            if total_facturas == 0 and total_salidas == 0:
                QMessageBox.information(self, "Sin datos", 
                                    "No se encontraron facturas ni salidas para el período seleccionado.")
                    
        except Exception as e:
            print(f"ERROR GENERAL al generar reporte consolidado: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Ocurrió un error al generar el reporte consolidado:\n{str(e)}")   
        
    def generar_resumen_por_dia(self, fecha_inicio, fecha_fin, facturas, salidas):
        """Genera el resumen por día para el consolidado"""
        # Crear diccionarios para agrupar por fecha
        facturas_por_dia = {}
        salidas_por_dia = {}
        
        # Agrupar facturas por fecha (solo la parte de la fecha, sin hora)
        for factura in facturas:
            fecha_str = factura.fecha.strftime("%Y-%m-%d")
            if fecha_str not in facturas_por_dia:
                facturas_por_dia[fecha_str] = []
            facturas_por_dia[fecha_str].append(factura)
        
        # Agrupar salidas por fecha
        for salida in salidas:
            # Extraer solo la parte de fecha (puede variar según el formato exacto)
            fecha_str = str(salida['fecha']).split(" ")[0]
            if fecha_str not in salidas_por_dia:
                salidas_por_dia[fecha_str] = []
            salidas_por_dia[fecha_str].append(salida)
        
        # Generar un conjunto con todas las fechas (de facturas y salidas)
        todas_fechas = set(facturas_por_dia.keys()) | set(salidas_por_dia.keys())
        todas_fechas = sorted(todas_fechas)  # Ordenar fechas
        
        # Limpiar tabla
        self.consolidado_dias_table.setRowCount(0)
        
        # Llenar tabla con datos por día
        for i, fecha in enumerate(todas_fechas):
            self.consolidado_dias_table.insertRow(i)
            
            # Facturas del día
            facturas_dia = facturas_por_dia.get(fecha, [])
            num_facturas = len(facturas_dia)
            
            # Calcular montos de facturas
            monto_usd = sum(getattr(f, 'pago_usd', 0) or 0 for f in facturas_dia)
            monto_eur = sum(getattr(f, 'pago_eur', 0) or 0 for f in facturas_dia)
            monto_cup = sum(getattr(f, 'pago_cup', 0) or 0 for f in facturas_dia)
            
            # Salidas del día
            salidas_dia = salidas_por_dia.get(fecha, [])
            
            # Calcular montos de salidas
            salidas_usd = sum(s.get('monto_usd', 0) or 0 for s in salidas_dia)
            salidas_eur = sum(s.get('monto_eur', 0) or 0 for s in salidas_dia)
            salidas_cup = sum(s.get('monto_cup', 0) or 0 for s in salidas_dia)
            
            # Crear items para cada columna
            fecha_item = QTableWidgetItem(fecha)
            num_facturas_item = QTableWidgetItem(str(num_facturas))
            
            monto_usd_item = QTableWidgetItem(f"{monto_usd:.2f}")
            monto_eur_item = QTableWidgetItem(f"{monto_eur:.2f}")
            monto_cup_item = QTableWidgetItem(f"{monto_cup:.2f}")
            
            salidas_usd_item = QTableWidgetItem(f"{salidas_usd:.2f}")
            salidas_eur_item = QTableWidgetItem(f"{salidas_eur:.2f}")
            salidas_cup_item = QTableWidgetItem(f"{salidas_cup:.2f}")
            
            # Alinear números a la derecha
            for item in [monto_usd_item, monto_eur_item, monto_cup_item, 
                        salidas_usd_item, salidas_eur_item, salidas_cup_item]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Añadir items a la tabla
            self.consolidado_dias_table.setItem(i, 0, fecha_item)
            self.consolidado_dias_table.setItem(i, 1, num_facturas_item)
            self.consolidado_dias_table.setItem(i, 2, monto_usd_item)
            self.consolidado_dias_table.setItem(i, 3, monto_eur_item)
            self.consolidado_dias_table.setItem(i, 4, monto_cup_item)
            self.consolidado_dias_table.setItem(i, 5, salidas_usd_item)
            self.consolidado_dias_table.setItem(i, 6, salidas_eur_item)
            self.consolidado_dias_table.setItem(i, 7, salidas_cup_item)
    
    def exportar_consolidado(self):
        """Exporta el reporte consolidado a un archivo CSV"""
        # Verificar si hay datos para exportar
        if self.consolidado_dias_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "No hay datos para exportar. Genere un consolidado primero.")
            return
        
        # Solicitar ubicación para guardar el archivo
        fecha_inicio = self.consolidado_fecha_inicio.date().toString("yyyyMMdd")
        fecha_fin = self.consolidado_fecha_fin.date().toString("yyyyMMdd")
        nombre_default = f"consolidado_{fecha_inicio}_{fecha_fin}.csv"
        
        ruta_archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Consolidado CSV",
            nombre_default,
            "Archivos CSV (*.csv);;Todos los archivos (*)"
        )
        
        if not ruta_archivo:  # El usuario canceló
            return
        
        try:
            with open(ruta_archivo, 'w', newline='', encoding='utf-8') as archivo_csv:
                writer = csv.writer(archivo_csv)
                
                # Escribir encabezados para resumen general
                writer.writerow(["RESUMEN CONSOLIDADO", fecha_inicio, "a", fecha_fin])
                writer.writerow([])
                
                # Escribir resumen de facturas
                writer.writerow(["FACTURAS"])
                writer.writerow(["Cantidad de facturas", self.consolidado_num_facturas.text().replace("Facturas: ", "")])
                writer.writerow(["Total facturado (USD)", self.consolidado_total_facturado.text().replace("Total Facturado (USD): $", "")])
                writer.writerow(["Promedio por factura", self.consolidado_promedio_factura.text().replace("Promedio por Factura: $", "")])
                writer.writerow([])
                
                # Escribir resumen de salidas
                writer.writerow(["SALIDAS"])
                writer.writerow(["Cantidad de salidas", self.consolidado_num_salidas.text().replace("Salidas: ", "")])
                writer.writerow(["Total salidas (USD)", self.consolidado_total_salidas.text().replace("Total Salidas (USD): $", "")])
                writer.writerow(["Promedio por salida", self.consolidado_promedio_salida.text().replace("Promedio por Salida: $", "")])
                writer.writerow([])
                
                # Escribir balance final
                writer.writerow(["BALANCE FINAL"])
                writer.writerow(["Balance USD", self.consolidado_balance_usd.text().replace("Balance USD: $", "")])
                writer.writerow(["Balance EUR", self.consolidado_balance_eur.text().replace("Balance EUR: €", "")])
                writer.writerow(["Balance CUP", self.consolidado_balance_cup.text().replace("Balance CUP: $", "")])
                writer.writerow(["Balance Transferencia", self.consolidado_balance_transf.text().replace("Balance Transferencia: $", "")])
                writer.writerow([])
                
                # Escribir resumen por día
                writer.writerow(["DETALLE DIARIO"])
                writer.writerow([])
                
                # Encabezados de la tabla de días
                encabezados = []
                for i in range(self.consolidado_dias_table.columnCount()):
                    encabezados.append(self.consolidado_dias_table.horizontalHeaderItem(i).text())
                writer.writerow(encabezados)
                
                # Datos diarios
                for fila in range(self.consolidado_dias_table.rowCount()):
                    datos_fila = []
                    for columna in range(self.consolidado_dias_table.columnCount()):
                        item = self.consolidado_dias_table.item(fila, columna)
                        if item is not None:
                            datos_fila.append(item.text())
                        else:
                            datos_fila.append("")
                    writer.writerow(datos_fila)
                
            QMessageBox.information(self, "Exportación Exitosa", 
                                  f"El consolidado se ha exportado correctamente a:\n{ruta_archivo}")
                                  
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", 
                               f"No se pudo exportar el consolidado:\n{str(e)}")