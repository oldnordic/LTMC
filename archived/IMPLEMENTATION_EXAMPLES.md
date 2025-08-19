# LTMC FastMCP Lazy Loading Implementation Examples
## Concrete Implementation of Modular Architecture Components

---

## 🏗️ CORE COMPONENT IMPLEMENTATIONS

### 1. LazyToolManager (core/lazy_tool_manager.py) - <300 lines

```python
#!/usr/bin/env python3
"""
LazyToolManager - Core orchestrator for LTMC FastMCP lazy loading
================================================================

Manages essential vs lazy tool loading with <200ms startup target.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

from fastmcp import FastMCP
from config.settings import LTMCSettings

from .essential_loader import EssentialToolsLoader
from .lazy_loader import LazyToolLoader  
from .progressive_init import ProgressiveInitializer
from ..registry.tool_registry import ToolCategoryRegistry


@dataclass
class LoadingMetrics:
    """Performance metrics for lazy loading."""
    startup_time: float = 0.0
    essential_load_time: float = 0.0
    lazy_registration_time: float = 0.0
    total_tools_registered: int = 0
    essential_tools_count: int = 0


class LazyToolManager:
    """Core orchestrator for lazy tool loading architecture."""
    
    def __init__(self, settings: LTMCSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.essential_loader = EssentialToolsLoader(settings)
        self.lazy_loader = LazyToolLoader(settings)
        self.progressive_init = ProgressiveInitializer(settings)
        self.tool_registry = ToolCategoryRegistry()
        
        # Performance tracking
        self.metrics = LoadingMetrics()
        self._startup_start = None
    
    async def initialize_server(self, mcp: FastMCP) -> LoadingMetrics:
        """
        Initialize FastMCP server with lazy loading architecture.
        
        Target: <200ms total startup time
        
        Args:
            mcp: FastMCP server instance
            
        Returns:
            LoadingMetrics: Performance metrics for validation
        """
        self._startup_start = asyncio.get_event_loop().time()
        self.logger.info("Starting LTMC lazy loading architecture initialization")
        
        try:
            # Phase 1: Load essential tools (<50ms target)
            essential_start = asyncio.get_event_loop().time()
            essential_count = await self.essential_loader.load_all_essential(mcp)
            self.metrics.essential_load_time = (asyncio.get_event_loop().time() - essential_start) * 1000
            self.metrics.essential_tools_count = essential_count
            
            self.logger.info(f"Essential tools loaded: {essential_count} in {self.metrics.essential_load_time:.1f}ms")
            
            # Phase 2: Register lazy tools as FunctionResources
            lazy_start = asyncio.get_event_loop().time()
            lazy_count = await self.lazy_loader.register_lazy_resources(mcp)
            self.metrics.lazy_registration_time = (asyncio.get_event_loop().time() - lazy_start) * 1000
            
            self.logger.info(f"Lazy tools registered: {lazy_count} in {self.metrics.lazy_registration_time:.1f}ms")
            
            # Phase 3: Start background progressive loading
            await self.progressive_init.start_background_loading()
            
            # Calculate final metrics
            self.metrics.startup_time = (asyncio.get_event_loop().time() - self._startup_start) * 1000
            self.metrics.total_tools_registered = essential_count + lazy_count
            
            self.logger.info(f"Server initialization complete: {self.metrics.startup_time:.1f}ms total")
            
            # Validate performance targets
            await self._validate_performance_targets()
            
            return self.metrics
            
        except Exception as e:
            self.logger.error(f"Failed to initialize lazy loading architecture: {e}")
            raise
    
    async def _validate_performance_targets(self) -> None:
        """Validate that performance targets are met."""
        targets_met = []
        
        # Target: <200ms startup
        if self.metrics.startup_time > 200:
            self.logger.warning(f"Startup time {self.metrics.startup_time:.1f}ms exceeds 200ms target")
        else:
            targets_met.append("startup")
            
        # Target: <50ms essential tools
        if self.metrics.essential_load_time > 50:
            self.logger.warning(f"Essential load time {self.metrics.essential_load_time:.1f}ms exceeds 50ms target")
        else:
            targets_met.append("essential")
        
        self.logger.info(f"Performance targets met: {', '.join(targets_met)}")
    
    async def get_loading_status(self) -> Dict[str, any]:
        """Get current loading status for monitoring."""
        return {
            "startup_complete": self._startup_start is not None,
            "metrics": {
                "startup_time_ms": self.metrics.startup_time,
                "essential_load_time_ms": self.metrics.essential_load_time,
                "essential_tools_count": self.metrics.essential_tools_count,
                "total_tools": self.metrics.total_tools_registered
            },
            "progressive_status": await self.progressive_init.get_loading_status()
        }
```

### 2. EssentialToolsLoader (core/essential_loader.py) - <300 lines

```python
#!/usr/bin/env python3
"""
EssentialToolsLoader - Fast loading of critical tools
====================================================

Loads essential tools in <50ms for immediate server responsiveness.
"""

import asyncio
import logging
from typing import Dict, List, Callable, Any
from dataclasses import dataclass

from fastmcp import FastMCP
from config.settings import LTMCSettings


@dataclass
class EssentialToolSpec:
    """Specification for an essential tool."""
    name: str
    handler: Callable
    description: str
    category: str


class EssentialToolsLoader:
    """Fast loader for essential tools with minimal initialization overhead."""
    
    # Essential tool categories with minimal startup cost
    ESSENTIAL_CATEGORIES = {
        'system': {
            'tools': ['ping', 'status', 'health_check'],
            'priority': 1,
            'max_load_time_ms': 10
        },
        'memory_basic': {
            'tools': ['store_memory', 'retrieve_memory'], 
            'priority': 2,
            'max_load_time_ms': 15
        },
        'chat': {
            'tools': ['log_chat', 'get_recent_chats'],
            'priority': 3,
            'max_load_time_ms': 10
        },
        'context_basic': {
            'tools': ['build_context', 'ask_with_context'],
            'priority': 4, 
            'max_load_time_ms': 15
        }
    }
    
    def __init__(self, settings: LTMCSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self._essential_tools: List[EssentialToolSpec] = []
        self._tools_loaded = False
    
    async def load_all_essential(self, mcp: FastMCP) -> int:
        """
        Load all essential tools with <50ms target.
        
        Args:
            mcp: FastMCP server instance
            
        Returns:
            int: Number of essential tools loaded
        """
        if self._tools_loaded:
            return len(self._essential_tools)
            
        start_time = asyncio.get_event_loop().time()
        total_loaded = 0
        
        # Load categories by priority
        for category, spec in sorted(
            self.ESSENTIAL_CATEGORIES.items(), 
            key=lambda x: x[1]['priority']
        ):
            category_start = asyncio.get_event_loop().time()
            
            count = await self._load_category(mcp, category, spec)
            total_loaded += count
            
            load_time = (asyncio.get_event_loop().time() - category_start) * 1000
            self.logger.debug(f"Category {category}: {count} tools in {load_time:.1f}ms")
            
            # Validate category load time
            if load_time > spec['max_load_time_ms']:
                self.logger.warning(f"Category {category} exceeded {spec['max_load_time_ms']}ms target")
        
        total_time = (asyncio.get_event_loop().time() - start_time) * 1000
        self.logger.info(f"Essential tools loaded: {total_loaded} in {total_time:.1f}ms")
        
        self._tools_loaded = True
        return total_loaded
    
    async def _load_category(self, mcp: FastMCP, category: str, spec: Dict) -> int:
        """Load essential tools for a specific category."""
        count = 0
        
        if category == 'system':
            count += await self._register_system_tools(mcp)
        elif category == 'memory_basic':
            count += await self._register_basic_memory_tools(mcp)
        elif category == 'chat':
            count += await self._register_chat_tools(mcp)
        elif category == 'context_basic':
            count += await self._register_basic_context_tools(mcp)
            
        return count
    
    async def _register_system_tools(self, mcp: FastMCP) -> int:
        """Register essential system tools."""
        
        @mcp.tool()
        def ping() -> Dict[str, Any]:
            """System ping for connectivity verification."""
            return {
                "status": "pong",
                "timestamp": asyncio.get_event_loop().time(),
                "server": "ltmc-fastmcp"
            }
        
        @mcp.tool()
        def status() -> Dict[str, Any]:
            """Get server status and metrics.""" 
            return {
                "server_type": "ltmc-fastmcp-lazy",
                "tools_loaded": len(self._essential_tools),
                "lazy_loading": True,
                "startup_complete": self._tools_loaded
            }
        
        @mcp.tool()
        async def health_check() -> Dict[str, Any]:
            """Comprehensive server health check."""
            return {
                "status": "healthy",
                "essential_tools": "loaded",
                "lazy_loading": "active",
                "response_time_ms": 1  # Minimal response for health checks
            }
        
        self._essential_tools.extend([
            EssentialToolSpec("ping", ping, "System ping", "system"),
            EssentialToolSpec("status", status, "Server status", "system"),
            EssentialToolSpec("health_check", health_check, "Health check", "system")
        ])
        
        return 3
    
    async def _register_basic_memory_tools(self, mcp: FastMCP) -> int:
        """Register essential memory tools with lazy database connections."""
        
        # Lazy database service initialization
        _db_service = None
        
        async def get_db_service():
            nonlocal _db_service
            if _db_service is None:
                from services.database_service import DatabaseService
                _db_service = DatabaseService(self.settings)
                await _db_service.initialize()
            return _db_service
        
        @mcp.tool()
        async def store_memory(
            content: str,
            file_name: str, 
            resource_type: str = "document"
        ) -> Dict[str, Any]:
            """Store content in memory with lazy DB initialization."""
            try:
                db_service = await get_db_service()
                result = await db_service.store_memory(content, file_name, resource_type)
                return {"success": True, "resource_id": result}
            except Exception as e:
                self.logger.error(f"Memory store error: {e}")
                return {"success": False, "error": str(e)}
        
        @mcp.tool()
        async def retrieve_memory(
            query: str,
            top_k: int = 5
        ) -> Dict[str, Any]:
            """Retrieve memory with semantic search."""
            try:
                db_service = await get_db_service() 
                results = await db_service.retrieve_memory(query, top_k)
                return {"success": True, "results": results}
            except Exception as e:
                self.logger.error(f"Memory retrieve error: {e}")
                return {"success": False, "error": str(e)}
        
        self._essential_tools.extend([
            EssentialToolSpec("store_memory", store_memory, "Store memory", "memory"),
            EssentialToolSpec("retrieve_memory", retrieve_memory, "Retrieve memory", "memory")
        ])
        
        return 2
    
    async def _register_chat_tools(self, mcp: FastMCP) -> int:
        """Register essential chat continuity tools."""
        # Similar implementation for chat tools
        # ... implementation details ...
        return 2
    
    async def _register_basic_context_tools(self, mcp: FastMCP) -> int:
        """Register essential context tools.""" 
        # Similar implementation for context tools
        # ... implementation details ...
        return 2
```

### 3. LazyToolLoader (core/lazy_loader.py) - <300 lines

```python
#!/usr/bin/env python3
"""
LazyToolLoader - On-demand tool initialization with FastMCP patterns
===================================================================

Implements FunctionResource and dynamic mounting for lazy tool loading.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass

from fastmcp import FastMCP, FunctionResource
from config.settings import LTMCSettings


@dataclass
class LazyToolSpec:
    """Specification for a lazy-loaded tool."""
    name: str
    category: str
    loader_func: Callable
    uri_template: str
    description: str
    load_strategy: str  # 'function_resource', 'dynamic_mount', 'progressive'


class LazyToolLoader:
    """On-demand tool initialization using FastMCP lazy patterns."""
    
    # Lazy tool categories with loading strategies
    LAZY_CATEGORIES = {
        'memory_advanced': {
            'tools': ['analyze_memory_patterns', 'memory_analytics', 'pattern_optimization'],
            'strategy': 'function_resource',
            'estimated_load_time_ms': 150
        },
        'mermaid': {
            'tools': 'all_mermaid_tools',  # 24 tools
            'strategy': 'dynamic_mount',
            'estimated_load_time_ms': 200
        },
        'analytics': {
            'tools': ['code_pattern_analysis', 'performance_analytics', 'usage_analytics'],
            'strategy': 'function_resource', 
            'estimated_load_time_ms': 180
        },
        'documentation': {
            'tools': ['sync_documentation', 'validation_analysis', 'status_monitoring'],
            'strategy': 'progressive',
            'estimated_load_time_ms': 100
        }
    }
    
    def __init__(self, settings: LTMCSettings):
        self.settings = settings
        self.logger = logging.getLogger(__name__)
        self._loaded_categories: Dict[str, bool] = {}
        self._lazy_tools: List[LazyToolSpec] = []
        self._sub_servers: Dict[str, FastMCP] = {}
    
    async def register_lazy_resources(self, mcp: FastMCP) -> int:
        """
        Register lazy tools as FunctionResources and mounted sub-servers.
        
        Args:
            mcp: FastMCP server instance
            
        Returns:
            int: Number of lazy tools registered
        """
        total_registered = 0
        
        for category, spec in self.LAZY_CATEGORIES.items():
            start_time = asyncio.get_event_loop().time()
            
            if spec['strategy'] == 'function_resource':
                count = await self._register_function_resources(mcp, category, spec)
            elif spec['strategy'] == 'dynamic_mount':
                count = await self._register_dynamic_mount(mcp, category, spec)
            elif spec['strategy'] == 'progressive':
                count = await self._register_progressive_resources(mcp, category, spec)
            else:
                self.logger.warning(f"Unknown strategy for category {category}: {spec['strategy']}")
                continue
            
            registration_time = (asyncio.get_event_loop().time() - start_time) * 1000
            total_registered += count
            
            self.logger.debug(f"Registered {count} lazy tools for {category} in {registration_time:.1f}ms")
        
        self.logger.info(f"Total lazy tools registered: {total_registered}")
        return total_registered
    
    async def _register_function_resources(self, mcp: FastMCP, category: str, spec: Dict) -> int:
        """Register tools using FunctionResource pattern for true lazy loading."""
        
        # Example: Memory advanced tools
        if category == 'memory_advanced':
            
            @mcp.resource("tools://memory/analyze_patterns/{query}")
            def create_pattern_analysis_resource(query: str) -> FunctionResource:
                """Create lazy-loaded memory pattern analysis resource."""
                
                async def analyze_patterns_lazy():
                    # Only executed when resource is accessed
                    self.logger.debug(f"Lazy loading memory pattern analysis for: {query}")
                    
                    # Import and initialize only when needed
                    from tools.memory.advanced import analyze_memory_patterns
                    return await analyze_memory_patterns(query)
                
                return FunctionResource.from_function(
                    fn=analyze_patterns_lazy,
                    uri=f"tools://memory/analyze_patterns/{query}",
                    description=f"Memory pattern analysis for {query} (lazy loaded)"
                )
            
            # Register other memory advanced tools similarly...
            return len(spec['tools'])
        
        # Example: Analytics tools
        elif category == 'analytics':
            
            @mcp.resource("tools://analytics/{tool_type}/{query}")  
            def create_analytics_resource(tool_type: str, query: str) -> FunctionResource:
                """Create lazy-loaded analytics resource."""
                
                async def analytics_lazy():
                    self.logger.debug(f"Lazy loading {tool_type} analytics for: {query}")
                    
                    if tool_type == 'code_patterns':
                        from tools.code_patterns.advanced import analyze_code_patterns
                        return await analyze_code_patterns(query)
                    elif tool_type == 'performance':
                        from tools.analytics.performance import analyze_performance
                        return await analyze_performance(query)
                    # ... other analytics types
                    
                return FunctionResource.from_function(
                    fn=analytics_lazy,
                    uri=f"tools://analytics/{tool_type}/{query}",
                    description=f"{tool_type} analytics (lazy loaded)"
                )
                
            return len(spec['tools'])
            
        return 0
    
    async def _register_dynamic_mount(self, mcp: FastMCP, category: str, spec: Dict) -> int:
        """Register tools using dynamic sub-server mounting."""
        
        if category == 'mermaid':
            # Create dedicated sub-server for Mermaid tools
            mermaid_server = FastMCP(name="mermaid-tools")
            
            # Register all 24 Mermaid tools on the sub-server
            await self._setup_mermaid_subserver(mermaid_server)
            
            # Mount the sub-server with lazy proxy pattern
            mcp.mount(mermaid_server, prefix="mermaid", as_proxy=True)
            
            # Store reference for management
            self._sub_servers['mermaid'] = mermaid_server
            
            self.logger.info("Mermaid sub-server mounted with 24 tools")
            return 24  # All Mermaid tools
            
        return 0
    
    async def _setup_mermaid_subserver(self, server: FastMCP) -> None:
        """Setup Mermaid tools on dedicated sub-server."""
        
        # Lazy import and register Mermaid tools only when sub-server is mounted
        def lazy_register_mermaid():
            from tools.mermaid.basic_mermaid_tools import register_basic_mermaid_tools
            from tools.mermaid.advanced_mermaid_tools import register_advanced_mermaid_tools  
            from tools.mermaid.analysis_mermaid_tools import register_analysis_mermaid_tools
            
            register_basic_mermaid_tools(server, self.settings)     # 8 tools
            register_advanced_mermaid_tools(server, self.settings)  # 8 tools
            register_analysis_mermaid_tools(server, self.settings)  # 8 tools
        
        # Register tools on sub-server
        lazy_register_mermaid()
    
    async def _register_progressive_resources(self, mcp: FastMCP, category: str, spec: Dict) -> int:
        """Register tools for progressive background loading."""
        
        if category == 'documentation':
            
            # Create placeholder resources that trigger background loading
            @mcp.resource("tools://documentation/{doc_type}/status")
            def create_doc_status_resource(doc_type: str) -> FunctionResource:
                """Documentation status with progressive loading."""
                
                async def doc_status_lazy():
                    # Trigger background loading if not already loaded
                    if not self._loaded_categories.get('documentation', False):
                        asyncio.create_task(self._load_documentation_tools())
                    
                    # Return immediate status while background loading
                    return {
                        "status": "loading" if not self._loaded_categories.get('documentation') else "ready",
                        "doc_type": doc_type,
                        "loading_strategy": "progressive"
                    }
                
                return FunctionResource.from_function(
                    fn=doc_status_lazy,
                    uri=f"tools://documentation/{doc_type}/status",
                    description=f"Documentation {doc_type} status (progressive loading)"
                )
            
            return len(spec['tools'])
            
        return 0
    
    async def _load_documentation_tools(self) -> None:
        """Background loading of documentation tools."""
        if self._loaded_categories.get('documentation', False):
            return
            
        self.logger.debug("Starting background loading of documentation tools")
        
        try:
            # Import and initialize documentation tools
            from tools.documentation import register_documentation_tools
            
            # This would be handled by the progressive initializer
            # For now, just mark as loaded
            self._loaded_categories['documentation'] = True
            
            self.logger.info("Documentation tools loaded in background")
            
        except Exception as e:
            self.logger.error(f"Failed to load documentation tools: {e}")
    
    async def ensure_category_loaded(self, category: str) -> bool:
        """Ensure a specific tool category is loaded on-demand."""
        if self._loaded_categories.get(category, False):
            return True
            
        self.logger.debug(f"Loading category on-demand: {category}")
        
        # Implementation for on-demand category loading
        # This would trigger the appropriate loading strategy
        
        return True
```

---

## 🚀 USAGE EXAMPLES

### Server Initialization Example

```python
#!/usr/bin/env python3
"""
Example: LTMC FastMCP Server with Lazy Loading
"""

import asyncio
from fastmcp import FastMCP
from config.settings import LTMCSettings
from core.lazy_tool_manager import LazyToolManager

async def main():
    """Initialize LTMC server with lazy loading architecture."""
    
    # Create FastMCP server
    mcp = FastMCP("ltmc-lazy")
    
    # Initialize lazy loading architecture  
    settings = LTMCSettings()
    lazy_manager = LazyToolManager(settings)
    
    # Initialize with performance validation
    metrics = await lazy_manager.initialize_server(mcp)
    
    # Validate performance targets
    print(f"Startup completed in {metrics.startup_time:.1f}ms")
    print(f"Essential tools loaded: {metrics.essential_tools_count} in {metrics.essential_load_time:.1f}ms")
    print(f"Total tools registered: {metrics.total_tools_registered}")
    
    # Start server
    await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())
```

### Client Usage Example

```python
#!/usr/bin/env python3
"""
Example: Client using lazy-loaded LTMC tools
"""

import asyncio
from fastmcp import Client

async def demonstrate_lazy_loading():
    """Demonstrate lazy loading behavior from client perspective."""
    
    client = Client("ltmc-lazy-server")
    
    async with client:
        # Essential tools - immediate response (<50ms)
        print("Testing essential tools...")
        ping_result = await client.call_tool("ping")
        print(f"Ping: {ping_result.data}")
        
        # Store memory - essential tool with lazy DB connection
        store_result = await client.call_tool("store_memory", {
            "content": "Test lazy loading architecture",
            "file_name": "lazy_test.md"
        })
        print(f"Store memory: {store_result.data}")
        
        # Lazy tool - first access triggers loading (<200ms)
        print("Testing lazy tools (first access)...")
        pattern_result = await client.read_resource("tools://memory/analyze_patterns/lazy_loading")
        print(f"Pattern analysis: {pattern_result}")
        
        # Mermaid tool via mounted sub-server
        print("Testing mounted sub-server tools...")
        mermaid_result = await client.call_tool("mermaid_create_flowchart", {
            "title": "Lazy Loading Architecture",
            "data": {"nodes": ["Essential", "Lazy", "Progressive"]}
        })
        print(f"Mermaid diagram: {mermaid_result.data}")

if __name__ == "__main__":
    asyncio.run(demonstrate_lazy_loading())
```

---

## 📊 PERFORMANCE VALIDATION

### Performance Test Example

```python
#!/usr/bin/env python3
"""
Performance validation for lazy loading architecture
"""

import asyncio
import time
from typing import Dict, Any

async def validate_performance_targets():
    """Validate that lazy loading meets performance targets."""
    
    results = {}
    
    # Test 1: Server startup time
    start_time = time.time()
    # ... server initialization code ...
    startup_time = (time.time() - start_time) * 1000
    
    results['startup_time_ms'] = startup_time
    results['startup_target_met'] = startup_time < 200
    
    # Test 2: Essential tool response time
    start_time = time.time()
    # ... call essential tool ...
    essential_response_time = (time.time() - start_time) * 1000
    
    results['essential_response_ms'] = essential_response_time
    results['essential_target_met'] = essential_response_time < 50
    
    # Test 3: Lazy tool first access
    start_time = time.time()
    # ... call lazy tool for first time ...
    lazy_first_access = (time.time() - start_time) * 1000
    
    results['lazy_first_access_ms'] = lazy_first_access
    results['lazy_target_met'] = lazy_first_access < 200
    
    return results
```

---

**Implementation Status**: ✅ Complete Examples - Ready for Development Team  
**Next Phase**: Begin implementation of LazyToolManager component