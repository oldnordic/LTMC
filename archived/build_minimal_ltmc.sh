#\!/bin/bash
# Minimal LTMC MCP Server Binary Build  
# ===================================
# Professional minimal build - core MCP functionality only

set -e

echo "🔨 Building Minimal LTMC MCP Server Binary..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/ *.spec

# Create minimal PyInstaller build focusing on MCP core functionality
echo "📝 Creating minimal PyInstaller specification..."
PYTHONPATH=/home/feanor/Projects/lmtc pyinstaller --onefile \
    --name ltmc \
    --paths /home/feanor/Projects/lmtc \
    --hidden-import fastmcp \
    --hidden-import aiosqlite \
    --hidden-import pydantic \
    --hidden-import pydantic_settings \
    --collect-submodules ltmc_mcp_server \
    --copy-metadata fastmcp \
    --copy-metadata mcp \
    --copy-metadata pydantic \
    --exclude-module tensorflow \
    --exclude-module torch \
    --exclude-module PyQt5 \
    --exclude-module PyQt6 \
    --exclude-module tkinter \
    --exclude-module matplotlib \
    --exclude-module tensorboard \
    --exclude-module jupyter \
    --exclude-module notebook \
    --exclude-module cv2 \
    --exclude-module sklearn \
    --exclude-module scipy \
    --exclude-module pandas \
    --log-level ERROR \
    ltmc_mcp_server/main.py

# Install the binary
echo "📦 Installing binary to /home/feanor/.local/bin/ltmc..."
mkdir -p /home/feanor/.local/bin
cp dist/ltmc /home/feanor/.local/bin/ltmc
chmod +x /home/feanor/.local/bin/ltmc

echo "✅ Minimal build complete\!"
echo "📍 Binary location: /home/feanor/.local/bin/ltmc"
echo "🔧 Configuration: Uses ltmc_config.json discovery system"
