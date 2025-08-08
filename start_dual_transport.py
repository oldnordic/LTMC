#!/usr/bin/env python3
"""LTMC Dual Transport Server Manager

Starts both STDIO and HTTP transports for LTMC MCP server.
- STDIO transport via FastMCP (for MCP clients like Claude Desktop)
- HTTP transport via FastAPI (for web clients and curl)
"""

import os
import sys
import signal
import subprocess
import time
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.chdir(str(project_root))


class LTMCDualTransportManager:
    """Manages dual transport LTMC server processes."""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = False
        
    def start_stdio_transport(self) -> subprocess.Popen:
        """Start the STDIO transport using FastMCP."""
        print("Starting LTMC MCP Server - STDIO Transport (FastMCP)")
        
        cmd = [
            sys.executable, 
            "ltmc_mcp_server.py"
        ]
        
        # Set environment for STDIO transport
        env = os.environ.copy()
        env['DB_PATH'] = 'ltmc.db'
        env['FAISS_INDEX_PATH'] = 'faiss_index'
        
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        
        print(f"STDIO transport started (PID: {process.pid})")
        return process
    
    def start_http_transport(self) -> subprocess.Popen:
        """Start the HTTP transport using FastAPI/uvicorn."""
        print("Starting LTMC MCP Server - HTTP Transport (FastAPI)")
        
        cmd = [
            sys.executable, "-c",
            """
import uvicorn
from ltms.mcp_server_http import app
import os
os.environ['DB_PATH'] = 'ltmc.db'
os.environ['FAISS_INDEX_PATH'] = 'faiss_index'
print("HTTP Server starting on http://localhost:5050")
uvicorn.run(app, host='localhost', port=5050, log_level='info')
"""
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print(f"HTTP transport started (PID: {process.pid})")
        print("HTTP Server will be available on http://localhost:5050")
        return process
    
    def start(self):
        """Start both transports."""
        try:
            print("="*60)
            print("LTMC Dual Transport Server Manager")
            print("="*60)
            print(f"Database: {os.getenv('DB_PATH', 'ltmc.db')}")
            print(f"FAISS Index: {os.getenv('FAISS_INDEX_PATH', 'faiss_index')}")
            print()
            
            # Start STDIO transport
            stdio_process = self.start_stdio_transport()
            self.processes.append(stdio_process)
            
            print()
            
            # Start HTTP transport
            http_process = self.start_http_transport()
            self.processes.append(http_process)
            
            print()
            print("Both transports started successfully!")
            print("- STDIO: Available for MCP clients (Claude Desktop, etc.)")
            print("- HTTP:  Available at http://localhost:5050")
            print()
            print("Press Ctrl+C to stop both servers")
            print("="*60)
            
            self.running = True
            self.wait_for_shutdown()
            
        except Exception as e:
            print(f"Error starting servers: {e}")
            self.shutdown()
            return 1
        
        return 0
    
    def wait_for_shutdown(self):
        """Wait for shutdown signal or process termination."""
        try:
            while self.running:
                time.sleep(1)
                
                # Check if any process has died
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        transport_type = "STDIO" if i == 0 else "HTTP"
                        print(f"\\n{transport_type} transport process died (PID: {process.pid})")
                        self.shutdown()
                        return
                        
        except KeyboardInterrupt:
            print("\\nReceived shutdown signal...")
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown all processes."""
        if not self.running:
            return
            
        self.running = False
        print("Shutting down both transports...")
        
        for i, process in enumerate(self.processes):
            if process.poll() is None:  # Process is still running
                transport_type = "STDIO" if i == 0 else "HTTP"
                print(f"Stopping {transport_type} transport (PID: {process.pid})")
                
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"Force killing {transport_type} transport")
                    process.kill()
                    process.wait()
        
        print("All transports stopped.")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            print(f"\\nReceived signal {signum}")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


def main():
    """Main entry point."""
    manager = LTMCDualTransportManager()
    manager.setup_signal_handlers()
    return manager.start()


if __name__ == "__main__":
    sys.exit(main())