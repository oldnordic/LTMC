"""
Session Context Management for Autonomous AI Reasoning
Production-ready session and conversation ID extraction for LTMC Sequential Thinking.

This module provides autonomous context extraction capabilities that enable AI agents
to maintain reasoning chains without explicit parameter passing.
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from uuid import uuid4

logger = logging.getLogger(__name__)


@dataclass
class SessionContext:
    """
    Complete session context for autonomous AI reasoning.
    
    Tracks all context elements needed for maintaining reasoning chains
    and conversation continuity across agent interactions.
    """
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    agent_id: Optional[str] = None
    chain_id: Optional[str] = None
    previous_thought_id: Optional[str] = None
    step_number: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    extraction_sources: List[str] = field(default_factory=list)
    generated_fields: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: Optional[float] = None  # Confidence level for context extraction (0.0 to 1.0)
    
    def is_complete(self) -> bool:
        """Check if context has all required fields for autonomous operation."""
        return all([
            self.session_id is not None,
            self.conversation_id is not None,
            self.metadata is not None
        ])
    
    def mark_generated(self, field_name: str) -> None:
        """Mark a field as auto-generated for audit trail."""
        if field_name not in self.generated_fields:
            self.generated_fields.append(field_name)
    
    def add_extraction_source(self, source: str) -> None:
        """Add a source used for context extraction."""
        if source not in self.extraction_sources:
            self.extraction_sources.append(source)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for storage or transmission."""
        return {
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "agent_id": self.agent_id,
            "chain_id": self.chain_id,
            "previous_thought_id": self.previous_thought_id,
            "step_number": self.step_number,
            "metadata": self.metadata,
            "extraction_sources": self.extraction_sources,
            "generated_fields": self.generated_fields,
            "timestamp": self.timestamp.isoformat()
        }


class SessionContextExtractor:
    """
    Extracts and generates session context from multiple sources.
    
    Implements a hierarchical extraction strategy to gather context
    from MCP requests, orchestration services, Mind Graph, and databases.
    """
    
    def __init__(self, db_manager=None, orchestration=None, mcp_base=None):
        """
        Initialize the context extractor.
        
        Args:
            db_manager: DatabaseManager instance for database queries
            orchestration: OrchestrationService for agent context
            mcp_base: MCPToolBase instance for Mind Graph context
        """
        self.db_manager = db_manager
        self.orchestration = orchestration
        self.mcp_base = mcp_base
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Cache for recent session contexts (TTL: 5 minutes)
        self._context_cache: Dict[str, tuple[SessionContext, float]] = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Sequence counter for conversation ID generation
        self._sequence_counter = 0
        
    async def extract_context(self, 
                             arguments: Dict[str, Any],
                             tool_name: str,
                             mcp_metadata: Optional[Dict] = None) -> SessionContext:
        """
        Extract complete session context from available sources.
        
        Uses a hierarchical approach to gather context from:
        1. Explicit parameters in arguments
        2. MCP request metadata
        3. Orchestration service state
        4. Mind Graph tracking
        5. Database state
        6. Intelligent generation
        
        Args:
            arguments: Tool arguments from MCP request
            tool_name: Name of the tool being invoked
            mcp_metadata: Optional MCP protocol metadata
            
        Returns:
            Complete SessionContext with all available information
        """
        start_time = time.time()
        context = SessionContext()
        
        try:
            # Level 1: Extract explicit parameters
            await self._extract_explicit_parameters(context, arguments)
            
            # Level 2: Extract from MCP metadata
            if mcp_metadata:
                await self._extract_mcp_metadata(context, mcp_metadata)
            
            # Level 3: Query orchestration context
            if self.orchestration and not context.agent_id:
                await self._extract_orchestration_context(context)
            
            # Level 4: Access Mind Graph context
            if self.mcp_base:
                await self._extract_mind_graph_context(context)
            
            # Level 5: Query database state
            if self.db_manager and not context.is_complete():
                await self._extract_database_context(context)
            
            # Level 6: Apply intelligent context inference
            caller_context = self.extract_caller_context(arguments, tool_name)
            inferred_context = self.infer_context_from_patterns(arguments, caller_context)
            context = self.apply_intelligent_defaults(context, caller_context, inferred_context)
            
            # Level 7: Generate any remaining missing fields
            await self._generate_missing_fields(context, tool_name)
            
            # Calculate confidence based on extraction sources
            context.confidence = self._calculate_confidence(context)
            
            # Validate and finalize context
            self._validate_context(context)
            
            # Cache the context for reuse
            self._cache_context(context)
            
            extraction_time = (time.time() - start_time) * 1000
            self.logger.debug(f"Context extraction completed in {extraction_time:.2f}ms from sources: {context.extraction_sources}")
            
            return context
            
        except Exception as e:
            self.logger.error(f"Context extraction failed: {e}")
            # Return partial context with error metadata
            context.metadata["extraction_error"] = str(e)
            context.add_extraction_source("error_fallback")
            return context
    
    async def _extract_explicit_parameters(self, context: SessionContext, arguments: Dict[str, Any]) -> None:
        """Extract explicitly provided parameters from arguments."""
        if "session_id" in arguments and arguments["session_id"]:
            context.session_id = arguments["session_id"]
            context.add_extraction_source("explicit_session_id")
        
        if "conversation_id" in arguments and arguments["conversation_id"]:
            context.conversation_id = arguments["conversation_id"]
            context.add_extraction_source("explicit_conversation_id")
        
        if "agent_id" in arguments and arguments["agent_id"]:
            context.agent_id = arguments["agent_id"]
            context.add_extraction_source("explicit_agent_id")
        
        if "previous_thought_id" in arguments and arguments["previous_thought_id"]:
            context.previous_thought_id = arguments["previous_thought_id"]
            context.add_extraction_source("explicit_previous_thought")
        
        if "step_number" in arguments and arguments["step_number"]:
            context.step_number = arguments["step_number"]
            context.add_extraction_source("explicit_step_number")
        
        if "metadata" in arguments and arguments["metadata"]:
            context.metadata.update(arguments["metadata"])
            context.add_extraction_source("explicit_metadata")
    
    async def _extract_mcp_metadata(self, context: SessionContext, mcp_metadata: Dict[str, Any]) -> None:
        """Extract context from MCP protocol metadata."""
        # Extract client session if available
        if "client_session" in mcp_metadata and not context.session_id:
            context.session_id = mcp_metadata["client_session"]
            context.add_extraction_source("mcp_client_session")
            context.mark_generated("session_id")
        
        # Extract request correlation ID
        if "correlation_id" in mcp_metadata and not context.conversation_id:
            context.conversation_id = mcp_metadata["correlation_id"]
            context.add_extraction_source("mcp_correlation_id")
            context.mark_generated("conversation_id")
        
        # Extract request ID for chain tracking
        if "request_id" in mcp_metadata:
            context.metadata["mcp_request_id"] = mcp_metadata["request_id"]
            context.add_extraction_source("mcp_request_id")
    
    async def _extract_orchestration_context(self, context: SessionContext) -> None:
        """Extract context from orchestration service."""
        try:
            if hasattr(self.orchestration, 'get_current_context'):
                orch_context = await self.orchestration.get_current_context()
                
                if orch_context:
                    if not context.agent_id and "agent_id" in orch_context:
                        context.agent_id = orch_context["agent_id"]
                        context.add_extraction_source("orchestration_agent_id")
                        context.mark_generated("agent_id")
                    
                    if not context.session_id and "session_id" in orch_context:
                        context.session_id = orch_context["session_id"]
                        context.add_extraction_source("orchestration_session_id")
                        context.mark_generated("session_id")
                    
                    if "workflow_id" in orch_context:
                        context.metadata["workflow_id"] = orch_context["workflow_id"]
                        context.add_extraction_source("orchestration_workflow")
        except Exception as e:
            self.logger.debug(f"Orchestration context extraction failed: {e}")
    
    async def _extract_mind_graph_context(self, context: SessionContext) -> None:
        """Extract context from Mind Graph tracking."""
        if not context.session_id and hasattr(self.mcp_base, 'current_session_id'):
            if self.mcp_base.current_session_id:
                context.session_id = self.mcp_base.current_session_id
                context.add_extraction_source("mind_graph_session")
                context.mark_generated("session_id")
        
        if not context.conversation_id and hasattr(self.mcp_base, 'current_conversation_id'):
            if self.mcp_base.current_conversation_id:
                context.conversation_id = self.mcp_base.current_conversation_id
                context.add_extraction_source("mind_graph_conversation")
                context.mark_generated("conversation_id")
        
        if hasattr(self.mcp_base, 'reasoning_chain_id'):
            if self.mcp_base.reasoning_chain_id:
                context.chain_id = self.mcp_base.reasoning_chain_id
                context.add_extraction_source("mind_graph_chain")
        
        if not context.agent_id and hasattr(self.mcp_base, 'agent_id'):
            context.agent_id = self.mcp_base.agent_id
            context.add_extraction_source("mind_graph_agent")
            context.mark_generated("agent_id")
    
    async def _extract_database_context(self, context: SessionContext) -> None:
        """Extract context from database state."""
        if not context.session_id:
            # Query for recent active session
            recent_session = await self._query_recent_session()
            if recent_session:
                context.session_id = recent_session
                context.add_extraction_source("database_recent_session")
                context.mark_generated("session_id")
        
        if context.session_id and not context.previous_thought_id:
            # Query for last thought in session
            last_thought = await self._query_last_thought(context.session_id)
            if last_thought:
                context.previous_thought_id = last_thought["thought_id"]
                context.step_number = last_thought.get("step_number", 0) + 1
                context.add_extraction_source("database_chain_recovery")
                context.mark_generated("previous_thought_id")
    
    async def _generate_missing_fields(self, context: SessionContext, tool_name: str) -> None:
        """Generate any missing required fields."""
        # Generate session_id if missing
        if not context.session_id:
            context.session_id = self.generate_session_id(
                agent_id=context.agent_id or "unknown",
                context_hash=tool_name
            )
            context.add_extraction_source("generated_session_id")
            context.mark_generated("session_id")
        
        # Generate conversation_id if missing
        if not context.conversation_id:
            context.conversation_id = await self.detect_or_generate_conversation_id(
                session_id=context.session_id
            )
            context.add_extraction_source("generated_conversation_id")
            context.mark_generated("conversation_id")
        
        # Generate agent_id if missing
        if not context.agent_id:
            context.agent_id = f"autonomous_{tool_name}_{uuid4().hex[:8]}"
            context.add_extraction_source("generated_agent_id")
            context.mark_generated("agent_id")
        
        # Generate chain_id if missing
        if not context.chain_id:
            context.chain_id = f"chain_{uuid4().hex[:12]}"
            context.add_extraction_source("generated_chain_id")
            context.mark_generated("chain_id")
        
        # Add generation metadata
        context.metadata["autonomous_generation"] = {
            "generated_fields": context.generated_fields,
            "extraction_sources": context.extraction_sources,
            "generation_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def generate_session_id(self, agent_id: str, context_hash: str) -> str:
        """
        Generate a unique session identifier.
        
        Format: session_{timestamp}_{agent_hash}_{context_hash}
        """
        timestamp = int(time.time())
        agent_hash = hashlib.md5(agent_id.encode()).hexdigest()[:8]
        ctx_hash = hashlib.md5(context_hash.encode()).hexdigest()[:4]
        
        return f"session_{timestamp}_{agent_hash}_{ctx_hash}"
    
    def generate_conversation_id(self, session_id: str, sequence: int) -> str:
        """
        Generate a unique conversation identifier.
        
        Format: conv_{timestamp_base36}_{session_hash}_{sequence}
        """
        timestamp_base36 = self._to_base36(int(time.time()))
        session_hash = hashlib.md5(session_id.encode()).hexdigest()[:8]
        
        return f"conv_{timestamp_base36}_{session_hash}_{sequence:03d}"
    
    async def detect_or_generate_conversation_id(self, session_id: str) -> str:
        """
        Detect existing conversation or generate new one.
        
        Checks for recent activity patterns to determine if this is
        a continuation of an existing conversation or a new one.
        """
        # Check cache first
        cached_conv = self._get_cached_conversation(session_id)
        if cached_conv:
            return cached_conv
        
        # Try to detect existing conversation pattern
        existing_conv = await self.detect_conversation_pattern(session_id, datetime.now(timezone.utc))
        if existing_conv:
            return existing_conv
        
        # Generate new conversation ID
        self._sequence_counter += 1
        return self.generate_conversation_id(session_id, self._sequence_counter)
    
    async def detect_conversation_pattern(self, session_id: str, timestamp: datetime) -> Optional[str]:
        """
        Detect existing conversation pattern.
        
        Looks for recent activity within 5 minute window to determine
        if this is part of an ongoing conversation.
        """
        if not self.db_manager:
            return None
        
        try:
            # Look for thoughts in the session within 5 minute window
            five_minutes_ago = (timestamp.timestamp() - 300)
            
            query = """
            SELECT DISTINCT metadata 
            FROM sequential_thoughts 
            WHERE session_id = ? 
            AND created_at > ?
            ORDER BY created_at DESC
            LIMIT 10
            """
            
            result = await self.db_manager.execute_query(query, (session_id, five_minutes_ago))
            if result:
                # Look for existing conversation_id in metadata
                for row in result:
                    metadata_str = row.get('metadata', '{}')
                    try:
                        import json
                        metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
                        if isinstance(metadata, dict) and 'conversation_id' in metadata:
                            conv_id = metadata['conversation_id']
                            self.logger.debug(f"Detected existing conversation: {conv_id}")
                            return conv_id
                    except (json.JSONDecodeError, TypeError) as e:
                        self.logger.debug(f"Failed to parse metadata for conversation detection: {e}")
                        continue
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Conversation pattern detection failed: {e}")
            return None
    
    async def recover_chain_context(self, session_id: str, step_number: int) -> Optional[Dict[str, Any]]:
        """
        Recover broken chain context from database.
        
        Attempts to reconstruct chain context when previous_thought_id
        is missing but step_number > 1.
        """
        if not self.db_manager or not session_id or step_number <= 1:
            return None
        
        try:
            # Query for the thought at step_number - 1
            query = """
            SELECT ulid_id, step_number, thought_type, metadata, created_at
            FROM sequential_thoughts 
            WHERE session_id = ? 
            AND step_number = ?
            ORDER BY created_at DESC 
            LIMIT 1
            """
            
            target_step = step_number - 1
            result = await self.db_manager.execute_query(query, (session_id, target_step))
            
            if result and len(result) > 0:
                thought_data = result[0]
                recovery_context = {
                    "previous_thought_id": thought_data.get('ulid_id'),
                    "previous_step_number": thought_data.get('step_number'),
                    "previous_thought_type": thought_data.get('thought_type'),
                    "recovery_timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # Try to extract conversation context from metadata
                metadata_str = thought_data.get('metadata', '{}')
                try:
                    import json
                    metadata = json.loads(metadata_str) if isinstance(metadata_str, str) else metadata_str
                    if isinstance(metadata, dict):
                        if 'conversation_id' in metadata:
                            recovery_context['conversation_id'] = metadata['conversation_id']
                        if 'chain_id' in metadata:
                            recovery_context['chain_id'] = metadata['chain_id']
                except (json.JSONDecodeError, TypeError) as e:
                    self.logger.debug(f"Could not extract metadata from recovered thought: {e}")
                
                self.logger.info(f"Chain recovery successful: found previous thought {recovery_context['previous_thought_id']} at step {target_step}")
                return recovery_context
            
            # If exact step not found, try to find the most recent thought
            query_latest = """
            SELECT ulid_id, step_number, thought_type, metadata, created_at
            FROM sequential_thoughts 
            WHERE session_id = ? 
            AND step_number < ?
            ORDER BY step_number DESC, created_at DESC 
            LIMIT 1
            """
            
            result_latest = await self.db_manager.execute_query(query_latest, (session_id, step_number))
            if result_latest and len(result_latest) > 0:
                thought_data = result_latest[0]
                recovery_context = {
                    "previous_thought_id": thought_data.get('ulid_id'),
                    "previous_step_number": thought_data.get('step_number'),
                    "recovery_type": "approximate",
                    "recovery_timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                self.logger.warning(f"Chain recovery: approximate recovery using step {thought_data.get('step_number')} for requested step {step_number}")
                return recovery_context
            
            return None
            
        except Exception as e:
            self.logger.error(f"Chain recovery failed: {e}")
            return None
    
    def _validate_context(self, context: SessionContext) -> bool:
        """Validate extracted context for completeness and consistency."""
        validation_errors = []
        
        # Required field validation
        if not context.session_id:
            validation_errors.append("missing session_id")
        
        if not context.conversation_id:
            validation_errors.append("missing conversation_id")
        
        # Step number consistency validation
        if context.step_number < 1:
            context.step_number = 1
            self.logger.debug("Context validation: adjusted step_number to 1")
        
        # Chain consistency validation
        if context.step_number > 1 and not context.previous_thought_id:
            self.logger.warning(f"Chain consistency issue: step {context.step_number} without previous_thought_id")
            # Don't fail validation - this will trigger chain recovery
        
        # Session ID format validation
        if context.session_id and not self._is_valid_session_id(context.session_id):
            validation_errors.append(f"invalid session_id format: {context.session_id}")
        
        # Conversation ID format validation  
        if context.conversation_id and not self._is_valid_conversation_id(context.conversation_id):
            validation_errors.append(f"invalid conversation_id format: {context.conversation_id}")
        
        # Atomic transaction compatibility validation
        atomic_check = self._validate_atomic_compatibility(context)
        if not atomic_check['valid']:
            validation_errors.extend(atomic_check['errors'])
        
        # Parameter consistency cross-validation
        consistency_check = self._validate_parameter_consistency(context)
        if not consistency_check['valid']:
            validation_errors.extend(consistency_check['errors'])
        
        if validation_errors:
            self.logger.warning(f"Context validation failed: {', '.join(validation_errors)}")
            return False
        
        return True
    
    def _cache_context(self, context: SessionContext) -> None:
        """Cache context for quick reuse."""
        cache_key = f"{context.session_id}:{context.conversation_id}"
        self._context_cache[cache_key] = (context, time.time())
        
        # Clean expired cache entries
        self._clean_cache()
    
    def _get_cached_conversation(self, session_id: str) -> Optional[str]:
        """Get cached conversation ID for session."""
        current_time = time.time()
        
        for cache_key, (context, timestamp) in self._context_cache.items():
            if context.session_id == session_id:
                if current_time - timestamp < self._cache_ttl:
                    return context.conversation_id
        
        return None
    
    def _clean_cache(self) -> None:
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._context_cache.items()
            if current_time - timestamp > self._cache_ttl
        ]
        
        for key in expired_keys:
            del self._context_cache[key]
    
    async def _query_recent_session(self) -> Optional[str]:
        """Query database for recent active session."""
        if not self.db_manager:
            return None
        
        try:
            # Query SQLite for most recent session within last 5 minutes
            current_time = datetime.now(timezone.utc)
            five_minutes_ago = current_time.timestamp() - 300
            
            # Use database manager's execute method
            query = """
            SELECT DISTINCT session_id 
            FROM sequential_thoughts 
            WHERE created_at > ? 
            ORDER BY created_at DESC 
            LIMIT 1
            """
            
            result = await self.db_manager.execute_query(query, (five_minutes_ago,))
            if result and len(result) > 0:
                session_id = result[0].get('session_id')
                self.logger.debug(f"Found recent session: {session_id}")
                return session_id
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Recent session query failed: {e}")
            return None
    
    async def _query_last_thought(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Query database for last thought in session."""
        if not self.db_manager or not session_id:
            return None
        
        try:
            # Query SQLite for most recent thought in session
            query = """
            SELECT ulid_id, step_number, thought_type, created_at
            FROM sequential_thoughts 
            WHERE session_id = ? 
            ORDER BY step_number DESC, created_at DESC 
            LIMIT 1
            """
            
            result = await self.db_manager.execute_query(query, (session_id,))
            if result and len(result) > 0:
                thought_data = result[0]
                self.logger.debug(f"Found last thought in session {session_id}: step {thought_data.get('step_number')}")
                return {
                    "thought_id": thought_data.get('ulid_id'),
                    "step_number": thought_data.get('step_number', 0),
                    "thought_type": thought_data.get('thought_type'),
                    "created_at": thought_data.get('created_at')
                }
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Last thought query failed: {e}")
            return None
    
    def _to_base36(self, num: int) -> str:
        """Convert integer to base36 string for compact representation."""
        chars = "0123456789abcdefghijklmnopqrstuvwxyz"
        result = ""
        
        while num > 0:
            num, remainder = divmod(num, 36)
            result = chars[remainder] + result
        
        return result or "0"
    
    def _is_valid_session_id(self, session_id: str) -> bool:
        """Validate session ID format for consistency."""
        if not session_id or not isinstance(session_id, str):
            return False
        
        # Accept various session ID formats
        valid_patterns = [
            r'^session_\d+_[a-f0-9]{8}_[a-f0-9]{4}$',  # Generated format
            r'^session_[a-zA-Z0-9_-]+$',  # Generic session format
            r'^[a-zA-Z0-9_-]{8,64}$'  # Generic ID format
        ]
        
        import re
        return any(re.match(pattern, session_id) for pattern in valid_patterns)
    
    def _is_valid_conversation_id(self, conv_id: str) -> bool:
        """Validate conversation ID format for consistency."""
        if not conv_id or not isinstance(conv_id, str):
            return False
        
        # Accept various conversation ID formats
        valid_patterns = [
            r'^conv_[a-z0-9]+_[a-f0-9]{8}_\d{3}$',  # Generated format
            r'^conversation_[a-zA-Z0-9_-]+$',  # Explicit format
            r'^conv_[a-zA-Z0-9_-]+$',  # Generic conv format
            r'^[a-zA-Z0-9_-]{8,64}$'  # Generic ID format
        ]
        
        import re
        return any(re.match(pattern, conv_id) for pattern in valid_patterns)
    
    def _validate_atomic_compatibility(self, context: SessionContext) -> Dict[str, Any]:
        """Validate parameters for atomic transaction compatibility."""
        validation_result = {"valid": True, "errors": []}
        
        # Check for fields that could cause transaction conflicts
        if context.session_id and len(context.session_id) > 255:
            validation_result["errors"].append("session_id too long for database constraint")
        
        if context.conversation_id and len(context.conversation_id) > 255:
            validation_result["errors"].append("conversation_id too long for database constraint")
        
        if context.agent_id and len(context.agent_id) > 255:
            validation_result["errors"].append("agent_id too long for database constraint")
        
        # Validate metadata for database storage compatibility
        try:
            import json
            metadata_json = json.dumps(context.metadata)
            if len(metadata_json) > 10000:  # 10KB limit
                validation_result["errors"].append("metadata too large for efficient storage")
        except (TypeError, ValueError) as e:
            validation_result["errors"].append(f"metadata not JSON serializable: {e}")
        
        # Check for potential SQL injection patterns (basic check)
        dangerous_patterns = [';', '--', '/*', '*/', 'DROP', 'DELETE', 'UPDATE', 'INSERT']
        for field_name, field_value in [
            ('session_id', context.session_id),
            ('conversation_id', context.conversation_id),
            ('agent_id', context.agent_id),
            ('previous_thought_id', context.previous_thought_id),
            ('chain_id', context.chain_id)
        ]:
            if field_value and isinstance(field_value, str):
                for pattern in dangerous_patterns:
                    if pattern.upper() in field_value.upper():
                        validation_result["errors"].append(f"potentially dangerous pattern in {field_name}")
                        break
        
        if validation_result["errors"]:
            validation_result["valid"] = False
        
        return validation_result
    
    def _validate_parameter_consistency(self, context: SessionContext) -> Dict[str, Any]:
        """Validate parameter consistency across different sources."""
        validation_result = {"valid": True, "errors": []}
        
        # Step number consistency with chain linkage
        if context.step_number == 1 and context.previous_thought_id:
            validation_result["errors"].append("step_number=1 inconsistent with previous_thought_id presence")
        
        if context.step_number > 1 and not context.previous_thought_id:
            # This is a warning, not an error - chain recovery will handle it
            self.logger.debug(f"Step {context.step_number} without previous_thought_id - will trigger chain recovery")
        
        # Conversation and session consistency
        if context.conversation_id and context.session_id:
            # Check if conversation_id contains session reference (for generated IDs)
            if 'conv_' in context.conversation_id and context.session_id not in context.conversation_id:
                # This is acceptable - conversation IDs don't have to contain session info
                pass
        
        # Generation consistency
        if 'session_id' in context.generated_fields and not context.session_id:
            validation_result["errors"].append("session_id marked as generated but missing")
        
        if 'conversation_id' in context.generated_fields and not context.conversation_id:
            validation_result["errors"].append("conversation_id marked as generated but missing")
        
        # Source consistency
        if not context.extraction_sources:
            validation_result["errors"].append("no extraction sources recorded")
        
        # Timestamp consistency
        if context.timestamp and context.timestamp > datetime.now(timezone.utc):
            validation_result["errors"].append("context timestamp is in the future")
        
        if validation_result["errors"]:
            validation_result["valid"] = False
        
        return validation_result
    
    # MCPContextExtractor Methods - Intelligent Context Inference
    
    def extract_caller_context(self, arguments: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        """
        Extract caller context from MCP request patterns.
        
        Intelligently detects calling agent, tool context, and request patterns
        to provide better context for autonomous parameter generation.
        """
        caller_context = {
            "caller_type": "unknown",
            "caller_agent": None,
            "request_pattern": "single",
            "context_hints": []
        }
        
        # Detect agent from metadata patterns
        if "metadata" in arguments:
            metadata = arguments["metadata"]
            if isinstance(metadata, dict):
                # Look for agent identification in metadata
                if "agent_id" in metadata:
                    caller_context["caller_agent"] = metadata["agent_id"]
                    caller_context["caller_type"] = "identified_agent"
                    caller_context["context_hints"].append("explicit_agent_metadata")
                
                if "autonomous_generation" in metadata:
                    caller_context["caller_type"] = "autonomous_agent"
                    caller_context["context_hints"].append("autonomous_reasoning")
                
                if "handoff_from_agent" in metadata:
                    caller_context["caller_type"] = "handoff_agent"
                    caller_context["caller_agent"] = metadata["handoff_from_agent"]
                    caller_context["context_hints"].append("agent_handoff")
        
        # Detect request pattern from parameters
        if "step_number" in arguments and arguments["step_number"] > 1:
            caller_context["request_pattern"] = "sequential"
            caller_context["context_hints"].append("sequential_reasoning")
        
        if "previous_thought_id" in arguments:
            caller_context["request_pattern"] = "chain_continuation"
            caller_context["context_hints"].append("chain_continuation")
        
        # Detect tool context patterns
        if tool_name == "sequential_thinking":
            caller_context["context_hints"].append("reasoning_tool")
            if "autonomous" in str(arguments.get("action", "")):
                caller_context["context_hints"].append("autonomous_invocation")
        
        # Detect conversation continuation patterns
        conversation_indicators = ["conversation_id", "session_id", "chain_id"]
        for indicator in conversation_indicators:
            if indicator in arguments and arguments[indicator]:
                caller_context["context_hints"].append(f"explicit_{indicator}")
                # Store explicit conversation_id for special handling
                if indicator == "conversation_id":
                    caller_context["explicit_conversation_id"] = arguments[indicator]
        
        return caller_context
    
    def infer_context_from_patterns(self, arguments: Dict[str, Any], caller_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Infer additional context using pattern recognition and intelligence.
        
        Uses the caller context and argument patterns to make intelligent
        inferences about missing context parameters.
        """
        inferred_context = {
            "confidence": 0.0,
            "inferences": {},
            "reasoning": []
        }
        
        # High confidence inferences
        if caller_context["request_pattern"] == "chain_continuation":
            if "previous_thought_id" in arguments:
                inferred_context["inferences"]["session_continuation"] = True
                inferred_context["reasoning"].append("Chain continuation implies session continuation")
                inferred_context["confidence"] += 0.3
        
        if caller_context["caller_type"] == "handoff_agent":
            inferred_context["inferences"]["conversation_continuation"] = True
            inferred_context["reasoning"].append("Agent handoff implies conversation continuation")
            inferred_context["confidence"] += 0.4
        
        # Medium confidence inferences
        if "sequential_reasoning" in caller_context["context_hints"]:
            inferred_context["inferences"]["incremental_step"] = True
            inferred_context["reasoning"].append("Sequential reasoning suggests incremental step pattern")
            inferred_context["confidence"] += 0.2
        
        if "autonomous_reasoning" in caller_context["context_hints"]:
            inferred_context["inferences"]["auto_context_needed"] = True
            inferred_context["reasoning"].append("Autonomous reasoning requires full context extraction")
            inferred_context["confidence"] += 0.2
        
        # Content-based inferences
        content = arguments.get("content", "")
        if isinstance(content, str):
            # Detect problem-solving patterns
            problem_keywords = ["problem", "issue", "challenge", "goal", "objective", "need to"]
            if any(keyword.lower() in content.lower() for keyword in problem_keywords):
                inferred_context["inferences"]["problem_solving"] = True
                inferred_context["reasoning"].append("Content suggests problem-solving context")
                inferred_context["confidence"] += 0.1
            
            # Detect conclusion patterns
            conclusion_keywords = ["therefore", "conclusion", "result", "finally", "in summary", "to conclude"]
            if any(keyword.lower() in content.lower() for keyword in conclusion_keywords):
                inferred_context["inferences"]["reasoning_conclusion"] = True
                inferred_context["reasoning"].append("Content suggests reasoning conclusion")
                inferred_context["confidence"] += 0.1
        
        # Normalize confidence
        inferred_context["confidence"] = min(1.0, inferred_context["confidence"])
        
        return inferred_context
    
    def apply_intelligent_defaults(self, context: SessionContext, caller_context: Dict[str, Any], 
                                 inferred_context: Dict[str, Any]) -> SessionContext:
        """
        Apply intelligent defaults based on caller and inferred context.
        
        Uses the extracted caller context and pattern inferences to set
        intelligent defaults that maintain reasoning chain integrity.
        """
        # Apply agent-based defaults
        if caller_context["caller_type"] == "handoff_agent" and not context.agent_id:
            # For handoffs, generate a new agent ID but reference the handoff
            context.agent_id = f"handoff_agent_{uuid4().hex[:8]}"
            context.metadata["handoff_source"] = caller_context["caller_agent"]
            context.mark_generated("agent_id")
            context.add_extraction_source("handoff_agent_inference")
        
        # Apply step number intelligence
        if inferred_context["inferences"].get("incremental_step") and context.step_number == 1:
            # If we have strong evidence of sequential reasoning but step=1, 
            # check if we should increment
            if context.previous_thought_id or inferred_context["inferences"].get("session_continuation"):
                context.step_number = 2  # Minimum for continuation
                context.mark_generated("step_number")
                context.add_extraction_source("sequential_inference")
        
        # Apply conversation continuity intelligence
        if inferred_context["inferences"].get("conversation_continuation"):
            if not context.conversation_id and context.session_id:
                # Generate conversation ID with continuation pattern
                context.conversation_id = f"conv_continue_{uuid4().hex[:8]}"
                context.mark_generated("conversation_id")
                context.add_extraction_source("conversation_continuation_inference")
        
        # Handle explicit conversation_id that was passed directly (not in standard location)
        if not context.conversation_id and caller_context.get("explicit_conversation_id"):
            context.conversation_id = caller_context["explicit_conversation_id"]
            context.add_extraction_source("explicit_conversation_id_relocated")
            self.logger.debug(f"Applied explicit conversation_id from caller context: {context.conversation_id}")
        
        # Apply problem-solving context
        if inferred_context["inferences"].get("problem_solving"):
            context.metadata["reasoning_type"] = "problem_solving"
            context.add_extraction_source("problem_solving_inference")
        
        if inferred_context["inferences"].get("reasoning_conclusion"):
            context.metadata["reasoning_type"] = "conclusion"
            context.add_extraction_source("conclusion_inference")
        
        # Add inference metadata
        context.metadata["context_intelligence"] = {
            "caller_context": caller_context,
            "inferred_context": inferred_context,
            "confidence_score": inferred_context["confidence"],
            "applied_reasoning": inferred_context["reasoning"]
        }
        
        return context
    
    def _calculate_confidence(self, context: SessionContext) -> float:
        """
        Calculate confidence level based on extraction sources and completeness.
        
        Args:
            context: The session context to evaluate
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.0
        
        # High confidence sources (0.2 each)
        high_confidence_sources = [
            "explicit_session_id",
            "explicit_conversation_id",
            "explicit_agent_id",
            "explicit_previous_thought",
            "explicit_metadata"
        ]
        
        # Medium confidence sources (0.15 each)
        medium_confidence_sources = [
            "mind_graph_session",
            "mind_graph_conversation",
            "mind_graph_agent",
            "orchestration_session_id",
            "orchestration_agent_id",
            "database_existing_session"
        ]
        
        # Low confidence sources (0.1 each)
        low_confidence_sources = [
            "generated_session_id",
            "generated_conversation_id",
            "generated_agent_id",
            "generated_chain_id",
            "chain_recovery",
            "inference"
        ]
        
        # Calculate confidence from sources
        for source in context.extraction_sources:
            if any(high_src in source for high_src in high_confidence_sources):
                confidence += 0.2
            elif any(med_src in source for med_src in medium_confidence_sources):
                confidence += 0.15
            elif any(low_src in source for low_src in low_confidence_sources):
                confidence += 0.1
            else:
                confidence += 0.05  # Unknown source
        
        # Bonus for complete context
        if context.is_complete():
            confidence += 0.2
        
        # Bonus for chain continuity
        if context.previous_thought_id and context.step_number > 1:
            confidence += 0.1
        
        # Cap at 1.0
        confidence = min(1.0, confidence)
        
        # Check for inference confidence in metadata
        if context.metadata and "context_intelligence" in context.metadata:
            inferred_confidence = context.metadata["context_intelligence"].get("confidence_score", 0.0)
            # Average with inferred confidence if available
            confidence = (confidence + inferred_confidence) / 2
        
        return round(confidence, 2)