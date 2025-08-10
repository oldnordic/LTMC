"""
Database Configuration Manager
=============================

Manages connections to all database systems:
- SQLite (ltmc.db with existing schema)
- Redis (port 6382, password 'ltmc_cache_2025') 
- FAISS (semantic vectors)
- Neo4j (port 7687, password 'kwe_password')

Preserves existing database schemas from research.
"""

import asyncio
import aiosqlite
import redis.asyncio as redis
import neo4j
import faiss
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any
import logging

from .settings import LTMCSettings


class DatabaseManager:
    """
    Manages all database connections following MCP security requirements.
    
    Based on research:
    - Existing SQLite schema with Resources, ChatHistory, todos, CodePatterns
    - Redis on port 6382 with password 'ltmc_cache_2025'
    - Neo4j on port 7687 with password 'kwe_password'
    - FAISS index in data/faiss_index directory
    """
    
    def __init__(self, settings: LTMCSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Connection pools/instances
        self.sqlite_pool: Optional[aiosqlite.Connection] = None
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self.neo4j_driver: Optional[neo4j.AsyncDriver] = None
        self.faiss_index: Optional[faiss.IndexFlatL2] = None
        
        # Connection status
        self.connections_initialized = False
        
    async def initialize_all_databases(self) -> Dict[str, bool]:
        """
        Initialize all database connections.
        
        Returns:
            Dict[str, bool]: Status of each database initialization
        """
        results = {}
        
        # Ensure directories exist
        self.settings.ensure_data_directories()
        
        # Initialize SQLite
        try:
            await self._initialize_sqlite()
            results["sqlite"] = True
            self.logger.info("✅ SQLite database initialized")
        except Exception as e:
            results["sqlite"] = False
            self.logger.error(f"❌ SQLite initialization failed: {e}")
        
        # Initialize Redis
        try:
            await self._initialize_redis()
            results["redis"] = True
            self.logger.info("✅ Redis connection initialized")
        except Exception as e:
            results["redis"] = False
            self.logger.error(f"❌ Redis initialization failed: {e}")
        
        # Initialize FAISS
        try:
            await self._initialize_faiss()
            results["faiss"] = True
            self.logger.info("✅ FAISS index initialized")
        except Exception as e:
            results["faiss"] = False
            self.logger.error(f"❌ FAISS initialization failed: {e}")
        
        # Initialize Neo4j
        try:
            await self._initialize_neo4j()
            results["neo4j"] = True
            self.logger.info("✅ Neo4j driver initialized")
        except Exception as e:
            results["neo4j"] = False
            self.logger.error(f"❌ Neo4j initialization failed: {e}")
        
        self.connections_initialized = all(results.values())
        return results
    
    async def _initialize_sqlite(self) -> None:
        """Initialize SQLite with existing schema."""
        # Connect to database
        self.sqlite_pool = await aiosqlite.connect(self.settings.db_path)
        
        # Create tables using async-compatible schema
        await self._create_async_tables(self.sqlite_pool)
        await self.sqlite_pool.commit()
    
    async def _create_async_tables(self, conn: aiosqlite.Connection) -> None:
        """Create full database schema with async operations."""
        cursor = await conn.cursor()
        
        # Resources table (from existing schema)
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS Resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT,
                type TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # ResourceChunks table (from existing schema)
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS ResourceChunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER,
                chunk_text TEXT NOT NULL,
                vector_id INTEGER UNIQUE NOT NULL,
                FOREIGN KEY (resource_id) REFERENCES Resources (id)
            )
        """)
        
        # ChatHistory table (enhanced from existing schema)
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS ChatHistory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                agent_name TEXT,
                metadata TEXT,
                source_tool TEXT
            )
        """)
        
        # ContextLinks table (from existing schema)
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS ContextLinks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER,
                target_id INTEGER,
                relationship TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (source_id) REFERENCES Resources (id),
                FOREIGN KEY (target_id) REFERENCES Resources (id)
            )
        """)
        
        # CodePatterns table (from existing schema)  
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS CodePatterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_prompt TEXT NOT NULL,
                generated_code TEXT NOT NULL,
                result TEXT NOT NULL,
                tags TEXT,
                timestamp TEXT NOT NULL,
                language TEXT,
                complexity_score REAL
            )
        """)
        
        # Todos table (from existing schema)
        await cursor.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'medium',
                created_at TEXT NOT NULL,
                completed_at TEXT,
                tags TEXT,
                metadata TEXT
            )
        """)
        
        await conn.commit()
    
    async def _initialize_redis(self) -> None:
        """Initialize Redis connection pool."""
        if not self.settings.redis_enabled:
            self.logger.info("Redis disabled in settings")
            return
        
        # Create connection pool
        self.redis_pool = redis.ConnectionPool(
            host=self.settings.redis_host,
            port=self.settings.redis_port,
            password=self.settings.redis_password,
            db=self.settings.redis_db,
            decode_responses=True,
            max_connections=10
        )
        
        # Test connection
        redis_client = redis.Redis(connection_pool=self.redis_pool)
        await redis_client.ping()
        await redis_client.close()
    
    async def _initialize_faiss(self) -> None:
        """Initialize FAISS index for semantic search."""
        index_path = self.settings.faiss_index_path
        
        if index_path.exists():
            # Load existing index
            self.faiss_index = faiss.read_index(str(index_path))
            self.logger.info(f"Loaded existing FAISS index with {self.faiss_index.ntotal} vectors")
        else:
            # Create new index (384 dimensions for sentence transformers)
            self.faiss_index = faiss.IndexFlatL2(384)
            faiss.write_index(self.faiss_index, str(index_path))
            self.logger.info("Created new FAISS index")
    
    async def _initialize_neo4j(self) -> None:
        """Initialize Neo4j driver."""
        if not self.settings.neo4j_enabled:
            self.logger.info("Neo4j disabled in settings")
            return
        
        # Create async driver
        self.neo4j_driver = neo4j.AsyncGraphDatabase.driver(
            self.settings.get_neo4j_uri(),
            auth=(self.settings.neo4j_user, self.settings.neo4j_password)
        )
        
        # Test connection
        await self.neo4j_driver.verify_connectivity()
    
    async def close_all_connections(self) -> None:
        """Close all database connections."""
        if self.sqlite_pool:
            await self.sqlite_pool.close()
            
        if self.redis_pool:
            await self.redis_pool.disconnect()
            
        if self.neo4j_driver:
            await self.neo4j_driver.close()
        
        self.logger.info("All database connections closed")