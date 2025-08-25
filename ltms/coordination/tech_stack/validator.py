"""
LTMC Tech Stack Validator - AST-based Pattern Validation

Production-grade tech stack validator with real LTMC database operations.
Smart modularized component focused on MCP pattern validation.

Performance SLA: <500ms validation operations
No mocks, stubs, or placeholders - production ready only.
"""

import ast
import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# Import LTMC tools
from ltms.tools.consolidated import memory_action, pattern_action

# Configure logging
logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation result severity levels"""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Structured validation result with LTMC integration"""
    validator: str
    severity: ValidationSeverity
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    details: Dict[str, Any] = None
    timestamp: float = None
    ltmc_ref: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.details is None:
            self.details = {}


class TechStackValidator:
    """
    Production-grade tech stack validator with real LTMC database operations.
    
    Focused on:
    - Real python-mcp-sdk pattern validation using AST analysis
    - LTMC memory integration for persistence
    - Performance-optimized for <500ms SLA
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize validator with LTMC integration"""
        self.project_root = Path(project_root) if project_root else Path(".")
        self.validation_cache = {}
        self.performance_metrics = {}
        
        # Initialize LTMC patterns - lazy initialization to avoid event loop conflicts
        self._patterns_initialized = False
    
    async def _ensure_patterns_initialized(self) -> None:
        """Ensure LTMC patterns are initialized (lazy initialization)"""
        if not self._patterns_initialized:
            await self._initialize_ltmc_patterns()
            self._patterns_initialized = True
    
    async def _initialize_ltmc_patterns(self) -> None:
        """Initialize LTMC patterns for tech stack validation"""
        try:
            # Store known MCP patterns in LTMC memory
            mcp_patterns = {
                "mcp_tool_decorator": "@mcp.tool",
                "mcp_server_creation": "mcp.server.Server()",
                "stdio_transport": "stdio.StdioServerTransport",
                "mcp_types_import": "from mcp import types",
                "server_run": "server.run()"
            }
            
            for pattern_name, pattern_code in mcp_patterns.items():
                await memory_action(
                    action="store",
                    file_name=f"mcp_pattern_{pattern_name}",
                    content=f"MCP Pattern: {pattern_name} = {pattern_code}",
                    tags=["tech_stack", "mcp_pattern", "validation"],
                    conversation_id="tech_stack_patterns"
                )
                
            logger.info("LTMC patterns initialized for tech stack validation")
            
        except Exception as e:
            logger.error(f"Failed to initialize LTMC patterns: {e}")
            raise
    
    async def validate_python_mcp_sdk_pattern(self, file_path: Path) -> List[ValidationResult]:
        """
        Real AST-based validation of python-mcp-sdk patterns.
        No mocks - actual code analysis.
        """
        start_time = time.time()
        results = []
        
        # Ensure patterns are initialized
        await self._ensure_patterns_initialized()
        
        try:
            if not file_path.exists():
                return [ValidationResult(
                    validator="python_mcp_sdk",
                    severity=ValidationSeverity.ERROR,
                    message=f"File not found: {file_path}"
                )]
            
            # Real AST parsing and analysis
            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()
            
            try:
                tree = ast.parse(file_content, filename=str(file_path))
            except SyntaxError as e:
                return [ValidationResult(
                    validator="python_mcp_sdk",
                    severity=ValidationSeverity.ERROR,
                    message=f"Syntax error in {file_path}: {e}",
                    line_number=e.lineno
                )]
            
            # Real MCP pattern detection
            mcp_patterns_found = await self._detect_mcp_patterns(tree, file_path)
            
            # Validate detected patterns against LTMC memory
            for pattern in mcp_patterns_found:
                # Store detection in LTMC memory
                ltmc_ref = await memory_action(
                    action="store",
                    file_name=f"validation_result_{pattern['type']}_{int(time.time())}",
                    content=f"MCP pattern detected: {pattern['type']} in {file_path}",
                    tags=["validation", "mcp_detection", "pattern_found"],
                    conversation_id="validation_results"
                )
                
                # Create validation result
                if pattern['valid']:
                    results.append(ValidationResult(
                        validator="python_mcp_sdk",
                        severity=ValidationSeverity.INFO,
                        message=f"Valid MCP pattern: {pattern['type']}",
                        file_path=str(file_path),
                        line_number=pattern['line'],
                        details=pattern,
                        ltmc_ref=ltmc_ref.get('file_name') if isinstance(ltmc_ref, dict) else str(ltmc_ref)
                    ))
                else:
                    results.append(ValidationResult(
                        validator="python_mcp_sdk", 
                        severity=ValidationSeverity.WARNING,
                        message=f"Invalid MCP pattern: {pattern['type']} - {pattern.get('issue', 'unknown issue')}",
                        file_path=str(file_path),
                        line_number=pattern['line'],
                        details=pattern,
                        ltmc_ref=ltmc_ref.get('file_name') if isinstance(ltmc_ref, dict) else str(ltmc_ref)
                    ))
            
            # Performance tracking
            elapsed = time.time() - start_time
            self.performance_metrics['mcp_validation'] = elapsed
            
            # SLA compliance check
            if elapsed > 0.5:  # 500ms SLA
                results.append(ValidationResult(
                    validator="python_mcp_sdk",
                    severity=ValidationSeverity.WARNING,
                    message=f"Validation exceeded SLA: {elapsed:.3f}s > 500ms",
                    details={"elapsed_time": elapsed}
                ))
            
            return results
            
        except Exception as e:
            logger.error(f"MCP pattern validation failed: {e}")
            return [ValidationResult(
                validator="python_mcp_sdk",
                severity=ValidationSeverity.ERROR,
                message=f"Validation failed: {str(e)}"
            )]
    
    async def _detect_mcp_patterns(self, tree: ast.AST, file_path: Path) -> List[Dict[str, Any]]:
        """Real AST-based MCP pattern detection"""
        from .pattern_detector import MCPPatternVisitor
        
        visitor = MCPPatternVisitor()
        visitor.visit(tree)
        
        return visitor.patterns
    
    def _has_fastapi_imports(self, content: str) -> bool:
        """Real FastAPI import detection"""
        fastapi_indicators = [
            "from fastapi import",
            "import fastapi",
            "from fastapi.responses import",
            "from fastapi.middleware import",
            "FastAPI(",
            "@app.get",
            "@app.post", 
            "uvicorn.run"
        ]
        
        return any(indicator in content for indicator in fastapi_indicators)
    
    def _has_mcp_imports(self, content: str) -> bool:
        """Real MCP import detection"""
        mcp_indicators = [
            "from mcp import",
            "import mcp",
            "@mcp.tool",
            "mcp.server",
            "stdio.StdioServerTransport",
            "server.run()",
            "@Tool"
        ]
        
        return any(indicator in content for indicator in mcp_indicators)
    
    async def detect_fastapi_mcp_conflict(self, directory: Path) -> List[ValidationResult]:
        """
        Real FastAPI/MCP conflict detection with actual import analysis.
        Detects event loop conflicts, import conflicts, and port binding issues.
        """
        from .conflict_detector import detect_framework_conflicts
        
        return await detect_framework_conflicts(self, directory)