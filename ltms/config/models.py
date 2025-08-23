"""
Configuration data models for LTMC centralized configuration system
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database configuration for different instances"""
    path: str
    type: str = "sqlite"
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None


@dataclass
class RedisConfig:
    """Redis configuration for different instances"""
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    enabled: bool = True


@dataclass
class Neo4jConfig:
    """Neo4j configuration for different instances"""
    uri: str = "bolt://localhost:7687"
    username: str = "neo4j"
    password: str = ""
    enabled: bool = True


@dataclass
class FAISSConfig:
    """FAISS index configuration for different instances"""
    path: str
    dimension: int = 384
    index_type: str = "flat"
    normalize: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration for different instances"""
    level: str = "INFO"
    file: Optional[str] = None
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


@dataclass
class InstanceConfig:
    """Complete configuration for a data instance"""
    name: str
    description: str
    database: Optional[DatabaseConfig] = None  # KWE doesn't use SQLite
    redis: RedisConfig = None
    neo4j: Neo4jConfig = None
    faiss: Optional[FAISSConfig] = None  # KWE doesn't use FAISS
    logging: LoggingConfig = None
    data_dir: str = ""
    vector_dimension: int = 384
    max_chunk_size: int = 1000
    embedding_model: str = "all-MiniLM-L6-v2"
    use_faiss: bool = True  # Whether this instance uses FAISS
    use_sqlite: bool = True  # Whether this instance uses SQLite
