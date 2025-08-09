#!/usr/bin/env python3
"""P1 Comprehensive Implementation Validation.

Final validation suite to verify complete P1 implementation success:
- STDIO response format standardization
- Client library MCP protocol unwrapping
- Transport consistency across HTTP and STDIO
- Documentation accuracy and completeness
"""

import json
import time
import subprocess
import requests
from pathlib import Path
from typing import Dict, Any, List
from client_utils import create_client, unwrap_mcp_response, normalize_response_format

class P1ValidationSuite:
    """P1 comprehensive validation test suite."""
    
    def __init__(self):
        self.results = {}
        self.test_count = 0
        self.passed_count = 0
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        self.test_count += 1
        if passed:
            self.passed_count += 1
            
        self.results[test_name] = {
            "passed": passed,
            "details": details
        }
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"      {details}")
    
    def test_stdio_response_standardization(self) -> bool:
        """Test P1 STDIO response standardization."""
        print("\n1. STDIO Response Format Standardization")
        print("-" * 45)
        
        try:
            # Test STDIO proxy directly
            test_request = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "store_memory",
                    "arguments": {
                        "content": "P1 STDIO validation test",
                        "file_name": f"p1_stdio_validation_{int(time.time())}.md"
                    }
                },
                "id": 1
            }
            
            # Start STDIO proxy and test
            process = subprocess.Popen(
                ["python3", "ltmc_stdio_proxy.py"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Initialize
            init_sequence = [
                {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "p1-validator", "version": "1.0.0"}
                    },
                    "id": 1
                },
                {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                    "params": {}
                }
            ]
            
            # Send initialization
            for req in init_sequence:
                process.stdin.write(json.dumps(req) + "\n")
                process.stdin.flush()
                if req.get("id"):  # Read response for requests with ID
                    response_line = process.stdout.readline()
                    if response_line.strip():
                        response = json.loads(response_line.strip())
                        if "protocolVersion" not in response:
                            self.log_test("STDIO Initialization", False, f"Invalid init response: {response}")
                            process.terminate()
                            return False
            
            # Send test request
            process.stdin.write(json.dumps(test_request) + "\n")
            process.stdin.flush()
            
            # Read response
            response_line = process.stdout.readline()
            process.terminate()
            
            if response_line.strip():
                response = json.loads(response_line.strip())
                
                # Validate direct JSON format (not MCP-wrapped)
                if "jsonrpc" in response:
                    self.log_test("STDIO Direct JSON Format", False, "Response still MCP-wrapped")
                    return False
                elif "success" in response:
                    self.log_test("STDIO Direct JSON Format", True, "Direct JSON response achieved")
                    return True
                else:
                    self.log_test("STDIO Direct JSON Format", False, f"Unexpected format: {response}")
                    return False
            else:
                self.log_test("STDIO Direct JSON Format", False, "No response received")
                return False
                
        except Exception as e:
            self.log_test("STDIO Response Standardization", False, f"Error: {e}")
            return False
    
    def test_client_library_enhancement(self) -> bool:
        """Test P1 client library enhancements."""
        print("\n2. Client Library MCP Protocol Unwrapping")
        print("-" * 45)
        
        # Test unwrapping utility
        mock_mcp_response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"success": True, "message": "Test result"}
        }
        
        unwrapped = unwrap_mcp_response(mock_mcp_response)
        if unwrapped.get("success") and unwrapped.get("message") == "Test result":
            self.log_test("MCP Response Unwrapping", True, "Correctly extracts result from MCP wrapper")
        else:
            self.log_test("MCP Response Unwrapping", False, f"Failed to unwrap: {unwrapped}")
            return False
        
        # Test response normalization
        direct_response = {"success": True, "data": "test"}
        normalized = normalize_response_format(direct_response)
        if normalized == direct_response:
            self.log_test("Response Normalization", True, "Direct responses preserved")
        else:
            self.log_test("Response Normalization", False, "Direct response modified incorrectly")
            return False
        
        # Test client library transport abstraction
        try:
            for transport in ["http", "stdio"]:
                client = create_client(transport=transport)
                result = client.store_memory(
                    f"P1 client test {transport}",
                    f"p1_client_test_{transport}_{int(time.time())}.md"
                )
                client.close()
                
                if result.get("success"):
                    self.log_test(f"Client Library {transport.upper()}", True, "Transport abstraction working")
                else:
                    self.log_test(f"Client Library {transport.upper()}", False, f"Failed: {result}")
                    return False
        except Exception as e:
            self.log_test("Client Library Transport Abstraction", False, f"Error: {e}")
            return False
            
        return True
    
    def test_transport_consistency(self) -> bool:
        """Test P1 transport consistency."""
        print("\n3. HTTP and STDIO Transport Consistency")
        print("-" * 45)
        
        try:
            test_tools = [
                ("store_memory", {
                    "content": "P1 consistency validation",
                    "file_name": f"p1_consistency_{int(time.time())}.md"
                }),
                ("add_todo", {
                    "title": "P1 Validation Todo",
                    "description": "Transport consistency test",
                    "priority": "medium"
                })
            ]
            
            transport_results = {}
            
            for transport in ["http", "stdio"]:
                client = create_client(transport=transport)
                transport_results[transport] = {}
                
                for tool_name, args in test_tools:
                    result = client.call_tool(tool_name, args)
                    transport_results[transport][tool_name] = result
                
                client.close()
            
            # Compare results
            consistent = True
            for tool_name, _ in test_tools:
                http_keys = set(transport_results["http"][tool_name].keys())
                stdio_keys = set(transport_results["stdio"][tool_name].keys())
                
                if http_keys != stdio_keys:
                    self.log_test(f"Transport Consistency - {tool_name}", False, 
                                f"Key mismatch: HTTP {http_keys} vs STDIO {stdio_keys}")
                    consistent = False
                else:
                    self.log_test(f"Transport Consistency - {tool_name}", True, 
                                f"Identical response keys: {sorted(http_keys)}")
            
            return consistent
            
        except Exception as e:
            self.log_test("Transport Consistency", False, f"Error: {e}")
            return False
    
    def test_documentation_accuracy(self) -> bool:
        """Test P1 documentation accuracy."""
        print("\n4. Documentation Accuracy and Completeness")
        print("-" * 45)
        
        # Check if documentation exists
        doc_path = Path("docs/P1_API_DOCUMENTATION.md")
        if not doc_path.exists():
            self.log_test("Documentation Exists", False, "P1 API documentation not found")
            return False
        else:
            self.log_test("Documentation Exists", True, "P1 API documentation found")
        
        # Check documentation content
        doc_content = doc_path.read_text()
        required_sections = [
            "P1 Implementation",
            "Transport Overview",
            "Response Format Specification",
            "Tool Response Examples",
            "Client Library Usage",
            "Migration Guide"
        ]
        
        for section in required_sections:
            if section in doc_content:
                self.log_test(f"Documentation - {section}", True, "Section present")
            else:
                self.log_test(f"Documentation - {section}", False, "Section missing")
                return False
        
        return True
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run complete P1 validation suite."""
        print("P1 COMPREHENSIVE IMPLEMENTATION VALIDATION")
        print("=" * 55)
        print("Validating all P1 objectives and success criteria...")
        
        # Run all validation tests
        tests = [
            self.test_stdio_response_standardization,
            self.test_client_library_enhancement, 
            self.test_transport_consistency,
            self.test_documentation_accuracy
        ]
        
        overall_success = True
        for test_method in tests:
            if not test_method():
                overall_success = False
        
        # Final assessment
        print(f"\nP1 VALIDATION RESULTS")
        print("=" * 25)
        print(f"Tests Passed: {self.passed_count}/{self.test_count}")
        print(f"Success Rate: {self.passed_count/self.test_count*100:.1f}%")
        
        if overall_success and self.passed_count == self.test_count:
            print("\n🎉 P1 IMPLEMENTATION: COMPLETE SUCCESS")
            print("✅ STDIO response format standardization: ACHIEVED")
            print("✅ Client library MCP unwrapping: ACHIEVED")
            print("✅ Transport consistency: ACHIEVED")
            print("✅ Documentation: COMPLETE")
            print("\nP1 OBJECTIVES: ALL SUCCESS CRITERIA MET")
        else:
            print("\n❌ P1 IMPLEMENTATION: ISSUES DETECTED")
            print("Manual review and fixes required")
        
        return {
            "overall_success": overall_success,
            "test_results": self.results,
            "passed_count": self.passed_count,
            "total_count": self.test_count
        }

def main():
    """Run P1 comprehensive validation."""
    validator = P1ValidationSuite()
    results = validator.run_comprehensive_validation()
    
    # Log results to LTMC
    try:
        import requests
        log_data = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "log_code_attempt",
                "arguments": {
                    "input_prompt": "P1 Comprehensive Implementation Validation",
                    "generated_code": f"P1 validation results: {results['passed_count']}/{results['total_count']} tests passed",
                    "result": "pass" if results["overall_success"] else "fail",
                    "tags": ["p1", "validation", "comprehensive", "final-test"]
                }
            },
            "id": 1
        }
        
        response = requests.post(
            "http://localhost:5050/jsonrpc",
            json=log_data,
            timeout=5
        )
        print(f"\n✅ Validation results logged to LTMC: {response.json()}")
    except:
        print("\n⚠️  Could not log results to LTMC")
    
    return results["overall_success"]

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)