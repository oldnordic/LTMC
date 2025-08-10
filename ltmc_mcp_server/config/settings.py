"""
LTMC Settings Configuration
=========================

Pydantic-based settings following MCP security requirements.
Respects existing database configurations from research.

Database configs from existing schema:
- SQLite: ltmc.db with Resources, ChatHistory, todos, CodePatterns tables  
- Redis: Port 6382, password 'ltmc_cache_2025'
- Neo4j: Port 7687, password 'kwe_password'  
- FAISS: data/faiss_index directory
"""

from pydantic import Field
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional
import os


class LTMCSettings(BaseSettings):
    """
    LTMC server configuration following MCP security standards.
    
    Based on research findings:
    - MCP Protocol requires explicit user consent
    - Security-first design with access controls
    - Transparent user controls for AI interactions
    """
    
    # Server settings
    server_name: str = "ltmc"
    server_version: str = "1.0.0"
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Database settings (preserving existing schema)
    db_path: str = Field(default="ltmc.db", description="SQLite database path")
    ltmc_data_dir: Path = Field(default=Path("data"), description="Data directory")
    faiss_index_path: Path = Field(default=Path("data/faiss_index"), description="FAISS index path")
    
    # Redis settings (existing config from research)
    redis_enabled: bool = Field(default=True, description="Enable Redis caching")
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6382, description="Redis port (existing LTMC instance)")
    redis_password: str = Field(default="ltmc_cache_2025", description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    
    # Neo4j settings (existing config from research)  
    neo4j_enabled: bool = Field(default=True, description="Enable Neo4j graph database")
    neo4j_host: str = Field(default="localhost", description="Neo4j host")
    neo4j_port: int = Field(default=7687, description="Neo4j port")
    neo4j_user: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="kwe_password", description="Neo4j password")
    
    # Performance settings
    cache_enabled: bool = Field(default=True, description="Enable caching")
    lazy_loading_enabled: bool = Field(default=True, description="Enable lazy loading")
    connection_pooling_enabled: bool = Field(default=True, description="Enable connection pooling")
    
    # Security settings (MCP Protocol compliance)
    require_user_consent: bool = Field(default=True, description="Require explicit user consent")
    enable_access_controls: bool = Field(default=True, description="Enable access controls")
    transparent_user_controls: bool = Field(default=True, description="Transparent user controls")
    
    # ML Integration settings
    ml_integration_enabled: bool = Field(default=True, description="Enable ML integration")
    ml_learning_coordination: bool = Field(default=True, description="Enable ML coordination")
    ml_knowledge_sharing: bool = Field(default=True, description="Enable knowledge sharing")
    ml_adaptive_resources: bool = Field(default=True, description="Enable adaptive resources")
    
    # Performance targets (from research - <15ms targets)
    performance_target_ms: int = Field(default=15, description="Performance target in milliseconds")
    
    model_config = {
        "env_prefix": "LTMC_",
        "case_sensitive": False
    }
        
    def get_redis_url(self) -> Optional[str]:
        """Get Redis connection URL."""
        if not self.redis_enabled:
            return None
        
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        else:
            return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_neo4j_uri(self) -> Optional[str]:
        """Get Neo4j connection URI."""
        if not self.neo4j_enabled:
            return None
            
        return f"bolt://{self.neo4j_host}:{self.neo4j_port}"
    
    def ensure_data_directories(self) -> None:
        """Ensure all data directories exist."""
        self.ltmc_data_dir.mkdir(parents=True, exist_ok=True)
        self.faiss_index_path.parent.mkdir(parents=True, exist_ok=True)