#!/usr/bin/env python3
"""
Context Restoration Schema Definitions

This module defines the JSON schemas and data structures for lean context
restoration after chat compaction. Optimized for minimal context window usage
while maintaining essential state continuity.

Key Components:
- Lean context JSON schema
- Context validation
- Schema versioning for backward compatibility
- Performance-optimized serialization
"""

from typing import Dict, Any, List, Optional, Union, Literal
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json


class ContextSchemaVersion(Enum):
    """Schema version for backward compatibility."""
    V1_0 = "1.0"
    V1_1 = "1.1"  # Future version support


class TodoStatus(Enum):
    """Todo item status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass
class TodoItem:
    """
    Lean todo item representation for context restoration.
    
    Only includes essential fields to minimize context size.
    """
    content: str
    status: TodoStatus
    id: str
    priority: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with enum serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TodoItem':
        """Create from dictionary with enum deserialization."""
        if isinstance(data.get('status'), str):
            data['status'] = TodoStatus(data['status'])
        return cls(**data)


@dataclass
class CompactionMetadata:
    """Metadata about the compaction event."""
    session_id: str
    compaction_time: str
    context_version: str
    original_context_size: Optional[int] = None
    compressed_ratio: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompactionMetadata':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ImmediateContext:
    """
    Essential context for immediate work resumption.
    
    This contains the minimal data needed for the agent to continue
    working without needing to reload full conversation history.
    """
    active_todos: List[TodoItem]
    current_file: Optional[str] = None
    current_goal: Optional[str] = None
    current_plan: Optional[str] = None
    recent_actions: Optional[List[str]] = None
    active_directory: Optional[str] = None
    last_command: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with nested serialization."""
        data = asdict(self)
        data['active_todos'] = [todo.to_dict() for todo in self.active_todos]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ImmediateContext':
        """Create from dictionary with nested deserialization."""
        if 'active_todos' in data and isinstance(data['active_todos'], list):
            data['active_todos'] = [
                TodoItem.from_dict(todo) if isinstance(todo, dict) else todo
                for todo in data['active_todos']
            ]
        return cls(**data)


@dataclass
class RecoveryInfo:
    """Information for recovering full context when needed."""
    full_context_available: bool
    recovery_session_id: str
    recovery_conversation_id: str
    backup_location: Optional[str] = None
    recovery_query: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecoveryInfo':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class LeanContextSchema:
    """
    Main lean context schema for post-compaction restoration.
    
    This is the complete schema that gets serialized to JSON and stored
    for context restoration after compaction events.
    """
    compaction_metadata: CompactionMetadata
    immediate_context: ImmediateContext
    recovery_info: RecoveryInfo
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire schema to dictionary."""
        return {
            'compaction_metadata': self.compaction_metadata.to_dict(),
            'immediate_context': self.immediate_context.to_dict(),
            'recovery_info': self.recovery_info.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LeanContextSchema':
        """Create from dictionary with full nested deserialization."""
        return cls(
            compaction_metadata=CompactionMetadata.from_dict(data['compaction_metadata']),
            immediate_context=ImmediateContext.from_dict(data['immediate_context']),
            recovery_info=RecoveryInfo.from_dict(data['recovery_info'])
        )
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'LeanContextSchema':
        """Deserialize from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def validate_schema(self) -> Dict[str, Any]:
        """
        Validate schema integrity and completeness.
        
        Returns:
            Validation report with status and any issues
        """
        issues = []
        warnings = []
        
        # Validate required fields
        if not self.compaction_metadata.session_id:
            issues.append("Missing session_id in compaction metadata")
            
        if not self.recovery_info.recovery_session_id:
            issues.append("Missing recovery_session_id in recovery info")
            
        # Validate todo items
        if not self.immediate_context.active_todos:
            warnings.append("No active todos in immediate context")
        else:
            for i, todo in enumerate(self.immediate_context.active_todos):
                if not todo.content.strip():
                    issues.append(f"Empty content in todo item {i}")
                if not todo.id:
                    issues.append(f"Missing ID in todo item {i}")
        
        # Validate context completeness
        if not self.immediate_context.current_goal and not self.immediate_context.current_file:
            warnings.append("No current goal or active file specified")
        
        # Check schema version compatibility
        supported_versions = [v.value for v in ContextSchemaVersion]
        if self.compaction_metadata.context_version not in supported_versions:
            issues.append(f"Unsupported schema version: {self.compaction_metadata.context_version}")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "schema_version": self.compaction_metadata.context_version,
            "validation_time": datetime.utcnow().isoformat()
        }
    
    def get_context_size_estimate(self) -> Dict[str, int]:
        """
        Estimate the size impact of this context.
        
        Returns:
            Size estimates in characters and tokens (approximate)
        """
        json_str = self.to_json()
        char_count = len(json_str)
        
        # Rough token estimate (4 chars per token average)
        token_estimate = char_count // 4
        
        # Count components
        todo_count = len(self.immediate_context.active_todos)
        action_count = len(self.immediate_context.recent_actions or [])
        
        return {
            "total_characters": char_count,
            "estimated_tokens": token_estimate,
            "todo_items": todo_count,
            "recent_actions": action_count,
            "schema_version": self.compaction_metadata.context_version
        }


class ContextSchemaValidator:
    """Utility class for validating context schemas."""
    
    @staticmethod
    def validate_json_structure(json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate raw JSON structure before deserialization.
        
        Args:
            json_data: Raw JSON dictionary
            
        Returns:
            Validation report
        """
        required_top_level = ['compaction_metadata', 'immediate_context', 'recovery_info']
        missing_fields = [field for field in required_top_level if field not in json_data]
        
        if missing_fields:
            return {
                "valid": False,
                "error": f"Missing required top-level fields: {missing_fields}",
                "type": "structure_error"
            }
        
        # Validate nested required fields
        metadata = json_data.get('compaction_metadata', {})
        if not isinstance(metadata.get('session_id'), str):
            return {
                "valid": False,
                "error": "Invalid or missing session_id in compaction_metadata",
                "type": "field_error"
            }
        
        immediate = json_data.get('immediate_context', {})
        if not isinstance(immediate.get('active_todos'), list):
            return {
                "valid": False,
                "error": "active_todos must be a list in immediate_context",
                "type": "field_error"
            }
        
        recovery = json_data.get('recovery_info', {})
        if not isinstance(recovery.get('full_context_available'), bool):
            return {
                "valid": False,
                "error": "full_context_available must be boolean in recovery_info",
                "type": "field_error"
            }
        
        return {
            "valid": True,
            "message": "JSON structure is valid"
        }
    
    @staticmethod
    def create_minimal_context(session_id: str, 
                             todos: Optional[List[Dict[str, Any]]] = None,
                             current_file: Optional[str] = None,
                             current_goal: Optional[str] = None) -> LeanContextSchema:
        """
        Create a minimal valid context schema.
        
        Useful for fallback scenarios or testing.
        """
        
        # Convert todos to TodoItem objects
        todo_items = []
        if todos:
            for todo_dict in todos:
                try:
                    todo_items.append(TodoItem.from_dict(todo_dict))
                except Exception:
                    # Fallback for malformed todos
                    todo_items.append(TodoItem(
                        content=str(todo_dict.get('content', 'Malformed todo')),
                        status=TodoStatus.PENDING,
                        id=str(todo_dict.get('id', f'fallback_{len(todo_items)}'))
                    ))
        
        # Default fallback todo if none provided
        if not todo_items:
            todo_items.append(TodoItem(
                content="Resume previous work",
                status=TodoStatus.PENDING,
                id="fallback_resume"
            ))
        
        return LeanContextSchema(
            compaction_metadata=CompactionMetadata(
                session_id=session_id,
                compaction_time=datetime.utcnow().isoformat(),
                context_version=ContextSchemaVersion.V1_0.value
            ),
            immediate_context=ImmediateContext(
                active_todos=todo_items,
                current_file=current_file,
                current_goal=current_goal,
                recent_actions=["Context compacted", "Ready to resume"]
            ),
            recovery_info=RecoveryInfo(
                full_context_available=False,  # Minimal context has no full backup
                recovery_session_id=session_id,
                recovery_conversation_id=f"minimal_{session_id}"
            )
        )


# Schema factory functions for common use cases
def create_development_context(session_id: str,
                             current_file: str,
                             todos: List[Dict[str, Any]],
                             goal: Optional[str] = None) -> LeanContextSchema:
    """Create context schema optimized for development work."""
    
    todo_items = [TodoItem.from_dict(todo) for todo in todos]
    
    return LeanContextSchema(
        compaction_metadata=CompactionMetadata(
            session_id=session_id,
            compaction_time=datetime.utcnow().isoformat(),
            context_version=ContextSchemaVersion.V1_0.value
        ),
        immediate_context=ImmediateContext(
            active_todos=todo_items,
            current_file=current_file,
            current_goal=goal or "Continue development work",
            recent_actions=["File editing", "Code implementation"],
            active_directory="/home/feanor/Projects/ltmc"
        ),
        recovery_info=RecoveryInfo(
            full_context_available=True,
            recovery_session_id=session_id,
            recovery_conversation_id=f"development_{session_id}",
            recovery_query=f"development session {session_id}"
        )
    )


def create_testing_context(session_id: str,
                          test_files: List[str],
                          todos: List[Dict[str, Any]]) -> LeanContextSchema:
    """Create context schema optimized for testing workflows."""
    
    todo_items = [TodoItem.from_dict(todo) for todo in todos]
    
    return LeanContextSchema(
        compaction_metadata=CompactionMetadata(
            session_id=session_id,
            compaction_time=datetime.utcnow().isoformat(),
            context_version=ContextSchemaVersion.V1_0.value
        ),
        immediate_context=ImmediateContext(
            active_todos=todo_items,
            current_file=test_files[0] if test_files else None,
            current_goal="Run and validate tests",
            recent_actions=["Test execution", "Validation checks"],
            current_plan=f"Testing {len(test_files)} files"
        ),
        recovery_info=RecoveryInfo(
            full_context_available=True,
            recovery_session_id=session_id,
            recovery_conversation_id=f"testing_{session_id}",
            recovery_query=f"test session {session_id}"
        )
    )


if __name__ == "__main__":
    # Test schema functionality
    def test_schema_system():
        """Test the context schema system."""
        
        # Create test data
        test_todos = [
            {
                "content": "Implement context compaction",
                "status": "in_progress",
                "id": "task1",
                "priority": "high"
            },
            {
                "content": "Write comprehensive tests",
                "status": "pending", 
                "id": "task2"
            }
        ]
        
        # Test development context
        dev_context = create_development_context(
            session_id="test_dev_123",
            current_file="ltms/context/restoration_schema.py",
            todos=test_todos,
            goal="Implement context compaction system"
        )
        
        # Test serialization
        json_str = dev_context.to_json(indent=2)
        print("Serialized Context:")
        print(json_str)
        
        # Test deserialization
        restored_context = LeanContextSchema.from_json(json_str)
        print(f"\nRestored session ID: {restored_context.compaction_metadata.session_id}")
        print(f"Active todos: {len(restored_context.immediate_context.active_todos)}")
        
        # Test validation
        validation_report = dev_context.validate_schema()
        print(f"\nValidation result: {validation_report}")
        
        # Test size estimation
        size_info = dev_context.get_context_size_estimate()
        print(f"\nContext size: {size_info}")
        
        # Test minimal context creation
        minimal_context = ContextSchemaValidator.create_minimal_context(
            session_id="minimal_test_456",
            current_goal="Resume work after compaction"
        )
        
        print(f"\nMinimal context todos: {len(minimal_context.immediate_context.active_todos)}")
        print(f"Minimal context size: {minimal_context.get_context_size_estimate()}")
    
    test_schema_system()