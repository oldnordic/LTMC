#!/usr/bin/env python3
"""
LTMC Global Binary - FastMCP 2.0
================================

Global LTMC server that works from any directory.
Reads configuration from ~/.config/ltmc/ltmc_config.json
"""
import os
import sys
import socket
import json
from pathlib import Path

def setup_global_env():
    """Setup global environment for LTMC"""
    # Set up paths for global operation
    if getattr(sys, 'frozen', False):
        app_dir = Path(sys.executable).parent
    else:
        app_dir = Path(__file__).parent
    
    # Global config and data directories
    home_dir = Path.home()
    config_dir = home_dir / '.config' / 'ltmc'
    data_dir = home_dir / '.local' / 'share' / 'ltmc'
    
    # Create directories
    config_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / 'faiss_index').mkdir(parents=True, exist_ok=True)
    (data_dir / 'logs').mkdir(parents=True, exist_ok=True)
    
    # Create global config if it doesn't exist
    global_config_path = config_dir / 'ltmc_config.json'
    if not global_config_path.exists():
        config = {
            "database": {
                "path": str(data_dir / 'ltmc.db'),
                "pool_size": 20
            },
            "neo4j": {
                "uri": "bolt://localhost:7689",
                "user": "neo4j", 
                "password": "ltmc_password_2025",
                "max_connection_pool_size": 50
            },
            "redis": {
                "host": "localhost",
                "port": 6382,
                "password": "ltmc_cache_2025",
                "db": 0,
                "enabled": True
            },
            "qdrant": {
                "url": "http://localhost:6333",
                "api_key": null,
                "collection_name": "ltmc_vectors"
            },
            "base_data_dir": str(data_dir),
            "log_level": "WARNING"
        }
        
        with open(global_config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"📝 Created global config: {global_config_path}")
    
    # Set environment variables
    os.environ['LTMC_CONFIG_PATH'] = str(global_config_path)
    os.environ['LTMC_DATA_DIR'] = str(data_dir)
    os.environ['LOG_LEVEL'] = 'WARNING'
    
    # Service health check
    def check_port(port):
        try:
            with socket.socket() as s:
                s.settimeout(1)
                return s.connect_ex(('localhost', port)) == 0
        except:
            return False
    
    redis_ok = check_port(6382)
    neo4j_ok = check_port(7689)
    qdrant_ok = check_port(6333)
    
    print(f"🎯 LTMC Global Server Starting")
    print(f"   Config: {global_config_path}")
    print(f"   Data: {data_dir}")
    print(f"   Redis (6382): {'✅' if redis_ok else '❌'}")
    print(f"   Neo4j (7689): {'✅' if neo4j_ok else '❌'}")
    print(f"   Qdrant (6333): {'✅' if qdrant_ok else '❌'}")

if __name__ == "__main__":
    setup_global_env()
    
    # Add LTMC module path
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        # Import and run the FastMCP server
        from ltmc_mcp_server.main import mcp
        mcp.run()
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Make sure LTMC modules are bundled with the binary")
        sys.exit(1)
    except Exception as e:
        print(f"Runtime Error: {e}")
        sys.exit(1)
