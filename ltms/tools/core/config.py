"""
Configuration management for LTMC modular MCP tools.
Provides centralized access to tool-specific configurations.

File: ltms/tools/core/config.py
Lines: ~120 (under 300 limit)
Purpose: Configuration management for modular MCP tools
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from ltms.config.json_config_loader import get_config as get_ltmc_config

logger = logging.getLogger(__name__)


class ToolConfig:
    """Configuration manager for LTMC MCP tools.
    
    Provides centralized access to configuration with tool-specific overrides
    and validation.
    """
    
    def __init__(self):
        """Initialize tool configuration manager."""
        self._base_config = get_ltmc_config()
        self._tool_configs: Dict[str, Dict[str, Any]] = {}
        logger.info("ToolConfig initialized")
    
    def get_base_config(self):
        """Get the base LTMC configuration object.
        
        Returns:
            Base LTMC configuration instance
        """
        return self._base_config
    
    def get_db_path(self) -> str:
        """Get SQLite database path.
        
        Returns:
            Path to SQLite database file
        """
        return self._base_config.get_db_path()
    
    def get_faiss_index_path(self) -> str:
        """Get FAISS index path.
        
        Returns:
            Path to FAISS index directory
        """
        return self._base_config.get_faiss_index_path()
    
    def get_redis_config(self) -> Dict[str, Any]:
        """Get Redis configuration.
        
        Returns:
            Redis configuration dictionary
        """
        return {
            'host': getattr(self._base_config, 'REDIS_HOST', 'localhost'),
            'port': getattr(self._base_config, 'REDIS_PORT', 6379),
            'password': getattr(self._base_config, 'REDIS_PASSWORD', None),
            'db': getattr(self._base_config, 'REDIS_DB', 0)
        }
    
    def get_neo4j_config(self) -> Dict[str, Any]:
        """Get Neo4j configuration.
        
        Returns:
            Neo4j configuration dictionary
        """
        return {
            'uri': getattr(self._base_config, 'NEO4J_URI', 'bolt://localhost:7687'),
            'user': getattr(self._base_config, 'NEO4J_USER', 'neo4j'),
            'password': getattr(self._base_config, 'NEO4J_PASSWORD', 'password'),
            'database': getattr(self._base_config, 'NEO4J_DATABASE', 'neo4j')
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration settings.
        
        Returns:
            Performance configuration dictionary
        """
        return {
            'max_query_time_ms': 2000,  # 2 second SLA
            'max_tool_time_ms': 500,    # 500ms SLA
            'max_results': 1000,
            'default_limit': 100,
            'cache_ttl_seconds': 3600
        }
    
    def set_tool_config(self, tool_name: str, config: Dict[str, Any]):
        """Set tool-specific configuration.
        
        Args:
            tool_name: Name of the tool
            config: Tool-specific configuration dictionary
        """
        self._tool_configs[tool_name] = config
        logger.info(f"Tool configuration set for {tool_name}")
    
    def get_tool_config(self, tool_name: str, key: str = None, default: Any = None) -> Any:
        """Get tool-specific configuration value.
        
        Args:
            tool_name: Name of the tool
            key: Configuration key (if None, returns entire config)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        tool_config = self._tool_configs.get(tool_name, {})
        
        if key is None:
            return tool_config
        
        return tool_config.get(key, default)
    
    def validate_paths(self) -> Dict[str, bool]:
        """Validate that all configured paths exist or can be created.
        
        Returns:
            Dictionary of path validation results
        """
        results = {}
        
        # Validate DB path
        try:
            db_path = Path(self.get_db_path())
            db_path.parent.mkdir(parents=True, exist_ok=True)
            results['db_path'] = True
            logger.info(f"Database path validated: {db_path}")
        except Exception as e:
            results['db_path'] = False
            logger.error(f"Database path validation failed: {e}")
        
        # Validate FAISS index path
        try:
            faiss_path = Path(self.get_faiss_index_path())
            faiss_path.mkdir(parents=True, exist_ok=True)
            results['faiss_path'] = True
            logger.info(f"FAISS index path validated: {faiss_path}")
        except Exception as e:
            results['faiss_path'] = False
            logger.error(f"FAISS index path validation failed: {e}")
        
        return results
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration for tools.
        
        Returns:
            Logging configuration dictionary
        """
        return {
            'level': logging.INFO,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'log_to_file': True,
            'log_file_path': Path(self.get_db_path()).parent / 'ltmc_tools.log'
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration settings.
        
        Returns:
            Security configuration dictionary
        """
        return {
            'max_content_length': 10 * 1024 * 1024,  # 10MB max content
            'max_query_length': 1000,                # Max query string length
            'allowed_file_extensions': ['.txt', '.md', '.py', '.json', '.yaml', '.yml'],
            'sanitize_inputs': True,
            'validate_file_paths': True
        }


# Global instance
_tool_config: Optional[ToolConfig] = None


def get_tool_config() -> ToolConfig:
    """Get the global ToolConfig instance.
    
    Returns:
        Global ToolConfig instance
    """
    global _tool_config
    if _tool_config is None:
        _tool_config = ToolConfig()
    return _tool_config