#\!/bin/bash

set -e

echo "🚀 Building LTMC Binary (Simplified)"
echo "===================================="

# Create simple launcher
cat > ltmc_standalone.py << 'PYEOF'
#\!/usr/bin/env python3
import os
import sys
import socket
from pathlib import Path

def setup_env():
    if getattr(sys, 'frozen', False):
        app_dir = Path(sys.executable).parent
    else:
        app_dir = Path(__file__).parent
    
    for dir_name in ['data', 'logs', 'data/faiss_index']:
        (app_dir / dir_name).mkdir(parents=True, exist_ok=True)
    
    # Use centralized data location
    data_dir = Path('/home/feanor/Projects/data')
    data_dir.mkdir(parents=True, exist_ok=True)
    
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
    neo4j_ok = check_port(7689)  # LTMC's own Neo4j port
    
    os.environ['REDIS_ENABLED'] = 'true' if redis_ok else 'false'
    os.environ['REDIS_HOST'] = 'localhost'
    os.environ['REDIS_PORT'] = '6382'
    os.environ['REDIS_PASSWORD'] = 'ltmc_cache_2025'
    
    os.environ['NEO4J_ENABLED'] = 'true' if neo4j_ok else 'false'
    os.environ['NEO4J_URI'] = 'bolt://localhost:7689'  # LTMC's own Neo4j
    os.environ['NEO4J_USER'] = 'neo4j'
    os.environ['NEO4J_PASSWORD'] = 'ltmc_password_2025'  # LTMC's own password
    
    print(f"🎯 LTMC Server Starting")
    print(f"   Redis (6382): {'✅' if redis_ok else '❌'}")
    print(f"   Neo4j (7689): {'✅' if neo4j_ok else '❌'}")  # Show correct port

if __name__ == "__main__":
    setup_env()
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        # Import and run the FastMCP server
        from ltmc_mcp_server.main import mcp
        mcp.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
PYEOF

# Simple spec without problematic imports
cat > simple_ltmc.spec << 'SPECEOF'
# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import copy_metadata, collect_data_files

current_dir = os.path.dirname(os.path.abspath(SPEC))

# Copy metadata for packages that use importlib.metadata
datas = copy_metadata('fastmcp') + copy_metadata('mcp')

a = Analysis(
    ['ltmc_standalone.py'],
    pathex=[current_dir],
    binaries=[],
    datas=datas + [
        ('ltmc_mcp_server', 'ltmc_mcp_server'),
        ('ltms', 'ltms'),
        ('tools', 'tools'),
        ('config', 'config'),
        ('models', 'models'),
        ('services', 'services'),
        ('utils', 'utils'),
    ],
    hiddenimports=[
        'fastmcp',
        'fastmcp.server',
        'mcp',
        'mcp.server',
        'mcp.server.fastmcp',
        'redis',
        'neo4j',
        'qdrant_client',
        'faiss',
        'numpy',
        'asyncio',
        'asyncpg',
        'aiofiles',
        'uvicorn',
        'fastapi',
        'pydantic',
        'sqlite3',
        'json',
        'logging'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'PIL', 'PyQt5', 'PyQt6'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ltmc-server',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
SPECEOF

echo "Building binary..."
mkdir -p dist
pyinstaller simple_ltmc.spec --distpath dist --workpath build --noconfirm --clean

if [ -f "dist/ltmc-server" ]; then
    chmod +x dist/ltmc-server
    echo "✅ Binary created: $(pwd)/dist/ltmc-server"
    
    echo "Testing binary..."
    timeout 3 ./dist/ltmc-server --help 2>/dev/null || echo "Binary executable"
    
    echo "🎉 Build complete\!"
    echo "Binary location: $(pwd)/dist/ltmc-server"
else
    echo "❌ Build failed"
    exit 1
fi

rm -f ltmc_standalone.py simple_ltmc.spec
rm -rf build/
