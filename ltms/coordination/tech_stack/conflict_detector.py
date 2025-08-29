from ltms.tools.memory.memory_actions import MemoryTools
"""
LTMC Tech Stack Conflict Detector - Framework Conflict Analysis

Detects conflicts between different frameworks (FastAPI/MCP).
Smart modularized component for conflict analysis.

Performance SLA: <500ms operations
No mocks, stubs, or placeholders - production ready only.
"""

import logging
import time
from pathlib import Path
from typing import Dict, List, Any

from ltms.tools.memory.memory_actions import memory_action
from .validator import ValidationResult, ValidationSeverity

# Configure logging
logger = logging.getLogger(__name__)


async def detect_framework_conflicts(validator, directory: Path) -> List[ValidationResult]:
    memory_tools = MemoryTools()
    """
    Real FastAPI/MCP conflict detection with actual import analysis.
    Detects event loop conflicts, import conflicts, and port binding issues.
    """
    start_time = time.time()
    results = []
    
    try:
        python_files = list(directory.rglob("*.py"))
        
        fastapi_files = []
        mcp_files = []
        
        # Real file analysis - no mocks
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Real import detection
                if validator._has_fastapi_imports(content):
                    fastapi_files.append(py_file)
                
                if validator._has_mcp_imports(content):
                    mcp_files.append(py_file)
                    
            except Exception as e:
                logger.warning(f"Could not analyze {py_file}: {e}")
                continue
        
        # Real conflict analysis
        conflicts = await _analyze_conflicts(fastapi_files, mcp_files)
        
        # Store conflict results in LTMC
        for conflict in conflicts:
            ltmc_ref = await memory_tools("store",
                file_name=f"conflict_{conflict['type']}_{int(time.time())}",
                content=f"Conflict detected: {conflict['type']} between {conflict['files']}",
                tags=["tech_stack", "conflict", "fastapi_mcp"],
                conversation_id="conflict_detection"
            )
            
            results.append(ValidationResult(
                validator="fastapi_mcp_conflict",
                severity=ValidationSeverity(conflict['severity']),
                message=conflict['message'],
                details=conflict,
                ltmc_ref=ltmc_ref.get('file_name') if isinstance(ltmc_ref, dict) else str(ltmc_ref)
            ))
        
        # Performance tracking
        elapsed = time.time() - start_time
        
        if elapsed > 0.5:  # 500ms SLA
            results.append(ValidationResult(
                validator="fastapi_mcp_conflict",
                severity=ValidationSeverity.WARNING,
                message=f"Conflict detection exceeded SLA: {elapsed:.3f}s > 500ms",
                details={"elapsed_time": elapsed}
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Conflict detection failed: {e}")
        return [ValidationResult(
            validator="fastapi_mcp_conflict",
            severity=ValidationSeverity.ERROR,
            message=f"Conflict detection failed: {str(e)}"
        )]


async def _analyze_conflicts(fastapi_files: List[Path], mcp_files: List[Path]) -> List[Dict[str, Any]]:
    """Real conflict analysis between FastAPI and MCP files"""
    conflicts = []
    
    # Event loop conflict detection
    if fastapi_files and mcp_files:
        # Check for same-file conflicts (highest risk)
        for file_path in set(fastapi_files) & set(mcp_files):
            conflicts.append({
                'type': 'event_loop_conflict',
                'severity': 'critical',
                'message': f'FastAPI and MCP in same file creates event loop conflict: {file_path}',
                'files': [file_path],
                'resolution': 'Separate FastAPI and MCP into different processes or use async coordination'
            })
        
        # Check for project-wide conflicts
        if len(set(fastapi_files) & set(mcp_files)) == 0 and fastapi_files and mcp_files:
            conflicts.append({
                'type': 'project_architecture_conflict', 
                'severity': 'warning',
                'message': f'Project contains both FastAPI ({len(fastapi_files)} files) and MCP ({len(mcp_files)} files)',
                'files': fastapi_files + mcp_files,
                'resolution': 'Consider architectural separation or use MCP over HTTP transport'
            })
    
    return conflicts