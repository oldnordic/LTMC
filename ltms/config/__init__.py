"""
LTMC Configuration Package
Unified configuration for the shared knowledge base used by all tools
"""

from .json_config_loader import get_config

# Context compaction configuration imports
try:
    from ltms.context.compaction_hooks import (
        ContextCompactionManager, get_compaction_manager,
        claude_code_pre_compaction_hook, claude_code_post_compaction_hook
    )
    from ltms.context.restoration_schema import (
        LeanContextSchema, CompactionMetadata, ImmediateContext, RecoveryInfo,
        TodoItem, TodoStatus, ContextSchemaValidator,
        create_development_context, create_testing_context
    )
    
    # Context compaction configuration available
    CONTEXT_COMPACTION_AVAILABLE = True
    
    __all__ = [
        "get_config",
        # Context compaction manager
        "ContextCompactionManager", "get_compaction_manager",
        # Hook functions
        "claude_code_pre_compaction_hook", "claude_code_post_compaction_hook",
        # Schema classes
        "LeanContextSchema", "CompactionMetadata", "ImmediateContext", "RecoveryInfo",
        "TodoItem", "TodoStatus", "ContextSchemaValidator",
        # Context factory functions
        "create_development_context", "create_testing_context",
        # Status flag
        "CONTEXT_COMPACTION_AVAILABLE"
    ]
    
except ImportError as e:
    # Context compaction not available - fallback mode
    CONTEXT_COMPACTION_AVAILABLE = False
    
    __all__ = [
        "get_config",
        "CONTEXT_COMPACTION_AVAILABLE"
    ]
    
    # Create placeholder functions for graceful degradation
    def get_compaction_manager():
        """Placeholder when context compaction is not available."""
        return None
    
    def claude_code_pre_compaction_hook(*args, **kwargs):
        """Placeholder hook when context compaction is not available."""
        return {"status": "unavailable", "reason": "Context compaction not installed"}
    
    def claude_code_post_compaction_hook(*args, **kwargs):
        """Placeholder hook when context compaction is not available."""
        return {"status": "unavailable", "reason": "Context compaction not installed"}
    
    # Add placeholders to exports
    __all__.extend([
        "get_compaction_manager", 
        "claude_code_pre_compaction_hook", 
        "claude_code_post_compaction_hook"
    ])
