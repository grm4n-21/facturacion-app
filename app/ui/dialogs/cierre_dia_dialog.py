# -*- coding: utf-8 -*-

"""
Diálogo para el cierre diario de facturación.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                            QLabel, QLineEdit, QPushButton, QMessageBox,
                            QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt
import datetime

from app.services.cierre_dia import CierreDiaService
from app.services.exchange_rate import ExchangeRateService  # Añadir esta importación

class CierreDiaDialog(QDialog):
    """Diálogo para confirmar el cierre del día y verificar los montos"""
    
    def __init__(self, parent=None, exchange_service=None):  # Modificar constructor
        super().__init__(parent)
        
        self.setWindowTitle("Cierre de Día")
        self.setMinimumSize(700, 500)
        
        # Inicializar servicios
        self.cierre_service = CierreDiaService()
        self.exchange_service = exchange_service or ExchangeRateService()  # Inicializar el servicio
        
        # Variables para totales
        self.total_usd_valor = 0.0
        self.total_cup_valor = 0.0
        
        # Configurar la interfaz
        self.init_ui()
        
        # Cargar datos iniciales
        self.cargar_facturas_pendientes()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Información del cierre
        info_group = QGroupBox("Información del Cierre")
        info_layout = QVBoxLayout()
        
        # Fecha
        fecha_hoy = datetime.date.today().strftime("%d/%m/%Y")
        fecha_label = QLabel(f"Fecha: {fecha_hoy}")
        fecha_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(fecha_label)
        
        # Tabla de facturas pendientes
        self.facturas_table = QTableWidget()
        self.facturas_table.setColumnCount(7)
        self.facturas_table.setHorizontalHeaderLabels([
            "ID", "Orden", "Monto", "Moneda", "Pago USD", "Pago CUP", "Fecha"
        ])
        self.facturas_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        info_layout.addWidget(self.facturas_table)
        
        # Totales calculados
        totales_layout = QHBoxLayout()
        
        self.total_facturas = QLabel("Facturas: 0")
        self.total_usd_label = QLabel("Total USD en caja: $0.00")
        self.total_cup_label = QLabel("Total CUP en caja: $0.00")
        
        totales_layout.addWidget(self.total_facturas)
        totales_layout.addWidget(self.total_usd_label)
        totales_layout.addWidget(self.total_cup_label)
        
        info_layout.addLayout(totales_layout)
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        # Entrada de efectivo contado
        conteo_group = QGroupBox("Verificación de Efectivo Físico")
        conteo_layout = QFormLayout()
        
        # Instrucción clara
        instruccion_label = QLabel(
            "Introduzca aquí el dinero físico que ha contado en caja:"
        )
        instruccion_label.setStyleSheet("font-style: italic;")
        conteo_layout.addRow(instruccion_label)
        
        self.cup_contado_input = QLineEdit()
        self.cup_contado_input.setPlaceholderText("0.00")
        self.cup_contado_input.textChanged.connect(self.calcular_diferencias)
        
        self.usd_contado_input = QLineEdit()
        self.usd_contado_input.setPlaceholderText("0.00")
        self.usd_contado_input.textChanged.connect(self.calcular_diferencias)
        
        conteo_layout.addRow("Efectivo CUP contado:", self.cup_contado_input)
        conteo_layout.addRow("Efectivo USD contado:", self.usd_contado_input)
        
        # Diferencias
        self.diferencia_cup = QLabel("Diferencia CUP: $0.00")
        self.diferencia_usd = QLabel("Diferencia USD: $0.00")
        
        conteo_layout.addRow("", self.diferencia_cup)
        conteo_layout.addRow("", self.diferencia_usd)
        # Añadir esta sección:
# Etiqueta para mostrar posible cambio de divisas
        self.cambio_divisas_label = QLabel("")
        self.cambio_divisas_label.setVisible(False)
        conteo_layout.addRow("", self.cambio_divisas_label)

        conteo_group.setLayout(conteo_layout)
        main_layout.addWidget(conteo_group)
        
        # Botones
        botones_layout = QHBoxLayout()
                # Botones
        botones_layout = QHBoxLayout()
        
        self.cancelar_btn = QPushButton("Cancelar")
        self.cancelar_btn.clicked.connect(self.reject)
        
        self.aceptar_btn = QPushButton("Realizar Cierre")
        self.aceptar_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.aceptar_btn.clicked.connect(self.realizar_cierre)
        
        botones_layout.addWidget(self.cancelar_btn)
        botones_layout.addWidget(self.aceptar_btn)
        
        main_layout.addLayout(botones_layout)
    
    def cargar_facturas_pendientes(self):
        """Carga las facturas pendientes de cierre"""
        # Obtener facturas sin cerrar
        facturas = self.cierre_service.obtener_facturas_sin_cerrar()
        
        # Limpiar tabla
        self.facturas_table.setRowCount(0)
        
        # Variables para totales
        total_usd = 0.0
        total_cup = 0.0
        
        # Llenar tabla con datos
        for i, factura in enumerate(facturas):
            self.facturas_table.insertRow(i)
            
            # Crear items para cada columna
            id_item = QTableWidgetItem(str(factura['id']))
            orden_id_item = QTableWidgetItem(factura['orden_id'])
            monto_item = QTableWidgetItem(f"{factura['monto']:.2f}")
            moneda_item = QTableWidgetItem(factura['moneda'])
            pago_usd_item = QTableWidgetItem(f"{factura['pago_usd']:.2f}")
            pago_cup_item = QTableWidgetItem(f"{factura['pago_cup']:.2f}")
            fecha_item = QTableWidgetItem(factura['fecha'])
            
            # Alinear números a la derecha
            monto_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            pago_usd_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            pago_cup_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Añadir items a la tabla
            self.facturas_table.setItem(i, 0, id_item)
            self.facturas_table.setItem(i, 1, orden_id_item)
            self.facturas_table.setItem(i, 2, monto_item)
            self.facturas_table.setItem(i, 3, moneda_item)
            self.facturas_table.setItem(i, 4, pago_usd_item)
            self.facturas_table.setItem(i, 5, pago_cup_item)
            self.facturas_table.setItem(i, 6, fecha_item)
            
            # Actualizar totales de pagos recibidos
            total_usd += factura['pago_usd']
            total_cup += factura['pago_cup']
        
        # Almacenar totales para cálculos posteriores
        self.total_usd_valor = total_usd
        self.total_cup_valor = total_cup
        
        # Actualizar etiquetas de totales
        self.total_facturas.setText(f"Facturas: {len(facturas)}")
        self.total_usd_label.setText(f"Total USD en caja: ${total_usd:.2f}")
        self.total_cup_label.setText(f"Total CUP en caja: ${total_cup:.2f}")
        
        # Deshabilitar botón de cierre si no hay facturas
        self.aceptar_btn.setEnabled(len(facturas) > 0)
        
        if len(facturas) == 0:
            QMessageBox.information(
                self, 
                "Sin facturas pendientes",
                "No hay facturas pendientes para realizar el cierre del día."
            )

    def calcular_diferencias(self):
        """Calcula las diferencias entre lo contado y lo registrado y detecta posibles cambios de divisa"""
        try:
            # Obtener valores contados
            cup_contado = float(self.cup_contado_input.text() or 0)
            usd_contado = float(self.usd_contado_input.text() or 0)
            
            # Calcular diferencias individuales
            diferencia_cup = cup_contado - self.total_cup_valor
            diferencia_usd = usd_contado - self.total_usd_valor
            
            # Obtener tasa de cambio actual
            tasa = self.exchange_service.obtener_tasa_actual()
            
            # Verificar si es un posible cambio de divisas
            es_cambio_divisas = False
            mensaje_cambio = ""
            
            # Caso 1: Falta USD pero sobra el equivalente en CUP (alguien cambió USD por CUP)
            if diferencia_usd < -0.01 and diferencia_cup > 0:
                # Convertir la diferencia de USD a CUP para ver si coincide
                equivalente_cup = abs(diferencia_usd) * tasa
                if abs(equivalente_cup - diferencia_cup) / equivalente_cup < 0.05:  # 5% de tolerancia
                    es_cambio_divisas = True
                    mensaje_cambio = (f"✓ Posible cambio de {abs(diferencia_usd):.2f} USD a "
                                    f"{diferencia_cup:.2f} CUP (tasa aprox: {diferencia_cup/abs(diferencia_usd):.2f})")
            
            # Caso 2: Falta CUP pero sobra el equivalente en USD (alguien cambió CUP por USD)
            elif diferencia_cup < -0.01 and diferencia_usd > 0:
                # Convertir la diferencia de CUP a USD para ver si coincide
                equivalente_usd = abs(diferencia_cup) / tasa
                if abs(equivalente_usd - diferencia_usd) / equivalente_usd < 0.05:  # 5% de tolerancia
                    es_cambio_divisas = True
                    mensaje_cambio = (f"✓ Posible cambio de {abs(diferencia_cup):.2f} CUP a "
                                    f"{diferencia_usd:.2f} USD (tasa aprox: {abs(diferencia_cup)/diferencia_usd:.2f})")
            
            # Actualizar etiquetas con colores apropiados
            # Para diferencia CUP
            if abs(diferencia_cup) < 0.01:  # Casi exacto (por redondeo)
                self.diferencia_cup.setText(f"Diferencia CUP: $0.00 ✓")
                self.diferencia_cup.setStyleSheet("color: green; font-weight: bold;")
            elif diferencia_cup > 0:
                self.diferencia_cup.setText(f"Diferencia CUP: +${diferencia_cup:.2f} (Sobra)")
                self.diferencia_cup.setStyleSheet("color: blue;")
            else:
                self.diferencia_cup.setText(f"Diferencia CUP: -${abs(diferencia_cup):.2f} (Falta)")
                self.diferencia_cup.setStyleSheet("color: red;")
            
            # Para diferencia USD
            if abs(diferencia_usd) < 0.01:  # Casi exacto (por redondeo)
                self.diferencia_usd.setText(f"Diferencia USD: $0.00 ✓")
                self.diferencia_usd.setStyleSheet("color: green; font-weight: bold;")
            elif diferencia_usd > 0:
                self.diferencia_usd.setText(f"Diferencia USD: +${diferencia_usd:.2f} (Sobra)")
                self.diferencia_usd.setStyleSheet("color: blue;")
            else:
                self.diferencia_usd.setText(f"Diferencia USD: -${abs(diferencia_usd):.2f} (Falta)")
                self.diferencia_usd.setStyleSheet("color: red;")
            
            # Mostrar información sobre posible cambio de divisas
            if es_cambio_divisas:
                self.cambio_divisas_label.setText(mensaje_cambio)
                self.cambio_divisas_label.setStyleSheet("color: green; font-weight: bold; margin-top: 5px;")
                self.cambio_divisas_label.setVisible(True)
            else:
                self.cambio_divisas_label.setVisible(False)
                
        except ValueError:
            # Si hay un error en la conversión, mostrar mensaje
            self.diferencia_cup.setText("Diferencia CUP: Error en valor")
            self.diferencia_cup.setStyleSheet("color: red;")
            self.diferencia_usd.setText("Diferencia USD: Error en valor")
            self.diferencia_usd.setStyleSheet("color: red;")
            self.cambio_divisas_label.setVisible(False)

    def realizar_cierre(self):
        """Realiza el cierre del día con la verificación de efectivo"""
        try:
            # Obtener valores contados
            cup_contado = float(self.cup_contado_input.text() or 0)
            usd_contado = float(self.usd_contado_input.text() or 0)
            
            # Calcular diferencias para el mensaje
            diferencia_cup = cup_contado - self.total_cup_valor
            diferencia_usd = usd_contado - self.total_usd_valor
            
            # Obtener tasa de cambio actual
            tasa = self.exchange_service.obtener_tasa_actual()
            
            # Verificar si es un posible cambio de divisas
            es_cambio_divisas = False
            mensaje_cambio = ""
            
            # Caso 1: Falta USD pero sobra el equivalente en CUP
            if diferencia_usd < -0.01 and diferencia_cup > 0:
                equivalente_cup = abs(diferencia_usd) * tasa
                if abs(equivalente_cup - diferencia_cup) / equivalente_cup < 0.05:  # 5% de tolerancia
                    es_cambio_divisas = True
                    mensaje_cambio = f"\n\n✓ Posible cambio de {abs(diferencia_usd):.2f} USD a {diferencia_cup:.2f} CUP"
            
            # Caso 2: Falta CUP pero sobra el equivalente en USD
            elif diferencia_cup < -0.01 and diferencia_usd > 0:
                equivalente_usd = abs(diferencia_cup) / tasa
                if abs(equivalente_usd - diferencia_usd) / equivalente_usd < 0.05:  # 5% de tolerancia
                    es_cambio_divisas = True
                    mensaje_cambio = f"\n\n✓ Posible cambio de {abs(diferencia_cup):.2f} CUP a {diferencia_usd:.2f} USD"
            
            # Mensaje según situación
            mensaje_diferencia = ""
            if (diferencia_cup < 0 or diferencia_usd < 0) and not es_cambio_divisas:
                mensaje_diferencia = "\n\n⚠️ ADVERTENCIA: Hay una FALTA de dinero en caja. ⚠️"
            elif (diferencia_cup > 0 or diferencia_usd > 0) and not es_cambio_divisas:
                mensaje_diferencia = "\n\nNota: Hay un sobrante de dinero en caja."
            
            # Confirmar antes de proceder
            respuesta = QMessageBox.question(
                self,
                "Confirmar Cierre",
                f"¿Está seguro de realizar el cierre con los siguientes valores?\n\n"
                f"💵 Efectivo CUP contado: ${cup_contado:.2f}\n"
                f"💵 Efectivo USD contado: ${usd_contado:.2f}\n\n"
                f"📊 Total CUP registrado: ${self.total_cup_valor:.2f}\n"
                f"📊 Total USD registrado: ${self.total_usd_valor:.2f}\n\n"
                f"🔄 Diferencia CUP: ${diferencia_cup:.2f}\n"
                f"🔄 Diferencia USD: ${diferencia_usd:.2f}"
                f"{mensaje_cambio}{mensaje_diferencia}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if respuesta == QMessageBox.StandardButton.Yes:
                # Realizar cierre
                resultado = self.cierre_service.realizar_cierre_dia(usd_contado, cup_contado)
                
                if resultado['success']:
                    # Mensaje personalizado según si hay cambio de divisas
                    mensaje_exito = (
                        f"✅ El cierre del día se ha realizado correctamente.\n\n"
                        f"🧾 ID de cierre: {resultado['cierre_id']}\n"
                        f"📝 Facturas cerradas: {resultado['num_facturas']}\n\n"
                        f"💰 Total USD: ${resultado['total_usd']:.2f}\n"
                        f"💰 Total CUP: ${resultado['total_cup']:.2f}\n\n"
                        f"🔍 Diferencia USD: ${resultado['diferencia_usd']:.2f}\n"
                        f"🔍 Diferencia CUP: ${resultado['diferencia_cup']:.2f}"
                    )
                    
                    if es_cambio_divisas:
                        mensaje_exito += f"\n\n{mensaje_cambio}"
                    
                    QMessageBox.information(
                        self,
                        "Cierre Exitoso",
                        mensaje_exito
                    )
                    self.accept()  # Cerrar el diálogo
                else:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"❌ No se pudo realizar el cierre: {resultado['message']}"
                    )
                    
        except ValueError:
            QMessageBox.warning(
                self,
                "Error",
                "Por favor, ingrese valores numéricos válidos para los montos contados."
            )