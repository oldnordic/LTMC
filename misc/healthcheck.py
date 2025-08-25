#!/usr/bin/env python3
"""
LTMC MCP Server Health Check Script
==================================

Comprehensive health check for production deployment validation.
"""

import asyncio
import sys
import json
import subprocess
import time
from pathlib import Path

async def check_mcp_server_health():
    """Check MCP server health via stdio protocol."""
    try:
        # Test MCP protocol response
        process = await asyncio.create_subprocess_exec(
            sys.executable, "ltmc_stdio_wrapper.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Send ping request
        ping_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "ping",
                "arguments": {}
            }
        }
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(json.dumps(ping_request).encode() + b'\n'),
            timeout=5.0
        )
        
        if process.returncode == 0:
            response = json.loads(stdout.decode())
            if response.get("result", {}).get("status") == "pong":
                return True
        
        return False
        
    except Exception:
        return False

async def check_dependencies():
    """Check critical dependencies availability."""
    checks = {
        'redis': await check_redis(),
        'neo4j': await check_neo4j(), 
        'postgres': await check_postgres(),
        'file_system': check_file_system()
    }
    
    return all(checks.values())

async def check_redis():
    """Check Redis connectivity."""
    try:
        import redis
        client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        return client.ping()
    except:
        return False

async def check_neo4j():
    """Check Neo4j connectivity."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver("bolt://localhost:7687")
        with driver.session() as session:
            result = session.run("RETURN 1")
            return result.single()[0] == 1
    except:
        return False

async def check_postgres():
    """Check PostgreSQL connectivity."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="ltmc",
            user="ltmc"
        )
        conn.close()
        return True
    except:
        return False

def check_file_system():
    """Check file system accessibility."""
    try:
        # Check writable data directory
        data_dir = Path("/app/data")
        data_dir.mkdir(exist_ok=True)
        
        test_file = data_dir / "health_check.tmp"
        test_file.write_text("health_check")
        test_file.unlink()
        
        return True
    except:
        return False

async def main():
    """Main health check execution."""
    print("🔍 LTMC MCP Server Health Check")
    print("=" * 40)
    
    # Check MCP server
    print("Checking MCP server...")
    mcp_healthy = await check_mcp_server_health()
    print(f"   MCP Server: {'✅ Healthy' if mcp_healthy else '❌ Unhealthy'}")
    
    # Check dependencies  
    print("Checking dependencies...")
    deps_healthy = await check_dependencies()
    print(f"   Dependencies: {'✅ Healthy' if deps_healthy else '❌ Unhealthy'}")
    
    # Overall health
    overall_healthy = mcp_healthy and deps_healthy
    print(f"\nOverall Health: {'✅ HEALTHY' if overall_healthy else '❌ UNHEALTHY'}")
    
    sys.exit(0 if overall_healthy else 1)

if __name__ == "__main__":
    asyncio.run(main())
