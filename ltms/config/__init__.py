"""
LTMC Configuration Package
Unified configuration for the shared knowledge base used by all tools
"""

from .json_config_loader import get_config

__all__ = [
    "get_config"
]
