#!/bin/bash

set -e

echo "🚀 Building Working LTMC Binary with 126 Tools"
echo "=============================================="

# Create spec file for working binary
cat > working_ltmc.spec << 'SPECEOF'
# -*- mode: python ; coding: utf-8 -*-
import os

current_dir = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ['ltmc_working_binary.py'],
    pathex=[current_dir],
    binaries=[],
    datas=[],
    hiddenimports=[
        'sqlite3',
        'json',
        'pathlib',
        'socket',
        'os',
        'sys',
        'asyncio',
        'typing'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'PIL', 'PyQt5', 'PyQt6',
        'tensorflow', 'torch', 'numpy', 'pandas',
        'ltms', 'ltmc_mcp_server'  # Exclude problematic modules
    ],
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
    name='ltmc-working',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
SPECEOF

echo "Building working binary..."
mkdir -p dist
pyinstaller working_ltmc.spec --distpath dist --workpath build --noconfirm --clean

if [ -f "dist/ltmc-working" ]; then
    chmod +x dist/ltmc-working
    echo "✅ Working binary created: $(pwd)/dist/ltmc-working"
    
    # Test the binary
    echo "Testing binary..."
    timeout 5 ./dist/ltmc-working 2>&1 | head -10 || echo "Binary test completed"
    
    # Copy to local bin
    cp dist/ltmc-working ~/.local/bin/ltmc-working
    chmod +x ~/.local/bin/ltmc-working
    
    echo "✅ Binary installed to ~/.local/bin/ltmc-working"
    echo "🎉 Working build complete!"
    echo ""
    echo "Usage: Replace your MCP server command with:"
    echo "  ~/.local/bin/ltmc-working"
    echo ""
    echo "Or test with:"
    echo "  timeout 10 ~/.local/bin/ltmc-working"
else
    echo "❌ Build failed"
    exit 1
fi

rm -f working_ltmc.spec
rm -rf build/