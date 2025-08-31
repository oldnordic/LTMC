"""
Autonomous AI Reasoning System
Complete implementation integrating context intelligence, parameter generation,
and recursion control for fully autonomous thought creation.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

from .recursion_control import RecursionControlSystem, SafetyValidationSystem, RecursionState
from ltms.database.sync_coordinator import DatabaseSyncCoordinator
from ltms.database.atomic_transaction_context import AtomicTxContext

logger = logging.getLogger(__name__)


@dataclass
class AutonomousContext:
    """Context for autonomous reasoning operations"""
    session_id: str
    conversation_history: List[str] = field(default_factory=list)
    current_intent: Optional[str] = None
    reasoning_pattern: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    previous_thought_id: Optional[str] = None
    step_number: int = 1
    depth: int = 0
    performance_metrics: Dict[str, float] = field(default_factory=dict)


class MCPContextExtractor:
    """
    Extract context from MCP protocol communications for autonomous reasoning.
    """
    
    def __init__(self):
        self.context_cache: Dict[str, AutonomousContext] = {}
        self.pattern_detection_window = 5
        
    async def analyze_conversation_context(self, 
                                          raw_content: str,
                                          session_id: Optional[str] = None) -> AutonomousContext:
        """
        Analyze conversation context from MCP communication.
        
        Args:
            raw_content: Raw content from MCP protocol
            session_id: Optional session identifier
            
        Returns:
            Extracted autonomous context
        """
        start_time = time.time()
        
        # Generate session ID if not provided
        if not session_id:
            session_id = self._generate_session_id(raw_content)
        
        # Get or create context
        if session_id in self.context_cache:
            context = self.context_cache[session_id]
        else:
            context = AutonomousContext(session_id=session_id)
            self.context_cache[session_id] = context
        
        # Add to conversation history
        context.conversation_history.append(raw_content)
        
        # Infer intent from content
        context.current_intent = await self.infer_reasoning_intent(raw_content)
        
        # Detect reasoning patterns
        context.reasoning_pattern = await self.detect_reasoning_patterns(
            context.conversation_history
        )
        
        # Update performance metrics
        context.performance_metrics["context_extraction_ms"] = (time.time() - start_time) * 1000
        
        return context
    
    async def infer_reasoning_intent(self, content: str) -> str:
        """
        Infer the reasoning intent from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Inferred intent type
        """
        content_lower = content.lower()
        
        # Pattern-based intent detection
        if any(word in content_lower for word in ["analyze", "evaluate", "assess"]):
            return "analytical"
        elif any(word in content_lower for word in ["solve", "fix", "resolve"]):
            return "problem_solving"
        elif any(word in content_lower for word in ["create", "generate", "build"]):
            return "creative"
        elif any(word in content_lower for word in ["explain", "describe", "clarify"]):
            return "explanatory"
        elif any(word in content_lower for word in ["compare", "contrast", "difference"]):
            return "comparative"
        else:
            return "exploratory"
    
    async def detect_reasoning_patterns(self, history: List[str]) -> str:
        """
        Detect reasoning patterns from conversation history.
        
        Args:
            history: Conversation history
            
        Returns:
            Detected pattern type
        """
        if len(history) < 2:
            return "initial"
        
        # Analyze recent history for patterns
        recent = history[-self.pattern_detection_window:]
        
        # Check for iterative refinement
        if self._has_iterative_pattern(recent):
            return "iterative_refinement"
        
        # Check for exploratory branching
        if self._has_branching_pattern(recent):
            return "exploratory_branching"
        
        # Check for convergent thinking
        if self._has_convergent_pattern(recent):
            return "convergent_synthesis"
        
        return "sequential_progression"
    
    def _has_iterative_pattern(self, recent: List[str]) -> bool:
        """Check for iterative refinement pattern"""
        # Look for similar content with incremental changes
        if len(recent) < 2:
            return False
        
        similarities = []
        for i in range(1, len(recent)):
            sim = self._content_similarity(recent[i-1], recent[i])
            similarities.append(sim)
        
        # High similarity suggests iteration
        return sum(similarities) / len(similarities) > 0.7
    
    def _has_branching_pattern(self, recent: List[str]) -> bool:
        """Check for exploratory branching pattern"""
        # Look for diverse content exploring different aspects
        if len(recent) < 3:
            return False
        
        diversities = []
        for i in range(1, len(recent)):
            div = 1.0 - self._content_similarity(recent[i-1], recent[i])
            diversities.append(div)
        
        # High diversity suggests branching
        return sum(diversities) / len(diversities) > 0.5
    
    def _has_convergent_pattern(self, recent: List[str]) -> bool:
        """Check for convergent synthesis pattern"""
        # Look for content that references multiple previous points
        if len(recent) < 3:
            return False
        
        last_content = recent[-1].lower()
        references = 0
        
        for prev in recent[:-1]:
            # Check if recent content references previous content
            key_words = set(prev.lower().split())
            if len(key_words.intersection(set(last_content.split()))) > 5:
                references += 1
        
        return references >= 2
    
    def _content_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two content strings"""
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _generate_session_id(self, content: str) -> str:
        """Generate session ID from content"""
        timestamp = str(time.time())
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
        return f"auto_{timestamp}_{content_hash}"


class SessionContextExtractor:
    """
    Extract and manage session context for autonomous reasoning.
    """
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_chains: Dict[str, List[str]] = {}  # Session -> thought chain
        
    async def create_or_retrieve_session(self, context: AutonomousContext) -> str:
        """
        Create or retrieve session for autonomous reasoning.
        
        Args:
            context: Autonomous context
            
        Returns:
            Session identifier
        """
        session_id = context.session_id
        
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                "created_at": datetime.utcnow().isoformat(),
                "intent": context.current_intent,
                "pattern": context.reasoning_pattern,
                "thought_count": 0
            }
            self.session_chains[session_id] = []
            logger.info(f"Created new autonomous session: {session_id}")
        
        return session_id
    
    async def link_to_previous_thought(self, session_id: str) -> Optional[str]:
        """
        Get previous thought ID for linking.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Previous thought ID if exists
        """
        if session_id in self.session_chains:
            chain = self.session_chains[session_id]
            if chain:
                return chain[-1]
        return None
    
    async def maintain_chain_continuity(self, session_id: str,
                                       thought_id: str) -> Dict[str, Any]:
        """
        Maintain chain continuity for session.
        
        Args:
            session_id: Session identifier
            thought_id: New thought identifier
            
        Returns:
            Chain continuity information
        """
        if session_id not in self.session_chains:
            self.session_chains[session_id] = []
        
        chain = self.session_chains[session_id]
        chain.append(thought_id)
        
        # Update session info
        if session_id in self.active_sessions:
            self.active_sessions[session_id]["thought_count"] += 1
            self.active_sessions[session_id]["last_thought_id"] = thought_id
            self.active_sessions[session_id]["last_updated"] = datetime.utcnow().isoformat()
        
        return {
            "session_id": session_id,
            "chain_length": len(chain),
            "previous_thought_id": chain[-2] if len(chain) > 1 else None,
            "current_thought_id": thought_id
        }
    
    async def detect_session_boundaries(self, context: AutonomousContext) -> bool:
        """
        Detect if a new session should be started.
        
        Args:
            context: Autonomous context
            
        Returns:
            True if new session should be started
        """
        session_id = context.session_id
        
        # Check if session exists
        if session_id not in self.active_sessions:
            return True
        
        session_info = self.active_sessions[session_id]
        
        # Check for intent change
        if session_info.get("intent") != context.current_intent:
            logger.info(f"Intent change detected for session {session_id}")
            return True
        
        # Check for pattern change (significant shift in reasoning)
        if session_info.get("pattern") != context.reasoning_pattern:
            if context.reasoning_pattern == "initial":
                return False  # Don't create new session for initial pattern
            logger.info(f"Pattern change detected for session {session_id}")
            return True
        
        # Check for long chains (prevent infinite chains)
        if session_info.get("thought_count", 0) > 50:
            logger.warning(f"Session {session_id} exceeds 50 thoughts, consider new session")
            return True
        
        return False


class MetadataGenerator:
    """
    Generate rich metadata for autonomous reasoning operations.
    """
    
    def __init__(self):
        self.performance_tracker: Dict[str, List[float]] = {}
        
    async def generate_reasoning_metadata(self, 
                                         content: str,
                                         context: AutonomousContext) -> Dict[str, Any]:
        """
        Generate comprehensive metadata for reasoning.
        
        Args:
            content: Reasoning content
            context: Autonomous context
            
        Returns:
            Generated metadata
        """
        metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "session_id": context.session_id,
            "intent": context.current_intent,
            "reasoning_pattern": context.reasoning_pattern,
            "depth": context.depth,
            "step_number": context.step_number,
            "content_length": len(content),
            "content_hash": hashlib.sha256(content.encode()).hexdigest()[:16],
            "autonomous": True,
            "context_metrics": context.performance_metrics
        }
        
        # Add reasoning classification
        metadata["reasoning_class"] = await self.classify_reasoning_pattern(content)
        
        # Add performance metrics
        metadata["performance"] = await self.extract_performance_metrics(context.session_id)
        
        # Enrich with contextual data
        metadata = await self.enrich_with_contextual_data(metadata, context)
        
        return metadata
    
    async def classify_reasoning_pattern(self, content: str) -> str:
        """
        Classify the reasoning pattern from content.
        
        Args:
            content: Content to classify
            
        Returns:
            Reasoning classification
        """
        content_lower = content.lower()
        
        # Check for different reasoning types
        if "therefore" in content_lower or "thus" in content_lower:
            return "deductive"
        elif "probably" in content_lower or "likely" in content_lower:
            return "probabilistic"
        elif "if" in content_lower and "then" in content_lower:
            return "conditional"
        elif "because" in content_lower or "due to" in content_lower:
            return "causal"
        elif "similar" in content_lower or "like" in content_lower:
            return "analogical"
        else:
            return "exploratory"
    
    async def extract_performance_metrics(self, session_id: str) -> Dict[str, float]:
        """
        Extract performance metrics for session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Performance metrics
        """
        if session_id not in self.performance_tracker:
            self.performance_tracker[session_id] = []
        
        current_time = time.time()
        self.performance_tracker[session_id].append(current_time)
        
        # Calculate metrics
        timestamps = self.performance_tracker[session_id]
        
        metrics = {
            "total_operations": len(timestamps),
            "avg_interval_ms": 0,
            "operations_per_second": 0
        }
        
        if len(timestamps) > 1:
            intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
            metrics["avg_interval_ms"] = (sum(intervals) / len(intervals)) * 1000
            
            # Operations per second in last minute
            recent = [t for t in timestamps if current_time - t < 60]
            if recent:
                metrics["operations_per_second"] = len(recent) / 60
        
        return metrics
    
    async def enrich_with_contextual_data(self, 
                                         metadata: Dict[str, Any],
                                         context: AutonomousContext) -> Dict[str, Any]:
        """
        Enrich metadata with contextual information.
        
        Args:
            metadata: Base metadata
            context: Autonomous context
            
        Returns:
            Enriched metadata
        """
        # Add conversation context
        if context.conversation_history:
            metadata["conversation_depth"] = len(context.conversation_history)
            metadata["conversation_started"] = context.conversation_history[0][:100]
        
        # Add previous thought reference
        if context.previous_thought_id:
            metadata["previous_thought_id"] = context.previous_thought_id
            metadata["chain_continuity"] = True
        else:
            metadata["chain_continuity"] = False
        
        # Add any custom metadata from context
        if context.metadata:
            metadata["custom_context"] = context.metadata
        
        return metadata


class AutonomousReasoningCoordinator:
    """
    Main coordinator for autonomous AI reasoning operations.
    Integrates all components for fully autonomous thought creation.
    """
    
    def __init__(self, 
                 db_sync_coordinator: DatabaseSyncCoordinator,
                 max_recursion_depth: int = 10,
                 performance_target_ms: float = 200.0):
        """
        Initialize autonomous reasoning coordinator.
        
        Args:
            db_sync_coordinator: Database synchronization coordinator
            max_recursion_depth: Maximum recursion depth
            performance_target_ms: Target performance in milliseconds
        """
        self.db_coordinator = db_sync_coordinator
        self.performance_target_ms = performance_target_ms
        
        # Initialize components
        self.context_extractor = MCPContextExtractor()
        self.session_extractor = SessionContextExtractor()
        self.metadata_generator = MetadataGenerator()
        
        # Initialize safety systems
        self.recursion_control = RecursionControlSystem(
            max_depth=max_recursion_depth,
            warning_threshold=int(max_recursion_depth * 0.7),
            max_overhead_ms=5.0
        )
        self.safety_validation = SafetyValidationSystem(
            max_memory_mb=100.0,
            max_concurrent_operations=50
        )
        
        logger.info(f"AutonomousReasoningCoordinator initialized with "
                   f"max_depth={max_recursion_depth}, target_ms={performance_target_ms}")
    
    async def autonomous_thought_create(self, content: str,
                                       session_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Create thought with fully autonomous parameter generation.
        No manual parameters required - everything is inferred intelligently.
        
        Args:
            content: The reasoning content (only required parameter)
            session_hint: Optional hint for session identification
            
        Returns:
            Complete reasoning result with auto-generated context
        """
        start_time = time.time()
        result = {
            "success": False,
            "thought_id": None,
            "session_id": None,
            "metadata": {},
            "performance_ms": 0,
            "safety_status": {},
            "error": None
        }
        
        try:
            # Phase 1: Context Analysis
            context = await self.context_extractor.analyze_conversation_context(
                content, session_hint
            )
            
            # Phase 2: Session Management
            session_id = await self.session_extractor.create_or_retrieve_session(context)
            result["session_id"] = session_id
            
            # Check session boundaries
            if await self.session_extractor.detect_session_boundaries(context):
                logger.info(f"Session boundary detected, creating new session")
                context.session_id = f"{session_id}_new_{int(time.time())}"
                session_id = await self.session_extractor.create_or_retrieve_session(context)
                result["session_id"] = session_id
            
            # Get previous thought for linking
            previous_thought_id = await self.session_extractor.link_to_previous_thought(session_id)
            context.previous_thought_id = previous_thought_id
            
            # Phase 3: Safety Validation
            is_valid, error_msg = await self.safety_validation.validate_reasoning_input(
                content, context.metadata, session_id
            )
            if not is_valid:
                result["error"] = f"Safety validation failed: {error_msg}"
                return result
            
            # Check resource limits
            allowed, limit_error = await self.safety_validation.enforce_resource_limits(
                session_id, "thought_create"
            )
            if not allowed:
                result["error"] = f"Resource limit exceeded: {limit_error}"
                return result
            
            # Phase 4: Recursion Control
            depth, recursion_state = await self.recursion_control.track_reasoning_depth(
                session_id, f"thought_{int(time.time())}", content, previous_thought_id
            )
            context.depth = depth
            
            # Check recursion limits
            if recursion_state == RecursionState.BLOCKED:
                result["error"] = "Recursion limit exceeded - operation blocked"
                result["safety_status"] = {
                    "recursion_state": recursion_state.value,
                    "depth": depth
                }
                return result
            
            # Enforce depth limits if needed
            enforcement = await self.recursion_control.enforce_depth_limits(session_id, depth)
            if enforcement["enforced"]:
                logger.warning(f"Depth limit enforced: {enforcement['message']}")
                if enforcement["action"] == "blocked":
                    result["error"] = enforcement["message"]
                    return result
            
            # Phase 5: Metadata Generation
            metadata = await self.metadata_generator.generate_reasoning_metadata(
                content, context
            )
            result["metadata"] = metadata
            
            # Phase 6: Determine thought type based on context
            thought_type = self._determine_thought_type(context)
            
            # Phase 7: Create thought with autonomous parameters
            thought_data = {
                "session_id": session_id,
                "content": content,
                "metadata": metadata,
                "previous_thought_id": previous_thought_id,
                "thought_type": thought_type,
                "step_number": context.step_number
            }
            
            # Use atomic transaction for database consistency
            async with AtomicTxContext(self.db_coordinator) as tx_context:
                # Store thought atomically across all databases
                thought_result = await self._store_thought_atomically(
                    thought_data, tx_context
                )
                
                if thought_result["success"]:
                    result["thought_id"] = thought_result["thought_id"]
                    result["success"] = True
                    
                    # Update chain continuity
                    await self.session_extractor.maintain_chain_continuity(
                        session_id, thought_result["thought_id"]
                    )
                else:
                    raise Exception(f"Failed to store thought: {thought_result.get('error')}")
            
            # Phase 8: Performance optimization check
            performance_ms = (time.time() - start_time) * 1000
            result["performance_ms"] = performance_ms
            
            if performance_ms > self.performance_target_ms:
                logger.warning(f"Performance target missed: {performance_ms:.2f}ms > {self.performance_target_ms}ms")
                
                # Optimize reasoning path for future operations
                optimization = await self.recursion_control.optimize_reasoning_path(session_id)
                result["optimization_suggestions"] = optimization.get("optimizations", [])
            
            # Update safety status
            result["safety_status"] = {
                "recursion_state": recursion_state.value,
                "depth": depth,
                "resource_usage": await self.safety_validation.get_safety_metrics(session_id),
                "recursion_metrics": await self.recursion_control.get_session_metrics(session_id)
            }
            
            logger.info(f"Autonomous thought created successfully: {result['thought_id']} "
                       f"in {performance_ms:.2f}ms")
            
        except Exception as e:
            logger.error(f"Error in autonomous thought creation: {str(e)}")
            
            # Handle error with recovery
            recovery = await self.safety_validation.handle_reasoning_errors(
                e, session_id if 'session_id' in locals() else "unknown", 
                {"content": content[:100], "operation": "autonomous_thought_create"}
            )
            
            result["error"] = str(e)
            result["recovery"] = recovery
            
            # Apply graceful degradation if needed
            if 'session_id' in locals():
                degradation = await self.safety_validation.implement_graceful_degradation(
                    session_id, "thought_creation_failure"
                )
                result["degradation"] = degradation
        
        return result
    
    def _determine_thought_type(self, context: AutonomousContext) -> str:
        """
        Determine thought type from context.
        
        Args:
            context: Autonomous context
            
        Returns:
            Thought type string
        """
        # Initial thought
        if context.step_number == 1 or not context.previous_thought_id:
            return "problem"
        
        # Check for conclusion patterns
        if context.current_intent in ["analytical", "comparative"]:
            if context.depth > 5 or "therefore" in str(context.conversation_history[-1:]):
                return "conclusion"
        
        # Default to intermediate
        return "intermediate"
    
    async def _store_thought_atomically(self, 
                                       thought_data: Dict[str, Any],
                                       tx_context: AtomicTxContext) -> Dict[str, Any]:
        """
        Store thought atomically across all databases.
        
        Args:
            thought_data: Thought data to store
            tx_context: Atomic transaction context
            
        Returns:
            Storage result
        """
        import uuid
        from ulid import ULID
        
        # Generate ULID for thought
        thought_id = str(ULID())
        thought_data["ulid_id"] = thought_id
        thought_data["created_at"] = datetime.utcnow().isoformat()
        
        result = {
            "success": False,
            "thought_id": thought_id,
            "databases_updated": [],
            "error": None
        }
        
        try:
            # Store in SQLite (primary storage)
            await tx_context.execute_operation(
                "sqlite",
                "store_thought",
                thought_data
            )
            result["databases_updated"].append("sqlite")
            
            # Store in Neo4j (graph relationships)
            if thought_data.get("previous_thought_id"):
                await tx_context.execute_operation(
                    "neo4j",
                    "create_thought_node",
                    {
                        "ulid_id": thought_id,
                        "session_id": thought_data["session_id"],
                        "thought_type": thought_data["thought_type"],
                        "previous_id": thought_data["previous_thought_id"]
                    }
                )
                result["databases_updated"].append("neo4j")
            
            # Store in Redis (caching)
            await tx_context.execute_operation(
                "redis",
                "cache_thought",
                {
                    "key": f"thought:{thought_id}",
                    "value": thought_data,
                    "ttl": 3600  # 1 hour cache
                }
            )
            result["databases_updated"].append("redis")
            
            # Store in FAISS (vector search - if embeddings available)
            if "embedding" in thought_data.get("metadata", {}):
                await tx_context.execute_operation(
                    "faiss",
                    "store_vector",
                    {
                        "id": thought_id,
                        "vector": thought_data["metadata"]["embedding"],
                        "metadata": thought_data["metadata"]
                    }
                )
                result["databases_updated"].append("faiss")
            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Failed to store thought atomically: {e}")
            # Transaction will be rolled back by context manager
        
        return result
    
    async def get_reasoning_chain(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get complete reasoning chain for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of thoughts in chain order
        """
        if session_id not in self.session_extractor.session_chains:
            return []
        
        chain_ids = self.session_extractor.session_chains[session_id]
        chain = []
        
        for thought_id in chain_ids:
            # Retrieve from Redis cache first
            cached = await self.db_coordinator.redis_cache.get(f"thought:{thought_id}")
            if cached:
                chain.append(json.loads(cached))
            else:
                # Fall back to SQLite
                thought = await self.db_coordinator.sqlite_manager.get_thought(thought_id)
                if thought:
                    chain.append(thought)
        
        return chain
    
    async def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """
        Get comprehensive analytics for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session analytics dictionary
        """
        analytics = {
            "session_id": session_id,
            "session_info": self.session_extractor.active_sessions.get(session_id, {}),
            "chain_length": len(self.session_extractor.session_chains.get(session_id, [])),
            "recursion_metrics": await self.recursion_control.get_session_metrics(session_id),
            "safety_metrics": await self.safety_validation.get_safety_metrics(session_id),
            "optimization_suggestions": await self.recursion_control.optimize_reasoning_path(session_id)
        }
        
        return analytics


# Export main classes
__all__ = [
    'AutonomousReasoningCoordinator',
    'MCPContextExtractor', 
    'SessionContextExtractor',
    'MetadataGenerator',
    'AutonomousContext'
]