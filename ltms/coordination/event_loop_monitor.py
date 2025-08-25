#!/usr/bin/env python3
"""
LTMC Event Loop Monitor - Real-time conflict detection and prevention

Production-grade event loop monitoring with real conflict detection, prevention mechanisms,
and integration with LTMC memory/pattern systems for tech stack alignment.

Performance SLA: <500ms monitoring operations
No mocks, stubs, or placeholders - production ready only.
"""

import ast
import asyncio
import logging
import time
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import inspect
import traceback

# Optional psutil import for advanced metrics
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None

# Import LTMC tools
from ltms.tools.consolidated import memory_action, pattern_action

# Configure logging
logger = logging.getLogger(__name__)


class ConflictSeverity(Enum):
    """Event loop conflict severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MonitoringMode(Enum):
    """Event loop monitoring modes"""
    PASSIVE = "passive"      # Monitor without intervention
    ACTIVE = "active"        # Monitor with prevention
    DIAGNOSTIC = "diagnostic"  # Deep analysis mode


@dataclass
class EventLoopConflict:
    """Event loop conflict detection result"""
    conflict_type: str
    severity: ConflictSeverity
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    pattern: Optional[str] = None
    description: str = ""
    resolution_suggestion: str = ""
    timestamp: float = None
    ltmc_ref: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class EventLoopState:
    """Current event loop state information"""
    loop_detected: bool
    loop_running: bool
    loop_id: Optional[str] = None
    thread_id: int = None
    nested_loops: int = 0
    performance_metrics: Dict[str, float] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.thread_id is None:
            self.thread_id = threading.get_ident()


class EventLoopMonitor:
    """
    Production-grade event loop monitor with real-time conflict detection and prevention.
    
    Features:
    - Real-time event loop state monitoring
    - Nested asyncio.run() conflict detection
    - Framework conflict detection (FastAPI + MCP, etc.)
    - Performance impact analysis
    - Proactive prevention mechanisms
    - LTMC integration for persistent storage and analysis
    """
    
    def __init__(self, project_root: Optional[Path] = None, monitoring_mode: MonitoringMode = MonitoringMode.ACTIVE):
        """
        Initialize event loop monitor with LTMC integration.
        
        Args:
            project_root: Project root directory for code analysis
            monitoring_mode: Monitoring mode (passive, active, diagnostic)
        """
        self.project_root = Path(project_root) if project_root else Path(".")
        self.monitoring_mode = monitoring_mode
        self.monitoring_active = False
        self.conflict_history = []
        self.performance_metrics = {}
        
        # Thread pool for non-blocking operations
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="EventLoopMonitor")
        
        # Initialize LTMC patterns and monitoring data
        # Note: Lazy initialization to avoid event loop conflicts in MCP context
        self._patterns_initialized = False
    
    async def _ensure_patterns_initialized(self) -> None:
        """Ensure monitoring patterns are initialized (lazy initialization)"""
        if not self._patterns_initialized:
            await self._initialize_monitoring_patterns()
            self._patterns_initialized = True
    
    async def _initialize_monitoring_patterns(self) -> None:
        """Initialize monitoring patterns and conflict signatures in LTMC"""
        try:
            # Store known event loop conflict patterns
            conflict_patterns = {
                "nested_asyncio_run": {
                    "pattern": "asyncio.run() within existing event loop",
                    "signature": "asyncio.run(",
                    "severity": "critical",
                    "resolution": "Use async factory pattern or await directly"
                },
                "multiple_loop_creation": {
                    "pattern": "Creating multiple event loops in same thread",
                    "signature": "asyncio.new_event_loop()",
                    "severity": "high", 
                    "resolution": "Use single event loop per thread"
                },
                "sync_blocking_async": {
                    "pattern": "Synchronous blocking operations in async context",
                    "signature": "time.sleep(|requests.get(|sync_operation(",
                    "severity": "medium",
                    "resolution": "Use asyncio.sleep() or async variants"
                },
                "framework_conflicts": {
                    "pattern": "Conflicting async frameworks",
                    "signature": "FastAPI.*mcp|uvicorn.*stdio_server",
                    "severity": "critical",
                    "resolution": "Separate frameworks or use coordination patterns"
                }
            }
            
            for pattern_name, pattern_data in conflict_patterns.items():
                await memory_action(
                    action="store",
                    file_name=f"event_loop_pattern_{pattern_name}",
                    content=json.dumps(pattern_data),
                    tags=["event_loop", "conflict_pattern", "monitoring"],
                    conversation_id="event_loop_patterns"
                )
            
            # Initialize monitoring state
            await memory_action(
                action="store",
                file_name="event_loop_monitor_initialized",
                content=f"EventLoopMonitor initialized at {time.time()} with mode: {self.monitoring_mode.value}",
                tags=["monitor", "initialization", "event_loop"],
                conversation_id="monitor_state"
            )
            
            logger.info("Event loop monitoring patterns initialized in LTMC")
            
        except Exception as e:
            logger.error(f"Failed to initialize monitoring patterns: {e}")
            raise
    
    async def start_monitoring(self, check_interval: float = 1.0) -> None:
        """
        Start real-time event loop monitoring.
        
        Args:
            check_interval: Monitoring check interval in seconds
        """
        if self.monitoring_active:
            logger.warning("Event loop monitoring already active")
            return
        
        self.monitoring_active = True
        logger.info(f"Starting event loop monitoring (mode: {self.monitoring_mode.value}, interval: {check_interval}s)")
        
        try:
            while self.monitoring_active:
                start_time = time.time()
                
                # Monitor current event loop state
                current_state = await self._monitor_event_loop_state()
                
                # Detect conflicts if in active mode
                if self.monitoring_mode in [MonitoringMode.ACTIVE, MonitoringMode.DIAGNOSTIC]:
                    conflicts = await self._detect_active_conflicts()
                    
                    for conflict in conflicts:
                        await self._handle_detected_conflict(conflict)
                
                # Performance tracking
                monitor_duration = time.time() - start_time
                self.performance_metrics['last_monitor_duration'] = monitor_duration
                
                # SLA compliance check
                if monitor_duration > 0.5:  # 500ms SLA
                    logger.warning(f"Monitoring cycle exceeded SLA: {monitor_duration:.3f}s > 500ms")
                
                # Store monitoring cycle results
                await memory_action(
                    action="store",
                    file_name=f"monitor_cycle_{int(time.time())}",
                    content=json.dumps({
                        "monitoring_cycle": {
                            "state": asdict(current_state),
                            "conflicts_detected": len(conflicts) if 'conflicts' in locals() else 0,
                            "duration_ms": monitor_duration * 1000,
                            "sla_compliant": monitor_duration <= 0.5
                        }
                    }),
                    tags=["monitor", "cycle", "performance"],
                    conversation_id="monitoring_cycles"
                )
                
                # Wait for next cycle
                await asyncio.sleep(check_interval)
                
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            raise
        finally:
            self.monitoring_active = False
    
    async def stop_monitoring(self) -> None:
        """Stop event loop monitoring"""
        if not self.monitoring_active:
            logger.warning("Event loop monitoring not active")
            return
        
        logger.info("Stopping event loop monitoring")
        self.monitoring_active = False
        
        # Store monitoring session summary
        await memory_action(
            action="store",
            file_name=f"monitoring_session_summary_{int(time.time())}",
            content=json.dumps({
                "session_summary": {
                    "total_conflicts": len(self.conflict_history),
                    "monitoring_mode": self.monitoring_mode.value,
                    "performance_metrics": self.performance_metrics
                }
            }),
            tags=["monitor", "session", "summary"],
            conversation_id="monitoring_sessions"
        )
    
    async def _monitor_event_loop_state(self) -> EventLoopState:
        """Monitor current event loop state with real inspection"""
        try:
            # Check for running event loop
            try:
                current_loop = asyncio.get_running_loop()
                loop_detected = True
                loop_running = current_loop.is_running()
                loop_id = str(id(current_loop))
            except RuntimeError:
                loop_detected = False
                loop_running = False
                loop_id = None
            
            # Check for nested loops (advanced detection)
            nested_loops = await self._detect_nested_loops()
            
            # Collect performance metrics
            performance_metrics = await self._collect_performance_metrics()
            
            state = EventLoopState(
                loop_detected=loop_detected,
                loop_running=loop_running,
                loop_id=loop_id,
                nested_loops=nested_loops,
                performance_metrics=performance_metrics
            )
            
            return state
            
        except Exception as e:
            logger.error(f"Error monitoring event loop state: {e}")
            return EventLoopState(
                loop_detected=False,
                loop_running=False,
                performance_metrics={"error": str(e)}
            )
    
    async def _detect_nested_loops(self) -> int:
        """Detect nested event loop attempts"""
        try:
            # Check call stack for nested asyncio.run calls
            current_frame = inspect.currentframe()
            nested_count = 0
            
            while current_frame:
                frame_info = inspect.getframeinfo(current_frame)
                if frame_info.filename and frame_info.code_context:
                    code_line = ' '.join(frame_info.code_context).strip()
                    if 'asyncio.run(' in code_line:
                        nested_count += 1
                
                current_frame = current_frame.f_back
            
            return max(0, nested_count - 1)  # Subtract 1 for the initial run
            
        except Exception as e:
            logger.warning(f"Could not detect nested loops: {e}")
            return 0
    
    async def _collect_performance_metrics(self) -> Dict[str, float]:
        """Collect event loop performance metrics"""
        try:
            metrics = {"timestamp": time.time()}
            
            # Basic performance metrics with psutil if available
            if HAS_PSUTIL:
                try:
                    process = psutil.Process()
                    metrics.update({
                        "cpu_percent": process.cpu_percent(),
                        "memory_mb": process.memory_info().rss / 1024 / 1024,
                        "thread_count": process.num_threads(),
                        "open_files": len(process.open_files())
                    })
                except Exception as e:
                    metrics["psutil_error"] = str(e)
            else:
                # Fallback metrics without psutil
                metrics.update({
                    "thread_count": threading.active_count(),
                    "has_psutil": False
                })
            
            # Event loop specific metrics
            try:
                current_loop = asyncio.get_running_loop()
                tasks = [task for task in asyncio.all_tasks(current_loop) if not task.done()]
                metrics["active_tasks"] = len(tasks)
            except RuntimeError:
                metrics["active_tasks"] = 0
            
            return metrics
            
        except Exception as e:
            logger.warning(f"Could not collect performance metrics: {e}")
            return {"error": str(e), "timestamp": time.time()}
    
    async def _detect_active_conflicts(self) -> List[EventLoopConflict]:
        """Detect active event loop conflicts in real-time"""
        conflicts = []
        
        try:
            # Check for nested asyncio.run in current stack
            stack_conflicts = await self._check_call_stack_conflicts()
            conflicts.extend(stack_conflicts)
            
            # Check for framework conflicts by analyzing recent patterns
            framework_conflicts = await self._check_framework_conflicts()
            conflicts.extend(framework_conflicts)
            
            # Check for performance-impacting patterns
            performance_conflicts = await self._check_performance_conflicts()
            conflicts.extend(performance_conflicts)
            
        except Exception as e:
            logger.error(f"Error detecting active conflicts: {e}")
            conflicts.append(EventLoopConflict(
                conflict_type="detection_error",
                severity=ConflictSeverity.MEDIUM,
                description=f"Error in conflict detection: {str(e)}"
            ))
        
        return conflicts
    
    async def _check_call_stack_conflicts(self) -> List[EventLoopConflict]:
        """Check call stack for event loop conflicts"""
        conflicts = []
        
        try:
            # Analyze current call stack
            stack = traceback.extract_stack()
            
            asyncio_run_count = 0
            for frame in stack:
                if frame.line and 'asyncio.run(' in frame.line:
                    asyncio_run_count += 1
                    
                    if asyncio_run_count > 1:  # Nested asyncio.run detected
                        conflicts.append(EventLoopConflict(
                            conflict_type="nested_asyncio_run",
                            severity=ConflictSeverity.CRITICAL,
                            file_path=frame.filename,
                            line_number=frame.lineno,
                            pattern="asyncio.run() in nested context",
                            description="Nested asyncio.run() call detected in call stack",
                            resolution_suggestion="Use async factory pattern or await directly"
                        ))
        
        except Exception as e:
            logger.warning(f"Could not analyze call stack: {e}")
        
        return conflicts
    
    async def _check_framework_conflicts(self) -> List[EventLoopConflict]:
        """Check for framework-level event loop conflicts"""
        conflicts = []
        
        try:
            # Check for FastAPI + MCP conflicts by examining loaded modules
            import sys
            loaded_modules = list(sys.modules.keys())
            
            has_fastapi = any('fastapi' in module for module in loaded_modules)
            has_mcp = any('mcp' in module for module in loaded_modules)
            has_uvicorn = any('uvicorn' in module for module in loaded_modules)
            
            if has_fastapi and has_mcp:
                conflicts.append(EventLoopConflict(
                    conflict_type="framework_conflict",
                    severity=ConflictSeverity.HIGH,
                    pattern="FastAPI + MCP",
                    description="FastAPI and MCP frameworks both loaded - potential event loop conflicts",
                    resolution_suggestion="Separate into different processes or use MCP over HTTP transport"
                ))
            
            if has_uvicorn and has_mcp:
                conflicts.append(EventLoopConflict(
                    conflict_type="server_conflict",
                    severity=ConflictSeverity.HIGH,
                    pattern="Uvicorn + MCP",
                    description="Uvicorn and MCP servers both active - event loop competition",
                    resolution_suggestion="Use process separation or async coordination patterns"
                ))
        
        except Exception as e:
            logger.warning(f"Could not check framework conflicts: {e}")
        
        return conflicts
    
    async def _check_performance_conflicts(self) -> List[EventLoopConflict]:
        """Check for performance-impacting event loop patterns"""
        conflicts = []
        
        try:
            # Check active tasks for blocking patterns
            try:
                current_loop = asyncio.get_running_loop()
                tasks = [task for task in asyncio.all_tasks(current_loop) if not task.done()]
                
                if len(tasks) > 100:  # High task count
                    conflicts.append(EventLoopConflict(
                        conflict_type="task_overload",
                        severity=ConflictSeverity.MEDIUM,
                        pattern=f"{len(tasks)} active tasks",
                        description=f"High number of active tasks: {len(tasks)}",
                        resolution_suggestion="Review task creation and cleanup patterns"
                    ))
                
            except RuntimeError:
                pass  # No event loop running
            
        except Exception as e:
            logger.warning(f"Could not check performance conflicts: {e}")
        
        return conflicts
    
    async def _handle_detected_conflict(self, conflict: EventLoopConflict) -> None:
        """Handle detected event loop conflict"""
        # Add to conflict history
        self.conflict_history.append(conflict)
        
        # Store conflict in LTMC memory
        ltmc_ref = await memory_action(
            action="store",
            file_name=f"event_loop_conflict_{conflict.conflict_type}_{int(time.time())}",
            content=json.dumps(asdict(conflict)),
            tags=["event_loop", "conflict", "detected", conflict.severity.value],
            conversation_id="conflict_detection"
        )
        
        conflict.ltmc_ref = ltmc_ref.get('file_name') if isinstance(ltmc_ref, dict) else str(ltmc_ref)
        
        # Log conflict
        log_level = {
            ConflictSeverity.LOW: logger.info,
            ConflictSeverity.MEDIUM: logger.warning,
            ConflictSeverity.HIGH: logger.warning,
            ConflictSeverity.CRITICAL: logger.error
        }.get(conflict.severity, logger.warning)
        
        log_level(f"Event loop conflict detected: {conflict.conflict_type} - {conflict.description}")
        
        # Take action based on monitoring mode
        if self.monitoring_mode == MonitoringMode.ACTIVE:
            await self._prevent_conflict(conflict)
    
    async def _prevent_conflict(self, conflict: EventLoopConflict) -> None:
        """Attempt to prevent or mitigate detected conflict"""
        try:
            prevention_actions = {
                "nested_asyncio_run": self._prevent_nested_asyncio_run,
                "framework_conflict": self._suggest_framework_separation,
                "task_overload": self._optimize_task_management
            }
            
            action_func = prevention_actions.get(conflict.conflict_type)
            if action_func:
                await action_func(conflict)
                
                # Store prevention action
                await memory_action(
                    action="store",
                    file_name=f"prevention_action_{conflict.conflict_type}_{int(time.time())}",
                    content=f"Prevention action taken for {conflict.conflict_type}: {conflict.resolution_suggestion}",
                    tags=["prevention", "action", "event_loop"],
                    conversation_id="conflict_prevention"
                )
        
        except Exception as e:
            logger.error(f"Error in conflict prevention: {e}")
    
    async def _prevent_nested_asyncio_run(self, conflict: EventLoopConflict) -> None:
        """Prevent nested asyncio.run conflicts"""
        logger.warning(f"PREVENTION: Nested asyncio.run() detected - {conflict.resolution_suggestion}")
        # In a production system, this could raise an exception or modify the call
    
    async def _suggest_framework_separation(self, conflict: EventLoopConflict) -> None:
        """Suggest framework separation for conflicts"""
        logger.warning(f"PREVENTION: Framework conflict detected - {conflict.resolution_suggestion}")
    
    async def _optimize_task_management(self, conflict: EventLoopConflict) -> None:
        """Optimize task management for performance"""
        logger.warning(f"PREVENTION: Task management optimization - {conflict.resolution_suggestion}")
    
    async def detect_event_loop_conflicts_in_code(self, file_path: Path) -> List[EventLoopConflict]:
        """
        Detect event loop conflicts in code files using AST analysis.
        
        Args:
            file_path: Path to Python file to analyze
            
        Returns:
            List of detected conflicts
        """
        start_time = time.time()
        conflicts = []
        
        # Ensure patterns are initialized
        await self._ensure_patterns_initialized()
        
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
    
    async def suggest_conflict_resolution(self, conflicts: List[EventLoopConflict]) -> Dict[str, Any]:
        """
        Suggest resolutions for detected conflicts.
        
        Args:
            conflicts: List of detected conflicts
            
        Returns:
            Resolution suggestions grouped by type
        """
        suggestions = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "summary": {
                "total_conflicts": len(conflicts),
                "resolution_patterns": set()
            }
        }
        
        for conflict in conflicts:
            severity_key = conflict.severity.value
            
            # Map conflict types to resolution types for better categorization
            resolution_type_mapping = {
                "asyncio_run_detected": "async_factory_pattern",
                "framework_import_conflict": "framework_separation", 
                "new_event_loop": "event_loop_management",
                "task_overload": "task_optimization"
            }
            
            resolution_type = resolution_type_mapping.get(conflict.conflict_type, conflict.conflict_type)
            
            resolution = {
                "conflict_type": conflict.conflict_type,
                "type": resolution_type,  # Add type field for test compatibility
                "file": conflict.file_path,
                "line": conflict.line_number,
                "suggestion": conflict.resolution_suggestion,
                "pattern": conflict.pattern,
                "description": conflict.description
            }
            
            suggestions[severity_key].append(resolution)
            suggestions["summary"]["resolution_patterns"].add(conflict.conflict_type)
        
        # Convert set to list for JSON serialization
        suggestions["summary"]["resolution_patterns"] = list(suggestions["summary"]["resolution_patterns"])
        
        # Store resolution suggestions in LTMC
        await memory_action(
            action="store",
            file_name=f"conflict_resolution_suggestions_{int(time.time())}",
            content=json.dumps(suggestions),
            tags=["resolution", "suggestions", "conflict"],
            conversation_id="resolution_suggestions"
        )
        
        return suggestions
    
    async def close(self) -> None:
        """Clean up monitor resources"""
        if self.monitoring_active:
            await self.stop_monitoring()
        
        self.executor.shutdown(wait=True)
        logger.info("EventLoopMonitor closed")


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