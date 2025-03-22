# -*- coding: utf-8 -*-

"""
Pestaña de reportes de la aplicación.
Gestiona la visualización y exportación de reportes de facturación.
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
                             QLabel, QLineEdit, QPushButton, QDateEdit,
                             QTableWidget, QTableWidgetItem, QGroupBox,
                             QMessageBox, QFileDialog, QHeaderView, QTabWidget,
                             QComboBox)
from PyQt6.QtCore import Qt, QDate
import datetime
import csv
import os

from app.services.facturacion import FacturacionService
from app.services.cierre_dia import CierreDiaService

class ReportesTab(QWidget):
    """Pestaña para la visualización y exportación de reportes"""
    
    def __init__(self):
        super().__init__()
        
        # Inicializar servicios
        self.facturacion_service = FacturacionService()
        self.cierre_service = CierreDiaService()
        
        # Configurar la interfaz
        self.init_ui()
        
        
        self.cargar_cierres_dia()

    def __init__(self):
        super().__init__()
        
        # Inicializar servicios
        self.facturacion_service = FacturacionService()
        
        # Configurar la interfaz
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Grupo: Filtros de reporte
        filtros_group = QGroupBox("Filtros de Reporte")
        filtros_layout = QHBoxLayout()
        
        # Fechas
        fecha_layout = QFormLayout()
        
        hoy = QDate.currentDate()
        
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDate(hoy.addDays(-30))  # Último mes por defecto
        self.fecha_inicio.setCalendarPopup(True)
        fecha_layout.addRow("Desde:", self.fecha_inicio)
        
        self.fecha_fin = QDateEdit()
        self.fecha_fin.setDate(hoy)
        self.fecha_fin.setCalendarPopup(True)
        fecha_layout.addRow("Hasta:", self.fecha_fin)
        
        filtros_layout.addLayout(fecha_layout)
        
        # Botones
        botones_layout = QVBoxLayout()
        
        self.generar_btn = QPushButton("Generar Reporte")
        self.generar_btn.clicked.connect(self.generar_reporte)
        botones_layout.addWidget(self.generar_btn)
        
        self.exportar_btn = QPushButton("Exportar a CSV")
        self.exportar_btn.clicked.connect(self.exportar_csv)
        botones_layout.addWidget(self.exportar_btn)
        
        filtros_layout.addLayout(botones_layout)
        filtros_group.setLayout(filtros_layout)
        
        # Tabla de reporte
        self.reporte_table = QTableWidget()
        self.reporte_table.setColumnCount(5)
        self.reporte_table.setHorizontalHeaderLabels(["ID Orden", "Monto", "Moneda", "Equivalente (USD)", "Fecha"])
        self.reporte_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Panel de totales
        totales_group = QGroupBox("Resumen")
        totales_layout = QHBoxLayout()
        
        self.total_facturas = QLabel("Facturas: 0")
        self.total_usd = QLabel("Total USD: $0.00")
        self.total_cup = QLabel("Total CUP: $0.00")
        
        totales_layout.addWidget(self.total_facturas)
        totales_layout.addWidget(self.total_usd)
        totales_layout.addWidget(self.total_cup)
        
        totales_group.setLayout(totales_layout)
        
        # Añadir todo al layout principal
        main_layout.addWidget(filtros_group)
        main_layout.addWidget(self.reporte_table)
        main_layout.addWidget(totales_group)
    
    def generar_reporte(self):
        """Genera un reporte según los filtros seleccionados"""
        # Obtener fechas
        fecha_inicio = self.fecha_inicio.date().toString("yyyy-MM-dd")
        fecha_fin = self.fecha_fin.date().toString("yyyy-MM-dd")
        
        # Validar fechas
        if self.fecha_inicio.date() > self.fecha_fin.date():
            QMessageBox.warning(self, "Error", "La fecha de inicio debe ser anterior a la fecha final")
            return
        
        # Obtener facturas filtradas
        facturas = self.facturacion_service.obtener_facturas_por_fecha(fecha_inicio, fecha_fin)
        
        # Limpiar tabla
        self.reporte_table.setRowCount(0)
        
        # Variables para totales
        total_usd = 0.0
        total_cup = 0.0
        
        # Llenar tabla con datos
        for i, factura in enumerate(facturas):
            self.reporte_table.insertRow(i)
            
            # Crear items para cada columna
            orden_id_item = QTableWidgetItem(factura.orden_id)
            monto_item = QTableWidgetItem(f"{factura.monto:.2f}")
            moneda_item = QTableWidgetItem(factura.moneda)
            equivalente_item = QTableWidgetItem(f"{factura.monto_equivalente:.2f}")
            fecha_item = QTableWidgetItem(factura.fecha.strftime("%Y-%m-%d %H:%M"))
            
            # Añadir items a la tabla
            self.reporte_table.setItem(i, 0, orden_id_item)
            self.reporte_table.setItem(i, 1, monto_item)
            self.reporte_table.setItem(i, 2, moneda_item)
            self.reporte_table.setItem(i, 3, equivalente_item)
            self.reporte_table.setItem(i, 4, fecha_item)
            
            # Actualizar totales
            if factura.moneda == "USD":
                total_usd += factura.monto
                total_cup += factura.monto * self.facturacion_service.obtener_tasa_cambio()
            else:  # CUP
                total_cup += factura.monto
                total_usd += factura.monto_equivalente
        
        # Actualizar etiquetas de totales
        self.total_facturas.setText(f"Facturas: {len(facturas)}")
        self.total_usd.setText(f"Total USD: ${total_usd:.2f}")
        self.total_cup.setText(f"Total CUP: ${total_cup:.2f}")
        
        # Mensaje de finalización
        if len(facturas) == 0:
            QMessageBox.information(self, "Reporte", "No se encontraron facturas en el rango de fechas seleccionado")
        else:
            QMessageBox.information(self, "Reporte", f"Se han encontrado {len(facturas)} facturas")
    
    def exportar_csv(self):
        """Exporta el reporte actual a un archivo CSV"""
        # Verificar si hay datos para exportar
        if self.reporte_table.rowCount() == 0:
            QMessageBox.warning(self, "Error", "No hay datos para exportar. Genere un reporte primero.")
            return
        
        # Solicitar ubicación para guardar el archivo
        fecha_inicio = self.fecha_inicio.date().toString("yyyyMMdd")
        fecha_fin = self.fecha_fin.date().toString("yyyyMMdd")
        nombre_default = f"reporte_facturacion_{fecha_inicio}_{fecha_fin}.csv"
        
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
                for i in range(self.reporte_table.columnCount()):
                    encabezados.append(self.reporte_table.horizontalHeaderItem(i).text())
                writer.writerow(encabezados)
                
                # Escribir datos
                for fila in range(self.reporte_table.rowCount()):
                    datos_fila = []
                    for columna in range(self.reporte_table.columnCount()):
                        item = self.reporte_table.item(fila, columna)
                        if item is not None:
                            datos_fila.append(item.text())
                        else:
                            datos_fila.append("")
                    writer.writerow(datos_fila)
                
                # Escribir totales
                writer.writerow([])  # Línea en blanco
                writer.writerow(["Resumen", "", "", "", ""])
                writer.writerow(["Total Facturas", self.total_facturas.text().replace("Facturas: ", ""), "", "", ""])
                writer.writerow(["Total USD", self.total_usd.text().replace("Total USD: $", ""), "", "", ""])
                writer.writerow(["Total CUP", self.total_cup.text().replace("Total CUP: $", ""), "", "", ""])
                
            QMessageBox.information(self, "Exportación Exitosa", 
                                  f"El reporte se ha exportado correctamente a:\n{ruta_archivo}")
                                  
        except Exception as e:
            QMessageBox.critical(self, "Error de Exportación", 
                               f"No se pudo exportar el reporte:\n{str(e)}")