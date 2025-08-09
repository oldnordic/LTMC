"""Configuration management for LTMC with proper environment variable loading."""

import os
import sys
import logging
from pathlib import Path
from typing import Optional

# Setup stderr logging for configuration (stdio transport compatible)
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    
    # Find .env file in project root
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
        logger.info(f"Loaded environment variables from: {env_file}")
    else:
        logger.info(f"No .env file found at: {env_file}")
        
except ImportError:
    logger.info("python-dotenv not available, using system environment variables only")


class Config:
    """Centralized configuration management for LTMC."""
    
    # Database configuration
    DB_PATH: str = os.getenv("DB_PATH", "ltmc.db")
    
    # Vector store configuration
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", "faiss_index")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # Server configuration
    HTTP_HOST: str = os.getenv("HTTP_HOST", "localhost")
    HTTP_PORT: int = int(os.getenv("HTTP_PORT", "5050"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Redis configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6382"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "ltmc_dev_default")
    REDIS_ENABLED: bool = os.getenv("REDIS_ENABLED", "true").lower() == "true"
    
    # Orchestration configuration
    ORCHESTRATION_MODE: str = os.getenv("ORCHESTRATION_MODE", "basic")
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    BUFFER_ENABLED: bool = os.getenv("BUFFER_ENABLED", "true").lower() == "true"
    SESSION_STATE_ENABLED: bool = os.getenv("SESSION_STATE_ENABLED", "true").lower() == "true"
    
    # ML Integration configuration
    ML_INTEGRATION_ENABLED: bool = os.getenv("ML_INTEGRATION_ENABLED", "true").lower() == "true"
    ML_LEARNING_COORDINATION: bool = os.getenv("ML_LEARNING_COORDINATION", "true").lower() == "true"
    
    @classmethod
    def get_db_path(cls) -> str:
        """Get database path with validation."""
        db_path = cls.DB_PATH
        if not db_path:
            raise ValueError("DB_PATH environment variable is empty or not set")
        
        # Convert relative paths to absolute paths
        if not os.path.isabs(db_path):
            project_root = Path(__file__).parent.parent
            db_path = str(project_root / db_path)
        
        # Ensure parent directory exists
        db_dir = Path(db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        return db_path
    
    @classmethod
    def get_faiss_index_path(cls) -> str:
        """Get FAISS index path with validation."""
        index_path = cls.FAISS_INDEX_PATH
        if not index_path:
            raise ValueError("FAISS_INDEX_PATH environment variable is empty or not set")
        
        # Convert relative paths to absolute paths
        if not os.path.isabs(index_path):
            project_root = Path(__file__).parent.parent
            index_path = str(project_root / index_path)
        
        # Ensure parent directory exists
        index_dir = Path(index_path).parent
        index_dir.mkdir(parents=True, exist_ok=True)
        
        return index_path
    
    @classmethod
    def validate_config(cls) -> dict:
        """Validate configuration and return status."""
        issues = []
        
        # Check critical paths
        try:
            db_path = cls.get_db_path()
            if not db_path:
                issues.append("DB_PATH is empty")
        except Exception as e:
            issues.append(f"DB_PATH validation failed: {e}")
        
        try:
            index_path = cls.get_faiss_index_path()
            if not index_path:
                issues.append("FAISS_INDEX_PATH is empty")
        except Exception as e:
            issues.append(f"FAISS_INDEX_PATH validation failed: {e}")
        
        # Check Redis configuration if enabled
        if cls.REDIS_ENABLED:
            if not cls.REDIS_HOST:
                issues.append("REDIS_HOST is empty but Redis is enabled")
            if not cls.REDIS_PASSWORD:
                issues.append("REDIS_PASSWORD is empty but Redis is enabled")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "config": {
                "DB_PATH": cls.DB_PATH,
                "FAISS_INDEX_PATH": cls.FAISS_INDEX_PATH,
                "REDIS_ENABLED": cls.REDIS_ENABLED,
                "REDIS_HOST": cls.REDIS_HOST,
                "REDIS_PORT": cls.REDIS_PORT,
            }
        }
    
    @classmethod
    def print_config(cls):
        """Log current configuration for debugging (stdio transport safe)."""
        logger.info("=== LTMC Configuration ===")
        logger.info(f"DB_PATH: {cls.DB_PATH}")
        logger.info(f"FAISS_INDEX_PATH: {cls.FAISS_INDEX_PATH}")
        logger.info(f"EMBEDDING_MODEL: {cls.EMBEDDING_MODEL}")
        logger.info(f"HTTP_HOST: {cls.HTTP_HOST}")
        logger.info(f"HTTP_PORT: {cls.HTTP_PORT}")
        logger.info(f"LOG_LEVEL: {cls.LOG_LEVEL}")
        logger.info(f"REDIS_ENABLED: {cls.REDIS_ENABLED}")
        if cls.REDIS_ENABLED:
            logger.info(f"REDIS_HOST: {cls.REDIS_HOST}")
            logger.info(f"REDIS_PORT: {cls.REDIS_PORT}")
        logger.info(f"ORCHESTRATION_MODE: {cls.ORCHESTRATION_MODE}")
        logger.info("========================")


# Initialize configuration on import
config = Config()

# Validate configuration and log warnings (stdio transport safe)
validation_result = config.validate_config()
if not validation_result["valid"]:
    logger.warning("Configuration validation issues found:")
    for issue in validation_result["issues"]:
        logger.warning(f"  WARNING: {issue}")

# For backward compatibility, export commonly used values
DB_PATH = config.get_db_path()
FAISS_INDEX_PATH = config.get_faiss_index_path()
EMBEDDING_MODEL = config.EMBEDDING_MODEL