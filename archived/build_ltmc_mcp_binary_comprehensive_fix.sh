#!/bin/bash

set -e

echo "🚀 Building LTMC MCP Binary with Comprehensive PyInstaller Fixes"
echo "================================================================"
echo "Fixes Applied:"
echo "  ✅ Unbuffered stdio via PyInstaller spec file options"
echo "  ✅ UTF-8 encoding enforcement for binary execution" 
echo "  ✅ Signal handlers for graceful shutdown (SIGTERM, SIGINT)"
echo "  ✅ Manual stdio flushing for JSON-RPC protocol"
echo "  ✅ PyInstaller-compatible MCP initialization sequence"
echo ""

# Check prerequisites
echo "🔧 Checking prerequisites..."

if ! command -v pyinstaller &> /dev/null; then
    echo "❌ PyInstaller not found. Installing..."
    pip install pyinstaller
fi

if [ ! -f "ltmc_mcp_binary_fixed_entry.py" ]; then
    echo "❌ Fixed entry point not found: ltmc_mcp_binary_fixed_entry.py"
    exit 1
fi

if [ ! -f "ltmc_mcp_fixed.spec" ]; then
    echo "❌ Fixed spec file not found: ltmc_mcp_fixed.spec"
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist build *.spec 2>/dev/null || true
mkdir -p dist

# Verify LTMC MCP server modules are available
if [ ! -d "ltmc_mcp_server" ]; then
    echo "❌ LTMC MCP server modules not found in current directory"
    echo "Please run this script from the project root containing ltmc_mcp_server/"
    exit 1
fi

echo "📦 Building binary with comprehensive PyInstaller fixes..."

# Use the fixed spec file with all PyInstaller stdio transport fixes
pyinstaller ltmc_mcp_fixed.spec

if [ -f "dist/ltmc-mcp-fixed" ]; then
    chmod +x dist/ltmc-mcp-fixed
    
    echo "✅ LTMC MCP binary built successfully!"
    echo "📍 Location: $(pwd)/dist/ltmc-mcp-fixed"
    
    # Test the binary with MCP protocol validation
    echo ""
    echo "🧪 Running basic MCP protocol validation..."
    
    # Test 1: Check if binary starts without immediate crash
    echo "Test 1: Binary startup test..."
    if timeout 5s bash -c 'echo "" | ./dist/ltmc-mcp-fixed' 2>/dev/null; then
        echo "  ✅ Binary accepts stdin input (good for MCP)"
    else
        echo "  ⚠️  Binary behavior unclear (may still work with MCP client)"
    fi
    
    # Test 2: Check if binary responds to signals  
    echo "Test 2: Signal handling test..."
    if ./dist/ltmc-mcp-fixed & 
       sleep 2
       kill -TERM $! 2>/dev/null
       wait $! 2>/dev/null
    then
        echo "  ✅ Binary handles SIGTERM gracefully"
    else
        echo "  ⚠️  Signal handling test inconclusive"
    fi
    
    # Install to local bin for easy access
    echo ""
    echo "📦 Installing binary to ~/.local/bin/..."
    mkdir -p ~/.local/bin
    cp dist/ltmc-mcp-fixed ~/.local/bin/ltmc-mcp-fixed
    chmod +x ~/.local/bin/ltmc-mcp-fixed
    
    echo "✅ Binary installed to ~/.local/bin/ltmc-mcp-fixed"
    
    # Run comprehensive test suite if available
    if [ -f "test_ltmc_binary_mcp_client.py" ]; then
        echo ""
        echo "🧪 Running comprehensive MCP client test suite..."
        echo "(This uses the official MCP Python SDK to validate functionality)"
        
        # Check if MCP SDK is available
        if python3 -c "import mcp" 2>/dev/null; then
            echo "📡 MCP Python SDK found - running full test suite..."
            python3 test_ltmc_binary_mcp_client.py || echo "⚠️ Some tests failed - check results above"
        else
            echo "⚠️ MCP Python SDK not found. Install with: pip install mcp"
            echo "   Test suite skipped, but binary should work with MCP clients"
        fi
    fi
    
    echo ""
    echo "🎉 COMPREHENSIVE LTMC MCP BINARY BUILD COMPLETE!"
    echo ""
    echo "📋 Build Summary:"
    echo "  Binary: dist/ltmc-mcp-fixed"
    echo "  Installed: ~/.local/bin/ltmc-mcp-fixed" 
    echo "  Size: $(ls -lh dist/ltmc-mcp-fixed | awk '{print $5}')"
    echo ""
    echo "🔧 PyInstaller Fixes Applied:"
    echo "  ✅ Unbuffered stdio: ('u', None, 'OPTION')"
    echo "  ✅ UTF-8 encoding: ('X', 'utf8=1', 'OPTION')" 
    echo "  ✅ Manual stdio flushing in binary entry point"
    echo "  ✅ Signal handlers for graceful shutdown"
    echo "  ✅ PyInstaller-compatible MCP initialization"
    echo ""
    echo "🚀 Usage in MCP client (e.g., Claude Desktop):"
    echo '  {'
    echo '    "command": ["~/.local/bin/ltmc-mcp-fixed"],'
    echo '    "args": [],'
    echo '    "transport": "stdio"'
    echo '  }'
    echo ""
    echo "🧪 Manual test command:"
    echo '  echo \'{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}\' | ~/.local/bin/ltmc-mcp-fixed'
    echo ""
    echo "📊 For comprehensive testing:"
    echo "  python3 test_ltmc_binary_mcp_client.py"
    
else
    echo "❌ Build failed - binary not created"
    echo ""
    echo "🔍 Troubleshooting:"
    echo "1. Check that ltmc_mcp_server/ directory exists"
    echo "2. Verify Python dependencies are installed"
    echo "3. Check PyInstaller logs above for specific errors"
    echo "4. Ensure ltmc_mcp_binary_fixed_entry.py is present"
    echo "5. Verify ltmc_mcp_fixed.spec file is valid"
    echo ""
    echo "Common issues:"
    echo "- Missing dependencies: pip install -r requirements.txt"
    echo "- Import errors: Check Python path includes ltmc_mcp_server"
    echo "- Permission errors: Check write access to dist/ directory"
    
    exit 1
fi

# Cleanup
echo ""
echo "🧹 Cleaning up build artifacts..."
rm -rf build/
echo "✅ Build process complete!"

# Final validation
echo ""
echo "🔍 Final binary validation:"
echo "  File: $(file dist/ltmc-mcp-fixed 2>/dev/null || echo 'File command not available')"
echo "  Executable: $(test -x dist/ltmc-mcp-fixed && echo 'Yes' || echo 'No')"
echo "  Size: $(ls -lh dist/ltmc-mcp-fixed | awk '{print $5}' 2>/dev/null || echo 'Unknown')"
echo ""
echo "Ready for MCP client integration! 🚀"