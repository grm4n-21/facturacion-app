#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para configurar inicialmente la aplicación.
Inicializa la base de datos y establece la configuración predeterminada.
"""

import os
import sys
import sqlite3
import argparse
from pathlib import Path

# Asegurar que los módulos de la aplicación se puedan importar
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.config import Config
from app.database.db_manager import DatabaseManager

def setup_database(db_path=None, force=False):
    """
    Configura la base de datos de la aplicación
    
    Args:
        db_path: Ruta a la base de datos (opcional)
        force: Si es True, elimina la base de datos existente
        
    Returns:
        True si la configuración fue exitosa, False en caso contrario
    """
    try:
        # Si no se proporciona una ruta, usar la predeterminada
        if db_path is None:
            config = Config()
            db_path = config.get('database', 'path')
        
        # Convertir a objeto Path
        db_path = Path(db_path)
        
        # Verificar si la base de datos ya existe
        if db_path.exists() and force:
            print(f"Eliminando base de datos existente: {db_path}")
            os.remove(db_path)
        
        # Crear directorio si no existe
        os.makedirs(db_path.parent, exist_ok=True)
        
        # Inicializar base de datos
        print(f"Inicializando base de datos en: {db_path}")
        db_manager = DatabaseManager(db_path)
        db_manager.connect()
        db_manager.inicializar_tablas()
        
        # Insertar datos iniciales
        print("Insertar tasa de cambio predeterminada...")
        from datetime import date
        db_manager.execute(
            "INSERT OR REPLACE INTO tasa_cambio (fecha, valor) VALUES (?, ?)",
            (date.today().isoformat(), 24.0)
        )
        
        db_manager.commit()
        db_manager.disconnect()
        
        print("Base de datos configurada correctamente.")
        return True
        
    except Exception as e:
        print(f"Error al configurar la base de datos: {e}")
        return False

def setup_configuration():
    """
    Configura el archivo de configuración de la aplicación
    
    Returns:
        True si la configuración fue exitosa, False en caso contrario
    """
    try:
        print("Configurando aplicación...")
        config = Config()
        
        # Solicitar valores personalizados (opcional)
        print("Usando configuración predeterminada.")
        
        # Guardar configuración
        config.save()
        
        print("Configuración guardada correctamente.")
        return True
        
    except Exception as e:
        print(f"Error al configurar la aplicación: {e}")
        return False

def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(description='Configuración inicial de la aplicación de facturación')
    parser.add_argument('--force', action='store_true', help='Forzar recreación de la base de datos')
    parser.add_argument('--db-path', help='Ruta personalizada para la base de datos')
    
    args = parser.parse_args()
    
    print("=== Configuración inicial del Sistema de Facturación ===")
    
    # Configurar base de datos
    if setup_database(args.db_path, args.force):
        # Configurar aplicación
        if setup_configuration():
            print("\n¡Configuración completada con éxito!")
            print("La aplicación está lista para ser utilizada.")
            return 0
    
    print("\nError durante la configuración. Revise los mensajes anteriores.")
    return 1

if __name__ == "__main__":
    sys.exit(main())