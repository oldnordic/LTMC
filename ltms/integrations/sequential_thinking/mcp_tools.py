"""
Sequential MCP Tools for LTMC Integration
Production-ready MCP tools that integrate Sequential Thinking with LTMC's existing tool system.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from ltms.tools.core.mcp_base import MCPToolBase
from ltms.database.sync_coordinator import DatabaseSyncCoordinator
from ltms.tools.core.database_manager import DatabaseManager
from .ltmc_integration import SequentialThinkingCoordinator, ThoughtData
from .session_context import SessionContext, SessionContextExtractor
from .metadata_generator import (
    MetadataGenerator, MetadataTemplate, ReasoningType,
    ReasoningContext, MetadataEnrichment
)
from .recursion_control import RecursionControlSystem, RecursionState
from .safety_validation import SafetyValidationAgent, PerformanceState

logger = logging.getLogger(__name__)

class SequentialMCPTools(MCPToolBase):
    """
    Production MCP tools for Sequential Thinking integration with LTMC.
    Uses LTMC's existing database coordination for atomic operations.
    """
    
    def __init__(self, test_mode: bool = False):
        super().__init__("sequential_mcp")
        self.test_mode = test_mode
        self.db_manager = DatabaseManager()
        self.coordinator = None
        self._initialization_lock = asyncio.Lock()
        
        # Initialize session context extractor for autonomous operation
        self.context_extractor = SessionContextExtractor(
            db_manager=self.db_manager,
            orchestration=None,  # Will be set if orchestration is available
            mcp_base=self
        )
        
        # Initialize metadata generator for intelligent metadata creation
        self.metadata_generator = MetadataGenerator(db_manager=self.db_manager)
        
        # Initialize safety systems for autonomous reasoning
        self.recursion_control = RecursionControlSystem(
            max_depth=10,
            warning_threshold=7
        )
        self.safety_validator = SafetyValidationAgent(
            recursion_control=self.recursion_control
        )
        
        self.autonomous_mode = True  # Enable autonomous context extraction by default
        
    def get_valid_actions(self):
        """Get list of valid actions for this tool."""
        return ["thought_create", "thought_analyze_chain", "thought_find_similar", "sequential_health_status", "autonomous_thought_create"]
    
    async def execute_action(self, action: str, **kwargs):
        """Execute the specified action with given parameters."""
        if action == "thought_create":
            # Handle conversation_id specially - move it to metadata if present
            if 'conversation_id' in kwargs:
                conversation_id = kwargs.pop('conversation_id')
                # Ensure metadata exists and add conversation_id to it
                if 'metadata' not in kwargs:
                    kwargs['metadata'] = {}
                if isinstance(kwargs['metadata'], dict):
                    kwargs['metadata']['conversation_id'] = conversation_id
                logger.debug(f"Moved conversation_id {conversation_id} to metadata for thought_create")
            return await self.thought_create(**kwargs)
        elif action == "autonomous_thought_create":
            return await self.autonomous_thought_create(**kwargs)
        elif action == "thought_analyze_chain":
            return await self.thought_analyze_chain(**kwargs)
        elif action == "thought_find_similar":
            return await self.thought_find_similar(**kwargs)
        elif action == "sequential_health_status":
            return await self.sequential_health_status(**kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "available_actions": self.get_valid_actions()
            }
        
    async def _ensure_coordinator_initialized(self):
        """Lazy initialization of coordinator to ensure database managers are ready."""
        if self.coordinator is None:
            async with self._initialization_lock:
                if self.coordinator is None:
                    # Create DatabaseSyncCoordinator with LTMC's database managers
                    # Use proper manager objects with the correct interfaces
                    sqlite_manager = self.db_manager  # DatabaseManager now has store_document interface
                    neo4j_manager = self.db_manager.neo4j  # Neo4jManager with store_document_node interface
                    faiss_manager = self.db_manager.faiss  # FAISSManager with store_document_vector interface  
                    redis_manager = self.db_manager.redis  # RedisManager with cache_document interface
                    
                    # Verify managers are properly initialized
                    logger.debug(f"Initializing sync coordinator with managers:")
                    logger.debug(f"  SQLite: {type(sqlite_manager)} - has store_document: {hasattr(sqlite_manager, 'store_document')}")
                    logger.debug(f"  Neo4j: {type(neo4j_manager)} - has store_document_node: {hasattr(neo4j_manager, 'store_document_node') if neo4j_manager else False}")
                    logger.debug(f"  FAISS: {type(faiss_manager)} - has store_document_vector: {hasattr(faiss_manager, 'store_document_vector') if faiss_manager else False}")
                    logger.debug(f"  Redis: {type(redis_manager)} - has cache_document: {hasattr(redis_manager, 'cache_document') if redis_manager else False}")
                    
                    sync_coordinator = DatabaseSyncCoordinator(
                        sqlite_manager=sqlite_manager,
                        neo4j_manager=neo4j_manager,
                        faiss_store=faiss_manager,
                        redis_cache=redis_manager,
                        test_mode=self.test_mode
                    )
                    
                    self.coordinator = SequentialThinkingCoordinator(
                        sync_coordinator, 
                        test_mode=self.test_mode
                    )
                    
                    logger.info("SequentialMCPTools coordinator initialized")
    
    async def thought_create(self, session_id: str, content: str, 
                           metadata: Optional[Dict[str, Any]] = None,
                           previous_thought_id: Optional[str] = None,
                           thought_type: str = "intermediate",
                           step_number: int = 1) -> Dict[str, Any]:
        """
        Create a new thought in a sequential reasoning chain.
        
        Args:
            session_id: Unique session identifier for the reasoning chain
            content: The thought content  
            metadata: Optional metadata for context (auto-generated if None - enables autonomous AI reasoning)
            previous_thought_id: ULID of previous thought in chain (required for chain traceability)
            thought_type: Type of thought (problem, intermediate, conclusion)
            step_number: Step number in reasoning sequence
        
        Returns:
            Creation result with ULID, timing, and database status
        """
        await self._ensure_coordinator_initialized()
        
        # Parse metadata if it's a JSON string
        if isinstance(metadata, str):
            try:
                import json
                metadata = json.loads(metadata)
                logger.debug(f"Parsed metadata JSON: {type(metadata)}")
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Failed to parse metadata JSON: {e}")
                metadata = {"parsing_error": str(e)}
        
        # Auto-generate metadata if not provided (enables autonomous AI reasoning)
        if metadata is None:
            try:
                # Use existing infrastructure for intelligent metadata generation
                temp_context = SessionContext(
                    session_id=session_id,
                    conversation_id=None,  # Will be extracted/generated by metadata generator
                    agent_id=getattr(self, 'agent_id', 'autonomous_agent'),
                    chain_id=None,
                    previous_thought_id=previous_thought_id,
                    step_number=step_number,
                    metadata={'content': content},  # Pass content for AI analysis
                    extraction_sources=['autonomous_parameter_generation'],
                    generated_fields=['metadata'],
                    timestamp=datetime.now(),
                    confidence=0.8
                )
                
                # Use existing metadata generator with AI enhancement
                metadata = self._generate_metadata(temp_context, None)
                logger.info(f"Auto-generated metadata for autonomous thought creation in session {session_id}")
                
            except Exception as e:
                # Fallback to minimal metadata if generation fails
                logger.warning(f"Metadata generation failed, using fallback: {e}")
                metadata = {
                    "generated_by": "autonomous_fallback",
                    "generation_error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "session_id": session_id,
                    "agent_id": getattr(self, 'agent_id', 'autonomous_agent'),
                    "thought_type": thought_type,
                    "step_number": step_number,
                    "atomic_transaction_id": f"thought_{session_id}_{int(time.time() * 1000)}"
                }
        
        # Warning for missing previous_thought_id (breaks chain traceability)    
        if previous_thought_id is None and step_number > 1:
            logger.warning(f"Missing previous_thought_id for step {step_number} in session {session_id} - chain traceability broken")
        
        try:
            # Create ThoughtData model
            thought = ThoughtData(
                session_id=session_id,
                content=content,
                thought_type=thought_type,
                previous_thought_id=previous_thought_id,
                step_number=step_number,
                metadata=metadata
            )
            
            # Store using LTMC's coordination infrastructure
            result = await self.coordinator.store_thought(thought)
            
            # Ensure Neo4j NEXT chain linking for sequential traceability
            if previous_thought_id and self.db_manager._neo4j_manager:
                try:
                    # Create NEXT relationship from previous thought to current thought
                    neo4j_mgr = self.db_manager._neo4j_manager
                    await neo4j_mgr.create_relationship(
                        source_id=previous_thought_id,
                        target_id=thought.ulid_id,
                        relationship_type="NEXT",
                        properties={
                            "session_id": session_id,
                            "step_from": step_number - 1,
                            "step_to": step_number,
                            "thought_type": thought_type,
                            "created_at": thought.created_at.isoformat()
                        }
                    )
                    logger.debug(f"Created NEXT relationship: {previous_thought_id} -> {thought.ulid_id}")
                except Exception as e:
                    logger.warning(f"Failed to create NEXT relationship: {e}")
            elif previous_thought_id is None and step_number == 1:
                logger.debug(f"First thought in chain {session_id}: {thought.ulid_id}")
            
            self._track_mind_graph_change("thought_create", {
                "ulid_id": thought.ulid_id,
                "session_id": session_id,
                "thought_type": thought_type,
                "execution_time_ms": result.get("execution_time_ms")
            })
            
            return {
                "success": True,
                "data": {
                    "ulid_id": thought.ulid_id,
                    "session_id": session_id,
                    "content_hash": thought.content_hash,
                    "created_at": thought.created_at.isoformat(),
                    "databases_affected": result.get("databases", {}),
                    "execution_time_ms": result.get("execution_time_ms"),
                    "sla_compliant": result.get("sla_compliant", False)
                }
            }
            
        except Exception as e:
            logger.error(f"thought_create failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def thought_analyze_chain(self, session_id: str) -> Dict[str, Any]:
        """
        Analyze complete thought chain for a session.
        
        Args:
            session_id: Session identifier to analyze
            
        Returns:
            Complete thought chain with analysis metrics
        """
        await self._ensure_coordinator_initialized()
        
        try:
            # Retrieve complete chain using graph traversal
            chain = await self.coordinator.retrieve_thought_chain(session_id)
            
            if not chain:
                return {
                    "success": True,
                    "data": {
                        "session_id": session_id,
                        "chain_length": 0,
                        "thoughts": [],
                        "analysis": {"status": "empty_session"}
                    }
                }
            
            # Analyze chain structure
            analysis = self._analyze_chain_structure(chain)
            
            self._track_mind_graph_change("thought_chain_analyzed", {
                "session_id": session_id,
                "chain_length": len(chain),
                "analysis_summary": analysis.get("summary")
            })
            
            return {
                "success": True,
                "data": {
                    "session_id": session_id,
                    "chain_length": len(chain),
                    "thoughts": chain,
                    "analysis": analysis
                }
            }
            
        except Exception as e:
            logger.error(f"thought_analyze_chain failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def thought_find_similar(self, query: str, k: int = 5,
                                 include_chains: bool = True,
                                 session_id: Optional[str] = None,
                                 limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Find similar reasoning patterns using semantic search.
        
        Args:
            query: Search query for similar reasoning
            k: Number of similar results to return (default=5)
            include_chains: Whether to include chain context
            session_id: Optional session ID for scoped queries (currently ignored for compatibility)
            limit: Alternative parameter name for k (for standardization with other tools)
            
        Returns:
            Similar reasoning patterns with session context
        """
        await self._ensure_coordinator_initialized()
        
        # Parameter normalization for backward compatibility and standardization
        # If limit is provided, use it as k (allows both parameter names)
        if limit is not None:
            k = limit
            logger.debug(f"Using limit parameter as k: {limit}")
        
        # Log session_id for future scoped query support
        if session_id:
            logger.debug(f"Session ID provided for potential scoped search: {session_id}")
        
        try:
            # Use FAISS semantic search via LTMC coordination
            similar_thoughts = await self.coordinator.find_similar_reasoning(query, k)
            
            # Enrich with chain context if requested
            if include_chains:
                for thought in similar_thoughts:
                    session_id = thought.get("metadata", {}).get("session_id")
                    if session_id:
                        chain = await self.coordinator.retrieve_thought_chain(session_id)
                        thought["full_chain"] = chain
            
            self._track_mind_graph_change("similar_reasoning_search", {
                "query_preview": query[:50],
                "results_found": len(similar_thoughts),
                "include_chains": include_chains
            })
            
            return {
                "success": True,
                "data": {
                    "query": query,
                    "k": k,  # Show the actual k value used
                    "session_id": session_id,  # Include for transparency
                    "results_count": len(similar_thoughts),
                    "similar_thoughts": similar_thoughts
                }
            }
            
        except Exception as e:
            logger.error(f"thought_find_similar failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    async def sequential_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive health status for Sequential MCP integration.
        
        Returns:
            Complete health and performance metrics
        """
        await self._ensure_coordinator_initialized()
        
        try:
            health = await self.coordinator.get_health_status()
            
            return {
                "success": True,
                "data": health
            }
            
        except Exception as e:
            logger.error(f"sequential_health_status failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
    
    def _analyze_chain_structure(self, chain: list) -> Dict[str, Any]:
        """Analyze the structure and quality of a thought chain."""
        if not chain:
            return {"status": "empty", "summary": "No thoughts in chain"}
        
        analysis = {
            "total_thoughts": len(chain),
            "thought_types": {},
            "average_content_length": 0,
            "has_problem_definition": False,
            "has_conclusion": False,
            "coherence_score": 0.8,  # Placeholder - could implement actual coherence analysis
            "summary": ""
        }
        
        # Analyze thought types and content
        total_length = 0
        for thought in chain:
            thought_type = thought.get("thought_type", "unknown")
            analysis["thought_types"][thought_type] = analysis["thought_types"].get(thought_type, 0) + 1
            
            content_length = len(thought.get("content", ""))
            total_length += content_length
            
            if thought_type == "problem":
                analysis["has_problem_definition"] = True
            elif thought_type == "conclusion":
                analysis["has_conclusion"] = True
        
        analysis["average_content_length"] = total_length / len(chain) if chain else 0
        
        # Generate summary
        if analysis["has_problem_definition"] and analysis["has_conclusion"]:
            analysis["summary"] = f"Complete reasoning chain with {analysis['total_thoughts']} thoughts"
        else:
            analysis["summary"] = f"Partial reasoning chain with {analysis['total_thoughts']} thoughts"
        
        return analysis
    
    async def autonomous_thought_create(self, content: str, **kwargs) -> Dict[str, Any]:
        """
        Create a thought with automatic context extraction and comprehensive safety validation.
        
        This method automatically extracts session context from available sources,
        generates missing parameters intelligently, maintains chain continuity,
        and provides comprehensive safety validation including recursion control,
        performance monitoring, and emergency stop capabilities.
        
        Args:
            content: The thought content (required)
            **kwargs: Optional parameters that override auto-extraction
            
        Returns:
            Creation result with complete context metadata and safety metrics
        """
        start_time = time.time()
        
        await self._ensure_coordinator_initialized()
        
        try:
            # Step 1: Extract session context from all available sources
            context = await self._extract_session_context(kwargs)
            
            # Step 2: Perform safety validation before proceeding
            safety_result = await self.safety_validator.validate_autonomous_operation(
                session_id=context.session_id,
                thought_id=None,  # Will be generated during creation
                content=content,
                parent_id=context.previous_thought_id
            )
            
            if not safety_result['valid']:
                logger.warning(f"Safety validation failed: {safety_result.get('reason', 'Unknown')}")
                return {
                    "success": False,
                    "error": f"Safety validation failed: {safety_result.get('reason', 'Unknown')}",
                    "error_type": "SafetyValidationError",
                    "safety_metrics": safety_result,
                    "fallback": "Reduce complexity or wait for system recovery"
                }
            
            # Step 3: Check recursion control before creating thought
            recursion_result = await self.recursion_control.track_reasoning_depth(
                session_id=context.session_id,
                thought_id="temp_id",  # Temporary ID for depth checking
                content=content,
                parent_id=context.previous_thought_id
            )
            
            current_depth, recursion_state = recursion_result
            
            if recursion_state == RecursionState.BLOCKED:
                logger.error(f"Recursion blocked at depth {current_depth} in session {context.session_id}")
                return {
                    "success": False,
                    "error": f"Recursion limit exceeded (depth: {current_depth})",
                    "error_type": "RecursionBlockedError",
                    "recursion_state": recursion_state.value,
                    "current_depth": current_depth,
                    "fallback": "Start new reasoning session or wait for recovery"
                }
            
            # Step 4: Ensure chain continuity with auto-recovery
            context = await self._ensure_chain_continuity(context)
            
            # Step 5: Generate complete metadata from context
            # Pass content to context for AI analysis
            context.metadata['content'] = content
            metadata = self._generate_metadata(context, kwargs.get('metadata'))
            
            # Add safety and recursion metadata
            metadata['autonomous_safety'] = {
                'safety_validation': safety_result,
                'recursion_state': recursion_state.value,
                'current_depth': current_depth,
                'performance_state': safety_result.get('performance_state', 'unknown')
            }
            
            # Step 6: Log autonomous context extraction for audit
            logger.info(f"Autonomous thought creation with context from sources: {context.extraction_sources}")
            if context.generated_fields:
                logger.debug(f"Auto-generated fields: {context.generated_fields}")
            logger.debug(f"Safety validation: {safety_result.get('performance_state', 'unknown')}, Recursion: {recursion_state.value}")
            
            # Step 7: Monitor thought creation pipeline performance
            async def monitored_thought_creation():
                # Filter out any kwargs that thought_create doesn't accept
                # Only pass parameters that thought_create expects
                thought_type = kwargs.get('thought_type', 'intermediate')
                
                # Ensure conversation_id is in metadata, not as a direct parameter
                if 'conversation_id' in kwargs:
                    # Move conversation_id to metadata if it was passed as a kwarg
                    metadata['conversation_id'] = kwargs['conversation_id']
                
                return await self.thought_create(
                    session_id=context.session_id,
                    content=content,
                    metadata=metadata,
                    previous_thought_id=context.previous_thought_id,
                    thought_type=thought_type,
                    step_number=context.step_number
                )
            
            # Execute with performance monitoring
            pipeline_result = await self.safety_validator.monitor_thought_pipeline(
                monitored_thought_creation(),
                session_id=context.session_id,
                content=content
            )
            
            if not pipeline_result['success']:
                logger.error(f"Thought creation pipeline failed: {pipeline_result.get('error')}")
                return {
                    "success": False,
                    "error": f"Thought creation failed: {pipeline_result.get('error')}",
                    "error_type": "ThoughtCreationError",
                    "pipeline_metrics": pipeline_result.get('performance', {}),
                    "safety_metrics": safety_result
                }
            
            result = pipeline_result['result']
            
            # Step 8: Update recursion tracking with actual thought ID
            if result.get('success') and result.get('data', {}).get('ulid_id'):
                actual_thought_id = result['data']['ulid_id']
                await self.recursion_control.update_thought_id(
                    session_id=context.session_id,
                    old_id="temp_id",
                    new_id=actual_thought_id
                )
            
            # Step 9: Enhance result with comprehensive autonomous context metadata
            if result.get('success'):
                total_time_ms = (time.time() - start_time) * 1000
                
                result['data']['autonomous_context'] = {
                    'extraction_sources': context.extraction_sources,
                    'generated_fields': context.generated_fields,
                    'conversation_id': context.conversation_id,
                    'chain_id': context.chain_id,
                    'safety_validation': safety_result,
                    'recursion_control': {
                        'state': recursion_state.value,
                        'depth': current_depth,
                        'max_depth': self.recursion_control.max_depth
                    },
                    'performance_metrics': {
                        'total_autonomous_overhead_ms': total_time_ms,
                        'pipeline_metrics': pipeline_result.get('performance', {}),
                        'sla_compliant': total_time_ms < 200  # 200ms SLA for autonomous overhead
                    }
                }
                
                # Validate SLA compliance
                if total_time_ms > 200:
                    logger.warning(f"Autonomous overhead exceeded SLA: {total_time_ms:.1f}ms > 200ms")
                else:
                    logger.debug(f"Autonomous overhead within SLA: {total_time_ms:.1f}ms")
            
            return result
            
        except Exception as e:
            total_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Autonomous thought creation failed after {total_time_ms:.1f}ms: {e}")
            return {
                "success": False,
                "error": f"Autonomous reasoning failed: {str(e)}",
                "error_type": type(e).__name__,
                "execution_time_ms": total_time_ms,
                "fallback": "Use explicit thought_create with all parameters"
            }
    
    async def _extract_session_context(self, kwargs: Dict[str, Any]) -> SessionContext:
        """
        Extract session context using hierarchical extraction strategy.
        
        Args:
            kwargs: Parameters from MCP request
            
        Returns:
            Complete SessionContext with all available information
        """
        # Get MCP metadata if available (would come from transport layer)
        mcp_metadata = kwargs.pop('_mcp_metadata', None)
        
        # Extract context using the extractor
        context = await self.context_extractor.extract_context(
            arguments=kwargs,
            tool_name="sequential_thinking",
            mcp_metadata=mcp_metadata
        )
        
        return context
    
    async def _ensure_chain_continuity(self, context: SessionContext) -> SessionContext:
        """
        Ensure reasoning chain continuity with auto-recovery.
        
        Detects and recovers broken chains, auto-links thoughts,
        and maintains step number consistency.
        
        Args:
            context: Current session context
            
        Returns:
            Context with ensured chain continuity
        """
        # If step_number > 1 but no previous_thought_id, recover chain
        if context.step_number > 1 and not context.previous_thought_id:
            logger.warning(f"Chain recovery needed for session {context.session_id} at step {context.step_number}")
            
            # Attempt to recover chain context
            recovery_result = await self.context_extractor.recover_chain_context(
                session_id=context.session_id,
                step_number=context.step_number
            )
            
            if recovery_result:
                context.previous_thought_id = recovery_result.get('previous_thought_id')
                context.add_extraction_source('chain_recovery')
                context.mark_generated('previous_thought_id')
                logger.info(f"Chain recovered: linked to thought {context.previous_thought_id}")
            else:
                logger.warning("Chain recovery failed - starting new chain segment")
                context.step_number = 1  # Reset to start new segment
        
        # If we have previous_thought_id but step_number is 1, adjust
        elif context.previous_thought_id and context.step_number == 1:
            # This indicates a mismatch - increment step number
            context.step_number = 2  # Minimum step for linked thought
            context.mark_generated('step_number')
            logger.debug("Adjusted step_number for linked thought")
        
        return context
    
    def _generate_metadata(self, context: SessionContext, original_metadata: Optional[Dict]) -> Dict[str, Any]:
        """
        Generate complete metadata from context and original metadata using AI-enhanced templates.
        
        Phase 2B Enhancement: Uses AI-powered pattern detection and reasoning analysis
        to generate richer metadata for autonomous AI reasoning.
        
        Args:
            context: Extracted session context
            original_metadata: Original metadata from request
            
        Returns:
            Complete metadata dictionary with AI reasoning intelligence
        """
        # Extract content for AI analysis (if available)
        content = context.metadata.get('content', '') if context.metadata else ''
        
        # Try to get chain history for deeper analysis
        chain_history = None
        if context.session_id and self.db_manager:
            try:
                # Attempt to retrieve chain history for context
                chain_history = []  # Would be populated from database
            except Exception as e:
                logger.debug(f"Could not retrieve chain history: {e}")
        
        # Build session context for AI enhancement
        session_context = {
            'session_id': context.session_id,
            'agent_id': context.agent_id,
            'step_number': context.step_number,
            'confidence': context.confidence or 0.8,
            'decision_points': original_metadata.get('decision_points', []) if original_metadata else [],
            'parent_chain_id': context.chain_id,
            'parallel_chains': context.metadata.get('parallel_chains', []) if context.metadata else [],
            'caller_agent': context.metadata.get('caller_agent') if context.metadata else None,
            'handoff_context': context.metadata.get('handoff_context') if context.metadata else None,
            'error_corrections': context.metadata.get('error_corrections', []) if context.metadata else [],
            'previous_thought_id': context.previous_thought_id,
            'conversation_id': context.conversation_id,
            'chain_id': context.chain_id
        }
        
        # Use AI-enhanced metadata generation if content is available
        if content and len(content) > 10:  # Meaningful content threshold
            try:
                generated_metadata = self.metadata_generator.generate_ai_enhanced_metadata(
                    content=content,
                    session_context=session_context,
                    chain_history=chain_history
                )
                logger.debug("Generated AI-enhanced metadata with pattern detection")
            except Exception as e:
                logger.warning(f"AI enhancement failed, falling back to template generation: {e}")
                # Fallback to template-based generation
                generated_metadata = self._generate_template_metadata(context, session_context, original_metadata)
        else:
            # Use template-based generation for minimal content
            generated_metadata = self._generate_template_metadata(context, session_context, original_metadata)
        
        # Merge with original metadata preserving user-provided fields
        if original_metadata:
            # User-provided metadata takes precedence for explicit fields
            for key, value in original_metadata.items():
                if key not in ['session_id', 'conversation_id', 'agent_id']:  # Don't override extracted IDs
                    generated_metadata[key] = value
        
        # Add autonomous generation tracking
        if context.generated_fields:
            generated_metadata['autonomous_generation'] = {
                'generated_fields': context.generated_fields,
                'extraction_sources': context.extraction_sources,
                'confidence': context.confidence
            }
        
        # Add context-specific metadata
        if context.metadata:
            generated_metadata['context_metadata'] = context.metadata
        
        return generated_metadata
    
    def _generate_template_metadata(self, context: SessionContext, 
                                   session_context: Dict[str, Any],
                                   original_metadata: Optional[Dict]) -> Dict[str, Any]:
        """
        Generate metadata using template-based approach (fallback method).
        
        Args:
            context: Session context
            session_context: Session context dictionary
            original_metadata: Original metadata
            
        Returns:
            Template-generated metadata
        """
        # Determine reasoning type from context
        reasoning_type = self._determine_reasoning_type(context, original_metadata)
        
        # Build reasoning context for metadata generation
        reasoning_context = ReasoningContext(
            reasoning_type=reasoning_type,
            confidence_level=context.confidence or 0.8,
            decision_points=session_context.get('decision_points', []),
            parent_chain_id=context.chain_id,
            agent_id=context.agent_id,
            caller_agent=session_context.get('caller_agent'),
            handoff_context=session_context.get('handoff_context')
        )
        
        # Add parallel chains if detected
        if session_context.get('parallel_chains'):
            reasoning_context.parallel_chains = session_context['parallel_chains']
        
        # Build enrichment data
        enrichment = MetadataEnrichment(
            timestamp=context.timestamp.isoformat(),
            generation_method='template_based',
            extraction_sources=context.extraction_sources,
            context_confidence=context.confidence or 0.8,
            validation_status='validated',
            reasoning_trace=self._build_reasoning_trace(context)
        )
        
        # Determine best template based on context
        template = self._select_metadata_template(context, reasoning_context)
        
        # Generate metadata using the intelligent generator
        return self.metadata_generator.generate_metadata(
            template=template,
            context=reasoning_context,
            enrichment=enrichment,
            custom_fields=session_context
        )
    
    def _determine_reasoning_type(self, context: SessionContext, 
                                 original_metadata: Optional[Dict]) -> ReasoningType:
        """Determine the reasoning type from context and metadata."""
        # Check for explicit reasoning type in metadata
        if original_metadata and 'reasoning_type' in original_metadata:
            reasoning_str = original_metadata['reasoning_type']
            try:
                return ReasoningType(reasoning_str)
            except ValueError:
                pass
        
        # Infer from context
        if context.metadata:
            if context.metadata.get('handoff'):
                return ReasoningType.HANDOFF
            if context.metadata.get('parallel_chains'):
                return ReasoningType.PARALLEL
            if context.metadata.get('error_recovery'):
                return ReasoningType.CORRECTION
        
        # Check step position
        if context.step_number == 1:
            return ReasoningType.PROBLEM_SOLVING
        elif context.previous_thought_id:
            return ReasoningType.CHAIN_OF_THOUGHT
        
        # Default to sequential analysis
        return ReasoningType.SEQUENTIAL_ANALYSIS
    
    def _select_metadata_template(self, context: SessionContext,
                                 reasoning_context: ReasoningContext) -> MetadataTemplate:
        """Select the appropriate metadata template based on context."""
        # Check for handoff
        if reasoning_context.reasoning_type == ReasoningType.HANDOFF:
            return MetadataTemplate.AGENT_HANDOFF
        
        # Check for parallel reasoning
        if reasoning_context.parallel_chains:
            return MetadataTemplate.PARALLEL_REASONING
        
        # Check for error recovery
        if reasoning_context.reasoning_type == ReasoningType.CORRECTION:
            return MetadataTemplate.ERROR_RECOVERY
        
        # Check for chain continuation
        if context.previous_thought_id and context.step_number > 1:
            return MetadataTemplate.CHAIN_CONTINUATION
        
        # Check for session initialization
        if context.step_number == 1 and not context.previous_thought_id:
            return MetadataTemplate.SESSION_INIT
        
        # Default to autonomous reasoning
        return MetadataTemplate.AUTONOMOUS_REASONING
    
    def _build_reasoning_trace(self, context: SessionContext) -> List[Dict[str, Any]]:
        """Build reasoning trace from context extraction process."""
        trace = []
        
        # Add extraction steps
        for source in context.extraction_sources:
            trace.append({
                'step': source,
                'timestamp': context.timestamp.isoformat(),
                'success': True
            })
        
        # Add generated fields as reasoning decisions
        for field in context.generated_fields:
            trace.append({
                'decision': f'generated_{field}',
                'confidence': context.confidence or 0.8,
                'method': 'intelligent_default'
            })
        
        return trace

# Global unified function for LTMC tool registry integration
async def sequential_thinking_action(action: str, **params) -> Dict[str, Any]:
    """
    Unified sequential thinking operations following LTMC patterns.
    
    Actions: thought_create, thought_analyze_chain, thought_find_similar, sequential_health_status
    """
    # Parse JSON string parameters for MCP compatibility
    logger.debug(f"sequential_thinking_action called with params: {params}")
    for key, value in params.items():
        if isinstance(value, str) and key in ['metadata']:
            logger.debug(f"Parsing JSON for {key}: {value[:100]}...")
            try:
                import json
                parsed_value = json.loads(value)
                params[key] = parsed_value
                logger.debug(f"Successfully parsed {key}: {type(parsed_value)}")
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"JSON parsing failed for {key}: {e}")
                if key == 'metadata':
                    params[key] = {"parsing_error": f"Invalid JSON: {value[:50]}..."}
    
    tools = SequentialMCPTools()
    return await tools.execute_action(action, **params)


# Tool registry for LTMC integration (unified tools method)
SEQUENTIAL_MCP_TOOLS = {
    "sequential_thinking_action": {
        "handler": sequential_thinking_action,
        "description": "Sequential reasoning with atomic database storage: thought_create, thought_analyze_chain, thought_find_similar, sequential_health_status",
        "schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["thought_create", "autonomous_thought_create", "thought_analyze_chain", "thought_find_similar", "sequential_health_status"],
                    "description": "Sequential thinking action to perform (autonomous_thought_create auto-extracts context)"
                }
            },
            "required": ["action"],
            "additionalProperties": True
        }
    }
}