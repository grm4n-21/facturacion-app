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
        
        # Configurar tabla con más columnas para incluir todos los pagos
        self.setColumnCount(9)
        self.setHorizontalHeaderLabels([
            "ID Orden", "Monto", "Moneda", "Equivalente (USD)", 
            "Pago USD", "Pago EUR", "Pago CUP", "Pago Transfer.", "Fecha"
        ])
        
        # Configurar comportamiento
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSortingEnabled(True)
        
        # Ajustar ancho de columnas
        header = self.horizontalHeader()
        
        # Establecer anchos específicos para algunas columnas
        self.setColumnWidth(0, 100)  # ID Orden
        self.setColumnWidth(1, 80)   # Monto
        self.setColumnWidth(2, 60)   # Moneda
        self.setColumnWidth(3, 120)  # Equivalente
        self.setColumnWidth(4, 80)   # Pago USD
        self.setColumnWidth(5, 80)   # Pago EUR
        self.setColumnWidth(6, 80)   # Pago CUP
        self.setColumnWidth(7, 100)  # Pago Transferencia
        self.setColumnWidth(8, 140)  # Fecha
        
        # Resto de columnas se estiran automáticamente
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        
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
            
            # Nuevos items para los diferentes tipos de pago
            pago_usd_item = QTableWidgetItem(f"{getattr(factura, 'pago_usd', 0):.2f}")
            pago_eur_item = QTableWidgetItem(f"{getattr(factura, 'pago_eur', 0):.2f}")
            pago_cup_item = QTableWidgetItem(f"{getattr(factura, 'pago_cup', 0):.2f}")
            pago_transfer_item = QTableWidgetItem(f"{getattr(factura, 'pago_transferencia', 0):.2f}")
            
            fecha_item = QTableWidgetItem(factura.fecha.strftime("%Y-%m-%d %H:%M"))
            
            # Configurar alineación para valores numéricos
            for item in [monto_item, equivalente_item, pago_usd_item, 
                         pago_eur_item, pago_cup_item, pago_transfer_item]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Esquema de colores para visualizar mejor los diferentes tipos de moneda
            base_color = QColor(245, 245, 245)  # Color base gris claro
            
            # Colorear según tipo de moneda predominante
            # Internacional (USD o EUR)
            if factura.moneda == "USD" or factura.moneda == "EUR":
                base_color = QColor(230, 255, 230)  # Verde muy claro para moneda internacional
            # Nacional (CUP)
            else:
                base_color = QColor(230, 230, 255)  # Azul muy claro para moneda nacional
            
            # Resaltado especial si hay pagos en diferentes monedas (pago mixto)
            pagos = [
                getattr(factura, 'pago_usd', 0), 
                getattr(factura, 'pago_eur', 0),
                getattr(factura, 'pago_cup', 0), 
                getattr(factura, 'pago_transferencia', 0)
            ]
            pagos_positivos = sum(1 for p in pagos if p > 0)
            
            if pagos_positivos > 1:
                base_color = QColor(255, 240, 210)  # Amarillo claro para pagos mixtos
            
            # Aplicar color de fondo a todas las celdas de la fila
            all_items = [orden_id_item, monto_item, moneda_item, equivalente_item, 
                         pago_usd_item, pago_eur_item, pago_cup_item, pago_transfer_item, fecha_item]
            
            for item in all_items:
                item.setBackground(base_color)
            
            # Resaltar valores de pago específicos que son > 0
            if getattr(factura, 'pago_usd', 0) > 0:
                pago_usd_item.setBackground(QColor(200, 255, 200))  # Verde más intenso
            
            if getattr(factura, 'pago_eur', 0) > 0:
                pago_eur_item.setBackground(QColor(200, 230, 255))  # Azul claro
            
            if getattr(factura, 'pago_cup', 0) > 0:
                pago_cup_item.setBackground(QColor(255, 220, 220))  # Rosa claro
            
            if getattr(factura, 'pago_transferencia', 0) > 0:
                pago_transfer_item.setBackground(QColor(255, 240, 180))  # Amarillo
            
            # Almacenar el ID de la factura como datos de usuario en la primera columna
            orden_id_item.setData(Qt.ItemDataRole.UserRole, factura.id)
            
            # Añadir items a la tabla
            self.setItem(i, 0, orden_id_item)      # ID Orden
            self.setItem(i, 1, monto_item)         # Monto
            self.setItem(i, 2, moneda_item)        # Moneda
            self.setItem(i, 3, equivalente_item)   # Equivalente USD
            self.setItem(i, 4, pago_usd_item)      # Pago USD
            self.setItem(i, 5, pago_eur_item)      # Pago EUR
            self.setItem(i, 6, pago_cup_item)      # Pago CUP
            self.setItem(i, 7, pago_transfer_item) # Pago Transferencia
            self.setItem(i, 8, fecha_item)         # Fecha
    
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