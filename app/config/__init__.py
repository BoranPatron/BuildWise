"""
BuildWise Configuration Module

Dieses Modul enthält alle konfigurierbaren Einstellungen für das BuildWise-System.
"""

from .credit_config import CreditConfig, credit_config, validate_credit_config

__all__ = [
    "CreditConfig",
    "credit_config", 
    "validate_credit_config"
]
