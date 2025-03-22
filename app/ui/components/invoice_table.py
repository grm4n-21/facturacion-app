# -*- coding: utf-8 -*-

"""
Componente para mostrar tablas de facturas personalizadas.
"""

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from app.database.models import Factura

class InvoiceTableWidget(QTableWidget):
    """Widget personalizado para mostrar tablas de facturas"""
    
    factura_seleccionada = pyqtSignal(Factura)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Configurar tabla
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["ID Orden", "Monto", "Moneda", "Equivalente (USD)", "Fecha"])
        
        # Configurar comportamiento
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(True)
        
        # Ajustar ancho de columnas
        header = self.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Conectar señales
        self.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Almacenar lista de facturas
        self.facturas = []
    
    def cargar_facturas(self, facturas):
        """
        Carga una lista de facturas en la tabla
        
        Args:
            facturas: Lista de objetos Factura
        """
        self.facturas = facturas
        
        # Limpiar tabla
        self.setRowCount(0)
        
        # Llenar tabla con datos
        for i, factura in enumerate(facturas):
            self.insertRow(i)
            
            # Crear items para cada columna
            orden_id_item = QTableWidgetItem(factura.orden_id)
            monto_item = QTableWidgetItem(f"{factura.monto:.2f}")
            moneda_item = QTableWidgetItem(factura.moneda)
            equivalente_item = QTableWidgetItem(f"{factura.monto_equivalente:.2f}")
            fecha_item = QTableWidgetItem(factura.fecha.strftime("%Y-%m-%d %H:%M"))
            
            # Configurar alineación para valores numéricos
            monto_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            equivalente_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Colorear según moneda
            if factura.moneda == "USD":
                color = QColor(240, 255, 240)  # Verde claro
            else:
                color = QColor(240, 240, 255)  # Azul claro
            
            # Aplicar color de fondo a todas las celdas de la fila
            for j in range(5):
                item = [orden_id_item, monto_item, moneda_item, equivalente_item, fecha_item][j]
                item.setBackground(color)
            
            # Almacenar el ID de la factura como datos de usuario en la primera columna
            orden_id_item.setData(Qt.ItemDataRole.UserRole, factura.id)
            
            # Añadir items a la tabla
            self.setItem(i, 0, orden_id_item)
            self.setItem(i, 1, monto_item)
            self.setItem(i, 2, moneda_item)
            self.setItem(i, 3, equivalente_item)
            self.setItem(i, 4, fecha_item)
    
    def on_selection_changed(self):
        """Maneja el cambio de selección en la tabla"""
        indices_seleccionados = self.selectedIndexes()
        
        if not indices_seleccionados:
            return
            
        # Obtener el índice de fila seleccionada (tomamos el primero)
        fila = indices_seleccionados[0].row()
        
        # Verificar que hay facturas y que el índice es válido
        if not self.facturas or fila >= len(self.facturas):
            return
            
        # Emitir señal con la factura seleccionada
        self.factura_seleccionada.emit(self.facturas[fila])
    
    def obtener_facturas(self):
        """
        Devuelve la lista de facturas cargada en la tabla
        
        Returns:
            Lista de objetos Factura
        """
        return self.facturas