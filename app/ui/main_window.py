# -*- coding: utf-8 -*-

"""
Ventana principal de la aplicación.
Define la estructura general de la interfaz gráfica.
"""

from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                             QMenuBar, QMenu, QToolBar, QStatusBar, QMessageBox,
                             QLabel)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QSize, QTimer, QTime, QDate  # QDate se importa desde PyQt6.QtCore

from app.ui.editar_factura_tab import EditarFacturaTab
from app.ui.facturacion_tab import FacturacionTab
from app.ui.reportes_tab import ReportesTab
from app.ui.salidas_tab import SalidasTab
from app.ui.cierre_dia_tab import CierreDiaTab  # Importar la nueva pestaña
from app.services.exchange_rate import ExchangeRateService
from app.services.cierre_dia import CierreDiaService
from app.services.salidas_service import SalidasService

class MainWindow(QMainWindow):
    """Ventana principal de la aplicación de facturación"""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar servicios
        self.exchange_service = ExchangeRateService()
        self.cierre_service = CierreDiaService()
        self.salidas_service = SalidasService()  # Inicializar servicio de Salidas
        
        # Configurar la ventana
        self.setWindowTitle("Sistema de Facturación")
        self.setMinimumSize(1000, 600)
        
        # Crear el widget central con pestañas
        self.tabs = QTabWidget()
        
        # Crear las pestañas principales
        self.facturacion_tab = FacturacionTab(self.exchange_service)
        self.salidas_tab = SalidasTab(self.exchange_service)  # Crear pestaña de Salidas
        self.editar_factura_tab = EditarFacturaTab(self.exchange_service)  # Crear pestaña de Edición de Facturas
        self.cierre_tab = CierreDiaTab(self.exchange_service)  # Crear pestaña de Cierre de Día
        self.reportes_tab = ReportesTab()
        
        # Añadir pestañas al widget de pestañas
        self.tabs.addTab(self.facturacion_tab, "Facturación")
        self.tabs.addTab(self.salidas_tab, "Salidas de Caja")  # Añadir pestaña de Salidas
        self.tabs.addTab(self.editar_factura_tab, "Editar Factura")  # Añadir pestaña de Edición
        self.tabs.addTab(self.cierre_tab, "Cierre de Día")  # Añadir pestaña de Cierre
        self.tabs.addTab(self.reportes_tab, "Reportes")
        
        # Establecer el widget central
        self.setCentralWidget(self.tabs)
        
        # Configurar el menú
        self.crear_menu()
        
        # Configurar la barra de herramientas
        self.crear_toolbar()
        
        # Configurar la barra de estado con fecha actual
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)

        # Agregar fecha actual a la barra de estado
        fecha_actual = datetime.date.today().strftime("%d/%m/%Y")
        self.fecha_label = QLabel(f"Fecha: {fecha_actual}")
        self.statusBar.addPermanentWidget(self.fecha_label)
        self.statusBar.showMessage("Listo")
        
        # Verificar si es un nuevo día
        self.verificar_nuevo_dia()
        
        # Configurar temporizador para actualizar la fecha
        self.fecha_timer = QTimer(self)
        self.fecha_timer.timeout.connect(self.actualizar_fecha)
        # Calcular milisegundos hasta medianoche
        tiempo_actual = QTime.currentTime()
        tiempo_hasta_medianoche = QTime(23, 59, 59).msecsSinceStartOfDay() - tiempo_actual.msecsSinceStartOfDay() + 1000
        self.fecha_timer.start(tiempo_hasta_medianoche)
    
    def crear_menu(self):
        """Crea la barra de menú y sus acciones"""
        menubar = self.menuBar()
        
        # Menú Archivo
        menu_archivo = menubar.addMenu('&Archivo')
        
        # Acción: Actualizar tasa de cambio
        accion_tasa = QAction('&Actualizar Tasa de Cambio', self)
        accion_tasa.setStatusTip('Actualizar la tasa de cambio USD a CUP')
        accion_tasa.triggered.connect(self.actualizar_tasa_cambio)
        menu_archivo.addAction(accion_tasa)
        
        menu_archivo.addSeparator()

        # Acción: Editar factura
        accion_editar = QAction('&Editar Factura', self)
        accion_editar.setStatusTip('Modificar medios de pago de una factura existente')
        accion_editar.triggered.connect(self.abrir_editar_factura)
        menu_archivo.addAction(accion_editar)
        
        # Acción: Registrar Salida
        accion_salida = QAction('&Registrar Salida de Caja', self)
        accion_salida.setStatusTip('Registrar una nueva salida de dinero')
        accion_salida.triggered.connect(self.registrar_salida)
        menu_archivo.addAction(accion_salida)
        
        menu_archivo.addSeparator()
        
        # Acción: Cierre de día
        accion_cierre = QAction('&Realizar Cierre de Día', self)
        accion_cierre.setStatusTip('Cerrar la facturación del día actual')
        accion_cierre.triggered.connect(self.realizar_cierre_dia)
        menu_archivo.addAction(accion_cierre)
        
        menu_archivo.addSeparator()
        
        # Acción: Salir
        accion_salir = QAction('&Salir', self)
        accion_salir.setShortcut('Ctrl+Q')
        accion_salir.setStatusTip('Salir de la aplicación')
        accion_salir.triggered.connect(self.close)
        menu_archivo.addAction(accion_salir)
        
        # Menú Reportes
        menu_reportes = menubar.addMenu('&Reportes')
        
        # Acción: Exportar a CSV
        accion_exportar = QAction('&Exportar a CSV', self)
        accion_exportar.setStatusTip('Exportar reporte a archivo CSV')
        accion_exportar.triggered.connect(self.exportar_a_csv)
        menu_reportes.addAction(accion_exportar)
        
        # Acción: Exportar Salidas
        accion_exportar_salidas = QAction('&Exportar Salidas', self)
        accion_exportar_salidas.setStatusTip('Exportar reporte de salidas de caja')
        accion_exportar_salidas.triggered.connect(self.exportar_salidas)
        menu_reportes.addAction(accion_exportar_salidas)
        
        # Acción: Ver historial de cierres
        accion_historial = QAction('&Historial de Cierres', self)
        accion_historial.setStatusTip('Ver historial de cierres diarios')
        accion_historial.triggered.connect(self.ver_historial_cierres)
        menu_reportes.addAction(accion_historial)
        
        # Menú Ayuda
        menu_ayuda = menubar.addMenu('&Ayuda')
        
        # Acción: Acerca de
        accion_acerca = QAction('&Acerca de', self)
        accion_acerca.setStatusTip('Mostrar información sobre la aplicación')
        accion_acerca.triggered.connect(self.mostrar_acerca_de)
        menu_ayuda.addAction(accion_acerca)
    
    def crear_toolbar(self):
        """Crea la barra de herramientas con acciones comunes"""
        toolbar = QToolBar("Barra de herramientas principal")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        
        # Acción: Escanear
        accion_escanear = QAction('Escanear', self)
        accion_escanear.setStatusTip('Escanear código de una orden')
        accion_escanear.triggered.connect(self.escanear_codigo)
        toolbar.addAction(accion_escanear)
        
        # Acción: Registrar Salida
        accion_salida = QAction('Registrar Salida', self)
        accion_salida.setStatusTip('Registrar una salida de caja')
        accion_salida.triggered.connect(self.registrar_salida)
        toolbar.addAction(accion_salida)
        
        # Acción: Actualizar tasa
        accion_tasa = QAction('Actualizar Tasa', self)
        accion_tasa.setStatusTip('Actualizar tasa de cambio')
        accion_tasa.triggered.connect(self.actualizar_tasa_cambio)
        toolbar.addAction(accion_tasa)
        
        # Acción: Cierre de día
        accion_cierre = QAction('Cierre de Día', self)
        accion_cierre.setStatusTip('Realizar cierre del día actual')
        accion_cierre.triggered.connect(self.realizar_cierre_dia)
        toolbar.addAction(accion_cierre)

    def abrir_editar_factura(self):
        """Cambia a la pestaña de edición de facturas"""
        # Obtener el índice de la pestaña de edición de facturas
        indice_editar = self.tabs.indexOf(self.editar_factura_tab)
        if indice_editar >= 0:
            self.tabs.setCurrentIndex(indice_editar)
    
    def verificar_nuevo_dia(self):
        """Verifica si es un nuevo día y sugiere realizar el cierre del día anterior"""
        hay_cierre, ultimo_cierre = self.cierre_service.verificar_dia_actual()
        
        # Si no hay cierre para hoy y hay un último cierre (de otro día)
        if not hay_cierre and ultimo_cierre:
            fecha_hoy = datetime.date.today().isoformat()
            
            # Si el último cierre no es de ayer, significa que hay días sin cerrar
            fecha_ultimo = datetime.date.fromisoformat(ultimo_cierre)
            fecha_ayer = datetime.date.today() - datetime.timedelta(days=1)
            
            if fecha_ultimo < fecha_ayer:
                # Hay días sin cerrar
                dias_sin_cerrar = (fecha_hoy - ultimo_cierre).days
                QMessageBox.warning(
                    self,
                    "Días sin cerrar",
                    f"Se han detectado {dias_sin_cerrar} días sin realizar cierre "
                    f"desde el último cierre ({ultimo_cierre}).\n\n"
                    "Se recomienda realizar un cierre de día para mantener "
                    "la contabilidad ordenada."
                )
            elif self.cierre_service.obtener_facturas_sin_cerrar():
                # Hay facturas sin cerrar del día anterior
                QMessageBox.information(
                    self,
                    "Nuevo Día",
                    "Bienvenido a un nuevo día.\n\n"
                    "Hay facturas pendientes del día anterior. "
                    "¿Desea realizar el cierre del día anterior ahora?"
                )
    
    def actualizar_fecha(self):
        """Actualiza la etiqueta de fecha cuando cambia el día"""
        fecha_actual = datetime.date.today().strftime("%d/%m/%Y")
        self.fecha_label.setText(f"Fecha: {fecha_actual}")
        
        # Reiniciar el temporizador para la próxima medianoche
        self.fecha_timer.stop()
        tiempo_hasta_medianoche = 24 * 60 * 60 * 1000  # 24 horas en milisegundos
        self.fecha_timer.start(tiempo_hasta_medianoche)
        
        # Verificar si es un nuevo día
        self.verificar_nuevo_dia()
    
    def actualizar_tasa_cambio(self):
        """Muestra diálogo para actualizar la tasa de cambio"""
        self.facturacion_tab.mostrar_dialogo_tasa()
    
    def escanear_codigo(self):
        """Inicia el proceso de escaneo de código de barras"""
        self.tabs.setCurrentIndex(0)  # Cambiar a la pestaña de facturación
        self.facturacion_tab.iniciar_escaneo()
    
    def registrar_salida(self):
        """Abre la pestaña de salidas para registrar una nueva salida"""
        self.tabs.setCurrentIndex(1)  # Cambiar a la pestaña de salidas
        # Dar foco al primer campo de la pestaña de salidas
        if hasattr(self.salidas_tab, 'destinatario_input'):
            self.salidas_tab.destinatario_input.setFocus()
    
    def exportar_a_csv(self):
        """Exporta el reporte actual a un archivo CSV"""
        self.tabs.setCurrentIndex(2)  # Cambiar a la pestaña de reportes
        self.reportes_tab.exportar_csv()
    
    def exportar_salidas(self):
        """Exporta las salidas de caja a un archivo CSV"""
        # Diálogo para seleccionar fechas
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QDateEdit, QPushButton, QLabel
        
        dialogo = QDialog(self)
        dialogo.setWindowTitle("Exportar Salidas de Caja")
        layout = QVBoxLayout()
        
        # Fechas
        fechas_layout = QHBoxLayout()
        fechas_layout.addWidget(QLabel("Desde:"))
        desde_date = QDateEdit()
        desde_date.setDate(datetime.date.today().replace(day=1))  # Primer día del mes
        desde_date.setCalendarPopup(True)
        fechas_layout.addWidget(desde_date)
        
        fechas_layout.addWidget(QLabel("Hasta:"))
        hasta_date = QDateEdit()
        hasta_date.setDate(datetime.date.today())  # Hoy
        hasta_date.setCalendarPopup(True)
        fechas_layout.addWidget(hasta_date)
        
        layout.addLayout(fechas_layout)
        
        # Botones
        botones_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(dialogo.reject)
        botones_layout.addWidget(btn_cancelar)
        
        btn_exportar = QPushButton("Exportar")
        btn_exportar.clicked.connect(dialogo.accept)
        botones_layout.addWidget(btn_exportar)
        
        layout.addLayout(botones_layout)
        
        dialogo.setLayout(layout)
        
        if dialogo.exec():
            # Si se aceptó, exportar las salidas
            fecha_inicio = desde_date.date().toString("yyyy-MM-dd")
            fecha_fin = hasta_date.date().toString("yyyy-MM-dd")
            
            ruta_archivo = self.salidas_tab.exportar_salidas(fecha_inicio, fecha_fin)
            
            if ruta_archivo:
                QMessageBox.information(
                    self,
                    "Exportación exitosa",
                    f"Se ha exportado el reporte de salidas a:\n{ruta_archivo}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Error en exportación",
                    "No se pudo exportar el reporte de salidas."
                )
    
    def realizar_cierre_dia(self):
        """Muestra la pestaña de cierre de día para realizar el cierre"""
        # Cambiar a la pestaña de cierre
        self.tabs.setCurrentWidget(self.cierre_tab)
        
        # Mostrar un mensaje indicando las instrucciones para el cierre
        QMessageBox.information(
            self,
            "Cierre de Día",
            "Para realizar el cierre del día, por favor:\n"
            "1. Seleccione la fecha del cierre que desea realizar.\n"
            "2. Verifique las entradas y salidas de la fecha seleccionada.\n"
            "3. Cuente los billetes de cada denominación en USD, EUR, y CUP.\n"
            "4. Compare los totales contados con el saldo esperado.\n"
            "5. Haga clic en 'REALIZAR CIERRE DE DÍA' para registrar el cierre."
        )
        
        # Actualizar la pestaña de cierre para la fecha de hoy por defecto
        self.cierre_tab.fecha_selector.setDate(QDate.currentDate())
        self.cierre_tab.actualizar_resumen()
        
    def ver_historial_cierres(self):
            """Muestra el historial de cierres de día"""
            self.tabs.setCurrentIndex(2)  # Cambiar a la pestaña de reportes
            
            # Si la pestaña de reportes tiene pestañas internas, seleccionar la de cierres
            if hasattr(self.reportes_tab, 'tabs') and self.reportes_tab.tabs.count() > 1:
                self.reportes_tab.tabs.setCurrentIndex(1)  # Seleccionar pestaña de cierres
        
    def mostrar_acerca_de(self):
            """Muestra información sobre la aplicación"""
            QMessageBox.about(self, "Acerca de", 
                            "Sistema de Facturación v1.0\n\n"
                            "Aplicación para gestionar facturas con escáner de códigos\n"
                            "y soporte para múltiples monedas (USD, EUR y CUP).\n\n"
                            "Incluye funcionalidad de cierre diario y control de salidas\n"
                            "para mantener un registro ordenado de las operaciones de caja.")