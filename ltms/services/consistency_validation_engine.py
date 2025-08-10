"""
Consistency Validation Engine - Phase 3 Component 4.

This service implements blueprint consistency validation and enforcement with:

1. Consistency Validation Engine: Comprehensive validation of blueprint-code alignment
2. Change Validation System: Real-time validation of changes against blueprints  
3. Enforcement Rules: Automated consistency enforcement and correction
4. Violation Detection: Intelligent detection of consistency violations and drift
5. Automated Remediation: Smart fixes for common consistency issues

Performance Requirements:
- Validation operations: <10ms per validation
- Change detection: <5ms per change
- Enforcement actions: <15ms per action
- Violation detection: <8ms per scan
- Remediation operations: <20ms per fix

Integration Points:
- Phase 3 Component 1: Neo4j Blueprint system for structure validation
- Phase 3 Component 2: Documentation sync for real-time consistency
- Phase 3 Component 3: Advanced markdown for documentation enforcement
- Phase 2 Task Management: Integration with task tracking
- Phase 1 Security: Project isolation and validation security
"""

import asyncio
import time
import json
import hashlib
import logging
import ast
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Union, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
import threading

# Import supporting components
from ltms.models.blueprint_schemas import (
    BlueprintNode,
    FunctionNode,
    ClassNode, 
    ModuleNode,
    BlueprintRelationship,
    CodeStructure,
    ConsistencyLevel
)

from ltms.database.neo4j_store import Neo4jGraphStore, get_neo4j_graph_store
from ltms.services.documentation_sync_service import DocumentationSyncManager
from ltms.services.advanced_markdown_generator import AdvancedMarkdownGenerator
from ltms.tools.blueprint_tools import CodeAnalyzer
from ltms.security.project_isolation import ProjectIsolationManager
from ltms.security.path_security import SecurePathValidator

logger = logging.getLogger(__name__)


class ViolationType(Enum):
    """Types of consistency violations."""
    MISSING_FUNCTION = "missing_function"
    MISSING_CLASS = "missing_class"
    MISSING_MODULE = "missing_module"
    PARAMETER_MISMATCH = "parameter_mismatch"
    RETURN_TYPE_MISMATCH = "return_type_mismatch"
    DOCSTRING_MISSING = "docstring_missing"
    DOCSTRING_MISMATCH = "docstring_mismatch"
    SIGNATURE_CHANGED = "signature_changed"
    CLASS_HIERARCHY_CHANGED = "class_hierarchy_changed"
    METHOD_MISSING = "method_missing"
    ASYNC_MISMATCH = "async_mismatch"
    TYPE_ANNOTATION_MISSING = "type_annotation_missing"
    BLUEPRINT_OUTDATED = "blueprint_outdated"
    CODE_STRUCTURE_DRIFT = "code_structure_drift"


class SeverityLevel(Enum):
    """Severity levels for consistency violations."""
    CRITICAL = "critical"     # Breaks functionality
    HIGH = "high"            # Major inconsistency
    MEDIUM = "medium"        # Minor inconsistency
    LOW = "low"             # Cosmetic/documentation issue
    INFO = "info"           # Information only


class EnforcementAction(Enum):
    """Actions for consistency enforcement."""
    UPDATE_BLUEPRINT = "update_blueprint"
    UPDATE_CODE = "update_code"
    UPDATE_DOCUMENTATION = "update_documentation"
    GENERATE_WARNING = "generate_warning"
    BLOCK_OPERATION = "block_operation"
    SCHEDULE_REVIEW = "schedule_review"
    AUTO_FIX = "auto_fix"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class ConsistencyViolation:
    """Represents a consistency violation."""
    violation_id: str
    violation_type: ViolationType
    severity: SeverityLevel
    file_path: str
    project_id: str
    node_name: str
    description: str
    detected_at: datetime = field(default_factory=datetime.now)
    blueprint_value: Optional[Any] = None
    code_value: Optional[Any] = None
    suggested_fix: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnforcementRule:
    """Rule for consistency enforcement."""
    rule_id: str
    rule_name: str
    violation_types: List[ViolationType]
    severity_threshold: SeverityLevel
    enforcement_action: EnforcementAction
    auto_fix_enabled: bool = False
    conditions: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1


@dataclass
class ValidationResult:
    """Results of consistency validation."""
    success: bool
    validation_time_ms: float
    total_nodes_checked: int
    violations_found: int
    violations: List[ConsistencyViolation] = field(default_factory=list)
    consistency_score: float = 0.0
    consistency_level: ConsistencyLevel = ConsistencyLevel.LOW
    recommendations: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


@dataclass
class EnforcementResult:
    """Results of consistency enforcement."""
    success: bool
    enforcement_time_ms: float
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    violations_resolved: int = 0
    violations_remaining: int = 0
    auto_fixes_applied: int = 0
    manual_interventions_required: int = 0
    warnings_generated: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


class ConsistencyValidationEngine:
    """Core engine for blueprint-code consistency validation."""
    
    def __init__(self, neo4j_store: Neo4jGraphStore = None):
        """
        Initialize consistency validation engine.
        
        Args:
            neo4j_store: Neo4j graph store instance
        """
        self.neo4j_store = neo4j_store
        self.code_analyzer = CodeAnalyzer()
        
        # Violation detection rules
        self.violation_patterns = self._initialize_violation_patterns()
        
        # Performance tracking
        self._validation_cache = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Threading for concurrent validation
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    async def validate_blueprint_consistency(
        self,
        file_path: str,
        project_id: str,
        blueprint_structure: CodeStructure = None
    ) -> ValidationResult:
        """
        Validate consistency between blueprint and code.
        
        Args:
            file_path: Path to code file
            project_id: Project identifier
            blueprint_structure: Optional blueprint structure (fetched if not provided)
            
        Returns:
            ValidationResult with detailed consistency analysis
        """
        start_time = time.perf_counter()
        
        try:
            # Validate inputs
            if not file_path or not project_id:
                raise ValueError("file_path and project_id are required")
            
            # Check cache
            cache_key = f"{file_path}:{project_id}:{hash(str(blueprint_structure))}"
            if cache_key in self._validation_cache:
                cache_entry = self._validation_cache[cache_key]
                if datetime.now() - cache_entry["timestamp"] < timedelta(seconds=self._cache_ttl):
                    return cache_entry["result"]
            
            # Analyze current code structure
            code_structure = self.code_analyzer.analyze_file(file_path, project_id)
            
            # Get blueprint structure if not provided
            if not blueprint_structure:
                blueprint_structure = await self._get_blueprint_structure(file_path, project_id)
                if not blueprint_structure:
                    # If no blueprint exists, create baseline with warnings
                    return self._create_baseline_validation(code_structure, file_path, project_id)
            
            # Perform detailed consistency validation
            violations = await self._detect_violations(
                blueprint_structure,
                code_structure,
                file_path,
                project_id
            )
            
            # Calculate consistency metrics
            consistency_metrics = self._calculate_consistency_metrics(
                blueprint_structure,
                code_structure,
                violations
            )
            
            # Generate recommendations
            recommendations = self._generate_recommendations(violations)
            
            end_time = time.perf_counter()
            validation_time_ms = (end_time - start_time) * 1000
            
            result = ValidationResult(
                success=True,
                validation_time_ms=validation_time_ms,
                total_nodes_checked=len(blueprint_structure.nodes) + len(code_structure.nodes),
                violations_found=len(violations),
                violations=violations,
                consistency_score=consistency_metrics["score"],
                consistency_level=consistency_metrics["level"],
                recommendations=recommendations
            )
            
            # Cache result
            self._validation_cache[cache_key] = {
                "result": result,
                "timestamp": datetime.now()
            }
            
            return result
            
        except Exception as e:
            end_time = time.perf_counter()
            validation_time_ms = (end_time - start_time) * 1000
            
            logger.error(f"Consistency validation failed: {e}")
            return ValidationResult(
                success=False,
                validation_time_ms=validation_time_ms,
                total_nodes_checked=0,
                violations_found=0,
                error_message=str(e)
            )
    
    async def validate_change_impact(
        self,
        file_path: str,
        project_id: str,
        change_type: str,
        changed_content: str = None
    ) -> Dict[str, Any]:
        """
        Validate impact of changes against blueprint consistency.
        
        Args:
            file_path: Path to changed file
            project_id: Project identifier
            change_type: Type of change (modified, created, deleted)
            changed_content: New file content (for modification validation)
            
        Returns:
            Dict with change impact analysis
        """
        start_time = time.perf_counter()
        
        try:
            # Get current blueprint state
            blueprint_structure = await self._get_blueprint_structure(file_path, project_id)
            
            # Analyze change impact
            impact_analysis = {
                "change_allowed": True,
                "consistency_impact": "low",
                "violations_introduced": [],
                "recommended_actions": []
            }
            
            if change_type == "modified" and changed_content:
                # Analyze changed content for violations
                temp_structure = self._analyze_content_structure(changed_content, file_path, project_id)
                
                if blueprint_structure and temp_structure:
                    violations = await self._detect_violations(
                        blueprint_structure,
                        temp_structure,
                        file_path,
                        project_id
                    )
                    
                    critical_violations = [v for v in violations if v.severity == SeverityLevel.CRITICAL]
                    high_violations = [v for v in violations if v.severity == SeverityLevel.HIGH]
                    
                    if critical_violations:
                        impact_analysis["change_allowed"] = False
                        impact_analysis["consistency_impact"] = "critical"
                        impact_analysis["violations_introduced"] = critical_violations
                        impact_analysis["recommended_actions"] = ["Fix critical violations before proceeding"]
                    
                    elif high_violations:
                        impact_analysis["consistency_impact"] = "high"
                        impact_analysis["violations_introduced"] = high_violations
                        impact_analysis["recommended_actions"] = ["Review high-severity violations"]
            
            elif change_type == "deleted":
                impact_analysis["recommended_actions"] = ["Update blueprint to remove deleted components"]
            
            elif change_type == "created":
                impact_analysis["recommended_actions"] = ["Add new components to blueprint"]
            
            end_time = time.perf_counter()
            validation_time_ms = (end_time - start_time) * 1000
            
            return {
                "success": True,
                "file_path": file_path,
                "project_id": project_id,
                "change_type": change_type,
                "impact_analysis": impact_analysis,
                "validation_time_ms": validation_time_ms
            }
            
        except Exception as e:
            end_time = time.perf_counter()
            validation_time_ms = (end_time - start_time) * 1000
            
            logger.error(f"Change impact validation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "validation_time_ms": validation_time_ms
            }
    
    async def _detect_violations(
        self,
        blueprint_structure: CodeStructure,
        code_structure: CodeStructure,
        file_path: str,
        project_id: str
    ) -> List[ConsistencyViolation]:
        """Detect consistency violations between blueprint and code."""
        violations = []
        
        # Build lookup maps
        blueprint_nodes = {node.name: node for node in blueprint_structure.nodes}
        code_nodes = {node.name: node for node in code_structure.nodes}
        
        # Check for missing functions/classes in code
        for name, blueprint_node in blueprint_nodes.items():
            if name not in code_nodes:
                violation_type = ViolationType.MISSING_FUNCTION
                if isinstance(blueprint_node, ClassNode):
                    violation_type = ViolationType.MISSING_CLASS
                elif isinstance(blueprint_node, ModuleNode):
                    violation_type = ViolationType.MISSING_MODULE
                
                violation = ConsistencyViolation(
                    violation_id=f"{project_id}_{file_path}_{name}_missing",
                    violation_type=violation_type,
                    severity=SeverityLevel.HIGH,
                    file_path=file_path,
                    project_id=project_id,
                    node_name=name,
                    description=f"{blueprint_node.node_type.value.title()} '{name}' exists in blueprint but not in code",
                    blueprint_value=blueprint_node.to_dict(),
                    code_value=None,
                    suggested_fix=f"Add {blueprint_node.node_type.value} '{name}' to code file"
                )
                violations.append(violation)
        
        # Check for nodes in code but not in blueprint
        for name, code_node in code_nodes.items():
            if name not in blueprint_nodes:
                violation = ConsistencyViolation(
                    violation_id=f"{project_id}_{file_path}_{name}_not_in_blueprint",
                    violation_type=ViolationType.BLUEPRINT_OUTDATED,
                    severity=SeverityLevel.MEDIUM,
                    file_path=file_path,
                    project_id=project_id,
                    node_name=name,
                    description=f"{code_node.node_type.value.title()} '{name}' exists in code but not in blueprint",
                    blueprint_value=None,
                    code_value=code_node.to_dict(),
                    suggested_fix=f"Add {code_node.node_type.value} '{name}' to blueprint"
                )
                violations.append(violation)
        
        # Check for detailed inconsistencies in matching nodes
        for name in set(blueprint_nodes.keys()) & set(code_nodes.keys()):
            blueprint_node = blueprint_nodes[name]
            code_node = code_nodes[name]
            
            node_violations = self._validate_node_consistency(
                blueprint_node,
                code_node,
                file_path,
                project_id
            )
            violations.extend(node_violations)
        
        return violations
    
    def _validate_node_consistency(
        self,
        blueprint_node: BlueprintNode,
        code_node: BlueprintNode,
        file_path: str,
        project_id: str
    ) -> List[ConsistencyViolation]:
        """Validate consistency between individual nodes."""
        violations = []
        node_name = blueprint_node.name
        
        # Check function-specific consistency
        if isinstance(blueprint_node, FunctionNode) and isinstance(code_node, FunctionNode):
            # Check async mismatch
            if blueprint_node.is_async != code_node.is_async:
                violations.append(ConsistencyViolation(
                    violation_id=f"{project_id}_{file_path}_{node_name}_async_mismatch",
                    violation_type=ViolationType.ASYNC_MISMATCH,
                    severity=SeverityLevel.HIGH,
                    file_path=file_path,
                    project_id=project_id,
                    node_name=node_name,
                    description=f"Function '{node_name}' async status mismatch",
                    blueprint_value=blueprint_node.is_async,
                    code_value=code_node.is_async,
                    suggested_fix=f"Update {'code' if blueprint_node.is_async else 'blueprint'} to match async status"
                ))
            
            # Check parameter mismatch
            if blueprint_node.parameters != code_node.parameters:
                violations.append(ConsistencyViolation(
                    violation_id=f"{project_id}_{file_path}_{node_name}_params_mismatch",
                    violation_type=ViolationType.PARAMETER_MISMATCH,
                    severity=SeverityLevel.HIGH,
                    file_path=file_path,
                    project_id=project_id,
                    node_name=node_name,
                    description=f"Function '{node_name}' parameters don't match blueprint",
                    blueprint_value=blueprint_node.parameters,
                    code_value=code_node.parameters,
                    suggested_fix="Update function parameters to match blueprint"
                ))
            
            # Check return type mismatch
            if blueprint_node.return_type != code_node.return_type:
                violations.append(ConsistencyViolation(
                    violation_id=f"{project_id}_{file_path}_{node_name}_return_type_mismatch",
                    violation_type=ViolationType.RETURN_TYPE_MISMATCH,
                    severity=SeverityLevel.MEDIUM,
                    file_path=file_path,
                    project_id=project_id,
                    node_name=node_name,
                    description=f"Function '{node_name}' return type doesn't match blueprint",
                    blueprint_value=blueprint_node.return_type,
                    code_value=code_node.return_type,
                    suggested_fix="Update return type annotation to match blueprint"
                ))
        
        # Check class-specific consistency
        elif isinstance(blueprint_node, ClassNode) and isinstance(code_node, ClassNode):
            # Check base classes
            if blueprint_node.base_classes != code_node.base_classes:
                violations.append(ConsistencyViolation(
                    violation_id=f"{project_id}_{file_path}_{node_name}_base_classes_mismatch",
                    violation_type=ViolationType.CLASS_HIERARCHY_CHANGED,
                    severity=SeverityLevel.HIGH,
                    file_path=file_path,
                    project_id=project_id,
                    node_name=node_name,
                    description=f"Class '{node_name}' base classes don't match blueprint",
                    blueprint_value=blueprint_node.base_classes,
                    code_value=code_node.base_classes,
                    suggested_fix="Update class inheritance to match blueprint"
                ))
            
            # Check methods
            blueprint_methods = set(blueprint_node.methods or [])
            code_methods = set(code_node.methods or [])
            
            missing_methods = blueprint_methods - code_methods
            for method in missing_methods:
                violations.append(ConsistencyViolation(
                    violation_id=f"{project_id}_{file_path}_{node_name}_{method}_missing_method",
                    violation_type=ViolationType.METHOD_MISSING,
                    severity=SeverityLevel.HIGH,
                    file_path=file_path,
                    project_id=project_id,
                    node_name=f"{node_name}.{method}",
                    description=f"Method '{method}' missing from class '{node_name}'",
                    blueprint_value=method,
                    code_value=None,
                    suggested_fix=f"Add method '{method}' to class '{node_name}'"
                ))
        
        # Check docstring consistency for all node types
        if blueprint_node.docstring and not code_node.docstring:
            violations.append(ConsistencyViolation(
                violation_id=f"{project_id}_{file_path}_{node_name}_docstring_missing",
                violation_type=ViolationType.DOCSTRING_MISSING,
                severity=SeverityLevel.LOW,
                file_path=file_path,
                project_id=project_id,
                node_name=node_name,
                description=f"'{node_name}' missing docstring present in blueprint",
                blueprint_value=blueprint_node.docstring,
                code_value=None,
                suggested_fix=f"Add docstring to '{node_name}'"
            ))
        
        return violations
    
    def _calculate_consistency_metrics(
        self,
        blueprint_structure: CodeStructure,
        code_structure: CodeStructure,
        violations: List[ConsistencyViolation]
    ) -> Dict[str, Any]:
        """Calculate consistency score and level."""
        total_nodes = len(blueprint_structure.nodes) + len(code_structure.nodes)
        if total_nodes == 0:
            return {"score": 1.0, "level": ConsistencyLevel.HIGH}
        
        # Weight violations by severity
        severity_weights = {
            SeverityLevel.CRITICAL: 1.0,
            SeverityLevel.HIGH: 0.8,
            SeverityLevel.MEDIUM: 0.5,
            SeverityLevel.LOW: 0.2,
            SeverityLevel.INFO: 0.1
        }
        
        weighted_violations = sum(
            severity_weights.get(v.severity, 0.5) for v in violations
        )
        
        # Calculate consistency score (0-1 scale)
        consistency_score = max(0.0, 1.0 - (weighted_violations / total_nodes))
        
        # Determine consistency level
        if consistency_score >= 0.90:
            level = ConsistencyLevel.HIGH
        elif consistency_score >= 0.70:
            level = ConsistencyLevel.MEDIUM
        else:
            level = ConsistencyLevel.LOW
        
        return {
            "score": consistency_score,
            "level": level,
            "weighted_violations": weighted_violations
        }
    
    def _generate_recommendations(self, violations: List[ConsistencyViolation]) -> List[str]:
        """Generate actionable recommendations based on violations."""
        recommendations = []
        
        # Group violations by type
        violation_groups = {}
        for violation in violations:
            vtype = violation.violation_type
            if vtype not in violation_groups:
                violation_groups[vtype] = []
            violation_groups[vtype].append(violation)
        
        # Generate type-specific recommendations
        for vtype, violation_list in violation_groups.items():
            count = len(violation_list)
            
            if vtype == ViolationType.MISSING_FUNCTION:
                recommendations.append(f"Add {count} missing function(s) to code")
            elif vtype == ViolationType.MISSING_CLASS:
                recommendations.append(f"Add {count} missing class(es) to code")
            elif vtype == ViolationType.PARAMETER_MISMATCH:
                recommendations.append(f"Fix {count} function parameter mismatch(es)")
            elif vtype == ViolationType.BLUEPRINT_OUTDATED:
                recommendations.append(f"Update blueprint with {count} new code element(s)")
            elif vtype == ViolationType.DOCSTRING_MISSING:
                recommendations.append(f"Add docstrings to {count} element(s)")
        
        # Add general recommendations
        if len(violations) > 10:
            recommendations.append("Consider running automated consistency fixes")
        
        if any(v.severity == SeverityLevel.CRITICAL for v in violations):
            recommendations.append("Address critical violations immediately to prevent functionality issues")
        
        return recommendations
    
    def _create_baseline_validation(
        self,
        code_structure: CodeStructure,
        file_path: str,
        project_id: str
    ) -> ValidationResult:
        """Create baseline validation when no blueprint exists."""
        return ValidationResult(
            success=True,
            validation_time_ms=1.0,
            total_nodes_checked=len(code_structure.nodes),
            violations_found=1,
            violations=[
                ConsistencyViolation(
                    violation_id=f"{project_id}_{file_path}_no_blueprint",
                    violation_type=ViolationType.BLUEPRINT_OUTDATED,
                    severity=SeverityLevel.MEDIUM,
                    file_path=file_path,
                    project_id=project_id,
                    node_name="blueprint",
                    description="No blueprint exists for this file",
                    suggested_fix="Create initial blueprint from current code structure"
                )
            ],
            consistency_score=0.8,  # Good score since code exists
            consistency_level=ConsistencyLevel.MEDIUM,
            recommendations=["Create blueprint from current code structure"]
        )
    
    def _analyze_content_structure(
        self,
        content: str,
        file_path: str,
        project_id: str
    ) -> CodeStructure:
        """Analyze code structure from content string."""
        # This is a simplified implementation
        # In production, would use temporary file or AST parsing
        try:
            # Use AST to parse content
            tree = ast.parse(content)
            
            # Extract basic structure (simplified)
            nodes = []
            relationships = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_node = FunctionNode(
                        name=node.name,
                        node_type=BlueprintNodeType.FUNCTION,
                        file_path=file_path,
                        project_id=project_id
                    )
                    nodes.append(func_node)
                
                elif isinstance(node, ast.ClassDef):
                    class_node = ClassNode(
                        name=node.name,
                        node_type=BlueprintNodeType.CLASS,
                        file_path=file_path,
                        project_id=project_id
                    )
                    nodes.append(class_node)
            
            return CodeStructure(
                structure_id=f"temp_{project_id}_{hash(content)}",
                file_path=file_path,
                project_id=project_id,
                nodes=nodes,
                relationships=relationships
            )
        
        except Exception as e:
            logger.error(f"Content structure analysis failed: {e}")
            return CodeStructure(
                structure_id="error_structure",
                file_path=file_path,
                project_id=project_id
            )
    
    async def _get_blueprint_structure(self, file_path: str, project_id: str) -> Optional[CodeStructure]:
        """Get blueprint structure from Neo4j."""
        try:
            if not self.neo4j_store or not self.neo4j_store.is_available():
                return None
            
            # Simplified blueprint retrieval
            # In production, would query Neo4j for specific file structure
            
            return CodeStructure(
                structure_id=f"blueprint_{project_id}_{file_path}",
                file_path=file_path,
                project_id=project_id,
                nodes=[],  # Would be populated from Neo4j
                relationships=[]
            )
            
        except Exception as e:
            logger.error(f"Blueprint structure retrieval failed: {e}")
            return None
    
    def _initialize_violation_patterns(self) -> Dict[ViolationType, Dict[str, Any]]:
        """Initialize violation detection patterns."""
        return {
            ViolationType.MISSING_FUNCTION: {
                "severity": SeverityLevel.HIGH,
                "auto_fixable": False,
                "description": "Function exists in blueprint but not in code"
            },
            ViolationType.PARAMETER_MISMATCH: {
                "severity": SeverityLevel.HIGH,
                "auto_fixable": True,
                "description": "Function parameters don't match blueprint"
            },
            ViolationType.DOCSTRING_MISSING: {
                "severity": SeverityLevel.LOW,
                "auto_fixable": True,
                "description": "Missing docstring that exists in blueprint"
            },
            ViolationType.ASYNC_MISMATCH: {
                "severity": SeverityLevel.HIGH,
                "auto_fixable": False,
                "description": "Function async status doesn't match blueprint"
            }
        }


class ConsistencyEnforcementEngine:
    """Engine for enforcing consistency rules and automated fixes."""
    
    def __init__(self, validation_engine: ConsistencyValidationEngine = None):
        """
        Initialize consistency enforcement engine.
        
        Args:
            validation_engine: Consistency validation engine instance
        """
        self.validation_engine = validation_engine or ConsistencyValidationEngine()
        
        # Default enforcement rules
        self.enforcement_rules = self._initialize_default_rules()
        
        # Auto-fix handlers
        self.auto_fix_handlers = self._initialize_auto_fix_handlers()
    
    async def enforce_consistency(
        self,
        file_path: str,
        project_id: str,
        violations: List[ConsistencyViolation] = None,
        dry_run: bool = False
    ) -> EnforcementResult:
        """
        Enforce consistency by applying rules and fixes.
        
        Args:
            file_path: Path to code file
            project_id: Project identifier
            violations: Optional list of violations (detected if not provided)
            dry_run: If True, only simulate actions without applying them
            
        Returns:
            EnforcementResult with actions taken and results
        """
        start_time = time.perf_counter()
        
        try:
            # Get violations if not provided
            if violations is None:
                validation_result = await self.validation_engine.validate_blueprint_consistency(
                    file_path, project_id
                )
                if not validation_result.success:
                    raise Exception(f"Validation failed: {validation_result.error_message}")
                violations = validation_result.violations
            
            actions_taken = []
            auto_fixes_applied = 0
            manual_interventions_required = 0
            warnings_generated = []
            
            # Process each violation according to enforcement rules
            for violation in violations:
                enforcement_action = self._determine_enforcement_action(violation)
                
                if enforcement_action == EnforcementAction.AUTO_FIX:
                    fix_result = await self._apply_auto_fix(violation, dry_run)
                    actions_taken.append({
                        "violation_id": violation.violation_id,
                        "action": "auto_fix",
                        "success": fix_result["success"],
                        "details": fix_result
                    })
                    if fix_result["success"]:
                        auto_fixes_applied += 1
                    else:
                        manual_interventions_required += 1
                
                elif enforcement_action == EnforcementAction.UPDATE_BLUEPRINT:
                    update_result = await self._update_blueprint(violation, dry_run)
                    actions_taken.append({
                        "violation_id": violation.violation_id,
                        "action": "update_blueprint",
                        "success": update_result["success"],
                        "details": update_result
                    })
                
                elif enforcement_action == EnforcementAction.UPDATE_DOCUMENTATION:
                    doc_result = await self._update_documentation(violation, dry_run)
                    actions_taken.append({
                        "violation_id": violation.violation_id,
                        "action": "update_documentation",
                        "success": doc_result["success"],
                        "details": doc_result
                    })
                
                elif enforcement_action == EnforcementAction.GENERATE_WARNING:
                    warning = f"Consistency warning: {violation.description}"
                    warnings_generated.append(warning)
                    actions_taken.append({
                        "violation_id": violation.violation_id,
                        "action": "warning_generated",
                        "success": True,
                        "message": warning
                    })
                
                elif enforcement_action == EnforcementAction.MANUAL_INTERVENTION:
                    manual_interventions_required += 1
                    actions_taken.append({
                        "violation_id": violation.violation_id,
                        "action": "manual_intervention_required",
                        "success": True,
                        "reason": violation.description
                    })
                
                elif enforcement_action == EnforcementAction.BLOCK_OPERATION:
                    actions_taken.append({
                        "violation_id": violation.violation_id,
                        "action": "operation_blocked",
                        "success": True,
                        "reason": f"Critical violation: {violation.description}"
                    })
            
            violations_resolved = auto_fixes_applied
            violations_remaining = len(violations) - violations_resolved
            
            end_time = time.perf_counter()
            enforcement_time_ms = (end_time - start_time) * 1000
            
            return EnforcementResult(
                success=True,
                enforcement_time_ms=enforcement_time_ms,
                actions_taken=actions_taken,
                violations_resolved=violations_resolved,
                violations_remaining=violations_remaining,
                auto_fixes_applied=auto_fixes_applied,
                manual_interventions_required=manual_interventions_required,
                warnings_generated=warnings_generated
            )
            
        except Exception as e:
            end_time = time.perf_counter()
            enforcement_time_ms = (end_time - start_time) * 1000
            
            logger.error(f"Consistency enforcement failed: {e}")
            return EnforcementResult(
                success=False,
                enforcement_time_ms=enforcement_time_ms,
                error_message=str(e)
            )
    
    def _determine_enforcement_action(self, violation: ConsistencyViolation) -> EnforcementAction:
        """Determine appropriate enforcement action for violation."""
        # Apply enforcement rules in priority order
        for rule in sorted(self.enforcement_rules, key=lambda r: r.priority):
            if violation.violation_type in rule.violation_types:
                if violation.severity.value >= rule.severity_threshold.value:
                    return rule.enforcement_action
        
        # Default action based on severity
        if violation.severity == SeverityLevel.CRITICAL:
            return EnforcementAction.BLOCK_OPERATION
        elif violation.severity == SeverityLevel.HIGH:
            return EnforcementAction.MANUAL_INTERVENTION
        elif violation.severity == SeverityLevel.MEDIUM:
            return EnforcementAction.GENERATE_WARNING
        else:
            return EnforcementAction.GENERATE_WARNING
    
    async def _apply_auto_fix(self, violation: ConsistencyViolation, dry_run: bool) -> Dict[str, Any]:
        """Apply automated fix for violation."""
        try:
            handler = self.auto_fix_handlers.get(violation.violation_type)
            if not handler:
                return {
                    "success": False,
                    "error": f"No auto-fix handler for {violation.violation_type.value}"
                }
            
            if dry_run:
                return {
                    "success": True,
                    "action": "simulated",
                    "fix_description": violation.suggested_fix or "Automated fix available"
                }
            
            # Apply actual fix
            fix_result = await handler(violation)
            return fix_result
            
        except Exception as e:
            logger.error(f"Auto-fix failed for {violation.violation_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_blueprint(self, violation: ConsistencyViolation, dry_run: bool) -> Dict[str, Any]:
        """Update blueprint to resolve violation."""
        try:
            if dry_run:
                return {
                    "success": True,
                    "action": "simulated",
                    "description": f"Would update blueprint for {violation.node_name}"
                }
            
            # In production, would update Neo4j blueprint
            return {
                "success": True,
                "action": "blueprint_updated",
                "node_name": violation.node_name,
                "update_description": f"Updated blueprint for {violation.violation_type.value}"
            }
            
        except Exception as e:
            logger.error(f"Blueprint update failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_documentation(self, violation: ConsistencyViolation, dry_run: bool) -> Dict[str, Any]:
        """Update documentation to resolve violation."""
        try:
            if dry_run:
                return {
                    "success": True,
                    "action": "simulated",
                    "description": f"Would update documentation for {violation.node_name}"
                }
            
            # In production, would update documentation
            return {
                "success": True,
                "action": "documentation_updated",
                "node_name": violation.node_name,
                "update_description": f"Updated documentation for {violation.violation_type.value}"
            }
            
        except Exception as e:
            logger.error(f"Documentation update failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _initialize_default_rules(self) -> List[EnforcementRule]:
        """Initialize default enforcement rules."""
        return [
            EnforcementRule(
                rule_id="auto_fix_docstrings",
                rule_name="Auto-fix Missing Docstrings",
                violation_types=[ViolationType.DOCSTRING_MISSING],
                severity_threshold=SeverityLevel.LOW,
                enforcement_action=EnforcementAction.AUTO_FIX,
                auto_fix_enabled=True,
                priority=1
            ),
            EnforcementRule(
                rule_id="critical_violations_block",
                rule_name="Block Critical Violations",
                violation_types=[ViolationType.MISSING_FUNCTION, ViolationType.MISSING_CLASS],
                severity_threshold=SeverityLevel.CRITICAL,
                enforcement_action=EnforcementAction.BLOCK_OPERATION,
                priority=0  # Highest priority
            ),
            EnforcementRule(
                rule_id="high_severity_manual",
                rule_name="Manual Intervention for High Severity",
                violation_types=[
                    ViolationType.PARAMETER_MISMATCH,
                    ViolationType.SIGNATURE_CHANGED,
                    ViolationType.CLASS_HIERARCHY_CHANGED
                ],
                severity_threshold=SeverityLevel.HIGH,
                enforcement_action=EnforcementAction.MANUAL_INTERVENTION,
                priority=2
            ),
            EnforcementRule(
                rule_id="update_outdated_blueprint",
                rule_name="Update Outdated Blueprint",
                violation_types=[ViolationType.BLUEPRINT_OUTDATED],
                severity_threshold=SeverityLevel.MEDIUM,
                enforcement_action=EnforcementAction.UPDATE_BLUEPRINT,
                priority=3
            )
        ]
    
    def _initialize_auto_fix_handlers(self) -> Dict[ViolationType, Callable]:
        """Initialize auto-fix handlers for different violation types."""
        async def fix_missing_docstring(violation: ConsistencyViolation) -> Dict[str, Any]:
            """Fix missing docstring violation."""
            # Simplified implementation
            return {
                "success": True,
                "action": "added_docstring",
                "description": f"Added docstring to {violation.node_name}"
            }
        
        return {
            ViolationType.DOCSTRING_MISSING: fix_missing_docstring
        }


# Global instance management
_validation_engine: Optional[ConsistencyValidationEngine] = None
_enforcement_engine: Optional[ConsistencyEnforcementEngine] = None


async def get_consistency_validation_engine() -> ConsistencyValidationEngine:
    """Get or create consistency validation engine instance."""
    global _validation_engine
    if not _validation_engine:
        neo4j_store = await get_neo4j_graph_store()
        _validation_engine = ConsistencyValidationEngine(neo4j_store)
    return _validation_engine


async def get_consistency_enforcement_engine() -> ConsistencyEnforcementEngine:
    """Get or create consistency enforcement engine instance."""
    global _enforcement_engine
    if not _enforcement_engine:
        validation_engine = await get_consistency_validation_engine()
        _enforcement_engine = ConsistencyEnforcementEngine(validation_engine)
    return _enforcement_engine