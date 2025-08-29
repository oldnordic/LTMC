"""
MCP Batch Execution System
Handles batched execution of multiple tool calls with optimization strategies.

File: ltms/subagent/batch_execution.py
Lines: ~150 (under 300 limit)
Purpose: Batch processing and execution strategies for multiple tool calls
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass
from collections import defaultdict

from .optimization_core import ToolCall, MCPCoreOptimizer

logger = logging.getLogger(__name__)


@dataclass
class BatchedExecution:
    """Represents a batch of tool calls for optimized execution."""
    batch_id: str
    tool_calls: List[ToolCall]
    shared_context: Dict[str, Any]
    estimated_tokens: int
    execution_strategy: str  # "parallel", "sequential", "optimized"


class MCPBatchExecutor:
    """
    Batch execution system for MCP tool calls.
    
    Groups compatible tools and executes them with optimal strategies
    for Claude Code subagent integration.
    """
    
    def __init__(self, core_optimizer: MCPCoreOptimizer):
        self.core_optimizer = core_optimizer
        
    async def batch_optimize_tools(self, tool_calls: List[Dict[str, Any]], 
                                 session_id: str) -> List[Any]:
        """
        Execute multiple tool calls with batch optimization.
        
        Args:
            tool_calls: List of tool call specifications
            session_id: Session identifier
            
        Returns:
            List of tool execution results
        """
        if not tool_calls:
            return []
        
        # Convert to ToolCall objects
        calls = []
        for call_spec in tool_calls:
            call = ToolCall(
                tool_name=call_spec["name"],
                arguments=call_spec["arguments"],
                session_id=session_id,
                timestamp=datetime.now(),
                estimated_tokens=self.core_optimizer._estimate_tokens(call_spec),
                priority=call_spec.get("priority", "normal")
            )
            calls.append(call)
        
        # Create optimized batches
        batches = await self._create_optimized_batches(calls, session_id)
        
        # Execute batches
        all_results = []
        for batch in batches:
            batch_results = await self._execute_batch(batch, session_id)
            all_results.extend(batch_results)
        
        return all_results
    
    async def _create_optimized_batches(self, tool_calls: List[ToolCall], 
                                      session_id: str) -> List[BatchedExecution]:
        """
        Create optimized batches from tool calls.
        
        Groups compatible tools and optimizes execution order.
        """
        # Group tools by compatibility
        compatibility_groups = self._group_compatible_tools(tool_calls)
        
        batches = []
        for group_name, calls in compatibility_groups.items():
            # Create batch with shared context
            shared_context = await self._extract_shared_context(calls, session_id)
            
            batch = BatchedExecution(
                batch_id=f"{session_id}_{group_name}_{len(batches)}",
                tool_calls=calls,
                shared_context=shared_context,
                estimated_tokens=sum(call.estimated_tokens for call in calls),
                execution_strategy=self._determine_execution_strategy(calls)
            )
            batches.append(batch)
        
        return batches
    
    def _group_compatible_tools(self, tool_calls: List[ToolCall]) -> Dict[str, List[ToolCall]]:
        """
        Group tool calls that can be optimized together.
        
        Tools are grouped by:
        - Same tool type (can share database connections)
        - Similar resource requirements
        - Compatible execution patterns
        """
        groups = defaultdict(list)
        
        for call in tool_calls:
            # Group by tool category
            if call.tool_name.startswith('memory_'):
                group_key = "memory_ops"
            elif call.tool_name.startswith('graph_'):
                group_key = "graph_ops"  
            elif call.tool_name.startswith('unix_'):
                group_key = "unix_ops"
            elif call.tool_name.startswith('pattern_'):
                group_key = "pattern_ops"
            else:
                group_key = f"single_{call.tool_name}"
            
            groups[group_key].append(call)
        
        return dict(groups)
    
    async def _execute_batch(self, batch: BatchedExecution, 
                           session_id: str) -> List[Any]:
        """
        Execute a batch of tool calls with optimization.
        """
        logger.debug(f"Executing batch {batch.batch_id} with {len(batch.tool_calls)} calls")
        
        results = []
        
        if batch.execution_strategy == "parallel":
            # Execute tools in parallel where safe
            tasks = []
            for call in batch.tool_calls:
                task = self._execute_single_call_in_batch(call, batch.shared_context, session_id)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
        elif batch.execution_strategy == "sequential":
            # Execute tools sequentially
            for call in batch.tool_calls:
                result = await self._execute_single_call_in_batch(call, batch.shared_context, session_id)
                results.append(result)
                
        else:  # optimized strategy
            # Custom optimization based on tool patterns
            results = await self._execute_optimized_sequence(batch, session_id)
        
        return results
    
    async def _execute_single_call_in_batch(self, call: ToolCall, 
                                          shared_context: Dict[str, Any],
                                          session_id: str) -> Any:
        """Execute a single tool call within a batch context."""
        # Merge shared context with call arguments
        enhanced_args = call.arguments.copy()
        enhanced_args.update(shared_context)
        
        return await self.core_optimizer.optimize_tool_call(
            call.tool_name, enhanced_args, session_id, call.priority
        )
    
    async def _execute_optimized_sequence(self, batch: BatchedExecution, 
                                        session_id: str) -> List[Any]:
        """Execute batch using optimized sequencing strategies."""
        results = []
        
        # Sort by priority and dependencies
        sorted_calls = sorted(batch.tool_calls, 
                            key=lambda x: (x.priority == "high", x.timestamp))
        
        accumulated_context = batch.shared_context.copy()
        
        for call in sorted_calls:
            # Execute with accumulated context
            enhanced_args = call.arguments.copy()
            enhanced_args.update(accumulated_context)
            
            result = await self.core_optimizer.optimize_tool_call(
                call.tool_name, enhanced_args, session_id, call.priority
            )
            results.append(result)
            
            # Update accumulated context with result if useful
            if self._is_context_relevant(result, call.tool_name):
                accumulated_context[f"previous_{call.tool_name}_result"] = result
        
        return results
    
    async def _extract_shared_context(self, tool_calls: List[ToolCall], 
                                    session_id: str) -> Dict[str, Any]:
        """Extract context that can be shared across tool calls in a batch."""
        shared_context = {}
        
        # Find common arguments
        if tool_calls:
            first_call = tool_calls[0]
            for key, value in first_call.arguments.items():
                if all(call.arguments.get(key) == value for call in tool_calls[1:]):
                    shared_context[f"shared_{key}"] = value
        
        # Add session-level context
        if session_id in self.core_optimizer.context_cache:
            shared_context.update(self.core_optimizer.context_cache[session_id])
        
        return shared_context
    
    def _determine_execution_strategy(self, tool_calls: List[ToolCall]) -> str:
        """Determine optimal execution strategy for a batch of tool calls."""
        # Simple heuristics for execution strategy
        if len(tool_calls) == 1:
            return "sequential"
        
        # Check if all tools are read-only operations
        read_only_tools = {"unix_action", "pattern_action", "cache_action"}
        if all(call.tool_name in read_only_tools for call in tool_calls):
            return "parallel"
        
        # Check if tools have dependencies
        write_tools = {"memory_action", "graph_action", "blueprint_action"}
        has_writes = any(call.tool_name in write_tools for call in tool_calls)
        
        if has_writes:
            return "optimized"  # Need careful ordering
        else:
            return "parallel"
    
    def _is_context_relevant(self, result: Any, tool_name: str) -> bool:
        """Check if tool result should be added to context for future calls."""
        # Memory and graph results are often useful as context
        relevant_tools = {"memory_action", "graph_action", "pattern_action"}
        return tool_name in relevant_tools