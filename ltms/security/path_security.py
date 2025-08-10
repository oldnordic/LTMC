"""
LTMC Secure Path Validator

Comprehensive path security validation and input sanitization.
Prevents path traversal, code injection, and system file access attacks.

Performance Target: <3ms for all path validation operations
Security Focus: Complete attack vector prevention

TDD Implementation: This module was implemented to satisfy failing tests that define
the exact security behavior required for path-based attack prevention.
"""

import os
import re
import time
import unicodedata
from pathlib import Path
from typing import List, Set, Optional, Union
import logging

logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Raised when security validation fails."""
    pass


class SecurePathValidator:
    """
    Secure Path Validator for LTMC Attack Prevention
    
    Provides comprehensive protection against:
    - Path traversal attacks (../../../etc/passwd)
    - Code injection attempts (eval, __import__, shell commands)
    - System file access (/etc/passwd, /root/.ssh/)
    - Unicode normalization attacks
    - Buffer overflow attempts
    
    Performance: All operations complete in <3ms for high-throughput usage.
    """
    
    # Dangerous patterns that indicate potential attacks
    DANGEROUS_PATTERNS = [
        # Path traversal patterns
        r'\.\.[\\/]',
        r'[\\/]\.\.[\\/]',
        r'[\\/]\.\.$',
        r'%2e%2e[%2f%5c]',  # URL encoded traversal
        r'%252e%252e',      # Double URL encoded
        
        # Code injection patterns
        r'__import__\s*\(',
        r'eval\s*\(',
        r'exec\s*\(',
        r'subprocess\.',
        r'os\.system',
        r'os\.popen',
        r'commands\.',
        
        # Shell command injection
        r'[;&|`$]\s*\w+',
        r'\$\([^)]+\)',
        r'`[^`]+`',
        
        # SQL injection patterns
        r'[\'"];?\s*(DROP|DELETE|INSERT|UPDATE|SELECT)',
        r'UNION\s+SELECT',
        r'--\s*$',
        
        # Template injection
        r'\{\{[^}]+\}\}',
        r'\$\{[^}]+\}',
        r'%\{[^}]+\}',
        
        # Script tags and HTML injection
        r'<script[^>]*>',
        r'<iframe[^>]*>',
        r'javascript:',
        r'data:text/html',
    ]
    
    # System directories that should never be accessible
    SYSTEM_DIRECTORIES = [
        '/etc/', '/root/', '/proc/', '/sys/', '/dev/', '/var/log/',
        '/usr/lib/python', '/usr/local/lib/python', '/opt/',
        '/boot/', '/lib/', '/lib64/', '/sbin/', '/usr/sbin/',
        '/var/cache/', '/var/lib/', '/var/spool/',
        '/home/.ssh/', '/.ssh/', '/root/.bash_history',
        '/var/tmp/', '/tmp/.*_session', '/tmp/.*_token',
        '/home/user/.bash_history'
    ]
    
    # Dangerous executable extensions
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.vbe',
        '.js', '.jse', '.jar', '.sh', '.bash', '.zsh', '.fish',
        '.ps1', '.psm1', '.psd1', '.ps1xml', '.psc1', '.pssc',
        '.msi', '.msp', '.mst', '.dll', '.so', '.dylib'
    }
    
    # Safe extensions that are generally allowed
    ALLOWED_EXTENSIONS = {
        '.txt', '.md', '.json', '.xml', '.csv', '.yaml', '.yml',
        '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css',
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.tar', '.gz', '.bz2', '.xz', '.7z'
    }
    
    def __init__(self, secure_root: Union[str, Path]):
        """
        Initialize SecurePathValidator.
        
        Args:
            secure_root: Root directory for secure operations
        """
        self.secure_root = Path(secure_root).resolve()
        
        # Compile regex patterns for performance
        self._compiled_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE) 
            for pattern in self.DANGEROUS_PATTERNS
        ]
        
        self._system_dir_pattern = re.compile(
            '|'.join(re.escape(d) for d in self.SYSTEM_DIRECTORIES),
            re.IGNORECASE
        )
        
        # Security constraints
        self._max_path_length = 4096
        self._max_input_length = 10000
        self._max_depth = 100
        
        logger.info(f"SecurePathValidator initialized with root: {self.secure_root}")
    
    def validate_file_operation(self, file_path: str, operation: str, project_id: str) -> bool:
        """
        Validate a file operation for security threats.
        
        Args:
            file_path: Path being accessed
            operation: Operation type (read, write, execute)
            project_id: Project context for logging
            
        Returns:
            True if operation is safe
            
        Raises:
            SecurityError: If operation poses security risk
            
        Performance: Completes in <3ms for all validation checks
        """
        start_time = time.perf_counter()
        
        try:
            # Validate input length
            if len(file_path) > self._max_path_length:
                raise SecurityError(f"Path exceeds maximum length ({self._max_path_length}): {len(file_path)}")
            
            # Normalize path for analysis
            normalized_path = self._normalize_path(file_path)
            
            # Check for dangerous patterns
            for pattern in self._compiled_patterns:
                if pattern.search(normalized_path):
                    raise SecurityError(f"Dangerous pattern detected in path: {file_path}")
            
            # Check for path traversal
            if self._contains_path_traversal(normalized_path):
                raise SecurityError(f"Path traversal detected: {file_path}")
            
            # Check for system directory access
            if self._is_system_directory(normalized_path):
                raise SecurityError(f"System directory access denied: {file_path}")
            
            # Operation-specific validation
            if operation == 'execute':
                if not self._is_safe_executable(normalized_path):
                    raise SecurityError(f"Unsafe executable: {file_path}")
            
            # Check for Unicode attacks
            if self._contains_unicode_attacks(file_path):
                raise SecurityError(f"Unicode attack detected: {file_path}")
            
            # Check path depth (prevent deep directory attacks)
            if self._get_path_depth(normalized_path) > self._max_depth:
                raise SecurityError(f"Path depth exceeds limit: {file_path}")
            
            execution_time = (time.perf_counter() - start_time) * 1000
            if execution_time > 3.0:
                logger.warning(f"Path validation exceeded 3ms: {execution_time:.2f}ms")
            
            logger.debug(f"Path validation passed for {project_id}: {file_path} ({execution_time:.2f}ms)")
            return True
            
        except SecurityError:
            execution_time = (time.perf_counter() - start_time) * 1000
            logger.warning(f"Path validation failed for {project_id}: {file_path} ({execution_time:.2f}ms)")
            raise
    
    def sanitize_user_input(self, user_input: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize user input to remove dangerous content.
        
        Args:
            user_input: Raw user input
            max_length: Maximum allowed length (defaults to class limit)
            
        Returns:
            Sanitized input string
            
        Raises:
            SecurityError: If input exceeds length limits
        """
        start_time = time.perf_counter()
        
        if max_length is None:
            max_length = self._max_input_length
        
        if len(user_input) > max_length:
            raise SecurityError(f"Input exceeds maximum length ({max_length}): {len(user_input)}")
        
        try:
            # Normalize unicode to prevent homograph attacks
            normalized = unicodedata.normalize('NFKC', user_input)
            
            # Remove dangerous characters
            sanitized = re.sub(r'[<>:"|?*\x00-\x1f\x7f-\x9f]', '', normalized)
            
            # Remove code injection patterns
            sanitized = re.sub(r'[;&|`$]', '', sanitized)
            
            # Remove quotes that could be used for injection
            sanitized = re.sub(r'[\'"]', '', sanitized)
            
            # Remove null bytes
            sanitized = sanitized.replace('\x00', '')
            
            # Limit line breaks
            sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)
            
            execution_time = (time.perf_counter() - start_time) * 1000
            logger.debug(f"Input sanitized in {execution_time:.2f}ms")
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Input sanitization failed: {e}")
            raise SecurityError(f"Input sanitization failed: {e}")
    
    def _is_safe_executable(self, file_path: str) -> bool:
        """
        Check if executable file is safe to run.
        
        Args:
            file_path: Path to executable file
            
        Returns:
            True if executable is considered safe
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        # Block dangerous extensions
        if extension in self.DANGEROUS_EXTENSIONS:
            return False
        
        # Allow specific safe extensions
        if extension in self.ALLOWED_EXTENSIONS:
            return True
        
        # Be conservative - block unknown extensions
        return False
    
    def _normalize_path(self, path: str) -> str:
        """
        Normalize path for security analysis.
        
        Args:
            path: Input path
            
        Returns:
            Normalized path
        """
        # Convert to string if Path object
        if isinstance(path, Path):
            path = str(path)
        
        # Normalize unicode
        normalized = unicodedata.normalize('NFKC', path)
        
        # Convert backslashes to forward slashes
        normalized = normalized.replace('\\', '/')
        
        # Remove multiple consecutive slashes
        normalized = re.sub(r'/+', '/', normalized)
        
        # URL decode
        normalized = normalized.replace('%2e', '.').replace('%2f', '/').replace('%5c', '/')
        normalized = normalized.replace('%252e', '.').replace('%252f', '/').replace('%255c', '/')
        
        # Convert to lowercase for case-insensitive analysis
        normalized = normalized.lower()
        
        return normalized
    
    def _contains_path_traversal(self, path: str) -> bool:
        """
        Check for path traversal patterns.
        
        Args:
            path: Normalized path to check
            
        Returns:
            True if path traversal is detected
        """
        # Check for basic traversal patterns
        if '../' in path or '..\\' in path or path.endswith('..'):
            return True
        
        # Check for encoded traversal
        if '%2e%2e' in path or '%252e' in path:
            return True
        
        # Check for mixed separator traversal
        if re.search(r'\.\.[\\/]', path) or re.search(r'[\\/]\.\.', path):
            return True
        
        return False
    
    def _is_system_directory(self, path: str) -> bool:
        """
        Check if path accesses system directories.
        
        Args:
            path: Normalized path to check
            
        Returns:
            True if path accesses system directories
        """
        # Check against system directory patterns
        if self._system_dir_pattern.search(path):
            return True
        
        # Additional specific checks for absolute paths
        if path.startswith('/etc/') or path.startswith('/root/') or path.startswith('/proc/'):
            return True
        
        if path.startswith('/sys/') or path.startswith('/dev/') or path.startswith('/var/log/'):
            return True
            
        if path.startswith('/usr/lib/python') or path.startswith('/usr/local/lib/python'):
            return True
            
        if path.startswith('/opt/') or path.startswith('/boot/') or path.startswith('/lib/'):
            return True
            
        if path.startswith('/sbin/') or path.startswith('/usr/sbin/'):
            return True
            
        if path.startswith('/var/cache/') or path.startswith('/var/lib/') or path.startswith('/var/spool/'):
            return True
        
        # Specific file pattern checks
        if '/etc/passwd' in path or '/etc/shadow' in path or '/.ssh/' in path:
            return True
            
        if '.bash_history' in path or '_session' in path or '_token' in path:
            return True
        
        return False
    
    def _contains_unicode_attacks(self, path: str) -> bool:
        """
        Check for Unicode-based attacks.
        
        Args:
            path: Original path to check (before normalization)
            
        Returns:
            True if Unicode attack patterns are detected
        """
        # Check for Unicode path traversal (before normalization removes them)
        if '\u002e\u002e' in path:
            return True
        
        # Check for zero-width characters
        zero_width_chars = ['\u200b', '\u200c', '\u200d', '\ufeff', '\u202e']
        for char in zero_width_chars:
            if char in path:
                return True
        
        # Check for mixed scripts that could indicate homoglyph attacks
        # This is a basic check - more sophisticated detection could be added
        has_latin = any('\u0000' <= c <= '\u007f' for c in path)
        has_cyrillic = any('\u0400' <= c <= '\u04ff' for c in path)
        
        if has_latin and has_cyrillic:
            return True
        
        return False
    
    def _get_path_depth(self, path: str) -> int:
        """
        Calculate path depth (number of directory levels).
        
        Args:
            path: Path to analyze
            
        Returns:
            Number of directory levels
        """
        # Remove leading/trailing slashes and split
        clean_path = path.strip('/')
        if not clean_path:
            return 0
        
        return len(clean_path.split('/'))
    
    def get_security_statistics(self) -> dict:
        """
        Get security validation statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            "max_path_length": self._max_path_length,
            "max_input_length": self._max_input_length,
            "max_depth": self._max_depth,
            "dangerous_patterns_count": len(self.DANGEROUS_PATTERNS),
            "system_directories_count": len(self.SYSTEM_DIRECTORIES),
            "dangerous_extensions_count": len(self.DANGEROUS_EXTENSIONS)
        }