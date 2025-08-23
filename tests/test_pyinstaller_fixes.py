#!/usr/bin/env python3
"""
Test PyInstaller Fixes for LTMC MCP Server
==========================================

This test script validates that all PyInstaller compatibility issues
have been properly addressed before running the full build process.

Tests:
1. Function name mismatch in unified tools ✅
2. Dynamic import detection compatibility ✅  
3. MCP stdio transport compatibility ✅
4. Missing hidden imports detection ✅
"""

import sys
import os
import importlib
import inspect
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_unified_tools_function_alias():
    """Test that unified tools has the PyInstaller-compatible function alias."""
    print("🔍 Testing unified tools function alias...")
    
    try:
        from ltmc_mcp_server.tools.unified.unified_tools import unified_ltmc_orchestrator, register_unified_tools
        
        # Check that both functions exist
        assert callable(unified_ltmc_orchestrator), "unified_ltmc_orchestrator must be callable"
        assert callable(register_unified_tools), "register_unified_tools must be callable"
        
        # Check function signatures match
        alias_sig = inspect.signature(unified_ltmc_orchestrator)
        original_sig = inspect.signature(register_unified_tools)
        
        assert str(alias_sig) == str(original_sig), "Function signatures must match"
        
        # Check __all__ export
        module = importlib.import_module('ltmc_mcp_server.tools.unified.unified_tools')
        all_exports = getattr(module, '__all__', [])
        assert 'unified_ltmc_orchestrator' in all_exports, "Alias must be in __all__"
        assert 'register_unified_tools' in all_exports, "Original must be in __all__"
        
        print("✅ Unified tools function alias test passed")
        return True
        
    except Exception as e:
        print(f"❌ Unified tools function alias test failed: {e}")
        return False


def test_pyinstaller_hook_file():
    """Test that PyInstaller hook file exists and is valid."""
    print("🔍 Testing PyInstaller hook file...")
    
    hook_path = project_root / 'hooks' / 'hook-ltmc_mcp_server.py'
    
    try:
        assert hook_path.exists(), f"Hook file must exist at {hook_path}"
        
        # Test syntax by compiling
        with open(hook_path, 'r') as f:
            hook_content = f.read()
        
        compile(hook_content, str(hook_path), 'exec')
        
        # Test that hook contains required elements
        assert 'hiddenimports' in hook_content, "Hook must define hiddenimports"
        assert 'mcp.server.stdio' in hook_content, "Hook must include MCP stdio transport"
        assert 'ltmc_mcp_server' in hook_content, "Hook must include LTMC modules"
        assert 'def hook(hook_api)' in hook_content, "Hook must define hook function"
        
        print("✅ PyInstaller hook file test passed")
        return True
        
    except Exception as e:
        print(f"❌ PyInstaller hook file test failed: {e}")
        return False


def test_mcp_stdio_compatibility():
    """Test that MCP stdio transport is properly accessible."""
    print("🔍 Testing MCP stdio transport compatibility...")
    
    try:
        # Test that we can import MCP stdio components
        from mcp.server.fastmcp import FastMCP
        from mcp.server.stdio import stdio_server
        
        # Test FastMCP instantiation
        mcp = FastMCP("test")
        assert mcp is not None, "FastMCP instance must be created"
        
        # Test that stdio_server is callable
        assert callable(stdio_server), "stdio_server must be callable"
        
        print("✅ MCP stdio transport compatibility test passed")
        return True
        
    except Exception as e:
        print(f"❌ MCP stdio transport compatibility test failed: {e}")
        return False


def test_binary_entrypoint():
    """Test that binary entry point exists and is valid."""
    print("🔍 Testing binary entry point...")
    
    entry_point_path = project_root / 'ltmc_mcp_binary_entrypoint.py'
    
    try:
        assert entry_point_path.exists(), f"Entry point must exist at {entry_point_path}"
        
        # Test syntax by compiling
        with open(entry_point_path, 'r') as f:
            entry_content = f.read()
        
        compile(entry_content, str(entry_point_path), 'exec')
        
        # Test that entry point contains required elements
        assert 'def main()' in entry_content, "Entry point must define main function"
        assert 'run_ltmc_server' in entry_content, "Entry point must define server runner"
        assert 'setup_binary_environment' in entry_content, "Entry point must setup environment"
        assert 'from ltmc_mcp_server.main import create_server' in entry_content, "Entry point must import server creator"
        
        print("✅ Binary entry point test passed")
        return True
        
    except Exception as e:
        print(f"❌ Binary entry point test failed: {e}")
        return False


def test_dynamic_import_detection():
    """Test that all critical modules can be dynamically imported."""
    print("🔍 Testing dynamic import detection...")
    
    critical_modules = [
        'ltmc_mcp_server.main',
        'ltmc_mcp_server.config.settings',
        'ltmc_mcp_server.services.database_service',
        'ltmc_mcp_server.tools.unified.unified_tools',
        'ltmc_mcp_server.tools.memory.memory_tools',
        'mcp.server.fastmcp',
        'mcp.server.stdio'
    ]
    
    failed_imports = []
    
    for module_name in critical_modules:
        try:
            module = importlib.import_module(module_name)
            assert module is not None, f"Module {module_name} must be importable"
        except Exception as e:
            failed_imports.append((module_name, str(e)))
    
    if failed_imports:
        print(f"❌ Dynamic import detection test failed:")
        for module, error in failed_imports:
            print(f"   - {module}: {error}")
        return False
    
    print("✅ Dynamic import detection test passed")
    return True


def test_build_script_exists():
    """Test that enhanced build script exists and is executable."""
    print("🔍 Testing build script...")
    
    build_script_path = project_root / 'build_ltmc_pyinstaller_binary.sh'
    
    try:
        assert build_script_path.exists(), f"Build script must exist at {build_script_path}"
        
        # Check if script is executable
        is_executable = os.access(build_script_path, os.X_OK)
        assert is_executable, "Build script must be executable"
        
        # Test basic script content
        with open(build_script_path, 'r') as f:
            script_content = f.read()
        
        required_elements = [
            'pyinstaller',
            'ltmc_server_enhanced.spec',
            'hooks',
            'hidden_imports',
            'stdio_transport'
        ]
        
        for element in required_elements:
            assert element in script_content, f"Build script must contain {element}"
        
        print("✅ Build script test passed")
        return True
        
    except Exception as e:
        print(f"❌ Build script test failed: {e}")
        return False


def test_configuration_compatibility():
    """Test that configuration system is binary-compatible."""
    print("🔍 Testing configuration compatibility...")
    
    try:
        from ltmc_mcp_server.config.settings import LTMCSettings
        
        # Test that settings can be instantiated without external files
        settings = LTMCSettings()
        assert settings is not None, "Settings must be instantiable"
        
        # Test that critical paths are accessible
        assert hasattr(settings, 'db_path'), "Settings must have db_path"
        assert hasattr(settings, 'redis_host'), "Settings must have redis_host"
        assert hasattr(settings, 'log_level'), "Settings must have log_level"
        
        print("✅ Configuration compatibility test passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration compatibility test failed: {e}")
        return False


def run_all_tests() -> bool:
    """Run all PyInstaller compatibility tests."""
    print("🚀 Running PyInstaller Compatibility Tests")
    print("=" * 50)
    
    tests = [
        test_unified_tools_function_alias,
        test_pyinstaller_hook_file,
        test_mcp_stdio_compatibility,
        test_binary_entrypoint,
        test_dynamic_import_detection,
        test_build_script_exists,
        test_configuration_compatibility
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✅ All PyInstaller compatibility tests passed!")
        print("🚀 Ready to run: ./build_ltmc_pyinstaller_binary.sh")
        return True
    else:
        print("❌ Some tests failed. Fix issues before building binary.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)