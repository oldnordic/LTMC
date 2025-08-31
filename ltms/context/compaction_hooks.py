#!/usr/bin/env python3
"""
Context Compaction Hook System Integration with Claude Code

This module provides the core hook system for context compaction and restoration,
integrating with Claude Code's pre/post compaction lifecycle.

Key Features:
- Pre-compaction context capture and storage
- Post-compaction context restoration from lean JSON
- Integration with LTMC memory systems
- Performance-optimized context window management
- Real database operations for persistent state
"""

import json
import time
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime, timezone
from enum import Enum

from ltms.tools.memory.memory_actions import MemoryTools
from ltms.tools.core.database_manager import DatabaseManager
from ltms.config.json_config_loader import get_config

logger = logging.getLogger(__name__)


class ContextJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for context compaction data."""
    
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


class ContextCompactionManager:
    """
    Manages context compaction and restoration for Claude Code integration.
    
    This class handles the complete lifecycle of context management:
    1. Pre-compaction: Capture and store full context
    2. Generate lean restoration JSON
    3. Post-compaction: Restore minimal essential context
    4. On-demand: Retrieve full context when needed
    """
    
    def __init__(self):
        self.config = get_config()
        self.memory_tools = MemoryTools()
        self.db_manager = DatabaseManager()
        self.session_id = self._generate_session_id()
        
    def _generate_session_id(self) -> str:
        """Generate unique session ID for context tracking."""
        timestamp = int(time.time())
        return f"ctx_session_{timestamp}_{id(self)}"
    
    async def pre_compaction_hook(self, 
                                  current_context: Dict[str, Any],
                                  active_todos: List[Dict[str, Any]],
                                  active_file: Optional[str] = None,
                                  current_goal: Optional[str] = None) -> Dict[str, Any]:
        """
        Pre-compaction hook: Store full context and generate lean restoration data.
        
        Args:
            current_context: Full conversation context before compaction
            active_todos: Current todo list state
            active_file: Currently active file being worked on
            current_goal: Current primary objective
            
        Returns:
            Lean JSON context for post-compaction restoration
        """
        try:
            # Store full context in LTMC memory
            full_context_doc = {
                "session_id": self.session_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "full_context": current_context,
                "active_todos": active_todos,
                "active_file": active_file,
                "current_goal": current_goal,
                "compaction_trigger_time": time.time()
            }
            
            # Store in memory with conversation threading
            store_result = await self.memory_tools(
                "store",
                file_name=f"pre_compaction_context_{self.session_id}.json",
                content=json.dumps(full_context_doc, indent=2, cls=ContextJSONEncoder),
                resource_type="context_compaction",
                conversation_id=f"compaction_{self.session_id}",
                tags=["context_compaction", "pre_compaction", "full_context"]
            )
            
            if not store_result.get('success'):
                logger.error(f"Failed to store pre-compaction context: {store_result.get('error')}")
                
            # Generate lean restoration JSON
            lean_context = self._generate_lean_context(
                active_todos, active_file, current_goal, current_context
            )
            
            # Store restoration prompt for hook system
            restoration_file = f"/tmp/post_compact_restoration_instructions.md"
            await self._write_restoration_instructions(restoration_file, lean_context)
            
            logger.info(f"Pre-compaction hook completed for session {self.session_id}")
            return lean_context
            
        except Exception as e:
            logger.error(f"Pre-compaction hook failed: {e}")
            # Return minimal fallback context
            return {
                "status": "error",
                "session_id": self.session_id,
                "error": str(e),
                "fallback_context": "Context compaction failed, manual recovery may be needed"
            }
    
    def _generate_lean_context(self,
                              active_todos: List[Dict[str, Any]],
                              active_file: Optional[str],
                              current_goal: Optional[str],
                              full_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate lean JSON context for efficient post-compaction restoration.
        
        This creates a minimal but sufficient context payload that allows
        the agent to immediately resume work without loading full chat history.
        """
        
        # Extract only active/in-progress todos
        active_only_todos = [
            todo for todo in active_todos 
            if todo.get('status') in ['in_progress', 'pending']
        ]
        
        # Extract key context indicators
        recent_actions = self._extract_recent_actions(full_context)
        current_plan = self._extract_current_plan(full_context, active_todos)
        
        lean_context = {
            "compaction_metadata": {
                "session_id": self.session_id,
                "compaction_time": datetime.now(timezone.utc).isoformat(),
                "context_version": "1.0"
            },
            "immediate_context": {
                "active_todos": active_only_todos,
                "current_file": active_file,
                "current_goal": current_goal,
                "current_plan": current_plan,
                "recent_actions": recent_actions
            },
            "recovery_info": {
                "full_context_available": True,
                "recovery_session_id": self.session_id,
                "recovery_conversation_id": f"compaction_{self.session_id}"
            }
        }
        
        return lean_context
    
    def _extract_recent_actions(self, full_context: Dict[str, Any]) -> List[str]:
        """Extract most recent actions from full context."""
        # Look for recent tool uses, file operations, etc.
        recent_actions = []
        
        # Extract from conversation messages (if available)
        if 'messages' in full_context:
            messages = full_context['messages'][-5:]  # Last 5 messages
            for msg in messages:
                if isinstance(msg, dict) and 'content' in msg:
                    content = msg['content']
                    if 'antml:function_calls' in str(content):
                        recent_actions.append("Tool usage")
                    elif 'Write' in str(content) or 'Edit' in str(content):
                        recent_actions.append("File operation")
                        
        # Fallback to generic indicators
        if not recent_actions:
            recent_actions = ["Context preserved", "Ready to continue"]
            
        return recent_actions[:3]  # Keep it lean
    
    def _extract_current_plan(self, 
                             full_context: Dict[str, Any], 
                             active_todos: List[Dict[str, Any]]) -> Optional[str]:
        """Extract current plan or sequence from context."""
        
        # Look for explicit plan in todos
        for todo in active_todos:
            if 'plan' in todo.get('content', '').lower():
                return todo['content']
                
        # Look for sequence in in-progress items
        in_progress = [t for t in active_todos if t.get('status') == 'in_progress']
        if in_progress:
            return f"Working on: {in_progress[0]['content']}"
            
        return None
    
    async def _write_restoration_instructions(self, 
                                            file_path: str, 
                                            lean_context: Dict[str, Any]):
        """Write restoration instructions for post-compaction hook."""
        instructions = f"""# Context Restoration Instructions

## Session Information
- Session ID: {lean_context['compaction_metadata']['session_id']}
- Compaction Time: {lean_context['compaction_metadata']['compaction_time']}

## Immediate Context
{json.dumps(lean_context, indent=2)}

## Recovery Instructions
1. Use session ID `{self.session_id}` to retrieve full context if needed
2. Query conversation ID `compaction_{self.session_id}` for complete history
3. Active todos and current goal have been preserved above

## Agent Instructions
Continue with the active todos listed above. Full context is available in LTMC memory if deeper context is required.
"""
        
        with open(file_path, 'w') as f:
            f.write(instructions)
    
    async def post_compaction_hook(self) -> Dict[str, Any]:
        """
        Post-compaction hook: Restore lean context from stored instructions.
        
        This is called after chat compaction to restore minimal essential context.
        """
        try:
            restoration_file = "/tmp/post_compact_restoration_instructions.md"
            
            if not Path(restoration_file).exists():
                logger.warning("No restoration instructions found")
                return {"status": "no_restoration_data"}
                
            # Read restoration instructions
            with open(restoration_file, 'r') as f:
                instructions = f.read()
                
            # Extract JSON context (simple parsing)
            json_start = instructions.find('{')
            json_end = instructions.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                lean_context_str = instructions[json_start:json_end]
                lean_context = json.loads(lean_context_str)
                
                logger.info(f"Post-compaction context restored for session {lean_context.get('compaction_metadata', {}).get('session_id')}")
                return lean_context
            else:
                logger.error("Could not extract JSON context from restoration file")
                return {"status": "extraction_failed"}
                
        except Exception as e:
            logger.error(f"Post-compaction hook failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def retrieve_full_context(self, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieve full context from LTMC memory when needed.
        
        Args:
            session_id: Session ID to retrieve (defaults to current session)
            
        Returns:
            Full context data or None if not found
        """
        target_session = session_id or self.session_id
        
        try:
            # Query LTMC memory for full context
            retrieve_result = await self.memory_tools(
                "retrieve",
                query=f"pre_compaction_context_{target_session}",
                conversation_id=f"compaction_{target_session}",
                top_k=1
            )
            
            if retrieve_result.get('success') and retrieve_result.get('data', {}).get('documents'):
                documents = retrieve_result['data']['documents']
                if documents:
                    # Parse the stored context
                    context_content = documents[0].get('content', '{}')
                    full_context = json.loads(context_content)
                    logger.info(f"Retrieved full context for session {target_session}")
                    return full_context
                    
            logger.warning(f"No full context found for session {target_session}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve full context: {e}")
            return None
    
    async def validate_context_integrity(self) -> Dict[str, Any]:
        """
        Validate context compaction system integrity.
        
        Returns:
            Validation report with system status
        """
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "validations": {}
        }
        
        # Test database connectivity
        try:
            db_availability = self.db_manager.is_available()
            working_dbs = [k for k, v in db_availability.items() if v]
            report["validations"]["database_connectivity"] = {
                "status": "pass" if len(working_dbs) >= 3 else "warning",
                "working_databases": working_dbs,
                "total_available": len(working_dbs)
            }
        except Exception as e:
            report["validations"]["database_connectivity"] = {
                "status": "fail",
                "error": str(e)
            }
        
        # Test memory tools functionality
        try:
            test_result = await self.memory_tools(
                "store",
                file_name=f"context_validation_{int(time.time())}.txt",
                content="Context compaction system validation test",
                resource_type="validation_test",
                conversation_id="system_validation"
            )
            
            report["validations"]["memory_tools"] = {
                "status": "pass" if test_result.get('success') else "fail",
                "test_result": test_result
            }
        except Exception as e:
            report["validations"]["memory_tools"] = {
                "status": "fail",
                "error": str(e)
            }
        
        # Overall system status
        failed_validations = [
            k for k, v in report["validations"].items() 
            if v.get("status") == "fail"
        ]
        
        if not failed_validations:
            report["overall_status"] = "healthy"
        elif len(failed_validations) == 1:
            report["overall_status"] = "degraded"
        else:
            report["overall_status"] = "critical"
            
        return report


# Global instance for hook system integration
_compaction_manager = None

async def get_compaction_manager() -> ContextCompactionManager:
    """Get singleton context compaction manager."""
    global _compaction_manager
    if _compaction_manager is None:
        _compaction_manager = ContextCompactionManager()
    return _compaction_manager


# Hook functions for Claude Code integration
async def claude_code_pre_compaction_hook(**kwargs) -> Dict[str, Any]:
    """Claude Code pre-compaction hook entry point."""
    manager = await get_compaction_manager()
    return await manager.pre_compaction_hook(**kwargs)


async def claude_code_post_compaction_hook() -> Dict[str, Any]:
    """Claude Code post-compaction hook entry point."""
    manager = await get_compaction_manager()
    return await manager.post_compaction_hook()


if __name__ == "__main__":
    # Test the compaction system
    async def test_compaction_system():
        manager = ContextCompactionManager()
        
        # Test validation
        report = await manager.validate_context_integrity()
        print("System Validation Report:")
        print(json.dumps(report, indent=2))
        
        # Test compaction workflow
        test_context = {
            "messages": ["Test message 1", "Test message 2"],
            "current_task": "Testing compaction system"
        }
        
        test_todos = [
            {"content": "Test context compaction", "status": "in_progress", "id": "test1"},
            {"content": "Validate system integrity", "status": "pending", "id": "test2"}
        ]
        
        lean_context = await manager.pre_compaction_hook(
            current_context=test_context,
            active_todos=test_todos,
            active_file="ltms/context/compaction_hooks.py",
            current_goal="Implement context compaction system"
        )
        
        print("\nGenerated Lean Context:")
        print(json.dumps(lean_context, indent=2))
        
        # Test post-compaction restoration
        restored = await manager.post_compaction_hook()
        print("\nRestored Context:")
        print(json.dumps(restored, indent=2))
    
    asyncio.run(test_compaction_system())