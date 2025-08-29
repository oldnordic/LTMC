"""
LTMC Event Loop Conflict Detector - AST-based Analysis

Detects event loop conflicts in Python code using AST analysis.
Smart modularized component for loop conflict detection.

Performance SLA: <500ms operations
No mocks, stubs, or placeholders - production ready only.
"""

import ast
import logging
import time
from pathlib import Path
from typing import List

from ltms.tools.patterns.pattern_actions import pattern_action
from .monitor import EventLoopConflict, ConflictSeverity

# Configure logging
logger = logging.getLogger(__name__)


async def detect_code_conflicts(file_path: Path) -> List[EventLoopConflict]:
    """
    Detect event loop conflicts in code files using AST analysis.
    
    Args:
        file_path: Path to Python file to analyze
        
    Returns:
        List of detected conflicts
    """
    start_time = time.time()
    conflicts = []
    
    try:
        if not file_path.exists():
            return [EventLoopConflict(
                conflict_type="file_not_found",
                severity=ConflictSeverity.LOW,
                file_path=str(file_path),
                description=f"File not found: {file_path}"
            )]
        
        # Read and parse file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            return [EventLoopConflict(
                conflict_type="syntax_error",
                severity=ConflictSeverity.LOW,
                file_path=str(file_path),
                line_number=e.lineno,
                description=f"Syntax error: {e.msg}"
            )]
        
        # Analyze AST for event loop conflicts
        visitor = EventLoopConflictVisitor(str(file_path))
        visitor.visit(tree)
        conflicts.extend(visitor.conflicts)
        
        # Store analysis in LTMC
        pattern_action(
            action="log_attempt",
            code=content[:500] + "..." if len(content) > 500 else content,
            result="event_loop_conflict_analysis",
            tags=["ast_analysis", "conflict_detection", "code_analysis"],
            rationale=f"Found {len(conflicts)} potential event loop conflicts in {file_path.name}"
        )
        
        # Performance tracking
        analysis_time = time.time() - start_time
        if analysis_time > 0.5:  # 500ms SLA
            logger.warning(f"Code analysis exceeded SLA: {analysis_time:.3f}s > 500ms")
        
        return conflicts
        
    except Exception as e:
        logger.error(f"Error analyzing file {file_path}: {e}")
        return [EventLoopConflict(
            conflict_type="analysis_error",
            severity=ConflictSeverity.MEDIUM,
            file_path=str(file_path),
            description=f"Analysis failed: {str(e)}"
        )]


class EventLoopConflictVisitor(ast.NodeVisitor):
    """AST visitor for detecting event loop conflicts in code"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.conflicts = []
        self.imports = set()
        self.has_asyncio_run = False
        self.has_mcp = False
        self.has_fastapi = False
    
    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)
            if alias.name == 'asyncio':
                pass
            elif 'fastapi' in alias.name.lower():
                self.has_fastapi = True
            elif 'mcp' in alias.name.lower():
                self.has_mcp = True
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node):
        if node.module:
            self.imports.add(node.module)
            if 'fastapi' in node.module.lower():
                self.has_fastapi = True
            elif 'mcp' in node.module.lower():
                self.has_mcp = True
        self.generic_visit(node)
    
    def visit_Call(self, node):
        # Check for asyncio.run() calls
        if (isinstance(node.func, ast.Attribute) and
            isinstance(node.func.value, ast.Name) and
            node.func.value.id == 'asyncio' and
            node.func.attr == 'run'):
            
            self.has_asyncio_run = True
            self.conflicts.append(EventLoopConflict(
                conflict_type="asyncio_run_detected",
                severity=ConflictSeverity.HIGH,
                file_path=self.file_path,
                line_number=node.lineno,
                pattern="asyncio.run()",
                description="asyncio.run() call detected - may cause conflicts in MCP context",
                resolution_suggestion="Use async factory pattern or await directly in async context"
            ))
        
        # Check for new_event_loop calls
        if (isinstance(node.func, ast.Attribute) and
            isinstance(node.func.value, ast.Name) and
            node.func.value.id == 'asyncio' and
            node.func.attr == 'new_event_loop'):
            
            self.conflicts.append(EventLoopConflict(
                conflict_type="new_event_loop",
                severity=ConflictSeverity.MEDIUM,
                file_path=self.file_path,
                line_number=node.lineno,
                pattern="asyncio.new_event_loop()",
                description="New event loop creation detected",
                resolution_suggestion="Use existing event loop or ensure proper cleanup"
            ))
        
        self.generic_visit(node)
    
    def visit_Module(self, node):
        # Visit all nodes first to collect information
        self.generic_visit(node)
        
        # After visiting all nodes, check for framework conflicts
        if self.has_fastapi and self.has_mcp:
            self.conflicts.append(EventLoopConflict(
                conflict_type="framework_import_conflict",
                severity=ConflictSeverity.CRITICAL,
                file_path=self.file_path,
                pattern="FastAPI + MCP imports",
                description="Both FastAPI and MCP frameworks imported - event loop conflicts likely",
                resolution_suggestion="Separate frameworks into different processes or use MCP over HTTP transport"
            ))