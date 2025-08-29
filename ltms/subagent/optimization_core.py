"""
MCP Core Performance Optimization
Core optimization logic for MCP tool calls with caching and context management.

File: ltms/subagent/optimization_core.py
Lines: ~200 (under 300 limit)
Purpose: Core optimization system for single tool calls
"""

import json
import asyncio
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass

from ..config.json_config_loader import get_config
from ..services.redis_service import RedisCacheService, RedisConnectionManager

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """Represents a tool call request."""
    tool_name: str
    arguments: Dict[str, Any]
    session_id: str
    timestamp: datetime
    estimated_tokens: int = 0
    priority: str = "normal"  # "low", "normal", "high"


class MCPCoreOptimizer:
    """
    Core MCP tool call optimization system.
    
    Handles single tool call optimization with caching, context optimization,
    and performance tracking for Claude Code subagent integration.
    """
    
    def __init__(self):
        self.config = get_config()
        # Initialize Redis connection manager and cache service
        redis_manager = RedisConnectionManager()
        self.redis_service = RedisCacheService(redis_manager)
        self.context_cache: Dict[str, Dict[str, Any]] = {}
        self._compression_cache: Dict[str, str] = {}
        
    async def optimize_tool_call(self, tool_name: str, arguments: Dict[str, Any],
                               session_id: str, priority: str = "normal") -> Any:
        """
        Execute optimized single tool call with caching and context optimization.
        
        Args:
            tool_name: Name of tool to execute
            arguments: Tool arguments
            session_id: Session identifier
            priority: Execution priority
            
        Returns:
            Tool execution result
        """
        start_time = datetime.now()
        
        # Check cache first
        cache_result = await self._check_result_cache(tool_name, arguments, session_id)
        if cache_result:
            logger.debug(f"Cache hit for {tool_name} in session {session_id}")
            return cache_result
        
        # Optimize arguments using context
        optimized_args = await self._optimize_arguments(arguments, session_id)
        
        # Execute tool call
        try:
            from ..tools.common.tool_registry import get_consolidated_tools
            consolidated_tools = get_consolidated_tools()
            
            if tool_name not in consolidated_tools:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            tool_def = consolidated_tools[tool_name]
            
            if isinstance(tool_def, dict):
                tool_func = tool_def["handler"]
            else:
                tool_func = tool_def
            
            # Execute with timing
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**optimized_args)
            else:
                result = tool_func(**optimized_args)
            
            # Cache result for future use
            await self._cache_result(tool_name, arguments, session_id, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Optimized tool execution failed for {tool_name}: {e}")
            raise
    
    async def _check_result_cache(self, tool_name: str, arguments: Dict[str, Any], 
                                session_id: str) -> Optional[Any]:
        """Check if result is already cached."""
        try:
            # Create cache key
            cache_key = self._create_cache_key(tool_name, arguments, session_id)
            
            # Check Redis cache
            if self.redis_service.is_available():
                cached_result = await self.redis_service.get_json(f"result_cache:{cache_key}")
                if cached_result:
                    # Check if cache is still valid (5 minute TTL for most operations)
                    cache_time = datetime.fromisoformat(cached_result.get("timestamp", ""))
                    if datetime.now(timezone.utc) - cache_time < timedelta(minutes=5):
                        return cached_result.get("result")
            
            return None
            
        except Exception as e:
            logger.debug(f"Cache check failed: {e}")
            return None
    
    async def _cache_result(self, tool_name: str, arguments: Dict[str, Any], 
                          session_id: str, result: Any):
        """Cache tool result for future use."""
        try:
            cache_key = self._create_cache_key(tool_name, arguments, session_id)
            
            cache_data = {
                "result": result,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tool_name": tool_name,
                "session_id": session_id
            }
            
            # Cache in Redis with 5 minute TTL
            if self.redis_service.is_available():
                await self.redis_service.set_json(
                    f"result_cache:{cache_key}", 
                    cache_data, 
                    expire_seconds=300
                )
                
        except Exception as e:
            logger.debug(f"Result caching failed: {e}")
    
    def _create_cache_key(self, tool_name: str, arguments: Dict[str, Any], 
                         session_id: str) -> str:
        """Create consistent cache key for tool call."""
        # Create deterministic hash of arguments
        args_str = json.dumps(arguments, sort_keys=True)
        args_hash = hashlib.md5(args_str.encode()).hexdigest()[:12]
        
        return f"{tool_name}:{args_hash}:{session_id}"
    
    async def _optimize_arguments(self, arguments: Dict[str, Any], 
                                session_id: str) -> Dict[str, Any]:
        """
        Optimize tool arguments using session context and compression.
        """
        optimized_args = arguments.copy()
        
        # Add session context if beneficial
        if session_id in self.context_cache:
            session_context = self.context_cache[session_id]
            
            # Only add context that's likely to be useful
            for key, value in session_context.items():
                if key not in optimized_args and self._is_context_useful(key, arguments):
                    optimized_args[f"context_{key}"] = value
        
        # Compress large string arguments
        for key, value in optimized_args.items():
            if isinstance(value, str) and len(value) > 1000:
                optimized_args[key] = await self._compress_string_argument(value)
        
        return optimized_args
    
    async def _compress_string_argument(self, text: str) -> str:
        """
        Compress large string arguments while preserving essential information.
        """
        # Simple compression: remove excessive whitespace and comments
        lines = text.split('\n')
        compressed_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Skip empty lines and simple comments
            if stripped and not (stripped.startswith('#') and len(stripped) < 50):
                compressed_lines.append(stripped)
        
        compressed = '\n'.join(compressed_lines)
        
        # If still too large, truncate with summary
        if len(compressed) > 2000:
            truncated = compressed[:1800]
            summary = f"\n... [truncated {len(compressed) - 1800} chars]"
            compressed = truncated + summary
        
        return compressed
    
    def _is_context_useful(self, context_key: str, arguments: Dict[str, Any]) -> bool:
        """Check if a context key would be useful for the given arguments."""
        # Avoid adding redundant context
        if context_key in arguments:
            return False
        
        # Some context is generally useful
        useful_context = {"project_path", "session_type", "recent_patterns"}
        return context_key in useful_context
    
    def _estimate_tokens(self, call_spec: Dict[str, Any]) -> int:
        """Estimate token count for a tool call."""
        # Simple token estimation based on argument size
        args_str = json.dumps(call_spec.get("arguments", {}))
        estimated_tokens = len(args_str) // 4  # Rough approximation
        
        # Add base cost per tool
        base_tokens = {
            "memory_action": 50,
            "graph_action": 75,
            "pattern_action": 100,
            "blueprint_action": 60,
            "unix_action": 40
        }
        
        tool_name = call_spec.get("name", "")
        estimated_tokens += base_tokens.get(tool_name, 30)
        
        return estimated_tokens