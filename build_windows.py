#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para crear el ejecutable de Windows de la aplicación de facturación.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# Configuración
APP_NAME = "Sistema de Facturación"
APP_VERSION = "1.0.0"
COMPANY_NAME = "Tu Empresa"
ICON_PATH = None  # Cambia esto si tienes un archivo .ico

# Directorios
CURRENT_DIR = Path.cwd()
BUILD_DIR = CURRENT_DIR / "build"
DIST_DIR = CURRENT_DIR / "dist"
TEMP_DIR = CURRENT_DIR / "build_temp"

# Crear directorios temporales
# Crear directorios temporales
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(TEMP_DIR / "data", exist_ok=True)
os.makedirs(TEMP_DIR / "scripts", exist_ok=True)

print(f"=== Construyendo {APP_NAME} v{APP_VERSION} ===")

# Verificar que PyInstaller esté instalado
try:
    subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
    print("PyInstaller está instalado.")
except (subprocess.SubprocessError, FileNotFoundError):
    print("PyInstaller no está instalado. Instalando...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

# Copiar archivos necesarios
print("Copiando archivos necesarios...")
try:
    shutil.copy("scripts/setup.py", TEMP_DIR / "scripts" / "setup.py")
    print("Script setup.py copiado correctamente.")
except Exception as e:
    print(f"Error al copiar setup.py: {e}")
    print("Continuando con la construcción...")

# Crear archivo README.txt
readme_content = f"""
{APP_NAME} v{APP_VERSION}
=======================

Aplicación de facturación con escáner

Desarrollado por: {COMPANY_NAME}
Fecha: {datetime.now().strftime("%Y-%m-%d")}

Instrucciones:
1. Ejecute el programa. La base de datos se inicializará automáticamente.
2. Si necesita reiniciar la base de datos, elimine el archivo data/facturacion.db y reinicie la aplicación.

Para soporte técnico, contacte a: tu-email@ejemplo.com
"""

with open(TEMP_DIR / "README.txt", "w", encoding="utf-8") as f:
    f.write(readme_content)

# Construir comando PyInstaller
pyinstaller_cmd = [
    "pyinstaller",
    "--name", APP_NAME,
    "--onefile",
    "--windowed",
    "--clean",
    "--noconfirm",
]

# Añadir icono si existe
if ICON_PATH and os.path.exists(ICON_PATH):
    pyinstaller_cmd.extend(["--icon", str(ICON_PATH)])

# Determinar el separador según el sistema operativo
separator = ";" if sys.platform == "win32" else ":"

# Añadir datos y scripts
data_args = [
    (str(TEMP_DIR / "scripts"), "scripts"),
    (str(TEMP_DIR / "data"), "data"),
    (str(TEMP_DIR / "README.txt"), "."),
]

for src, dst in data_args:
    pyinstaller_cmd.extend(["--add-data", f"{src}{separator}{dst}"])

# Especificar imports ocultos
hidden_imports = [
    "sqlite3",
    "PyQt6",
    "PyQt6.QtWidgets",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
]

for imp in hidden_imports:
    pyinstaller_cmd.extend(["--hidden-import", imp])

# Añadir el script principal
pyinstaller_cmd.append("app/main.py")

# Ejecutar PyInstaller
print("Ejecutando PyInstaller...")
print(f"Comando: {' '.join(map(str, pyinstaller_cmd))}")

try:
    subprocess.run(pyinstaller_cmd, check=True)
    print("PyInstaller completado con éxito.")
except subprocess.CalledProcessError as e:
    print(f"Error al ejecutar PyInstaller: {e}")
    sys.exit(1)

# Limpiar archivos temporales
print("Limpiando archivos temporales...")
shutil.rmtree(TEMP_DIR)

# Crear archivo ZIP para distribución
print("Creando archivo ZIP para distribución...")
zip_filename = f"{APP_NAME.replace(' ', '_')}_v{APP_VERSION}"
try:
    shutil.make_archive(zip_filename, "zip", DIST_DIR)
    print(f"Archivo ZIP creado: {zip_filename}.zip")
except Exception as e:
    print(f"Error al crear archivo ZIP: {e}")

print(f"""
Construcción completada con éxito.

El ejecutable se encuentra en:
  {DIST_DIR / f"{APP_NAME}.exe"}

El archivo ZIP para distribución se encuentra en:
  {CURRENT_DIR / f"{zip_filename}.zip"}

Para distribuir la aplicación, comparta el archivo ZIP.
""")