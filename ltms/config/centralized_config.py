"""
Unified LTMC Configuration System
Single configuration for the unified knowledge base used by all tools
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass


@dataclass
class LTMCConfig:
    """Unified LTMC configuration for all tools"""
    # Data storage paths - loaded from environment variables
    data_dir: str = os.getenv("LTMC_DATA_DIR", "/home/feanor/Projects/Data")
    database_path: str = os.getenv("DB_PATH", "/home/feanor/Projects/Data/ltmc.db")
    faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "/home/feanor/Projects/Data/ltmc/faiss_index.bin")
    
    # Redis configuration - loaded from environment variables
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6382"))
    redis_password: str = os.getenv("REDIS_PASSWORD", "ltmc_password_2025")
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    
    # Neo4j configuration - loaded from environment variables
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7689")
    neo4j_username: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "ltmc_password_2025")
    
    # Vector and embedding settings
    vector_dimension: int = 384
    max_chunk_size: int = 1000
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "/home/feanor/Projects/Data/logs/ltmc.log"
    
    def get_db_path(self) -> str:
        """Get database path for compatibility with existing services"""
        return self.database_path
    
    def get_faiss_index_path(self) -> str:
        """Get FAISS index path for compatibility with existing services"""
        return self.faiss_index_path


class ConfigManager:
    """Manages the unified LTMC configuration"""
    
    def __init__(self):
        self.config = self._load_from_json()
        self._ensure_directories()
    
    def _load_from_json(self) -> LTMCConfig:
        """Load configuration from ltmc_config.json"""
        config_path = Path(__file__).parent.parent.parent / "ltmc_config.json"
        
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    json_config = json.load(f)
                
                # Extract values from JSON config
                db_config = json_config.get("database", {})
                redis_config = json_config.get("redis", {})
                neo4j_config = json_config.get("neo4j", {})
                paths_config = json_config.get("paths", {})
                logging_config = json_config.get("logging", {})
                
                return LTMCConfig(
                    data_dir=paths_config.get("data_dir", "/home/feanor/Projects/Data"),
                    database_path=db_config.get("db_path", "/home/feanor/Projects/Data/ltmc.db"),
                    faiss_index_path=db_config.get("faiss_index_path", "/home/feanor/Projects/Data/ltmc/faiss_index.bin"),
                    redis_host=redis_config.get("host", "localhost"),
                    redis_port=redis_config.get("port", 6382),
                    redis_password=redis_config.get("password", "ltmc_password_2025"),
                    redis_db=redis_config.get("db", 0),
                    neo4j_uri=neo4j_config.get("uri", "bolt://localhost:7689"),
                    neo4j_username=neo4j_config.get("user", "neo4j"),
                    neo4j_password=neo4j_config.get("password", "ltmc_password_2025"),
                    vector_dimension=db_config.get("vector_dimension", 384),
                    max_chunk_size=db_config.get("max_chunk_size", 1000),
                    embedding_model=db_config.get("embedding_model", "all-MiniLM-L6-v2"),
                    log_level=logging_config.get("level", "INFO"),
                    log_file=logging_config.get("log_file", "/home/feanor/Projects/Data/logs/ltmc.log")
                )
            except Exception as e:
                print(f"Warning: Failed to load ltmc_config.json: {e}. Using defaults.")
                return LTMCConfig()
        else:
            print(f"Warning: ltmc_config.json not found at {config_path}. Using defaults.")
            return LTMCConfig()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        Path(self.config.data_dir).mkdir(parents=True, exist_ok=True)
        # Create parent directory for FAISS index, not the index file itself
        Path(os.path.dirname(self.config.faiss_index_path)).mkdir(parents=True, exist_ok=True)
        Path(os.path.dirname(self.config.log_file)).mkdir(parents=True, exist_ok=True)
    
    def get_environment_vars(self) -> dict:
        """Get environment variables for LTMC"""
        return {
            "LTMC_DATA_DIR": self.config.data_dir,
            "DB_PATH": self.config.database_path,
            "FAISS_INDEX_PATH": self.config.faiss_index_path,
            "VECTOR_DIMENSION": str(self.config.vector_dimension),
            "MAX_CHUNK_SIZE": str(self.config.max_chunk_size),
            "EMBEDDING_MODEL": self.config.embedding_model,
            "LOG_LEVEL": self.config.log_level,
            "LOG_FILE": self.config.log_file,
            "REDIS_ENABLED": "true",
            "REDIS_HOST": self.config.redis_host,
            "REDIS_PORT": str(self.config.redis_port),
            "REDIS_PASSWORD": self.config.redis_password,
            "REDIS_DB": str(self.config.redis_db),
            "NEO4J_URI": self.config.neo4j_uri,
            "NEO4J_USER": self.config.neo4j_username,
            "NEO4J_PASSWORD": self.config.neo4j_password,
            "NEO4J_ENABLED": "true"
        }
    
    def setup_environment(self):
        """Set environment variables for the current process"""
        env_vars = self.get_environment_vars()
        for key, value in env_vars.items():
            os.environ[key] = value


# Global configuration instance
config_manager = ConfigManager()


def get_config() -> LTMCConfig:
    """Get the unified LTMC configuration"""
    return config_manager.config


def setup_ltmc_environment():
    """Set up LTMC environment variables"""
    config_manager.setup_environment()


if __name__ == "__main__":
    setup_ltmc_environment()
    print("LTMC unified configuration loaded:")
    print(f"Data directory: {config_manager.config.data_dir}")
    print(f"Database: {config_manager.config.database_path}")
    print(f"FAISS index: {config_manager.config.faiss_index_path}")
    print(f"Redis: {config_manager.config.redis_host}:{config_manager.config.redis_port}")
    print(f"Neo4j: {config_manager.config.neo4j_uri}")
