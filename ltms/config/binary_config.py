"""
Binary Configuration System for LTMC
Reads config from files and handles missing dependencies with user prompts
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class BinaryConfig:
    """Configuration for LTMC binary"""
    # Data storage - loaded from environment variables
    base_data_dir: str = os.getenv("LTMC_DATA_DIR", "/home/feanor/Projects/Data")
    database_path: str = os.getenv("DB_PATH", "/home/feanor/Projects/Data/ltmc.db")
    faiss_index_path: str = os.getenv("FAISS_INDEX_PATH", "/home/feanor/Projects/Data/ltmc/faiss_index")
    
    # Redis
    redis_enabled: bool = True
    redis_host: str = "localhost"
    redis_port: int = 6382
    redis_password: str = "ltmc_cache_2025"
    
    # Neo4j
    neo4j_enabled: bool = True
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "kwe_password"
    
    # Logging
    log_level: str = "INFO"
    
    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_dimension: int = 384


class BinaryConfigManager:
    """Manages binary configuration with file reading and dependency checking"""
    
    def __init__(self, config_file: str = "ltmc_config.json"):
        self.config_file = config_file
        self.config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        config_paths = [
            self.config_file,
            "ltmc_config.env",
            "config/ltmc_config.json",
            os.path.expanduser("~/.ltmc/config.json")
        ]
        
        for path in config_paths:
            if os.path.exists(path):
                try:
                    if path.endswith('.json'):
                        with open(path, 'r') as f:
                            config_data = json.load(f)
                    elif path.endswith('.env'):
                        config_data = self._parse_env_file(path)
                    else:
                        continue
                    
                    self.config = BinaryConfig(**config_data)
                    print(f"✅ Configuration loaded from: {path}")
                    return
                except Exception as e:
                    print(f"⚠️  Failed to load config from {path}: {e}")
        
        # No config found, create default
        print("📝 No configuration file found, using defaults")
        self.config = BinaryConfig()
    
    def _parse_env_file(self, env_file: str) -> Dict[str, Any]:
        """Parse .env file into dictionary"""
        config = {}
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    # Convert types
                    if value.lower() in ('true', 'false'):
                        value = value.lower() == 'true'
                    elif value.isdigit():
                        value = int(value)
                    
                    config[key.lower()] = value
        
        return config
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check if all required dependencies are available"""
        results = {
            "sqlite": False,
            "faiss": False,
            "redis": False,
            "neo4j": False
        }
        
        # Check SQLite
        if os.path.exists(os.path.dirname(self.config.database_path)):
            results["sqlite"] = True
            print(f"✅ SQLite directory: {os.path.dirname(self.config.database_path)}")
        else:
            print(f"❌ SQLite directory missing: {os.path.dirname(self.config.database_path)}")
        
        # Check FAISS
        if os.path.exists(os.path.dirname(self.config.faiss_index_path)):
            results["faiss"] = True
            print(f"✅ FAISS directory: {os.path.dirname(self.config.faiss_index_path)}")
        else:
            print(f"❌ FAISS directory missing: {os.path.dirname(self.config.faiss_index_path)}")
        
        # Check Redis
        try:
            import redis
            r = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                password=self.config.redis_password,
                socket_connect_timeout=1
            )
            r.ping()
            results["redis"] = True
            print(f"✅ Redis: {self.config.redis_host}:{self.config.redis_port}")
        except Exception as e:
            print(f"❌ Redis connection failed: {e}")
        
        # Check Neo4j
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(
                self.config.neo4j_uri,
                auth=(self.config.neo4j_user, self.config.neo4j_password)
            )
            with driver.session() as session:
                session.run("RETURN 1")
            driver.close()
            results["neo4j"] = True
            print(f"✅ Neo4j: {self.config.neo4j_uri}")
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
        
        return results
    
    def setup_missing_dependencies(self):
        """Interactive setup for missing dependencies"""
        deps = self.check_dependencies()
        
        if not deps["sqlite"]:
            self._setup_sqlite()
        
        if not deps["faiss"]:
            self._setup_faiss()
        
        if not deps["redis"]:
            self._setup_redis()
        
        if not deps["neo4j"]:
            self._setup_neo4j()
    
    def _setup_sqlite(self):
        """Setup SQLite database"""
        print("\n🔧 Setting up SQLite database...")
        db_dir = os.path.dirname(self.config.database_path)
        
        try:
            os.makedirs(db_dir, exist_ok=True)
            import sqlite3
            conn = sqlite3.connect(self.config.database_path)
            conn.close()
            print(f"✅ SQLite database created: {self.config.database_path}")
        except Exception as e:
            print(f"❌ Failed to create SQLite database: {e}")
    
    def _setup_faiss(self):
        """Setup FAISS index directory"""
        print("\n🔧 Setting up FAISS index...")
        faiss_dir = os.path.dirname(self.config.faiss_index_path)
        
        try:
            os.makedirs(faiss_dir, exist_ok=True)
            print(f"✅ FAISS directory created: {faiss_dir}")
        except Exception as e:
            print(f"❌ Failed to create FAISS directory: {e}")
    
    def _setup_redis(self):
        """Setup Redis connection"""
        print("\n🔧 Redis setup required...")
        print("Options:")
        print("1. Install Redis locally")
        print("2. Use Docker: docker run -d -p 6382:6379 redis:alpine")
        print("3. Update configuration to point to existing Redis")
        
        choice = input("Choose option (1-3): ").strip()
        
        if choice == "1":
            print("📦 Installing Redis...")
            os.system("sudo apt-get install redis-server")
        elif choice == "2":
            print("🐳 Starting Redis with Docker...")
            os.system("docker run -d -p 6382:6379 redis:alpine")
        elif choice == "3":
            self._update_redis_config()
    
    def _setup_neo4j(self):
        """Setup Neo4j connection"""
        print("\n🔧 Neo4j setup required...")
        print("Options:")
        print("1. Install Neo4j locally")
        print("2. Use Docker: docker run -d -p 7687:7687 neo4j:latest")
        print("3. Update configuration to point to existing Neo4j")
        
        choice = input("Choose option (1-3): ").strip()
        
        if choice == "1":
            print("📦 Installing Neo4j...")
            print("Follow instructions at: https://neo4j.com/docs/operations-manual/current/installation/")
        elif choice == "2":
            print("🐳 Starting Neo4j with Docker...")
            os.system("docker run -d -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest")
        elif choice == "3":
            self._update_neo4j_config()
    
    def _update_redis_config(self):
        """Update Redis configuration"""
        host = input("Redis host [localhost]: ").strip() or "localhost"
        port = input("Redis port [6379]: ").strip() or "6379"
        password = input("Redis password (optional): ").strip() or ""
        
        self.config.redis_host = host
        self.config.redis_port = int(port)
        self.config.redis_password = password
        
        self.save_config()
        print("✅ Redis configuration updated")
    
    def _update_neo4j_config(self):
        """Update Neo4j configuration"""
        uri = input("Neo4j URI [bolt://localhost:7687]: ").strip() or "bolt://localhost:7687"
        user = input("Neo4j username [neo4j]: ").strip() or "neo4j"
        password = input("Neo4j password: ").strip()
        
        self.config.neo4j_uri = uri
        self.config.neo4j_user = user
        self.config.neo4j_password = password
        
        self.save_config()
        print("✅ Neo4j configuration updated")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config_data = asdict(self.config)
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            print(f"✅ Configuration saved to: {self.config_file}")
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
    
    def get_environment_vars(self) -> Dict[str, str]:
        """Get environment variables for LTMC"""
        return {
            "LTMC_DATA_DIR": self.config.base_data_dir,
            "DB_PATH": self.config.database_path,
            "FAISS_INDEX_PATH": self.config.faiss_index_path,
            "VECTOR_DIMENSION": str(self.config.vector_dimension),
            "EMBEDDING_MODEL": self.config.embedding_model,
            "LOG_LEVEL": self.config.log_level,
            "REDIS_ENABLED": str(self.config.redis_enabled).lower(),
            "REDIS_HOST": self.config.redis_host,
            "REDIS_PORT": str(self.config.redis_port),
            "REDIS_PASSWORD": self.config.redis_password,
            "NEO4J_URI": self.config.neo4j_uri,
            "NEO4J_USER": self.config.neo4j_user,
            "NEO4J_PASSWORD": self.config.neo4j_password,
            "NEO4J_ENABLED": str(self.config.neo4j_enabled).lower()
        }


def main():
    """Main function for binary configuration"""
    print("🔧 LTMC Binary Configuration Manager")
    print("=" * 40)
    
    config_manager = BinaryConfigManager()
    
    print(f"\n📁 Configuration: {config_manager.config_file}")
    print(f"🗄️  Data directory: {config_manager.config.base_data_dir}")
    print(f"💾 Database: {config_manager.config.database_path}")
    print(f"🔍 FAISS index: {config_manager.config.faiss_index_path}")
    
    print("\n🔍 Checking dependencies...")
    deps = config_manager.check_dependencies()
    
    if not all(deps.values()):
        print("\n⚠️  Some dependencies are missing!")
        setup = input("Would you like to set them up now? (y/n): ").strip().lower()
        
        if setup == 'y':
            config_manager.setup_missing_dependencies()
        else:
            print("📝 You can run this again later to set up dependencies")
    else:
        print("\n✅ All dependencies are available!")
    
    print("\n🚀 LTMC is ready to run!")


if __name__ == "__main__":
    main()
