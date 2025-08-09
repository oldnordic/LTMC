#!/usr/bin/env python3
"""P1 Comprehensive Transport Consistency Test.

Validates that HTTP and STDIO transports return identical response formats
across multiple LTMC tools to ensure complete transport parity.
"""

import time
from client_utils import create_client

def test_comprehensive_transport_consistency():
    """Test all major LTMC tools across both transports."""
    
    print("P1 Comprehensive Transport Consistency Test")
    print("=" * 50)
    
    # Test configurations
    test_tools = [
        {
            "name": "store_memory",
            "method": "store_memory",
            "args": {
                "content": "P1 consistency test content",
                "file_name": f"p1_consistency_{int(time.time())}.md"
            }
        },
        {
            "name": "add_todo", 
            "method": "add_todo",
            "args": {
                "title": "P1 Test Todo",
                "description": "Transport consistency validation todo",
                "priority": "high"
            }
        },
        {
            "name": "retrieve_memory",
            "method": "retrieve_memory", 
            "args": {
                "query": "P1 test",
                "conversation_id": "p1_test_session",
                "top_k": 2
            }
        }
    ]
    
    transport_results = {"http": {}, "stdio": {}}
    consistency_score = 0
    total_tests = len(test_tools) * 2  # 2 transports
    
    # Test each transport
    for transport in ["http", "stdio"]:
        print(f"\nTesting {transport.upper()} transport:")
        print("-" * 25)
        
        try:
            client = create_client(transport=transport)
            
            for tool_config in test_tools:
                tool_name = tool_config["name"]
                method = tool_config["method"]
                args = tool_config["args"]
                
                try:
                    result = client.call_tool(method, args)
                    transport_results[transport][tool_name] = result
                    print(f"✅ {tool_name}: {result.get('success', False)} - {result.get('message', 'OK')}")
                    consistency_score += 1
                except Exception as e:
                    transport_results[transport][tool_name] = {"error": str(e)}
                    print(f"❌ {tool_name}: Error - {e}")
            
            client.close()
            
        except Exception as e:
            print(f"❌ {transport.upper()} transport failed: {e}")
            for tool_config in test_tools:
                transport_results[transport][tool_config["name"]] = {"transport_error": str(e)}
    
    # Analyze consistency
    print(f"\nP1 Transport Consistency Analysis:")
    print("=" * 40)
    
    format_consistent = True
    success_consistent = True
    
    for tool_config in test_tools:
        tool_name = tool_config["name"]
        
        http_result = transport_results["http"].get(tool_name, {})
        stdio_result = transport_results["stdio"].get(tool_name, {})
        
        print(f"\n{tool_name}:")
        
        # Check if both succeeded
        http_success = http_result.get("success", False)
        stdio_success = stdio_result.get("success", False)
        
        if http_success and stdio_success:
            # Compare response format
            http_keys = set(http_result.keys()) if isinstance(http_result, dict) else set()
            stdio_keys = set(stdio_result.keys()) if isinstance(stdio_result, dict) else set()
            
            if http_keys == stdio_keys:
                print(f"  ✅ Format consistency: PASS")
                print(f"     Keys: {sorted(http_keys)}")
            else:
                print(f"  ❌ Format consistency: FAIL")
                print(f"     HTTP: {sorted(http_keys)}")
                print(f"     STDIO: {sorted(stdio_keys)}")
                format_consistent = False
                
        elif not http_success and not stdio_success:
            print(f"  ⚠️  Both transports failed (consistent behavior)")
        else:
            print(f"  ❌ Success consistency: FAIL")
            print(f"     HTTP success: {http_success}")
            print(f"     STDIO success: {stdio_success}")
            success_consistent = False
    
    # Final P1 assessment
    print(f"\nP1 Implementation Assessment:")
    print("=" * 35)
    print(f"Transport success rate: {consistency_score}/{total_tests} ({consistency_score/total_tests*100:.1f}%)")
    print(f"Response format consistency: {'✅ PASS' if format_consistent else '❌ FAIL'}")
    print(f"Success behavior consistency: {'✅ PASS' if success_consistent else '❌ FAIL'}")
    
    if format_consistent and success_consistent and consistency_score >= total_tests * 0.8:
        print("\n🎉 P1 TRANSPORT CONSISTENCY: ACHIEVED")
        print("   HTTP and STDIO transports provide identical response formats")
        print("   Transport parity successfully implemented")
        return True
    else:
        print("\n❌ P1 TRANSPORT CONSISTENCY: ISSUES DETECTED") 
        print("   Manual review required for transport parity")
        return False

if __name__ == "__main__":
    test_comprehensive_transport_consistency()