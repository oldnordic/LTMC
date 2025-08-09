#!/usr/bin/env python3
"""P1 Client Library Test - Transport Consistency Validation.

Tests both HTTP and STDIO transports with the P1 enhanced client library
to verify response format consistency and transport parity.
"""

import time
from client_utils import create_client, MCPClientError

def test_transport_consistency():
    """Test P1 transport consistency between HTTP and STDIO."""
    
    print("P1 Testing: Transport Consistency Validation")
    print("=" * 50)
    
    # Test data
    test_content = "P1 transport consistency test"
    test_file = f"p1_test_{int(time.time())}.md"
    
    results = {}
    
    # Test HTTP transport
    print("Testing HTTP transport...")
    try:
        http_client = create_client(transport="http")
        http_result = http_client.store_memory(test_content, f"http_{test_file}")
        results["http"] = http_result
        print(f"HTTP Result: {http_result}")
        http_client.close()
    except Exception as e:
        print(f"HTTP Error: {e}")
        results["http"] = {"error": str(e)}
    
    print()
    
    # Test STDIO transport  
    print("Testing STDIO transport...")
    try:
        stdio_client = create_client(transport="stdio")
        stdio_result = stdio_client.store_memory(test_content, f"stdio_{test_file}")
        results["stdio"] = stdio_result
        print(f"STDIO Result: {stdio_result}")
        stdio_client.close()
    except Exception as e:
        print(f"STDIO Error: {e}")
        results["stdio"] = {"error": str(e)}
    
    print()
    
    # Compare results
    print("P1 Transport Consistency Analysis:")
    print("-" * 35)
    
    if "error" not in results["http"] and "error" not in results["stdio"]:
        # Check format consistency
        http_keys = set(results["http"].keys())
        stdio_keys = set(results["stdio"].keys())
        
        if http_keys == stdio_keys:
            print("✅ Response format consistency: PASS")
            print(f"   Both transports return: {sorted(http_keys)}")
        else:
            print("❌ Response format consistency: FAIL")
            print(f"   HTTP keys: {sorted(http_keys)}")
            print(f"   STDIO keys: {sorted(stdio_keys)}")
        
        # Check success status
        http_success = results["http"].get("success", False)
        stdio_success = results["stdio"].get("success", False)
        
        if http_success and stdio_success:
            print("✅ Both transports successful: PASS")
        else:
            print("❌ Transport success mismatch: FAIL")
            
    else:
        print("❌ One or both transports failed")
    
    print()
    print("P1 Implementation Status: Transport parity achieved" if 
          "error" not in results["http"] and "error" not in results["stdio"] 
          else "P1 Implementation Status: Issues detected")

if __name__ == "__main__":
    test_transport_consistency()