# -*- coding: utf-8 -*-

"""
Módulo para la gestión de configuraciones de la aplicación.
"""

import os
import json
from pathlib import Path

class Config:
    """Clase para gestionar la configuración de la aplicación"""
    
    # Ruta predeterminada al archivo de configuración
    CONFIG_FILE = Path(os.path.expanduser("~")) / ".facturacion-app" / "config.json"
    
    # Configuración predeterminada
    DEFAULT_CONFIG = {
        "database": {
            "path": str(Path(__file__).parent.parent.parent / "data" / "facturacion.db")
        },
        "app": {
            "theme": "system",
            "language": "es"
        },
        "scanner": {
            "camera_index": 0,
            "timeout": 30
        },
        "exchange_rate": {
            "default_rate": 24.0
        }
    }
    
    def __init__(self):
        """Inicializa la configuración"""
        self._config = None
        self.load()
    
    def load(self):
        """Carga la configuración desde el archivo"""
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
        
        # Intentar cargar configuración
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
            else:
                # Configuración predeterminada
                self._config = self.DEFAULT_CONFIG
                self.save()
                
        except Exception as e:
            print(f"Error al cargar configuración: {e}")
            self._config = self.DEFAULT_CONFIG
    
    def save(self):
        """Guarda la configuración en el archivo"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)
            
            with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
                
        except Exception as e:
            print(f"Error al guardar configuración: {e}")
    
    def get(self, section, key, default=None):
        """
        Obtiene un valor de configuración
        
        Args:
            section: Sección de la configuración
            key: Clave del valor
            default: Valor predeterminado si no se encuentra
            
        Returns:
            Valor de configuración o valor predeterminado
        """
        try:
            return self._config[section][key]
        except (KeyError, TypeError):
            if default is not None:
                return default
            
            # Intentar obtener el valor predeterminado
            try:
                return self.DEFAULT_CONFIG[section][key]
            except (KeyError, TypeError):
                return None
    
    def set(self, section, key, value):
        """
        Establece un valor de configuración
        
        Args:
            section: Sección de la configuración
            key: Clave del valor
            value: Valor a establecer
            
        Returns:
            True si se estableció correctamente, False en caso contrario
        """
        try:
            # Crear sección si no existe
            if section not in self._config:
                self._config[section] = {}
            
            # Establecer valor
            self._config[section][key] = value
            
            # Guardar configuración
            self.save()
            
            return True
            
        except Exception as e:
            print(f"Error al establecer configuración: {e}")
            return False

# Crear instancia global
config = Config()