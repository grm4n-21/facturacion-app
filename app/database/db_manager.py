# -*- coding: utf-8 -*-

"""
Módulo para la gestión de la base de datos SQLite.
Maneja conexiones, consultas y operaciones sobre la base de datos.
"""

import sqlite3
import os
import datetime
from pathlib import Path

class DatabaseManager:
    """Gestor de conexiones y operaciones de base de datos"""
    
    def __init__(self, db_path=None):
        """
        Inicializa el gestor de base de datos
        
        Args:
            db_path: Ruta al archivo de la base de datos. Si es None, se usa la ruta predeterminada.
        """
        if db_path is None:
            # Usar ruta relativa desde la ubicación del script
            current_dir = Path(__file__).parent.parent.parent
            db_path = current_dir / "data" / "facturacion.db"
        
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Inicializar la base de datos si no existe
        self.connect()
        self.inicializar_tablas()
        self.disconnect()
    
    def connect(self):
        """Establece una conexión a la base de datos"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            return True
        except sqlite3.Error as e:
            print(f"Error al conectar a la base de datos: {e}")
            return False
    
    def disconnect(self):
        """Cierra la conexión a la base de datos"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
    
    def commit(self):
        """Confirma los cambios en la base de datos"""
        if self.connection:
            self.connection.commit()
    
    def execute(self, query, params=None):
        """
        Ejecuta una consulta SQL
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta (opcional)
            
        Returns:
            Cursor para procesar los resultados
        """
        if params is None:
            params = ()
        
        if not self.connection:
            self.connect()
            
        try:
            self.cursor.execute(query, params)
            return self.cursor
        except sqlite3.Error as e:
            print(f"Error al ejecutar consulta: {e}")
            print(f"Consulta: {query}")
            print(f"Parámetros: {params}")
            return None
    
    def fetch_all(self, query, params=None):
        """
        Ejecuta una consulta y devuelve todos los resultados
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta (opcional)
            
        Returns:
            Lista de resultados
        """
        cursor = self.execute(query, params)
        if cursor:
            return cursor.fetchall()
        return []
    
    def fetch_one(self, query, params=None):
        """
        Ejecuta una consulta y devuelve un solo resultado
        
        Args:
            query: Consulta SQL a ejecutar
            params: Parámetros para la consulta (opcional)
            
        Returns:
            Un solo resultado o None
        """
        cursor = self.execute(query, params)
        if cursor:
            return cursor.fetchone()
        return None
    
    def inicializar_tablas(self):
        """Crea las tablas si no existen"""
        # Tabla de tasas de cambio
        self.execute('''
        CREATE TABLE IF NOT EXISTS tasa_cambio (
            fecha TEXT PRIMARY KEY,
            usd_valor REAL NOT NULL,
            eur_valor REAL NOT NULL
        )
        ''')
        
        # Tabla de facturas
        self.execute('''
        CREATE TABLE IF NOT EXISTS facturas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orden_id TEXT NOT NULL,
            monto REAL NOT NULL,
            moneda TEXT NOT NULL,          -- 'USD', 'EUR', 'CUP'
            monto_equivalente REAL NOT NULL,
            pago_usd REAL DEFAULT 0,
            pago_eur REAL DEFAULT 0,
            pago_cup REAL DEFAULT 0,
            pago_transferencia REAL DEFAULT 0,
            transferencia_id TEXT,         -- ID de transferencia
            tasa_usada REAL NOT NULL,      -- Tasa de cambio usada al momento de la factura
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            dia_id INTEGER,
            cerrada INTEGER DEFAULT 0
        )
        ''')
        
        # Tabla de cierres de día
        self.execute('''
        CREATE TABLE IF NOT EXISTS cierres_dia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            total_usd REAL NOT NULL,
            total_eur REAL NOT NULL,
            total_cup REAL NOT NULL,
            total_transferencia REAL NOT NULL,
            num_facturas INTEGER NOT NULL,
            efectivo_contado_usd REAL DEFAULT 0,
            efectivo_contado_eur REAL DEFAULT 0,
            efectivo_contado_cup REAL DEFAULT 0,
            diferencia_usd REAL DEFAULT 0,
            diferencia_eur REAL DEFAULT 0,
            diferencia_cup REAL DEFAULT 0,
            fecha_cierre TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        self.commit()