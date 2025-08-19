#!/usr/bin/env python3
"""
LTMC MCP Binary - Fixed Entry Point for PyInstaller
==================================================

This entry point addresses all PyInstaller compatibility issues with MCP stdio transport:

1. Unbuffered stdio handling for immediate JSON-RPC message transmission  
2. UTF-8 encoding enforcement for proper character handling
3. Signal handlers for graceful shutdown when MCP clients disconnect
4. Manual stdio flushing to overcome PyInstaller buffering issues
5. Proper MCP protocol initialization sequence

Based on official MCP Python SDK patterns and PyInstaller documentation.
"""

import os
import sys
import signal
import asyncio
import logging
from pathlib import Path
from io import TextIOWrapper

# Set UTF-8 environment BEFORE any imports
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'

# PyInstaller path setup
if getattr(sys, 'frozen', False):
    # Running as PyInstaller binary
    application_path = sys._MEIPASS
    sys.path.insert(0, application_path)
    
    # Add LTMC server path specifically for PyInstaller
    server_path = os.path.join(application_path, 'ltmc_mcp_server')
    if os.path.exists(server_path):
        sys.path.insert(0, server_path)
else:
    # Running as script - add project root
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

# Suppress TensorFlow warnings for cleaner MCP output
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'


class BinaryStdioManager:
    """
    Manages stdio for PyInstaller binaries with MCP compatibility.
    
    Addresses PyInstaller issues:
    - Buffering problems that delay JSON-RPC messages
    - UTF-8 encoding issues in binary execution
    - Proper stream flushing for real-time communication
    """
    
    def __init__(self):
        self.setup_utf8_stdio()
    
    def setup_utf8_stdio(self):
        """Set up UTF-8 stdio streams for PyInstaller binary."""
        try:
            # Force UTF-8 encoding for stdin/stdout
            if hasattr(sys.stdin, 'buffer'):
                sys.stdin = TextIOWrapper(
                    sys.stdin.buffer,
                    encoding='utf-8',
                    line_buffering=True,
                    write_through=True
                )
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout = TextIOWrapper(
                    sys.stdout.buffer,
                    encoding='utf-8',
                    line_buffering=True,
                    write_through=True
                )
        except Exception as e:
            # Fallback for environments where buffer access fails
            print(f"Warning: Could not reconfigure stdio: {e}", file=sys.stderr)
    
    @staticmethod
    def flush_streams():
        """Manually flush stdio streams - critical for PyInstaller."""
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass


class GracefulShutdownHandler:
    """
    Handles graceful shutdown for MCP binary when clients disconnect.
    
    MCP clients expect servers to handle SIGTERM/SIGINT properly.
    """
    
    def __init__(self):
        self.shutting_down = False
        self.setup_signal_handlers()
    
    def setup_signal_handlers(self):
        """Set up cross-platform signal handlers."""
        def shutdown_handler(signum, frame):
            if not self.shutting_down:
                self.shutting_down = True
                print("MCP server shutting down gracefully", file=sys.stderr)
                sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)
        
        # Windows compatibility
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, shutdown_handler)


async def create_ltmc_server():
    """Create LTMC MCP server with PyInstaller compatibility."""
    try:
        # Import after path setup
        from ltmc_mcp_server.main import create_server
        
        # Create server with all tools
        server = await create_server()
        return server
        
    except ImportError as e:
        print(f"Import error in PyInstaller binary: {e}", file=sys.stderr)
        print(f"Python path: {sys.path}", file=sys.stderr)
        
        # Debug: Show available modules in PyInstaller bundle
        if getattr(sys, 'frozen', False):
            try:
                import os
                print("Available modules in bundle:", file=sys.stderr)
                for item in os.listdir(sys._MEIPASS):
                    print(f"  {item}", file=sys.stderr)
            except:
                pass
        sys.exit(1)
    except Exception as e:
        print(f"Error creating LTMC server: {e}", file=sys.stderr)
        sys.exit(1)


async def run_mcp_server():
    """Run LTMC MCP server with proper PyInstaller compatibility."""
    # Set up PyInstaller stdio management
    stdio_manager = BinaryStdioManager()
    shutdown_handler = GracefulShutdownHandler()
    
    try:
        # Create the LTMC server
        server = await create_ltmc_server()
        
        # Ensure streams are properly flushed before starting MCP protocol
        stdio_manager.flush_streams()
        
        # Run the MCP server with stdio transport
        await server.run_stdio_async()
        
    except KeyboardInterrupt:
        print("MCP server interrupted", file=sys.stderr)
    except Exception as e:
        print(f"MCP server error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        stdio_manager.flush_streams()


def main():
    """
    Main entry point with PyInstaller-compatible asyncio handling.
    
    Handles the asyncio event loop properly for both PyInstaller binaries
    and normal script execution.
    """
    try:
        # Check for existing event loop (e.g., in development environments)
        try:
            loop = asyncio.get_running_loop()
            # Running inside existing event loop - create task
            task = loop.create_task(run_mcp_server())
            return task
        except RuntimeError:
            # No existing event loop - safe to create one
            asyncio.run(run_mcp_server())
            
    except KeyboardInterrupt:
        print("LTMC MCP server stopped", file=sys.stderr)
    except Exception as e:
        print(f"Failed to start LTMC MCP server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()