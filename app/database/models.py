# -*- coding: utf-8 -*-

"""
Definiciones de modelos/entidades para la base de datos.
Define las clases que representan las entidades del sistema.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TasaCambio:
    """Representa una tasa de cambio USD a CUP para una fecha específica"""
    fecha: str  # Formato ISO: YYYY-MM-DD
    valor: float
    
    @classmethod
    def from_db_row(cls, row):
        """
        Crea una instancia a partir de una fila de base de datos
        
        Args:
            row: Tupla de datos de la base de datos
            
        Returns:
            Instancia de TasaCambio
        """
        return cls(
            fecha=row[0],
            valor=row[1]
        )

@dataclass
class Factura:
    """Representa una factura en el sistema"""
    id: Optional[int]
    orden_id: str
    monto: float
    moneda: str  # "USD", "EUR" o "CUP"
    monto_equivalente: float  # Siempre en USD para facilitar reportes
    fecha: datetime
    pago_usd: float = 0.0
    pago_eur: float = 0.0
    pago_cup: float = 0.0
    pago_transferencia: float = 0.0
    transferencia_id: Optional[str] = None
    tasa_usada: float = 0.0
    cerrada: bool = False
    dia_id: Optional[int] = None
    
    @classmethod
    def from_db_row(cls, row):
        """
        Crea una instancia a partir de una fila de base de datos
        
        Args:
            row: Tupla de datos de la base de datos
            
        Returns:
            Instancia de Factura
        """
        return cls(
            id=row[0],
            orden_id=row[1],
            monto=row[2],
            moneda=row[3],
            monto_equivalente=row[4],
            fecha=datetime.fromisoformat(row[5].replace("Z", "+00:00"))
            if "Z" in row[5] else datetime.fromisoformat(row[5])
        )