# -*- coding: utf-8 -*-

"""
Pestaña de edición de facturas. 
Permite modificar los medios de pago de facturas existentes que no estén cerradas.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
                            QLabel, QLineEdit, QPushButton, QGroupBox,
                            QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
                            QSplitter,QScrollArea,QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QRegularExpressionValidator, QColor
from datetime import datetime, date, timedelta

from app.database.models import Factura
from app.services.facturacion import FacturacionService
from app.services.exchange_rate import ExchangeRateService

class EditarFacturaTab(QWidget):
    """Pestaña para editar medios de pago de facturas existentes"""
    
    def __init__(self, exchange_service):
        super().__init__()
        
        # Inicializar servicios
        self.exchange_service = exchange_service
        self.facturacion_service = FacturacionService()
        
        # Factura actual
        self.factura_actual = None
        
        # Configurar la interfaz
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        
        # Título
        titulo_label = QLabel("Modificar Facturas")
        titulo_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo_label)
        
        # Crear un área de desplazamiento (scroll area)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Widget contenedor para el contenido que tendrá scroll
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        # Sección de búsqueda de factura
        busqueda_group = QGroupBox("Buscar Factura")
        busqueda_layout = QHBoxLayout()
        
        self.id_factura_input = QLineEdit()
        self.id_factura_input.setPlaceholderText("ID de la factura o ID de orden")
        busqueda_layout.addWidget(self.id_factura_input)
        
        buscar_btn = QPushButton("Buscar")
        buscar_btn.clicked.connect(self.buscar_factura)
        busqueda_layout.addWidget(buscar_btn)
        
        busqueda_group.setLayout(busqueda_layout)
        scroll_layout.addWidget(busqueda_group)
        
        # Crear un splitter para dividir la pantalla
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Sección de detalles de la factura
        detalles_group = QGroupBox("Detalles de la Factura")
        detalles_layout = QFormLayout()
        
        self.orden_id_label = QLabel("--")
        detalles_layout.addRow("ID de Orden:", self.orden_id_label)
        
        self.monto_label = QLabel("--")
        detalles_layout.addRow("Monto:", self.monto_label)
        
        self.moneda_label = QLabel("--")
        detalles_layout.addRow("Moneda:", self.moneda_label)
        
        self.fecha_label = QLabel("--")
        detalles_layout.addRow("Fecha:", self.fecha_label)
        
        self.estado_label = QLabel("--")
        detalles_layout.addRow("Estado:", self.estado_label)
        
        detalles_group.setLayout(detalles_layout)
        splitter.addWidget(detalles_group)
        
        # Sección de edición de medios de pago
        edicion_group = QGroupBox("Medios de Pago")
        edicion_layout = QFormLayout()
        
        # Campos para cada tipo de pago
        self.pago_usd_input = QLineEdit()
        self.pago_usd_input.setPlaceholderText("0.00")
        self.pago_usd_input.setValidator(QDoubleValidator(0, 999999.99, 2))
        self.pago_usd_input.textChanged.connect(self.verificar_balance)
        self.pago_usd_input.setStyleSheet("QLineEdit:disabled { color: #333333; }")
        edicion_layout.addRow("USD:", self.pago_usd_input)
        
        self.pago_eur_input = QLineEdit()
        self.pago_eur_input.setPlaceholderText("0.00")
        self.pago_eur_input.setValidator(QDoubleValidator(0, 999999.99, 2))
        self.pago_eur_input.textChanged.connect(self.verificar_balance)
        self.pago_eur_input.setStyleSheet("QLineEdit:disabled { color: #333333; }")
        edicion_layout.addRow("EUR:", self.pago_eur_input)
        
        self.pago_cup_input = QLineEdit()
        self.pago_cup_input.setPlaceholderText("0.00")
        self.pago_cup_input.setValidator(QDoubleValidator(0, 999999.99, 2))
        self.pago_cup_input.textChanged.connect(self.verificar_balance)
        self.pago_cup_input.setStyleSheet("QLineEdit:disabled { color: #333333; }")
        edicion_layout.addRow("CUP:", self.pago_cup_input)
        
        # Campo para transferencia
        from PyQt6.QtCore import QRegularExpression
        self.pago_transferencia_input = QLineEdit()
        self.pago_transferencia_input.setPlaceholderText("0.00")
        
        # Validador para números grandes
        regex = QRegularExpression("^[0-9]*\\.?[0-9]{0,2}$")
        validator = QRegularExpressionValidator(regex)
        self.pago_transferencia_input.setValidator(validator)
        self.pago_transferencia_input.textChanged.connect(self.verificar_balance)
        self.pago_transferencia_input.setStyleSheet("QLineEdit:disabled { color: #333333; }")
        edicion_layout.addRow("Transferencia:", self.pago_transferencia_input)
        
        # Campo para ID de transferencia
        self.transferencia_id_input = QLineEdit()
        self.transferencia_id_input.setPlaceholderText("ID o referencia de la transferencia")
        self.pago_transferencia_input.textChanged.connect(self.actualizar_campo_id_transferencia)
        self.transferencia_id_input.setStyleSheet("QLineEdit:disabled { color: #333333; }")
        edicion_layout.addRow("ID Transferencia:", self.transferencia_id_input)
        
        # Etiqueta para mostrar balance
        self.balance_label = QLabel("Balance: --")
        self.balance_label.setStyleSheet("font-weight: bold;")
        edicion_layout.addRow("", self.balance_label)
        
        # Mensaje de edición
        self.mensaje_edicion_label = QLabel("")
        self.mensaje_edicion_label.setStyleSheet("font-style: italic;")
        edicion_layout.addRow("", self.mensaje_edicion_label)
        
        edicion_group.setLayout(edicion_layout)
        splitter.addWidget(edicion_group)
        
        # Botones de acción
        botones_layout = QHBoxLayout()
        
        self.limpiar_btn = QPushButton("Limpiar")
        self.limpiar_btn.clicked.connect(self.limpiar_campos)
        botones_layout.addWidget(self.limpiar_btn)
        
        botones_layout.addStretch()
        
        self.actualizar_btn = QPushButton("Actualizar Factura")
        self.actualizar_btn.setStyleSheet("""
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
            QPushButton:disabled {
                background-color: #CCCCCC;
                color: #666666;
            }
        """)
        self.actualizar_btn.setEnabled(False)
        self.actualizar_btn.clicked.connect(self.actualizar_factura)
        botones_layout.addWidget(self.actualizar_btn)
        
        # Añadir el splitter y los botones al layout del scroll
        scroll_layout.addWidget(splitter)
        scroll_layout.addLayout(botones_layout)
        
        # Configurar el widget de scroll
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area, 1)
        
        # Tabla de facturas recientes
        self.facturas_table = QTableWidget()
        self.facturas_table.setColumnCount(9)
        self.facturas_table.setHorizontalHeaderLabels([
            "ID", "Orden ID", "Monto", "Moneda", "USD", "EUR", "CUP", "Transfer", "Fecha"
        ])
        self.facturas_table.setMinimumHeight(200)
        self.facturas_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.facturas_table.itemClicked.connect(self.seleccionar_factura_de_tabla)
        
        main_layout.addWidget(QLabel("Facturas Recientes (sin cerrar):"))
        main_layout.addWidget(self.facturas_table)
        
        # Cargar facturas recientes
        self.cargar_facturas_recientes()
        
        # Deshabilitar campos inicialmente
        self.habilitar_campos_edicion(False)
    
    def cargar_facturas_recientes(self):
        """Carga las facturas recientes sin cerrar"""
        facturas = self.facturacion_service.obtener_facturas_sin_cerrar()
        
        # Limpiar tabla
        self.facturas_table.setRowCount(0)
        
        # Llenar tabla con datos
        for i, factura in enumerate(facturas):
            self.facturas_table.insertRow(i)
            
            # Crear items para cada columna
            id_item = QTableWidgetItem(str(factura.get('id', '')))
            orden_id_item = QTableWidgetItem(factura.get('orden_id', ''))
            monto_item = QTableWidgetItem(f"{factura.get('monto', 0):.2f}")
            moneda_item = QTableWidgetItem(factura.get('moneda', ''))
            
            pago_usd = factura.get('pago_usd', 0) or 0
            pago_eur = factura.get('pago_eur', 0) or 0
            pago_cup = factura.get('pago_cup', 0) or 0
            pago_transferencia = factura.get('pago_transferencia', 0) or 0
            
            usd_item = QTableWidgetItem(f"{pago_usd:.2f}")
            eur_item = QTableWidgetItem(f"{pago_eur:.2f}")
            cup_item = QTableWidgetItem(f"{pago_cup:.2f}")
            transferencia_item = QTableWidgetItem(f"{pago_transferencia:.2f}")
            
            fecha_item = QTableWidgetItem(str(factura.get('fecha', '')))
            
            # Alinear números a la derecha
            for item in [monto_item, usd_item, eur_item, cup_item, transferencia_item]:
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Añadir items a la tabla
            self.facturas_table.setItem(i, 0, id_item)
            self.facturas_table.setItem(i, 1, orden_id_item)
            self.facturas_table.setItem(i, 2, monto_item)
            self.facturas_table.setItem(i, 3, moneda_item)
            self.facturas_table.setItem(i, 4, usd_item)
            self.facturas_table.setItem(i, 5, eur_item)
            self.facturas_table.setItem(i, 6, cup_item)
            self.facturas_table.setItem(i, 7, transferencia_item)
            self.facturas_table.setItem(i, 8, fecha_item)
    
    def seleccionar_factura_de_tabla(self, item):
        """Selecciona una factura de la tabla"""
        row = item.row()
        factura_id = self.facturas_table.item(row, 0).text()
        self.id_factura_input.setText(factura_id)
        self.buscar_factura()
    
    def buscar_factura(self):
        """Busca una factura por ID o ID de orden"""
        id_busqueda = self.id_factura_input.text().strip()
        if not id_busqueda:
            QMessageBox.warning(self, "Error", "Ingrese un ID de factura o ID de orden para buscar")
            return
        
        try:
            # Intentar buscar como ID numérico de factura
            factura_id = int(id_busqueda)
            factura = self.facturacion_service.obtener_factura_por_id(factura_id)
        except ValueError:
            # Si no es un número, buscar como ID de orden
            facturas = self.facturacion_service.obtener_facturas_por_orden_id(id_busqueda)
            factura = facturas[0] if facturas else None
        
        if not factura:
            QMessageBox.warning(self, "No encontrada", "No se encontró ninguna factura con ese ID")
            return
        
        # Verificar si la factura está cerrada
        if getattr(factura, 'cerrada', False):
            QMessageBox.warning(self, "Factura cerrada", 
                            "⚠️ Esta factura ya está cerrada y no puede ser modificada ⚠️\n\n"
                            "Las facturas se cierran automáticamente después del cierre de día.")
            
            # Mostrar los detalles de la factura pero no permitir edición
            self.mostrar_detalles_factura(factura, editable=False)
            return
        
        # Mostrar detalles de la factura editable
        self.mostrar_detalles_factura(factura, editable=True)
        
        # Guardar referencia a la factura actual
        self.factura_actual = factura
        
        # Habilitar campos de edición
        self.habilitar_campos_edicion(True)

    def mostrar_detalles_factura(self, factura, editable=True):
        """Muestra los detalles de la factura seleccionada"""
        try:
            # Mostrar campos no editables
            self.orden_id_label.setText(str(factura.orden_id))
            self.monto_label.setText(f"{factura.monto:.2f} {factura.moneda}")
            self.moneda_label.setText(factura.moneda)
            self.fecha_label.setText(factura.fecha.strftime("%Y-%m-%d %H:%M:%S"))
            
            # Mostrar estado con color
            estado_texto = "Abierta" if not getattr(factura, 'cerrada', False) else "Cerrada"
            color_estado = "#4CAF50" if estado_texto == "Abierta" else "#F44336"  # Verde o rojo
            self.estado_label.setText(estado_texto)
            self.estado_label.setStyleSheet(f"font-weight: bold; color: {color_estado};")
            
            # Cargar valores actuales de los pagos
            pago_usd = float(getattr(factura, 'pago_usd', 0) or 0)
            pago_eur = float(getattr(factura, 'pago_eur', 0) or 0)
            pago_cup = float(getattr(factura, 'pago_cup', 0) or 0)
            pago_transferencia = float(getattr(factura, 'pago_transferencia', 0) or 0)
            
            # Formatear y mostrar los valores
            self.pago_usd_input.setText(f"{pago_usd:.2f}")
            self.pago_eur_input.setText(f"{pago_eur:.2f}")
            self.pago_cup_input.setText(f"{pago_cup:.2f}")
            self.pago_transferencia_input.setText(f"{pago_transferencia:.2f}")
            
            # Mostrar ID de transferencia si existe
            transferencia_id = getattr(factura, 'transferencia_id', None) or ""
            self.transferencia_id_input.setText(transferencia_id)
            
            # Habilitar o deshabilitar campos según si es editable
            self.habilitar_campos_edicion(editable)
            
            # Actualizar campo de ID de transferencia
            self.actualizar_campo_id_transferencia()
            
            # Verificar balance
            self.verificar_balance()
            
            # Guardar referencia a la factura actual solo si es editable
            if editable:
                self.factura_actual = factura
            else:
                self.factura_actual = None
                
        except Exception as e:
            print(f"Error al mostrar detalles de la factura: {e}")
            QMessageBox.warning(self, "Error", f"Error al cargar detalles: {str(e)}")

    def habilitar_campos_edicion(self, habilitado):
        """Habilita o deshabilita los campos de edición"""
        self.pago_usd_input.setEnabled(habilitado)
        self.pago_eur_input.setEnabled(habilitado)
        self.pago_cup_input.setEnabled(habilitado)
        self.pago_transferencia_input.setEnabled(habilitado)
        
        # Habilitar o deshabilitar ID de transferencia según monto y estado
        tiene_transferencia = float(self.pago_transferencia_input.text() or 0) > 0
        self.transferencia_id_input.setEnabled(habilitado and tiene_transferencia)
        
        # Habilitar o deshabilitar botones
        self.actualizar_btn.setEnabled(habilitado)
        self.limpiar_btn.setEnabled(habilitado)
        
        # Estilo para campos según estado
        if habilitado:
            estilo_campos = "border: 1px solid #4CAF50; color: #000000;"
            mensaje = "Puede modificar los valores manteniendo el balance correcto."
            color_mensaje = "#4CAF50"  # Verde
        else:
            estilo_campos = "background-color: #f2f2f2; border: 1px solid #cccccc; color: #333333;"
            mensaje = "Esta factura está cerrada y no puede ser modificada."
            color_mensaje = "#F44336"  # Rojo
        
        # Aplicar estilos a los campos
        self.pago_usd_input.setStyleSheet(estilo_campos)
        self.pago_eur_input.setStyleSheet(estilo_campos)
        self.pago_cup_input.setStyleSheet(estilo_campos)
        self.pago_transferencia_input.setStyleSheet(estilo_campos)
        self.transferencia_id_input.setStyleSheet(estilo_campos)
        
        # Actualizar mensaje de edición
        self.mensaje_edicion_label.setText(mensaje)
        self.mensaje_edicion_label.setStyleSheet(f"color: {color_mensaje}; font-style: italic;")
        
    def actualizar_campo_id_transferencia(self):
        """Habilita o deshabilita el campo de ID de transferencia según el monto"""
        try:
            monto_texto = self.pago_transferencia_input.text().strip()
            if not monto_texto:
                self.transferencia_id_input.setEnabled(False)
                return
                
            monto = float(monto_texto)
            self.transferencia_id_input.setEnabled(monto > 0)
            
            if monto <= 0:
                self.transferencia_id_input.clear()
                
        except ValueError:
            self.transferencia_id_input.setEnabled(False)
    
    def verificar_balance(self):
        """Verifica si el balance de pago es correcto para la factura actual"""
        if not self.factura_actual:
            self.balance_label.setText("Balance: --")
            self.balance_label.setStyleSheet("font-weight: bold;")
            return
                
        try:
            # Obtener valores
            monto = self.factura_actual.monto
            moneda = self.factura_actual.moneda
            
            # Obtener pagos ingresados
            pago_usd = float(self.pago_usd_input.text() or 0)
            pago_eur = float(self.pago_eur_input.text() or 0)
            pago_cup = float(self.pago_cup_input.text() or 0)
            pago_transferencia = float(self.pago_transferencia_input.text() or 0)
            
            # Obtener tasas de cambio
            tasas = self.exchange_service.obtener_tasas_actuales()
            tasa_usd = tasas['usd']
            tasa_eur = tasas['eur']
            
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
            epsilon = 0.01  # Margen de error para redondeo
            if abs(balance) < epsilon:  # Si está cerca de cero (por redondeo)
                self.balance_label.setText("Balance: Correcto ✓")
                self.balance_label.setStyleSheet("color: green; font-weight: bold;")
                # Solo habilita el botón si la factura no está cerrada
                self.actualizar_btn.setEnabled(self.pago_usd_input.isEnabled())
            elif balance > 0:
                self.balance_label.setText(f"Balance: Sobra {balance:.2f} {moneda_balance}")
                self.balance_label.setStyleSheet("color: blue; font-weight: bold;")
                self.actualizar_btn.setEnabled(False)
            else:
                self.balance_label.setText(f"Balance: Faltan {-balance:.2f} {moneda_balance}")
                self.balance_label.setStyleSheet("color: red; font-weight: bold;")
                self.actualizar_btn.setEnabled(False)
                    
        except ValueError:
            self.balance_label.setText("Balance: Error en valores")
            self.balance_label.setStyleSheet("color: red; font-weight: bold;")
            self.actualizar_btn.setEnabled(False)
        except Exception as e:
            print(f"Error al verificar balance: {e}")
            self.balance_label.setText(f"Balance: Error - {str(e)}")
            self.balance_label.setStyleSheet("color: red; font-weight: bold;")
            self.actualizar_btn.setEnabled(False)
    
    def limpiar_campos(self):
        """Limpia los campos del formulario"""
        self.pago_usd_input.clear()
        self.pago_eur_input.clear()
        self.pago_cup_input.clear()
        self.pago_transferencia_input.clear()
        self.transferencia_id_input.clear()
        self.balance_label.setText("Balance: --")
        self.balance_label.setStyleSheet("")
    
    def actualizar_factura(self):
        """Actualiza la factura con los nuevos datos de pago"""
        if not self.factura_actual:
            return
            
        try:
            # Obtener valores
            factura_id = self.factura_actual.id
            pago_usd = float(self.pago_usd_input.text() or 0)
            pago_eur = float(self.pago_eur_input.text() or 0)
            pago_cup = float(self.pago_cup_input.text() or 0)
            pago_transferencia = float(self.pago_transferencia_input.text() or 0)
            transferencia_id = self.transferencia_id_input.text() if pago_transferencia > 0 else None
            
            # Validar que si hay transferencia, debe haber ID
            if pago_transferencia > 0 and not transferencia_id:
                QMessageBox.warning(self, "Error", "Si hay pago por transferencia, debe proporcionar un ID de transferencia")
                self.transferencia_id_input.setFocus()
                return
            
            # Validar balance
            epsilon = 0.01  # Margen de error para redondeo
            if not "Correcto" in self.balance_label.text() and abs(float(self.balance_label.text().split()[2])) > epsilon:
                QMessageBox.warning(self, "Error", "El balance de pagos debe ser exacto antes de actualizar la factura")
                return
            
            # Actualizar factura
            resultado = self.facturacion_service.actualizar_pagos_factura(
                factura_id=factura_id,
                pago_usd=pago_usd,
                pago_eur=pago_eur,
                pago_cup=pago_cup,
                pago_transferencia=pago_transferencia,
                transferencia_id=transferencia_id
            )
            
            if resultado:
                QMessageBox.information(self, "Éxito", "Factura actualizada correctamente")
                
                # Actualizar factura actual
                self.factura_actual = self.facturacion_service.obtener_factura_por_id(factura_id)
                self.mostrar_detalles_factura(self.factura_actual)
                
                # Recargar la tabla de facturas recientes
                self.cargar_facturas_recientes()
            else:
                QMessageBox.warning(self, "Error", "No se pudo actualizar la factura")
                
        except ValueError as e:
            QMessageBox.warning(self, "Error", f"Error al procesar los valores: {str(e)}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error inesperado: {str(e)}")