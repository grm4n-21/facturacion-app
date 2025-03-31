# -*- coding: utf-8 -*-

"""
Servicio simple de autenticación.
"""

class AuthService:
    """Servicio básico para verificar la clave de acceso"""
    
    def __init__(self):
        """Inicializa el servicio con una clave predeterminada"""
        # En una implementación real, esto debería estar cifrado y guardado en un archivo
        self.clave_acceso = "Sol981101*2102G"  # Clave predeterminada
    
    def verificar_clave(self, clave):
        """
        Verifica si la clave ingresada es correcta
        
        Args:
            clave: Clave a verificar
            
        Returns:
            True si la clave es correcta, False en caso contrario
        """
        return clave == self.clave_acceso