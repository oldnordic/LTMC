#!/usr/bin/env python3
"""
Simple Health Check Method Validation
====================================

Simple validation that health_check methods exist in database services.
This validates that the constraint fix Phase 1 deployment is complete.
"""

import inspect
from pathlib import Path

def check_health_method_exists(file_path: str, class_name: str) -> dict:
    """Check if health_check method exists in a class."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Look for health_check method definition
        has_health_check = "def health_check(" in content and "async def health_check(" in content
        has_return_dict = "Dict[str, Any]" in content or "-> Dict" in content
        has_measure_performance = "@measure_performance" in content
        
        # Count lines of implementation (rough estimate)
        lines = content.split('\n')
        health_check_lines = []
        in_health_check = False
        
        for line in lines:
            if "async def health_check(" in line:
                in_health_check = True
            elif in_health_check and line.strip().startswith("async def ") and "health_check" not in line:
                break
            elif in_health_check and line.strip().startswith("def ") and "health_check" not in line:
                break
            
            if in_health_check:
                health_check_lines.append(line)
        
        implementation_lines = len([l for l in health_check_lines if l.strip() and not l.strip().startswith('#')])
        
        # Check for delegation pattern (shorter but valid)
        is_delegation = "await" in content and "health_check()" in content and implementation_lines < 10
        is_valid = (has_health_check and implementation_lines > 10) or (has_health_check and is_delegation)
        
        return {
            "file_exists": True,
            "has_health_check": has_health_check,
            "has_return_dict": has_return_dict,
            "has_measure_performance": has_measure_performance,
            "implementation_lines": implementation_lines,
            "is_delegation": is_delegation,
            "status": "implemented" if is_valid else "missing"
        }
        
    except Exception as e:
        return {
            "file_exists": False,
            "error": str(e),
            "status": "error"
        }

def main():
    """Main validation."""
    print("🚀 Health Check Implementation Validation")
    print("="*50)
    
    # Services to check
    services = [
        {
            "name": "BasicDatabaseService (SQLite)",
            "path": "ltmc_mcp_server/services/basic_database_service.py",
            "class": "BasicDatabaseService"
        },
        {
            "name": "DatabaseService (Unified)",
            "path": "ltmc_mcp_server/services/database_service.py", 
            "class": "DatabaseService"
        },
        {
            "name": "RedisService",
            "path": "ltmc_mcp_server/services/redis_service.py",
            "class": "RedisService"
        },
        {
            "name": "Neo4jService", 
            "path": "ltmc_mcp_server/services/neo4j_service.py",
            "class": "Neo4jService"
        },
        {
            "name": "FAISSService",
            "path": "ltmc_mcp_server/services/faiss_service.py",
            "class": "FAISSService"
        }
    ]
    
    results = []
    
    for service in services:
        print(f"📊 Checking {service['name']}...")
        result = check_health_method_exists(service["path"], service["class"])
        result["service_name"] = service["name"]
        results.append(result)
        
        if result["status"] == "implemented":
            lines = result.get("implementation_lines", 0)
            has_perf = "✅" if result.get("has_measure_performance") else "⚠️ "
            is_delegation = result.get("is_delegation", False)
            delegation_note = " [delegation]" if is_delegation else ""
            print(f"   ✅ health_check method found ({lines} lines){delegation_note} {has_perf}")
        elif result["status"] == "missing":
            print(f"   ❌ health_check method missing or incomplete")
        else:
            print(f"   ❌ Error: {result.get('error', 'unknown')}")
    
    # Summary
    print("\n" + "="*50)
    print("🎯 VALIDATION SUMMARY")
    print("="*50)
    
    implemented_count = sum(1 for r in results if r["status"] == "implemented")
    total_count = len(results)
    
    for result in results:
        name = result["service_name"]
        status = result["status"]
        if status == "implemented":
            print(f"✅ {name}: Implemented")
        elif status == "missing":
            print(f"❌ {name}: Missing health_check method")
        else:
            print(f"❌ {name}: Error - {result.get('error', 'unknown')}")
    
    print(f"\n📈 Results: {implemented_count}/{total_count} services have health_check methods")
    
    if implemented_count == total_count:
        print("🎉 SUCCESS: All database services have health_check methods!")
        print("✅ Phase 1 constraint fix deployment: COMPLETED")
        return True
    else:
        print(f"⚠️  WARNING: {total_count - implemented_count} services missing health checks")
        print("❌ Phase 1 constraint fix deployment: INCOMPLETE")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)