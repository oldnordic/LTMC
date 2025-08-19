#!/usr/bin/env python3
"""
Health Check Validation Test
============================

Quick validation script to test all database service health checks.
This validates that the constraint fix Phase 1 deployment is working.
"""

import asyncio
import logging
from pathlib import Path
import sys

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ltmc_mcp_server.config.settings import LTMCSettings
from ltmc_mcp_server.services.database_service import DatabaseService
from ltmc_mcp_server.services.redis_service import RedisService
from ltmc_mcp_server.services.neo4j_service import Neo4jService
from ltmc_mcp_server.services.faiss_service import FAISSService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_all_health_checks():
    """Test all database service health checks."""
    logger.info("🚀 Starting Health Check Validation Test")
    
    # Initialize settings
    settings = LTMCSettings()
    
    # Test results storage
    results = {}
    
    # Test DatabaseService (SQLite)
    logger.info("📊 Testing SQLite/DatabaseService health check...")
    try:
        db_service = DatabaseService(settings)
        await db_service.initialize()
        
        health_result = await db_service.health_check()
        results["SQLite"] = health_result
        
        status = health_result.get("status", "unknown")
        service = health_result.get("service", "DatabaseService")
        latency = health_result.get("latency_ms", "unknown")
        
        if status == "healthy":
            logger.info(f"✅ SQLite ({service}) - {status} - {latency}ms")
        else:
            logger.error(f"❌ SQLite ({service}) - {status} - Error: {health_result.get('error', 'unknown')}")
            
    except Exception as e:
        logger.error(f"❌ SQLite health check failed with exception: {e}")
        results["SQLite"] = {"status": "error", "error": str(e)}
    
    # Test RedisService
    logger.info("📊 Testing Redis health check...")
    try:
        redis_service = RedisService(settings)
        await redis_service.initialize()
        
        health_result = await redis_service.health_check()
        results["Redis"] = health_result
        
        status = health_result.get("status", "unknown")
        service = health_result.get("service", "Redis")
        latency = health_result.get("latency_ms", "unknown")
        
        if status == "healthy":
            logger.info(f"✅ Redis ({service}) - {status} - {latency}ms")
        else:
            logger.error(f"❌ Redis ({service}) - {status} - Error: {health_result.get('error', 'unknown')}")
            
    except Exception as e:
        logger.error(f"❌ Redis health check failed with exception: {e}")
        results["Redis"] = {"status": "error", "error": str(e)}
    
    # Test Neo4jService
    logger.info("📊 Testing Neo4j health check...")
    try:
        neo4j_service = Neo4jService(settings)
        await neo4j_service.initialize()
        
        health_result = await neo4j_service.health_check()
        results["Neo4j"] = health_result
        
        status = health_result.get("status", "unknown")
        service = health_result.get("service", "Neo4j")
        latency = health_result.get("latency_ms", "unknown")
        
        if status == "healthy":
            logger.info(f"✅ Neo4j ({service}) - {status} - {latency}ms")
        else:
            logger.error(f"❌ Neo4j ({service}) - {status} - Error: {health_result.get('error', 'unknown')}")
            
    except Exception as e:
        logger.error(f"❌ Neo4j health check failed with exception: {e}")
        results["Neo4j"] = {"status": "error", "error": str(e)}
    
    # Test FAISSService
    logger.info("📊 Testing FAISS health check...")
    try:
        faiss_service = FAISSService(settings)
        await faiss_service.initialize()
        
        health_result = await faiss_service.health_check()
        results["FAISS"] = health_result
        
        status = health_result.get("status", "unknown")
        service = health_result.get("service", "FAISS")
        latency = health_result.get("latency_ms", "unknown")
        
        if status == "healthy":
            logger.info(f"✅ FAISS ({service}) - {status} - {latency}ms")
        else:
            logger.error(f"❌ FAISS ({service}) - {status} - Error: {health_result.get('error', 'unknown')}")
            
    except Exception as e:
        logger.error(f"❌ FAISS health check failed with exception: {e}")
        results["FAISS"] = {"status": "error", "error": str(e)}
    
    # Summary report
    logger.info("\n" + "="*60)
    logger.info("🎯 HEALTH CHECK VALIDATION SUMMARY")
    logger.info("="*60)
    
    healthy_count = 0
    total_count = len(results)
    
    for service_name, result in results.items():
        status = result.get("status", "unknown")
        if status == "healthy":
            healthy_count += 1
            logger.info(f"✅ {service_name}: {status}")
        else:
            logger.info(f"❌ {service_name}: {status} - {result.get('error', 'No error details')}")
    
    logger.info(f"\n📈 Results: {healthy_count}/{total_count} services healthy")
    
    if healthy_count == total_count:
        logger.info("🎉 SUCCESS: All database services have working health checks!")
        logger.info("✅ Phase 1 constraint fix deployment validation: PASSED")
        return True
    else:
        logger.error(f"⚠️  WARNING: {total_count - healthy_count} services have health check issues")
        logger.error("❌ Phase 1 constraint fix deployment validation: FAILED")
        return False


async def main():
    """Main entry point."""
    try:
        success = await test_all_health_checks()
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Health check validation failed with exception: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())