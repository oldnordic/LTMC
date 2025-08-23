"""
Centralized JSON Configuration Loader for LTMC
Single source of truth - reads ltmc_config.json from execution directory
"""

import os
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class LTMCJsonConfig:
    """Centralized LTMC configuration loaded from JSON"""
    
    def __init__(self, config_data: Dict[str, Any]):
        """Initialize configuration from JSON data"""
        self._config_data = config_data
        self._validate_config()
    
    # Database configuration
    @property
    def db_path(self) -> str:
        return self._config_data.get("database", {}).get("db_path", "ltmc.db")
    
    @property
    def faiss_index_path(self) -> str:
        return self._config_data.get("database", {}).get("faiss_index_path", "faiss_index")
    
    @property
    def embedding_model(self) -> str:
        return self._config_data.get("database", {}).get("embedding_model", "all-MiniLM-L6-v2")
    
    @property
    def vector_dimension(self) -> int:
        return self._config_data.get("database", {}).get("vector_dimension", 384)
    
    @property
    def max_chunk_size(self) -> int:
        return self._config_data.get("database", {}).get("max_chunk_size", 1000)
    
    # Redis configuration
    @property
    def redis_enabled(self) -> bool:
        return self._config_data.get("redis", {}).get("enabled", True)
    
    @property
    def redis_host(self) -> str:
        return self._config_data.get("redis", {}).get("host", "localhost")
    
    @property
    def redis_port(self) -> int:
        return self._config_data.get("redis", {}).get("port", 6382)
    
    @property
    def redis_password(self) -> str:
        return self._config_data.get("redis", {}).get("password", "")
    
    @property
    def redis_db(self) -> int:
        return self._config_data.get("redis", {}).get("db", 0)
    
    @property
    def redis_connection_timeout(self) -> int:
        return self._config_data.get("redis", {}).get("connection_timeout", 5)
    
    # Neo4j configuration
    @property
    def neo4j_enabled(self) -> bool:
        return self._config_data.get("neo4j", {}).get("enabled", True)
    
    @property
    def neo4j_uri(self) -> str:
        return self._config_data.get("neo4j", {}).get("uri", "bolt://localhost:7687")
    
    @property
    def neo4j_user(self) -> str:
        return self._config_data.get("neo4j", {}).get("user", "neo4j")
    
    @property
    def neo4j_password(self) -> str:
        return self._config_data.get("neo4j", {}).get("password", "")
    
    @property
    def neo4j_database(self) -> str:
        return self._config_data.get("neo4j", {}).get("database", "neo4j")
    
    @property
    def neo4j_connection_timeout(self) -> int:
        return self._config_data.get("neo4j", {}).get("connection_timeout", 10)
    
    # Server configuration
    @property
    def server_host(self) -> str:
        return self._config_data.get("server", {}).get("host", "localhost")
    
    @property
    def server_port(self) -> int:
        return self._config_data.get("server", {}).get("port", 5050)
    
    @property
    def server_transport(self) -> str:
        return self._config_data.get("server", {}).get("transport", "stdio")
    
    @property
    def server_reload(self) -> bool:
        return self._config_data.get("server", {}).get("reload", False)
    
    # Logging configuration
    @property
    def log_level(self) -> str:
        return self._config_data.get("logging", {}).get("level", "INFO")
    
    @property
    def log_file(self) -> str:
        return self._config_data.get("logging", {}).get("log_file", "ltmc.log")
    
    @property
    def stderr_enabled(self) -> bool:
        return self._config_data.get("logging", {}).get("stderr_enabled", True)
    
    @property
    def max_log_files(self) -> int:
        return self._config_data.get("logging", {}).get("max_log_files", 5)
    
    @property
    def max_log_size_mb(self) -> int:
        return self._config_data.get("logging", {}).get("max_log_size_mb", 10)
    
    # Feature flags
    @property
    def cache_enabled(self) -> bool:
        return self._config_data.get("features", {}).get("cache_enabled", True)
    
    @property
    def buffer_enabled(self) -> bool:
        return self._config_data.get("features", {}).get("buffer_enabled", True)
    
    @property
    def session_state_enabled(self) -> bool:
        return self._config_data.get("features", {}).get("session_state_enabled", True)
    
    @property
    def ml_integration_enabled(self) -> bool:
        return self._config_data.get("features", {}).get("ml_integration_enabled", True)
    
    @property
    def ml_learning_coordination(self) -> bool:
        return self._config_data.get("features", {}).get("ml_learning_coordination", True)
    
    @property
    def orchestration_mode(self) -> str:
        return self._config_data.get("features", {}).get("orchestration_mode", "basic")
    
    # Paths
    @property
    def data_dir(self) -> str:
        return self._config_data.get("paths", {}).get("data_dir", "/tmp/ltmc")
    
    @property
    def temp_dir(self) -> str:
        return self._config_data.get("paths", {}).get("temp_dir", "/tmp/ltmc")
    
    @property
    def backup_dir(self) -> str:
        return self._config_data.get("paths", {}).get("backup_dir", "/tmp/ltmc/backups")
    
    # Performance settings
    @property
    def max_connections(self) -> int:
        return self._config_data.get("performance", {}).get("max_connections", 100)
    
    @property
    def connection_pool_size(self) -> int:
        return self._config_data.get("performance", {}).get("connection_pool_size", 10)
    
    @property
    def query_timeout(self) -> int:
        return self._config_data.get("performance", {}).get("query_timeout", 30)
    
    @property
    def bulk_insert_batch_size(self) -> int:
        return self._config_data.get("performance", {}).get("bulk_insert_batch_size", 1000)
    
    @property
    def cache_ttl_seconds(self) -> int:
        return self._config_data.get("performance", {}).get("cache_ttl_seconds", 300)
    
    def _validate_config(self):
        """Validate configuration data"""
        required_sections = ["database", "redis", "neo4j", "logging", "features", "paths"]
        for section in required_sections:
            if section not in self._config_data:
                logger.warning(f"Missing configuration section: {section}")
    
    # Backward compatibility methods
    def get_db_path(self) -> str:
        """Get database path with validation - backward compatibility"""
        db_path = self.db_path
        if not db_path:
            raise ValueError("Database path is not configured")
        
        # Convert relative paths to absolute paths based on config file location
        if not os.path.isabs(db_path):
            config_dir = Path(__file__).parent.parent.parent
            db_path = str(config_dir / db_path)
        
        # Ensure parent directory exists
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        return db_path
    
    def get_faiss_index_path(self) -> str:
        """Get FAISS index path with validation - backward compatibility"""
        index_path = self.faiss_index_path
        if not index_path:
            raise ValueError("FAISS index path is not configured")
        
        # Convert relative paths to absolute paths based on config file location
        if not os.path.isabs(index_path):
            config_dir = Path(__file__).parent.parent.parent
            index_path = str(config_dir / index_path)
        
        # Ensure parent directory exists
        index_dir = Path(index_path).parent
        index_dir.mkdir(parents=True, exist_ok=True)
        
        return index_path


class JsonConfigLoader:
    """Loads LTMC configuration from JSON file in execution directory"""
    
    DEFAULT_CONFIG_NAME = "ltmc_config.json"
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self.DEFAULT_CONFIG_NAME
        self.config: Optional[LTMCJsonConfig] = None
        self.load_config()
    
    def find_config_file(self) -> Optional[Path]:
        """Find ltmc_config.json in execution directory or nearby locations"""
        search_paths = [
            # Current working directory (where binary is executed)
            Path.cwd() / self.config_file,
            
            # Directory containing this Python file
            Path(__file__).parent.parent.parent / self.config_file,
            
            # Parent directories (for development)
            Path(__file__).parent.parent.parent.parent / self.config_file,
            
            # User home directory
            Path.home() / ".ltmc" / self.config_file,
            
            # System-wide config
            Path("/etc/ltmc") / self.config_file,
        ]
        
        for path in search_paths:
            if path.exists() and path.is_file():
                logger.info(f"Found config file: {path}")
                return path
        
        return None
    
    def load_config(self) -> bool:
        """Load configuration from JSON file"""
        config_path = self.find_config_file()
        
        if not config_path:
            logger.error(f"Configuration file '{self.config_file}' not found in any search location")
            logger.error("Search locations:")
            for path in [Path.cwd(), Path(__file__).parent.parent.parent, Path.home() / ".ltmc"]:
                logger.error(f"  - {path / self.config_file}")
            
            # Create default config as fallback
            self._create_default_config()
            return False
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.config = LTMCJsonConfig(config_data)
            logger.info(f"Configuration loaded successfully from: {config_path}")
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {config_path}: {e}")
            self._create_default_config()
            return False
        except Exception as e:
            logger.error(f"Failed to load config file {config_path}: {e}")
            self._create_default_config()
            return False
    
    def _create_default_config(self):
        """Create default configuration"""
        logger.warning("Using default configuration")
        default_config = {
            "version": "1.0.0",
            "database": {
                "db_path": "ltmc.db",
                "faiss_index_path": "faiss_index",
                "embedding_model": "all-MiniLM-L6-v2",
                "vector_dimension": 384,
                "max_chunk_size": 1000
            },
            "redis": {
                "enabled": True,
                "host": "localhost",
                "port": 6382,
                "password": "",
                "db": 0,
                "connection_timeout": 5
            },
            "neo4j": {
                "enabled": True,
                "uri": "bolt://localhost:7687",
                "user": "neo4j",
                "password": "",
                "database": "neo4j",
                "connection_timeout": 10
            },
            "server": {
                "host": "localhost",
                "port": 5050,
                "transport": "stdio",
                "reload": False
            },
            "logging": {
                "level": "INFO",
                "log_file": "ltmc.log",
                "stderr_enabled": True,
                "max_log_files": 5,
                "max_log_size_mb": 10
            },
            "features": {
                "cache_enabled": True,
                "buffer_enabled": True,
                "session_state_enabled": True,
                "ml_integration_enabled": True,
                "ml_learning_coordination": True,
                "orchestration_mode": "basic"
            },
            "paths": {
                "data_dir": "/tmp/ltmc",
                "temp_dir": "/tmp/ltmc",
                "backup_dir": "/tmp/ltmc/backups"
            },
            "performance": {
                "max_connections": 100,
                "connection_pool_size": 10,
                "query_timeout": 30,
                "bulk_insert_batch_size": 1000,
                "cache_ttl_seconds": 300
            }
        }
        
        self.config = LTMCJsonConfig(default_config)
    
    def get_config(self) -> LTMCJsonConfig:
        """Get configuration instance"""
        if not self.config:
            self.load_config()
        return self.config
    
    def reload_config(self) -> bool:
        """Reload configuration from file"""
        return self.load_config()


# Global configuration loader instance
_config_loader: Optional[JsonConfigLoader] = None


def get_config_loader() -> JsonConfigLoader:
    """Get global configuration loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = JsonConfigLoader()
    return _config_loader


def get_config() -> LTMCJsonConfig:
    """Get configuration instance - main API entry point"""
    return get_config_loader().get_config()


def reload_config() -> bool:
    """Reload configuration from file"""
    return get_config_loader().reload_config()


# Backward compatibility exports
def get_db_path() -> str:
    """Get database path - backward compatibility"""
    return get_config().get_db_path()


def get_faiss_index_path() -> str:
    """Get FAISS index path - backward compatibility"""
    return get_config().get_faiss_index_path()


# Export main configuration class for type hints
Config = LTMCJsonConfig