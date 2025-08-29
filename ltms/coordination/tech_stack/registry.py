from ltms.tools.memory.memory_actions import MemoryTools
"""
LTMC Stack Registry - Tech Stack Configuration Management

Production-grade tech stack rules storage and compatibility matrix validation.
Smart modularized component focused on configuration management.

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
from ltms.tools.memory.memory_actions import memory_action
from ltms.tools.patterns.pattern_actions import pattern_action

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
        memory_tools = MemoryTools()
        try:
            # Define core tech stack rules
            core_rules = self._get_core_tech_stack_rules()
            
            # Store each rule in LTMC memory
            for framework_name, rule_data in core_rules.items():
                await memory_tools("store",
                    file_name=f"tech_stack_rule_{framework_name}",
                    content=json.dumps(rule_data),
                    tags=["tech_stack", "rules", framework_name],
                    conversation_id="stack_registry"
                )
                
                logger.info(f"Stored tech stack rules for {framework_name}")
            
            # Initialize compatibility matrix
            compatibility_rules = self._get_compatibility_matrix()
            
            for rule_key, compatibility_data in compatibility_rules.items():
                await memory_tools("store",
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
        memory_tools = MemoryTools()
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
            store_result = await memory_tools("store",
                file_name=f"tech_stack_rule_{framework}",
                content=json.dumps(rules),
                tags=["tech_stack", "rules", framework, "user_defined"],
                conversation_id="stack_registry"
            )
            
            if store_result.get('success'):
                # Cache locally for performance
                self.rules_cache[framework] = rules
                
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
        memory_tools = MemoryTools()
        Retrieve tech stack rules from LTMC database.
        Real database queries, no mocked data.
        """
        start_time = time.time()
        
        try:
            # Check cache first
            if framework in self.rules_cache:
                return self.rules_cache[framework]
            
            # Retrieve from LTMC memory
            retrieve_result = await memory_tools("retrieve",
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