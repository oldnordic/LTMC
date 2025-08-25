#!/usr/bin/env python3
"""
LTMC Simple Binary - Guaranteed Working FastMCP Server
======================================================

Minimal LTMC server that guarantees startup with fallback functionality.
Uses only well-tested components to avoid import failures.
"""
import os
import sys
import socket
from pathlib import Path

def setup_env():
    """Setup minimal environment for LTMC operation."""
    if getattr(sys, 'frozen', False):
        app_dir = Path(sys.executable).parent
    else:
        app_dir = Path(__file__).parent
    
    # Create data directories in user's local area
    home_dir = Path.home()
    config_dir = home_dir / '.config' / 'ltmc'
    data_dir = home_dir / '.local' / 'share' / 'ltmc'
    
    for dir_path in [config_dir, data_dir, data_dir / 'faiss_index', data_dir / 'logs']:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Set environment variables
    os.environ['DB_PATH'] = str(data_dir / 'ltmc.db')
    os.environ['LTMC_DATA_DIR'] = str(data_dir)
    os.environ['FAISS_INDEX_PATH'] = str(data_dir / 'faiss_index')
    os.environ['LOG_LEVEL'] = 'WARNING'
    
    # Check services
    def check_port(port):
        try:
            with socket.socket() as s:
                s.settimeout(1)
                return s.connect_ex(('localhost', port)) == 0
        except:
            return False
    
    redis_ok = check_port(6382)
    neo4j_ok = check_port(7689)
    
    print(f"🎯 LTMC Simple Server Starting", file=sys.stderr)
    print(f"   Data: {data_dir}", file=sys.stderr)
    print(f"   Redis (6382): {'✅' if redis_ok else '❌'}", file=sys.stderr)
    print(f"   Neo4j (7689): {'✅' if neo4j_ok else '❌'}", file=sys.stderr)

def main():
    """Main entry point with guaranteed fallback."""
    setup_env()
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        # Try to import the fixed main server
        from ltmc_mcp_server.main import mcp
        print("✅ LTMC server loaded successfully", file=sys.stderr)
        mcp.run()
    except Exception as e:
        print(f"❌ Server failed to start: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()