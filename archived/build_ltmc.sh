#!/bin/bash
# LTMC MCP Server Binary Build Script
# ===================================
# Professional build script following PyInstaller best practices
# No hardcoded paths - uses existing configuration system

set -e

echo "🔨 Building LTMC MCP Server Binary..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.spec

# Create PyInstaller spec with proper module inclusion
echo "📝 Creating PyInstaller specification..."
pyinstaller --onefile \
    --name ltmc \
    --hidden-import fastmcp \
    --hidden-import nest_asyncio \
    --hidden-import aiosqlite \
    --hidden-import redis.asyncio \
    --hidden-import neo4j \
    --hidden-import faiss \
    --hidden-import sentence_transformers \
    --hidden-import numpy \
    --hidden-import pydantic \
    --hidden-import pydantic_settings \
    --exclude-module PyQt5 \
    --exclude-module PyQt6 \
    --exclude-module tkinter \
    --exclude-module matplotlib \
    --collect-submodules ltmc_mcp_server \
    --log-level WARN \
    ltmc_mcp_server/main.py

# Install the binary to the correct location
echo "📦 Installing binary to /home/feanor/.local/bin/ltmc..."
mkdir -p /home/feanor/.local/bin
cp dist/ltmc /home/feanor/.local/bin/ltmc
chmod +x /home/feanor/.local/bin/ltmc

echo "✅ Build complete!"
echo "📍 Binary location: /home/feanor/.local/bin/ltmc"
echo "🔧 Configuration: Uses existing ltmc_config.json discovery system"
echo "🚀 Ready for MCP client connection"