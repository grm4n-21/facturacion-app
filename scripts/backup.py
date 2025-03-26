#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para realizar respaldos de la base de datos de la aplicación.
"""

import os
import sys
import shutil
from datetime import datetime, date, timedelta
import argparse
import sqlite3
from pathlib import Path

# Asegurar que los módulos de la aplicación se puedan importar
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.config import Config

def backup_database(backup_dir=None):
    """
    Realiza un respaldo de la base de datos
    
    Args:
        backup_dir: Directorio donde se guardará el respaldo (opcional)
        
    Returns:
        Ruta al archivo de respaldo o None si falló
    """
    try:
        # Obtener la ruta de la base de datos
        config = Config()
        db_path = Path(config.get('database', 'path'))
        
        # Verificar que la base de datos existe
        if not db_path.exists():
            print(f"Error: La base de datos no existe en {db_path}")
            return None
        
        # Establecer directorio de respaldo
        if backup_dir is None:
            backup_dir = Path(os.path.expanduser("~")) / "facturacion-backups"
        else:
            backup_dir = Path(backup_dir)
        
        # Crear directorio de respaldo si no existe
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generar nombre de archivo de respaldo
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"facturacion_backup_{timestamp}.db"
        backup_path = backup_dir / backup_filename
        
        # Realizar respaldo
        print(f"Realizando respaldo de {db_path} a {backup_path}...")
        
        # Método 1: Copia directa del archivo
        shutil.copy2(db_path, backup_path)
        
        # Método 2 (alternativo): Usar las funciones de SQLite para backup
        # conn = sqlite3.connect(db_path)
        # backup_conn = sqlite3.connect(backup_path)
        # conn.backup(backup_conn)
        # backup_conn.close()
        # conn.close()
        
        print(f"Respaldo completado: {backup_path}")
        return backup_path
        
    except Exception as e:
        print(f"Error al realizar respaldo: {e}")
        return None

def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(description='Realizar respaldo de la base de datos')
    parser.add_argument('--dir', help='Directorio donde se guardará el respaldo')
    
    args = parser.parse_args()
    
    print("=== Respaldo de Base de Datos ===")
    
    backup_path = backup_database(args.dir)
    
    if backup_path:
        print("\nRespaldo completado con éxito.")
        print(f"Archivo de respaldo: {backup_path}")
        return 0
    else:
        print("\nError al realizar el respaldo. Revise los mensajes anteriores.")
        return 1

if __name__ == "__main__":
    sys.exit(main())