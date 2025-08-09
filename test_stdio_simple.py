#!/usr/bin/env python3
"""Simple test to understand STDIO behavior."""

import sys
import json
from pathlib import Path

# Add project root to path  
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and setup MCP server
from ltms.mcp_server import mcp

class OutputCapture:
    def __init__(self):
        self.original_stdout = sys.stdout
        self.captured_output = []
        
    def write(self, data):
        self.captured_output.append(data)
        print(f"CAPTURED: {repr(data)}", file=sys.stderr)
        self.original_stdout.write(data)
        
    def flush(self):
        self.original_stdout.flush()

if __name__ == "__main__":
    # Capture output
    capture = OutputCapture()
    sys.stdout = capture
    
    try:
        mcp.run(transport='stdio')
    finally:
        sys.stdout = capture.original_stdout