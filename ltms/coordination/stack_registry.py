"""
LTMC Stack Registry - Tech Stack Configuration and Compatibility Management

Production-grade tech stack rules storage and compatibility matrix validation.
Real LTMC database operations for persistent configuration management.

Performance SLA: <500ms operations
No mocks, stubs, or placeholders - production ready only.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Import LTMC tools
from ltms.tools.consolidated import memory_action, pattern_action

# Configure logging
logger = logging.getLogger(__name__)


class FrameworkType(Enum):
    """Supported framework types"""
    PYTHON_MCP_SDK = "python_mcp_sdk"
    FASTAPI_WEB = "fastapi_web"
    FLASK_WEB = "flask_web"
    DJANGO_WEB = "django_web"
    ASYNCIO_NATIVE = "asyncio_native"


class CompatibilityLevel(Enum):
    """Framework compatibility levels"""
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    REQUIRES_COORDINATION = "requires_coordination"
    CRITICAL_CONFLICT = "critical_conflict"


@dataclass
class TechStackRule:
    """Individual tech stack rule definition"""
    framework: FrameworkType
    required_imports: List[str]
    forbidden_imports: List[str]
    required_patterns: List[str]
    forbidden_patterns: List[str]
    event_loop_exclusive: bool
    async_required: bool
    validation_rules: Dict[str, Any]


@dataclass
class CompatibilityRule:
    """Framework compatibility rule definition"""
    framework_a: FrameworkType
    framework_b: FrameworkType
    compatibility: CompatibilityLevel
    conflict_type: Optional[str] = None
    severity: Optional[str] = None
    resolution: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class StackRegistry:
    """
    Centralized tech stack configuration registry with LTMC integration.
    
    Manages:
    - Tech stack rules storage and retrieval
    - Framework compatibility matrices
    - Pattern validation rules
    - Real LTMC database persistence
    """
    
    def __init__(self):
        """Initialize stack registry with LTMC integration"""
        self.rules_cache = {}
        self.compatibility_cache = {}
        self.pattern_cache = {}
        
        # Registry initialization flag for lazy loading
        self._registry_initialized = False
    
    @classmethod
    async def create_async(cls):
        """Async factory method to create StackRegistry with proper initialization"""
        instance = cls()
        await instance._initialize_stack_registry()
        instance._registry_initialized = True
        return instance
    
    async def _initialize_stack_registry(self) -> None:
        """Initialize stack registry with predefined rules in LTMC"""
        try:
            # Define core tech stack rules
            core_rules = self._get_core_tech_stack_rules()
            
            # Store each rule in LTMC memory
            for framework_name, rule_data in core_rules.items():
                await memory_action(
                    action="store",
                    file_name=f"tech_stack_rule_{framework_name}",
                    content=json.dumps(rule_data),
                    tags=["tech_stack", "rules", framework_name],
                    conversation_id="stack_registry"
                )
                
                logger.info(f"Stored tech stack rules for {framework_name}")
            
            # Initialize compatibility matrix
            compatibility_rules = self._get_compatibility_matrix()
            
            for rule_key, compatibility_data in compatibility_rules.items():
                await memory_action(
                    action="store",
                    file_name=f"compatibility_rule_{rule_key}",
                    content=json.dumps(compatibility_data),
                    tags=["tech_stack", "compatibility", "rules"],
                    conversation_id="compatibility_matrix"
                )
            
            logger.info("Stack registry initialized with core rules and compatibility matrix")
            
        except Exception as e:
            logger.error(f"Failed to initialize stack registry: {e}")
            raise
    
    def _get_core_tech_stack_rules(self) -> Dict[str, Dict[str, Any]]:
        """Define core tech stack rules for supported frameworks"""
        return {
            "python_mcp_sdk": {
                "required_imports": ["mcp", "mcp.server.stdio"],
                "forbidden_imports": ["fastapi", "flask", "django"],
                "required_patterns": ["@Tool()", "stdio_server()"],
                "forbidden_patterns": ["@app.get", "@app.post", "FastAPI()"],
                "event_loop_exclusive": True,
                "async_required": True,
                "validation_rules": {
                    "require_tool_decorators": True,
                    "require_stdio_transport": True,
                    "forbid_web_frameworks": True
                }
            },
            "fastapi_web": {
                "required_imports": ["fastapi"],
                "forbidden_imports": ["mcp.server.stdio"],
                "required_patterns": ["@app.get", "@app.post", "FastAPI()"],
                "forbidden_patterns": ["@Tool()", "stdio_server()"],
                "event_loop_exclusive": True,
                "async_required": True,
                "validation_rules": {
                    "require_fastapi_app": True,
                    "require_route_decorators": True,
                    "forbid_mcp_stdio": True
                }
            },
            "asyncio_native": {
                "required_imports": ["asyncio"],
                "forbidden_imports": [],
                "required_patterns": ["async def", "await"],
                "forbidden_patterns": [],
                "event_loop_exclusive": False,
                "async_required": True,
                "validation_rules": {
                    "allow_async_coordination": True,
                    "compatible_with_mcp": True
                }
            }
        }
    
    def _get_compatibility_matrix(self) -> Dict[str, Dict[str, Any]]:
        """Define framework compatibility matrix"""
        return {
            "python_mcp_sdk_vs_fastapi_web": {
                "framework_a": "python_mcp_sdk",
                "framework_b": "fastapi_web", 
                "compatibility": "critical_conflict",
                "conflict_type": "event_loop_conflict",
                "severity": "critical",
                "resolution": "separate_processes_or_use_http_transport",
                "details": {
                    "reason": "Both frameworks require exclusive event loop control",
                    "impact": "Runtime event loop conflicts and application crashes",
                    "alternatives": [
                        "Use MCP over HTTP transport instead of stdio",
                        "Separate FastAPI and MCP into different processes",
                        "Use async coordination patterns"
                    ]
                }
            },
            "python_mcp_sdk_vs_asyncio_native": {
                "framework_a": "python_mcp_sdk",
                "framework_b": "asyncio_native",
                "compatibility": "compatible",
                "conflict_type": None,
                "severity": "info",
                "resolution": "coordinate_async_patterns",
                "details": {
                    "reason": "MCP SDK is built on asyncio foundation",
                    "best_practices": [
                        "Use proper async/await patterns",
                        "Coordinate event loop management",
                        "Follow MCP async conventions"
                    ]
                }
            }
        }
    
    async def store_tech_stack_rules(self, framework: str, rules: Dict[str, Any]) -> bool:
        """
        Store tech stack rules in LTMC database with real persistence.
        No mocks - actual database operations.
        """
        start_time = time.time()
        
        try:
            # Validate rule structure
            if not self._validate_rule_structure(rules):
                logger.error(f"Invalid rule structure for {framework}")
                return False
            
            # Store in LTMC memory
            store_result = await memory_action(
                action="store",
                file_name=f"tech_stack_rule_{framework}",
                content=json.dumps(rules),
                tags=["tech_stack", "rules", framework, "user_defined"],
                conversation_id="stack_registry"
            )
            
            if store_result.get('success'):
                # Cache locally for performance
                self.rules_cache[framework] = rules
                
                # Store pattern rules
                if 'required_patterns' in rules:
                    for pattern in rules['required_patterns']:
                        pattern_action(
                            action="log_attempt",
                            code=pattern,
                            result="required_pattern",
                            tags=["tech_stack", framework, "required"],
                            rationale=f"Required pattern for {framework} framework"
                        )
                
                # Performance tracking
                elapsed = time.time() - start_time
                if elapsed > 0.5:  # 500ms SLA
                    logger.warning(f"Rule storage exceeded SLA: {elapsed:.3f}s > 500ms")
                
                logger.info(f"Successfully stored tech stack rules for {framework}")
                return True
            else:
                logger.error(f"Failed to store rules for {framework}: {store_result}")
                return False
                
        except Exception as e:
            logger.error(f"Error storing tech stack rules for {framework}: {e}")
            return False
    
    async def retrieve_tech_stack_rules(self, framework: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve tech stack rules from LTMC database.
        Real database queries, no mocked data.
        """
        start_time = time.time()
        
        try:
            # Check cache first
            if framework in self.rules_cache:
                return self.rules_cache[framework]
            
            # Retrieve from LTMC memory
            retrieve_result = await memory_action(
                action="retrieve",
                query=f"tech_stack_rule_{framework}",
                conversation_id="stack_registry"
            )
            
            if retrieve_result.get('success'):
                documents = retrieve_result.get('documents', [])
                
                # Find the framework rule document
                for doc in documents:
                    if f"tech_stack_rule_{framework}" in doc.get('file_name', ''):
                        try:
                            rule_data = json.loads(doc['content'])
                            
                            # Cache for performance
                            self.rules_cache[framework] = rule_data
                            
                            # Performance tracking
                            elapsed = time.time() - start_time
                            if elapsed > 0.5:  # 500ms SLA
                                logger.warning(f"Rule retrieval exceeded SLA: {elapsed:.3f}s > 500ms")
                            
                            return rule_data
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse rules for {framework}: {e}")
                            continue
                
                logger.warning(f"No rules found for framework: {framework}")
                return None
            else:
                logger.error(f"Failed to retrieve rules for {framework}: {retrieve_result}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving tech stack rules for {framework}: {e}")
            return None
    
    async def get_compatibility_matrix(self) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """
        Retrieve complete compatibility matrix from LTMC database.
        Real data retrieval with actual database queries.
        """
        start_time = time.time()
        
        try:
            # Check cache first
            if self.compatibility_cache:
                return self.compatibility_cache
            
            # Retrieve from LTMC memory
            retrieve_result = await memory_action(
                action="retrieve",
                query="compatibility_rule",
                conversation_id="compatibility_matrix"
            )
            
            if retrieve_result.get('success'):
                documents = retrieve_result.get('documents', [])
                compatibility_matrix = {}
                
                for doc in documents:
                    if 'compatibility_rule_' in doc.get('file_name', ''):
                        try:
                            compatibility_data = json.loads(doc['content'])
                            
                            # Extract framework pair key
                            framework_a = compatibility_data.get('framework_a')
                            framework_b = compatibility_data.get('framework_b')
                            
                            if framework_a and framework_b:
                                key = (framework_a, framework_b)
                                compatibility_matrix[key] = compatibility_data
                                
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse compatibility rule: {e}")
                            continue
                
                # Cache for performance
                self.compatibility_cache = compatibility_matrix
                
                # Performance tracking
                elapsed = time.time() - start_time
                if elapsed > 0.5:  # 500ms SLA
                    logger.warning(f"Compatibility matrix retrieval exceeded SLA: {elapsed:.3f}s > 500ms")
                
                logger.info(f"Retrieved {len(compatibility_matrix)} compatibility rules")
                return compatibility_matrix
            else:
                logger.error(f"Failed to retrieve compatibility matrix: {retrieve_result}")
                return {}
                
        except Exception as e:
            logger.error(f"Error retrieving compatibility matrix: {e}")
            return {}
    
    async def check_framework_compatibility(self, framework_a: str, framework_b: str) -> Optional[Dict[str, Any]]:
        """Check compatibility between two frameworks"""
        compatibility_matrix = await self.get_compatibility_matrix()
        
        # Check both directions
        key1 = (framework_a, framework_b)
        key2 = (framework_b, framework_a)
        
        if key1 in compatibility_matrix:
            return compatibility_matrix[key1]
        elif key2 in compatibility_matrix:
            return compatibility_matrix[key2]
        else:
            # Default compatibility assumption
            return {
                "framework_a": framework_a,
                "framework_b": framework_b,
                "compatibility": "requires_coordination",
                "severity": "warning",
                "resolution": "manual_validation_required"
            }
    
    def _validate_rule_structure(self, rules: Dict[str, Any]) -> bool:
        """Validate tech stack rule structure"""
        required_fields = [
            'required_imports', 'forbidden_imports', 
            'required_patterns', 'forbidden_patterns',
            'event_loop_exclusive', 'async_required'
        ]
        
        for field in required_fields:
            if field not in rules:
                logger.error(f"Missing required field: {field}")
                return False
        
        return True


class ValidationRules:
    """
    Framework-specific validation rules with real implementation.
    Integrates with StackRegistry for rule-based validation.
    """
    
    def __init__(self, stack_registry: StackRegistry):
        self.stack_registry = stack_registry
        self.validation_cache = {}
    
    async def validate_framework_compliance(self, framework: str, code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate framework compliance against stored rules.
        Real validation logic with actual rule checking.
        """
        start_time = time.time()
        
        try:
            # Get framework rules
            rules = await self.stack_registry.retrieve_tech_stack_rules(framework)
            if not rules:
                return {
                    'compliant': False,
                    'error': f'No rules found for framework: {framework}'
                }
            
            compliance_results = {
                'compliant': True,
                'violations': [],
                'warnings': [],
                'framework': framework,
                'validation_time': None
            }
            
            # Check required imports
            detected_imports = code_analysis.get('imports', [])
            for required_import in rules.get('required_imports', []):
                if not any(required_import in imp for imp in detected_imports):
                    compliance_results['violations'].append({
                        'type': 'missing_required_import',
                        'required': required_import,
                        'message': f'Missing required import: {required_import}'
                    })
                    compliance_results['compliant'] = False
            
            # Check forbidden imports
            for forbidden_import in rules.get('forbidden_imports', []):
                if any(forbidden_import in imp for imp in detected_imports):
                    compliance_results['violations'].append({
                        'type': 'forbidden_import_present',
                        'forbidden': forbidden_import,
                        'message': f'Forbidden import detected: {forbidden_import}'
                    })
                    compliance_results['compliant'] = False
            
            # Check required patterns
            detected_patterns = code_analysis.get('patterns', [])
            for required_pattern in rules.get('required_patterns', []):
                if not any(required_pattern in pattern for pattern in detected_patterns):
                    compliance_results['warnings'].append({
                        'type': 'missing_required_pattern',
                        'required': required_pattern,
                        'message': f'Missing required pattern: {required_pattern}'
                    })
            
            # Check forbidden patterns
            for forbidden_pattern in rules.get('forbidden_patterns', []):
                if any(forbidden_pattern in pattern for pattern in detected_patterns):
                    compliance_results['violations'].append({
                        'type': 'forbidden_pattern_present',
                        'forbidden': forbidden_pattern,
                        'message': f'Forbidden pattern detected: {forbidden_pattern}'
                    })
                    compliance_results['compliant'] = False
            
            # Performance tracking
            elapsed = time.time() - start_time
            compliance_results['validation_time'] = elapsed
            
            if elapsed > 0.5:  # 500ms SLA
                compliance_results['warnings'].append({
                    'type': 'performance_sla_violation',
                    'message': f'Validation exceeded SLA: {elapsed:.3f}s > 500ms'
                })
            
            return compliance_results
            
        except Exception as e:
            logger.error(f"Framework compliance validation failed: {e}")
            return {
                'compliant': False,
                'error': f'Validation failed: {str(e)}'
            }


class CompatibilityMatrix:
    """
    Framework compatibility matrix with real conflict detection.
    Manages compatibility rules and provides resolution recommendations.
    """
    
    def __init__(self, stack_registry: StackRegistry):
        self.stack_registry = stack_registry
        self.conflict_cache = {}
    
    async def analyze_multi_framework_project(self, detected_frameworks: List[str]) -> Dict[str, Any]:
        """
        Analyze compatibility across multiple frameworks in a project.
        Real conflict detection with actual compatibility matrix queries.
        """
        start_time = time.time()
        
        try:
            analysis_result = {
                'compatible': True,
                'frameworks': detected_frameworks,
                'conflicts': [],
                'warnings': [],
                'recommendations': [],
                'analysis_time': None
            }
            
            # Check all framework pairs for conflicts
            for i, framework_a in enumerate(detected_frameworks):
                for framework_b in detected_frameworks[i+1:]:
                    compatibility = await self.stack_registry.check_framework_compatibility(
                        framework_a, framework_b
                    )
                    
                    if compatibility:
                        compatibility_level = compatibility.get('compatibility')
                        
                        if compatibility_level == 'critical_conflict':
                            analysis_result['compatible'] = False
                            analysis_result['conflicts'].append({
                                'type': 'critical_conflict',
                                'frameworks': [framework_a, framework_b],
                                'conflict_type': compatibility.get('conflict_type'),
                                'severity': compatibility.get('severity'),
                                'resolution': compatibility.get('resolution'),
                                'details': compatibility.get('details')
                            })
                        elif compatibility_level == 'incompatible':
                            analysis_result['compatible'] = False
                            analysis_result['conflicts'].append({
                                'type': 'incompatible',
                                'frameworks': [framework_a, framework_b],
                                'resolution': compatibility.get('resolution')
                            })
                        elif compatibility_level == 'requires_coordination':
                            analysis_result['warnings'].append({
                                'type': 'requires_coordination',
                                'frameworks': [framework_a, framework_b],
                                'message': f'{framework_a} and {framework_b} require coordination',
                                'resolution': compatibility.get('resolution')
                            })
            
            # Generate recommendations
            if analysis_result['conflicts']:
                analysis_result['recommendations'].extend([
                    'Review framework conflicts and consider architectural changes',
                    'Separate conflicting frameworks into different processes',
                    'Use coordination patterns for framework integration'
                ])
            
            # Performance tracking
            elapsed = time.time() - start_time
            analysis_result['analysis_time'] = elapsed
            
            if elapsed > 0.5:  # 500ms SLA
                analysis_result['warnings'].append({
                    'type': 'performance_sla_violation',
                    'message': f'Analysis exceeded SLA: {elapsed:.3f}s > 500ms'
                })
            
            # Store analysis in LTMC for future reference
            await memory_action(
                action="store",
                file_name=f"multi_framework_analysis_{int(time.time())}",
                content=json.dumps(analysis_result),
                tags=["tech_stack", "compatibility", "multi_framework"],
                conversation_id="compatibility_analysis"
            )
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Multi-framework analysis failed: {e}")
            return {
                'compatible': False,
                'error': f'Analysis failed: {str(e)}'
            }
    
    async def load_configuration_from_file(self, config_path: Path) -> Dict[str, Any]:
        """
        Load configuration from ltmc_config.json with real file I/O.
        No mocked configuration - actual file operations.
        """
        start_time = time.time()
        
        try:
            if not config_path.exists():
                logger.error(f"Configuration file not found: {config_path}")
                return {'success': False, 'error': 'Configuration file not found'}
            
            # Real file I/O operation
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Validate configuration structure
            if not isinstance(config_data, dict):
                return {'success': False, 'error': 'Invalid configuration format'}
            
            # Store configuration in LTMC for persistence
            store_result = await memory_action(
                action="store",
                file_name="ltmc_configuration",
                content=json.dumps(config_data),
                tags=["config", "ltmc", "loaded"],
                conversation_id="configuration"
            )
            
            # Performance tracking
            elapsed = time.time() - start_time
            
            result = {
                'success': True,
                'config': config_data,
                'load_time': elapsed,
                'ltmc_stored': store_result.get('success', False)
            }
            
            if elapsed > 0.5:  # 500ms SLA
                logger.warning(f"Configuration loading exceeded SLA: {elapsed:.3f}s > 500ms")
                result['performance_warning'] = f'Loading exceeded SLA: {elapsed:.3f}s > 500ms'
            
            logger.info(f"Successfully loaded configuration from {config_path}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return {'success': False, 'error': f'Invalid JSON: {str(e)}'}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {'success': False, 'error': f'Load failed: {str(e)}'}