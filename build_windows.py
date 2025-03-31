#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para construir la aplicación para Windows
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Construye la aplicación para Windows"""
    # Obtener directorio raíz del proyecto
    root_dir = Path(__file__).parent.parent.absolute()
    
    # Cambiar al directorio raíz
    os.chdir(root_dir)
    
    # Verificar si estamos en Windows
    if sys.platform != "win32":
        print("Este script debe ejecutarse en Windows o usando cross-compilation")
        print(f"Plataforma actual: {sys.platform}")
        print("Intentando continuar de todos modos...")
    
    # Crear directorio dist si no existe
    dist_dir = root_dir / "dist"
    os.makedirs(dist_dir, exist_ok=True)
    
    # Construir la aplicación
    print("Construyendo la aplicación para Windows...")
    result = subprocess.run(
        ["pyinstaller", "--clean", "facturacion_app.spec"],
        shell=True,
        check=False
    )
    
    if result.returncode != 0:
        print("Error al construir la aplicación")
        sys.exit(1)
    
    print("La aplicación se ha construido correctamente")
    print(f"Puedes encontrar el ejecutable en: {dist_dir / 'Sistema de Facturacion'}")

if __name__ == "__main__":
    main()