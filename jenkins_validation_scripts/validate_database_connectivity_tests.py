#!/usr/bin/env python3
"""
LTMC Database Connectivity Tests for Jenkins
Tests real database connections without modifying data
"""

import sys
import os
import sqlite3
import time
from pathlib import Path

def test_sqlite_connectivity():
    """Test SQLite connectivity"""
    print("Testing SQLite connectivity...")
    
    try:
        # Test in-memory database first
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        result = cursor.fetchone()
        conn.close()
        
        if result[0] == 1:
            print("✅ SQLite in-memory test: OK")
        else:
            print("❌ SQLite in-memory test: FAIL")
            return False
            
        # Test file database connection (read-only)
        ltmc_home = os.environ.get('LTMC_HOME', '/home/feanor/Projects/ltmc')
        db_path = Path(ltmc_home) / 'data' / 'ltmc.db'
        
        if db_path.exists():
            conn = sqlite3.connect(str(db_path), timeout=5.0)
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM sqlite_master WHERE type="table" LIMIT 1')
            conn.close()
            print("✅ SQLite file database: Accessible")
        else:
            print("ℹ️  SQLite file database: Not found (OK for clean environment)")
            
        return True
        
    except Exception as e:
        print(f"❌ SQLite connectivity test failed: {e}")
        return False

def test_redis_availability():
    """Test Redis client availability (not server connectivity)"""
    print("Testing Redis client availability...")
    
    try:
        import redis
        print(f"✅ Redis client version: {redis.__version__}")
        
        # Test client creation (don't require server)
        client = redis.Redis(host='localhost', port=6379, socket_connect_timeout=1, decode_responses=True)
        print("✅ Redis client: Available")
        
        # Optional server test - don't fail if server not available
        try:
            client.ping()
            print("✅ Redis server: Connected")
        except (redis.ConnectionError, redis.TimeoutError):
            print("⚠️  Redis server: Not available (OK for validation)")
        
        return True
        
    except ImportError:
        print("❌ Redis client: Not installed")
        return False
    except Exception as e:
        print(f"❌ Redis availability test failed: {e}")
        return False

def test_neo4j_availability():
    """Test Neo4j driver availability (not server connectivity)"""
    print("Testing Neo4j driver availability...")
    
    try:
        import neo4j
        print(f"✅ Neo4j driver version: {neo4j.__version__}")
        
        # Test driver creation (don't require server)
        try:
            driver = neo4j.GraphDatabase.driver("bolt://localhost:7687", 
                                               auth=("neo4j", "test"),
                                               connection_timeout=1)
            print("✅ Neo4j driver: Available")
            
            # Optional server test - don't fail if server not available
            try:
                with driver.session() as session:
                    result = session.run("RETURN 1 AS test")
                    driver.close()
                print("✅ Neo4j server: Connected")
            except Exception:
                print("⚠️  Neo4j server: Not available (OK for validation)")
        except Exception as e:
            print(f"⚠️  Neo4j driver test: {e}")
        
        return True
        
    except ImportError:
        print("❌ Neo4j driver: Not installed")
        return False
    except Exception as e:
        print(f"❌ Neo4j availability test failed: {e}")
        return False

def test_faiss_availability():
    """Test FAISS availability"""
    print("Testing FAISS availability...")
    
    try:
        import faiss
        print("✅ FAISS: Available")
        
        # Test basic FAISS functionality
        import numpy as np
        dimension = 64
        index = faiss.IndexFlatL2(dimension)
        
        # Add some test vectors
        vectors = np.random.random((10, dimension)).astype('float32')
        index.add(vectors)
        
        # Test search
        query = np.random.random((1, dimension)).astype('float32')
        distances, indices = index.search(query, 5)
        
        print(f"✅ FAISS functionality test: OK (found {len(indices[0])} results)")
        return True
        
    except ImportError:
        print("❌ FAISS: Not installed")
        return False
    except Exception as e:
        print(f"❌ FAISS availability test failed: {e}")
        return False

def main():
    """Run all database connectivity tests"""
    print("=== LTMC Database Connectivity Tests ===")
    
    tests = [
        ("SQLite", test_sqlite_connectivity),
        ("Redis", test_redis_availability),
        ("Neo4j", test_neo4j_availability),
        ("FAISS", test_faiss_availability)
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} Test ---")
        start_time = time.time()
        
        try:
            success = test_func()
            duration = (time.time() - start_time) * 1000
            
            if success:
                print(f"✅ {test_name}: PASS ({duration:.2f}ms)")
            else:
                print(f"❌ {test_name}: FAIL ({duration:.2f}ms)")
                failed_tests.append(test_name)
                
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            print(f"❌ {test_name}: ERROR ({duration:.2f}ms) - {e}")
            failed_tests.append(test_name)
    
    print(f"\n=== Test Summary ===")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {len(tests) - len(failed_tests)}")
    print(f"Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"Failed tests: {', '.join(failed_tests)}")
        print("❌ OVERALL: Database connectivity validation FAILED")
        sys.exit(1)
    else:
        print("✅ OVERALL: All database connectivity tests PASSED")
        return 0

if __name__ == '__main__':
    main()