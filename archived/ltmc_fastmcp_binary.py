#!/usr/bin/env python3
"""
LTMC FastMCP Binary - Proper MCP Server Implementation
=====================================================

Standalone binary using proper FastMCP framework with correct stdio logging.
Fixes the original main.py import issues while maintaining all 126 tools.
"""

import os
import sys
from pathlib import Path

# Setup environment for binary execution
if getattr(sys, 'frozen', False):
    # Running as PyInstaller binary
    app_dir = Path(sys.executable).parent
else:
    # Running as script
    app_dir = Path(__file__).parent

# Add project root to path for imports
sys.path.insert(0, str(app_dir))

# Set up data directories in user space
home_dir = Path.home()
data_dir = home_dir / '.local' / 'share' / 'ltmc'
config_dir = home_dir / '.config' / 'ltmc'

# Create necessary directories
for dir_path in [data_dir, config_dir, data_dir / 'faiss_index', data_dir / 'logs']:
    dir_path.mkdir(parents=True, exist_ok=True)

# Set environment variables for configuration
os.environ['DB_PATH'] = str(data_dir / 'ltmc.db')
os.environ['LTMC_DATA_DIR'] = str(data_dir)
os.environ['FAISS_INDEX_PATH'] = str(data_dir / 'faiss_index')
os.environ['LOG_LEVEL'] = os.environ.get('LOG_LEVEL', 'WARNING')

def main():
    """Main entry point for LTMC FastMCP binary."""
    try:
        # Import and run the main LTMC server
        # This approach avoids relative import issues by running as module
        from ltmc_mcp_server.main import main as ltmc_main
        ltmc_main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        import logging
        logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
        logger = logging.getLogger(__name__)
        logger.error(f"❌ LTMC server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()