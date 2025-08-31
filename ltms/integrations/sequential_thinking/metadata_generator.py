"""
Metadata Generation System for Autonomous AI Reasoning
Intelligent auto-metadata generation with context awareness and reasoning templates.
"""

import logging
import json
import hashlib
import re
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from collections import defaultdict

logger = logging.getLogger(__name__)


class ReasoningType(Enum):
    """Types of AI reasoning patterns with enhanced classification."""
    # Core reasoning types
    PROBLEM_SOLVING = "problem_solving"
    SEQUENTIAL_ANALYSIS = "sequential_analysis"
    CHAIN_OF_THOUGHT = "chain_of_thought"
    DECISION_MAKING = "decision_making"
    EXPLORATION = "exploration"
    CONCLUSION = "conclusion"
    HANDOFF = "agent_handoff"
    PARALLEL = "parallel_reasoning"
    CORRECTION = "error_correction"
    REFINEMENT = "iterative_refinement"
    
    # Advanced AI reasoning patterns (Phase 2B)
    CAUSAL_REASONING = "causal_reasoning"
    DEDUCTIVE = "deductive_reasoning"
    INDUCTIVE = "inductive_reasoning"
    ABDUCTIVE = "abductive_reasoning"
    ANALOGICAL = "analogical_reasoning"
    SYNTHESIS = "synthesis"
    VALIDATION = "validation"
    HYPOTHESIS_TESTING = "hypothesis_testing"
    CRITICAL_ANALYSIS = "critical_analysis"
    META_REASONING = "meta_reasoning"  # Reasoning about reasoning


class MetadataTemplate(Enum):
    """Predefined metadata templates for different scenarios."""
    AUTONOMOUS_REASONING = "autonomous_reasoning"
    AGENT_HANDOFF = "agent_handoff"
    CHAIN_CONTINUATION = "chain_continuation"
    PARALLEL_REASONING = "parallel_reasoning"
    ERROR_RECOVERY = "error_recovery"
    SESSION_INIT = "session_initialization"
    CONCLUSION_SUMMARY = "conclusion_summary"


@dataclass
class ThoughtPattern:
    """Pattern detected in thought content for AI reasoning analysis."""
    pattern_type: str  # analysis, synthesis, validation, etc.
    confidence: float
    indicators: List[str]  # Keywords or structures that indicate pattern
    complexity_score: float  # 0.0 to 1.0
    
@dataclass
class AgentCapability:
    """AI agent capability tracking for autonomous reasoning."""
    agent_id: str
    capabilities: List[str]  # reasoning, analysis, synthesis, etc.
    specialization: Optional[str] = None
    performance_history: Dict[str, float] = field(default_factory=dict)
    reliability_score: float = 0.8

@dataclass
class ReasoningDepth:
    """Depth analysis for complex reasoning chains."""
    current_depth: int
    max_depth_reached: int
    branch_count: int  # Number of parallel branches
    convergence_points: List[int]  # Steps where branches converge
    complexity_metric: float  # Overall complexity score

@dataclass
class ReasoningContext:
    """Enhanced context for AI reasoning metadata generation."""
    reasoning_type: ReasoningType
    confidence_level: float  # 0.0 to 1.0
    decision_points: List[Dict[str, Any]] = field(default_factory=list)
    parent_chain_id: Optional[str] = None
    parallel_chains: List[str] = field(default_factory=list)
    error_corrections: List[Dict[str, Any]] = field(default_factory=list)
    agent_id: Optional[str] = None
    caller_agent: Optional[str] = None
    handoff_context: Optional[Dict[str, Any]] = None
    
    # Phase 2B enhancements
    thought_patterns: List[ThoughtPattern] = field(default_factory=list)
    agent_capability: Optional[AgentCapability] = None
    reasoning_depth: Optional[ReasoningDepth] = None
    semantic_context: Dict[str, Any] = field(default_factory=dict)
    hypothesis_chain: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class MetadataEnrichment:
    """Enrichment data for metadata generation."""
    timestamp: str
    generation_method: str
    extraction_sources: List[str]
    context_confidence: float
    validation_status: str
    atomic_transaction_id: Optional[str] = None
    database_consistency: Dict[str, str] = field(default_factory=dict)
    reasoning_trace: List[Dict[str, Any]] = field(default_factory=list)


class ReasoningAnalyzer:
    """
    AI-powered reasoning pattern analyzer for intelligent metadata generation.
    Detects thought patterns, reasoning types, and complexity metrics.
    """
    
    def __init__(self):
        """Initialize the reasoning analyzer with pattern detection rules."""
        self.pattern_indicators = self._initialize_pattern_indicators()
        self.reasoning_keywords = self._initialize_reasoning_keywords()
        self._analysis_cache = {}  # Performance optimization cache
        
    def _initialize_pattern_indicators(self) -> Dict[str, List[str]]:
        """Initialize indicators for different thought patterns."""
        return {
            "analysis": ["analyze", "examine", "investigate", "break down", "decompose", "inspect"],
            "synthesis": ["combine", "integrate", "merge", "unify", "synthesize", "construct"],
            "validation": ["verify", "validate", "confirm", "check", "test", "prove"],
            "hypothesis": ["assume", "hypothesize", "suppose", "postulate", "conjecture", "theorize"],
            "causal": ["because", "therefore", "thus", "hence", "consequently", "as a result"],
            "deductive": ["if...then", "given that", "it follows", "necessarily", "must be"],
            "inductive": ["pattern suggests", "evidence indicates", "generally", "tends to", "likely"],
            "abductive": ["best explanation", "plausible", "probable cause", "might be", "suggests"],
            "analogical": ["similar to", "like", "resembles", "comparable", "analogous", "parallel"],
            "critical": ["however", "but", "although", "despite", "nevertheless", "on the other hand"],
            "meta": ["thinking about", "reasoning process", "approach", "methodology", "strategy"]
        }
    
    def _initialize_reasoning_keywords(self) -> Dict[ReasoningType, List[str]]:
        """Initialize keywords for reasoning type classification."""
        return {
            ReasoningType.CAUSAL_REASONING: ["cause", "effect", "because", "result", "leads to"],
            ReasoningType.DEDUCTIVE: ["premise", "conclusion", "logically", "necessarily", "proof"],
            ReasoningType.INDUCTIVE: ["pattern", "trend", "observation", "generalize", "probability"],
            ReasoningType.ABDUCTIVE: ["explanation", "hypothesis", "plausible", "likely cause"],
            ReasoningType.ANALOGICAL: ["similar", "analogy", "comparison", "metaphor", "parallel"],
            ReasoningType.SYNTHESIS: ["combine", "integrate", "merge", "synthesize", "unify"],
            ReasoningType.VALIDATION: ["verify", "validate", "test", "confirm", "check"],
            ReasoningType.HYPOTHESIS_TESTING: ["test", "experiment", "hypothesis", "prediction"],
            ReasoningType.CRITICAL_ANALYSIS: ["critique", "evaluate", "assess", "judge", "analyze"],
            ReasoningType.META_REASONING: ["reasoning about", "thinking process", "cognitive", "meta"]
        }
    
    def analyze_thought_content(self, content: str, context: Optional[Dict] = None) -> List[ThoughtPattern]:
        """
        Analyze thought content to detect reasoning patterns.
        
        Args:
            content: The thought content to analyze
            context: Optional context for enhanced analysis
            
        Returns:
            List of detected thought patterns with confidence scores
        """
        # Check cache first for performance
        cache_key = hashlib.md5(f"{content[:100]}".encode()).hexdigest()
        if cache_key in self._analysis_cache:
            cached = self._analysis_cache[cache_key]
            if time.time() - cached["timestamp"] < 300:  # 5 minute cache
                return cached["patterns"]
        
        patterns = []
        content_lower = content.lower()
        
        # Detect patterns based on indicators
        for pattern_type, indicators in self.pattern_indicators.items():
            detected_indicators = [ind for ind in indicators if ind in content_lower]
            if detected_indicators:
                confidence = min(1.0, len(detected_indicators) * 0.2)  # Max confidence at 5 indicators
                complexity = self._calculate_complexity(content, pattern_type)
                patterns.append(ThoughtPattern(
                    pattern_type=pattern_type,
                    confidence=confidence,
                    indicators=detected_indicators,
                    complexity_score=complexity
                ))
        
        # Cache results
        self._analysis_cache[cache_key] = {
            "patterns": patterns,
            "timestamp": time.time()
        }
        
        # Limit cache size
        if len(self._analysis_cache) > 1000:
            # Remove oldest entries
            sorted_cache = sorted(self._analysis_cache.items(), 
                                key=lambda x: x[1]["timestamp"])
            self._analysis_cache = dict(sorted_cache[-500:])
        
        return patterns
    
    def classify_reasoning_type(self, content: str, patterns: List[ThoughtPattern]) -> ReasoningType:
        """
        Classify the predominant reasoning type from content and patterns.
        
        Args:
            content: Thought content
            patterns: Detected thought patterns
            
        Returns:
            Most likely reasoning type
        """
        content_lower = content.lower()
        scores = defaultdict(float)
        
        # Score based on keyword presence
        for reasoning_type, keywords in self.reasoning_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    scores[reasoning_type] += 1.0
        
        # Boost scores based on detected patterns
        pattern_mapping = {
            "causal": ReasoningType.CAUSAL_REASONING,
            "deductive": ReasoningType.DEDUCTIVE,
            "inductive": ReasoningType.INDUCTIVE,
            "abductive": ReasoningType.ABDUCTIVE,
            "analogical": ReasoningType.ANALOGICAL,
            "synthesis": ReasoningType.SYNTHESIS,
            "validation": ReasoningType.VALIDATION,
            "hypothesis": ReasoningType.HYPOTHESIS_TESTING,
            "critical": ReasoningType.CRITICAL_ANALYSIS,
            "meta": ReasoningType.META_REASONING
        }
        
        for pattern in patterns:
            if pattern.pattern_type in pattern_mapping:
                reasoning_type = pattern_mapping[pattern.pattern_type]
                scores[reasoning_type] += pattern.confidence * 2.0
        
        # Return highest scoring type, or default to CHAIN_OF_THOUGHT
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return ReasoningType.CHAIN_OF_THOUGHT
    
    def calculate_reasoning_depth(self, chain_data: List[Dict], 
                                 current_step: int) -> ReasoningDepth:
        """
        Calculate reasoning depth metrics for the current chain.
        
        Args:
            chain_data: Historical chain data
            current_step: Current step number
            
        Returns:
            ReasoningDepth metrics
        """
        if not chain_data:
            return ReasoningDepth(
                current_depth=1,
                max_depth_reached=1,
                branch_count=0,
                convergence_points=[],
                complexity_metric=0.0
            )
        
        # Analyze chain structure
        depths = {}
        branches = defaultdict(list)
        max_depth = 1
        
        for thought in chain_data:
            thought_id = thought.get("ulid_id", thought.get("id"))
            parent_id = thought.get("previous_thought_id")
            step = thought.get("step_number", 1)
            
            if parent_id:
                parent_depth = depths.get(parent_id, 0)
                depths[thought_id] = parent_depth + 1
                max_depth = max(max_depth, depths[thought_id])
                branches[parent_id].append(thought_id)
        
        # Find convergence points (nodes with multiple children)
        convergence_points = [
            step for step, children in branches.items() 
            if len(children) > 1
        ]
        
        # Calculate complexity metric
        branch_count = len([b for b in branches.values() if len(b) > 1])
        complexity = self._calculate_chain_complexity(
            len(chain_data), max_depth, branch_count, len(convergence_points)
        )
        
        return ReasoningDepth(
            current_depth=depths.get(chain_data[-1].get("ulid_id"), 1) if chain_data else 1,
            max_depth_reached=max_depth,
            branch_count=branch_count,
            convergence_points=convergence_points,
            complexity_metric=complexity
        )
    
    def _calculate_complexity(self, content: str, pattern_type: str) -> float:
        """Calculate complexity score for thought content."""
        # Base complexity on content length and structure
        base_score = min(1.0, len(content) / 1000)  # Normalize to 1000 chars
        
        # Adjust based on pattern type
        pattern_weights = {
            "analysis": 0.7,
            "synthesis": 0.9,
            "validation": 0.5,
            "hypothesis": 0.8,
            "causal": 0.6,
            "deductive": 0.8,
            "inductive": 0.7,
            "abductive": 0.9,
            "analogical": 0.8,
            "critical": 0.85,
            "meta": 1.0  # Meta-reasoning is most complex
        }
        
        weight = pattern_weights.get(pattern_type, 0.5)
        
        # Check for complex structures (nested clauses, conditionals)
        complex_indicators = ["if", "then", "however", "although", "moreover", "furthermore"]
        complexity_boost = sum(0.05 for ind in complex_indicators if ind in content.lower())
        
        return min(1.0, base_score * weight + complexity_boost)
    
    def _calculate_chain_complexity(self, chain_length: int, max_depth: int,
                                   branch_count: int, convergence_count: int) -> float:
        """Calculate overall chain complexity metric."""
        # Normalize factors
        length_factor = min(1.0, chain_length / 20)  # Normalize to 20 steps
        depth_factor = min(1.0, max_depth / 10)  # Normalize to depth 10
        branch_factor = min(1.0, branch_count / 5)  # Normalize to 5 branches
        convergence_factor = min(1.0, convergence_count / 3)  # Normalize to 3 convergences
        
        # Weighted combination
        complexity = (
            length_factor * 0.2 +
            depth_factor * 0.3 +
            branch_factor * 0.3 +
            convergence_factor * 0.2
        )
        
        return complexity
    
    def identify_agent_capabilities(self, agent_id: str, 
                                   history: List[Dict]) -> AgentCapability:
        """
        Identify and track AI agent capabilities from reasoning history.
        
        Args:
            agent_id: Agent identifier
            history: Historical reasoning data for the agent
            
        Returns:
            AgentCapability profile
        """
        capabilities = set()
        performance_history = {}
        
        # Analyze history to identify capabilities
        for thought in history:
            if thought.get("agent_id") == agent_id:
                reasoning_type = thought.get("reasoning_type")
                if reasoning_type:
                    capabilities.add(reasoning_type)
                    
                # Track performance (confidence as proxy)
                confidence = thought.get("confidence_level", 0.5)
                if reasoning_type not in performance_history:
                    performance_history[reasoning_type] = []
                performance_history[reasoning_type].append(confidence)
        
        # Calculate average performance per capability
        avg_performance = {
            cap: sum(scores) / len(scores) 
            for cap, scores in performance_history.items()
        }
        
        # Determine specialization (highest performing capability)
        specialization = None
        if avg_performance:
            specialization = max(avg_performance.items(), key=lambda x: x[1])[0]
        
        # Calculate overall reliability
        all_scores = [s for scores in performance_history.values() for s in scores]
        reliability = sum(all_scores) / len(all_scores) if all_scores else 0.8
        
        return AgentCapability(
            agent_id=agent_id,
            capabilities=list(capabilities),
            specialization=specialization,
            performance_history=avg_performance,
            reliability_score=reliability
        )


class MetadataGenerator:
    """
    Intelligent metadata generator for autonomous AI reasoning chains.
    Provides context-aware templates and enrichment capabilities.
    """
    
    def __init__(self, db_manager=None):
        """
        Initialize metadata generator with AI reasoning capabilities.
        
        Args:
            db_manager: Database manager for metadata validation and consistency
        """
        self.db_manager = db_manager
        self.templates = self._initialize_templates()
        self.validation_rules = self._initialize_validation_rules()
        self._metadata_cache = {}  # Cache for recently generated metadata
        
        # Phase 2B: AI reasoning pattern detection
        self._pattern_cache = {}  # Cache for detected patterns
        self._agent_registry = {}  # Registry of known AI agents and capabilities
        self._reasoning_analyzer = ReasoningAnalyzer()  # Initialize reasoning analyzer
        
    def _initialize_templates(self) -> Dict[MetadataTemplate, Dict[str, Any]]:
        """Initialize metadata templates for different reasoning scenarios."""
        return {
            MetadataTemplate.AUTONOMOUS_REASONING: {
                "template_type": "autonomous_reasoning",
                "required_fields": ["reasoning_type", "confidence_level", "agent_id"],
                "base_structure": {
                    "autonomous": True,
                    "reasoning_type": None,
                    "confidence_level": 0.0,
                    "agent_id": None,
                    "generation_timestamp": None,
                    "context_sources": [],
                    "decision_points": [],
                    "reasoning_trace": []
                }
            },
            MetadataTemplate.AGENT_HANDOFF: {
                "template_type": "agent_handoff",
                "required_fields": ["source_agent", "target_agent", "handoff_context"],
                "base_structure": {
                    "handoff": True,
                    "source_agent": None,
                    "target_agent": None,
                    "handoff_timestamp": None,
                    "handoff_context": {},
                    "chain_continuity": True,
                    "preserved_context": {}
                }
            },
            MetadataTemplate.CHAIN_CONTINUATION: {
                "template_type": "chain_continuation",
                "required_fields": ["parent_chain_id", "step_number", "previous_thought_id"],
                "base_structure": {
                    "chain_continuation": True,
                    "parent_chain_id": None,
                    "step_number": 0,
                    "previous_thought_id": None,
                    "chain_integrity": True,
                    "continuity_verified": False
                }
            },
            MetadataTemplate.PARALLEL_REASONING: {
                "template_type": "parallel_reasoning",
                "required_fields": ["parent_chain_id", "parallel_chains", "coordination_id"],
                "base_structure": {
                    "parallel_reasoning": True,
                    "parent_chain_id": None,
                    "parallel_chains": [],
                    "coordination_id": None,
                    "sync_points": [],
                    "merge_strategy": None
                }
            },
            MetadataTemplate.ERROR_RECOVERY: {
                "template_type": "error_recovery",
                "required_fields": ["error_type", "recovery_strategy", "original_chain_id"],
                "base_structure": {
                    "error_recovery": True,
                    "error_type": None,
                    "recovery_strategy": None,
                    "original_chain_id": None,
                    "recovery_timestamp": None,
                    "corrections_applied": []
                }
            },
            MetadataTemplate.SESSION_INIT: {
                "template_type": "session_initialization",
                "required_fields": ["session_id", "agent_id", "initialization_context"],
                "base_structure": {
                    "session_init": True,
                    "session_id": None,
                    "agent_id": None,
                    "initialization_timestamp": None,
                    "initialization_context": {},
                    "session_goals": [],
                    "expected_chain_length": None
                }
            },
            MetadataTemplate.CONCLUSION_SUMMARY: {
                "template_type": "conclusion_summary",
                "required_fields": ["chain_id", "conclusion_type", "summary"],
                "base_structure": {
                    "conclusion": True,
                    "chain_id": None,
                    "conclusion_type": None,
                    "summary": None,
                    "conclusion_timestamp": None,
                    "chain_metrics": {},
                    "final_confidence": 0.0
                }
            }
        }
    
    def _initialize_validation_rules(self) -> Dict[str, Any]:
        """Initialize validation rules for metadata consistency."""
        return {
            "field_constraints": {
                "session_id": {"max_length": 128, "pattern": r"^[a-zA-Z0-9_-]+$"},
                "agent_id": {"max_length": 64, "pattern": r"^[a-zA-Z0-9_-]+$"},
                "confidence_level": {"min": 0.0, "max": 1.0, "type": float},
                "step_number": {"min": 1, "type": int},
                "timestamp": {"format": "ISO8601", "timezone_required": True}
            },
            "consistency_rules": {
                "chain_continuity": "previous_thought_id must exist for step_number > 1",
                "parallel_coordination": "parallel_chains must have valid chain_ids",
                "handoff_validation": "source_agent and target_agent must be different",
                "confidence_progression": "confidence should increase or stabilize over chain"
            },
            "atomic_requirements": {
                "transaction_id": "Required for multi-database operations",
                "database_consistency": "All databases must report success",
                "rollback_capability": "Metadata must support rollback scenarios"
            }
        }
    
    def generate_metadata(self, 
                         template: MetadataTemplate,
                         context: ReasoningContext,
                         enrichment: Optional[MetadataEnrichment] = None,
                         custom_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate intelligent metadata using templates and context.
        
        Args:
            template: Metadata template to use
            context: Reasoning context for metadata generation
            enrichment: Optional enrichment data
            custom_fields: Additional custom fields to include
            
        Returns:
            Generated metadata dictionary with full context
        """
        try:
            # Get base template
            template_config = self.templates[template]
            metadata = template_config["base_structure"].copy()
            
            # Apply reasoning context
            metadata = self._apply_reasoning_context(metadata, context)
            
            # Add enrichment if provided
            if enrichment:
                metadata = self._apply_enrichment(metadata, enrichment)
            
            # Add custom fields
            if custom_fields:
                metadata.update(custom_fields)
            
            # Generate automatic fields
            metadata = self._generate_automatic_fields(metadata, template, context)
            
            # Validate metadata
            validation_result = self.validate_metadata(metadata, template)
            if not validation_result["valid"]:
                logger.warning(f"Metadata validation warnings: {validation_result['warnings']}")
                metadata["_validation_warnings"] = validation_result["warnings"]
            
            # Cache metadata for consistency checking
            cache_key = self._generate_cache_key(metadata)
            self._metadata_cache[cache_key] = {
                "metadata": metadata,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "template": template.value
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to generate metadata: {e}")
            # Return minimal valid metadata on error
            return self._generate_fallback_metadata(template, context, str(e))
    
    def _apply_reasoning_context(self, metadata: Dict[str, Any], 
                                context: ReasoningContext) -> Dict[str, Any]:
        """Apply enhanced reasoning context to metadata with AI intelligence."""
        metadata["reasoning_type"] = context.reasoning_type.value
        metadata["confidence_level"] = context.confidence_level
        metadata["decision_points"] = context.decision_points
        
        if context.agent_id:
            metadata["agent_id"] = context.agent_id
            
        if context.parent_chain_id:
            metadata["parent_chain_id"] = context.parent_chain_id
            
        if context.parallel_chains:
            metadata["parallel_chains"] = context.parallel_chains
            
        if context.error_corrections:
            metadata["error_corrections"] = context.error_corrections
            
        if context.handoff_context:
            metadata["handoff_context"] = context.handoff_context
            metadata["source_agent"] = context.caller_agent
            metadata["target_agent"] = context.agent_id
        
        # Phase 2B: Apply AI reasoning enhancements
        if context.thought_patterns:
            metadata["thought_patterns"] = [
                {
                    "type": p.pattern_type,
                    "confidence": p.confidence,
                    "indicators": p.indicators,
                    "complexity": p.complexity_score
                }
                for p in context.thought_patterns
            ]
        
        if context.agent_capability:
            metadata["agent_capability"] = {
                "agent_id": context.agent_capability.agent_id,
                "capabilities": context.agent_capability.capabilities,
                "specialization": context.agent_capability.specialization,
                "reliability": context.agent_capability.reliability_score
            }
        
        if context.reasoning_depth:
            metadata["reasoning_depth"] = {
                "current": context.reasoning_depth.current_depth,
                "max_reached": context.reasoning_depth.max_depth_reached,
                "branches": context.reasoning_depth.branch_count,
                "convergences": context.reasoning_depth.convergence_points,
                "complexity": context.reasoning_depth.complexity_metric
            }
        
        if context.semantic_context:
            metadata["semantic_context"] = context.semantic_context
        
        if context.hypothesis_chain:
            metadata["hypothesis_chain"] = context.hypothesis_chain
            
        return metadata
    
    def _apply_enrichment(self, metadata: Dict[str, Any], 
                         enrichment: MetadataEnrichment) -> Dict[str, Any]:
        """Apply enrichment data to metadata."""
        metadata["generation_metadata"] = {
            "timestamp": enrichment.timestamp,
            "method": enrichment.generation_method,
            "extraction_sources": enrichment.extraction_sources,
            "context_confidence": enrichment.context_confidence,
            "validation_status": enrichment.validation_status
        }
        
        if enrichment.atomic_transaction_id:
            metadata["atomic_transaction_id"] = enrichment.atomic_transaction_id
            
        if enrichment.database_consistency:
            metadata["database_consistency"] = enrichment.database_consistency
            
        if enrichment.reasoning_trace:
            metadata["reasoning_trace"] = enrichment.reasoning_trace
            
        return metadata
    
    def _generate_automatic_fields(self, metadata: Dict[str, Any],
                                  template: MetadataTemplate,
                                  context: ReasoningContext) -> Dict[str, Any]:
        """Generate automatic fields based on template and context."""
        # Add timestamp if not present
        if "timestamp" not in metadata and "generation_timestamp" not in metadata:
            metadata["generation_timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Generate unique metadata ID
        metadata["metadata_id"] = self._generate_metadata_id(template, context)
        
        # Add template information
        metadata["template_used"] = template.value
        
        # Calculate metadata hash for integrity
        metadata["metadata_hash"] = self._calculate_metadata_hash(metadata)
        
        # Add chain relationship indicators
        if context.parent_chain_id:
            metadata["chain_relationships"] = {
                "parent": context.parent_chain_id,
                "siblings": context.parallel_chains,
                "continuity_type": "linear" if not context.parallel_chains else "parallel"
            }
        
        # Add confidence indicators
        metadata["confidence_indicators"] = {
            "overall": context.confidence_level,
            "decision_confidence": self._calculate_decision_confidence(context.decision_points),
            "chain_confidence": self._calculate_chain_confidence(metadata)
        }
        
        return metadata
    
    def _generate_metadata_id(self, template: MetadataTemplate, 
                             context: ReasoningContext) -> str:
        """Generate unique metadata ID."""
        components = [
            template.value,
            context.reasoning_type.value,
            str(context.confidence_level),
            context.agent_id or "unknown",
            datetime.now(timezone.utc).isoformat()
        ]
        hash_input = "_".join(components)
        return f"meta_{hashlib.sha256(hash_input.encode()).hexdigest()[:12]}"
    
    def _calculate_metadata_hash(self, metadata: Dict[str, Any]) -> str:
        """Calculate hash of metadata for integrity checking."""
        # Remove hash field itself to avoid recursion
        metadata_copy = {k: v for k, v in metadata.items() if k != "metadata_hash"}
        metadata_str = json.dumps(metadata_copy, sort_keys=True, default=str)
        return hashlib.sha256(metadata_str.encode()).hexdigest()
    
    def _calculate_decision_confidence(self, decision_points: List[Dict[str, Any]]) -> float:
        """Calculate aggregate confidence from decision points."""
        if not decision_points:
            return 0.5  # Neutral confidence if no decisions
            
        confidences = [dp.get("confidence", 0.5) for dp in decision_points]
        return sum(confidences) / len(confidences)
    
    def _calculate_chain_confidence(self, metadata: Dict[str, Any]) -> float:
        """Calculate chain confidence based on metadata completeness."""
        required_fields = ["reasoning_type", "agent_id", "generation_timestamp"]
        present_fields = sum(1 for field in required_fields if field in metadata)
        
        base_confidence = present_fields / len(required_fields)
        
        # Boost confidence if chain relationships are defined
        if "chain_relationships" in metadata:
            base_confidence = min(1.0, base_confidence + 0.2)
            
        # Boost confidence if validation passed
        if "_validation_warnings" not in metadata:
            base_confidence = min(1.0, base_confidence + 0.1)
            
        return base_confidence
    
    def _generate_cache_key(self, metadata: Dict[str, Any]) -> str:
        """Generate cache key for metadata."""
        key_components = [
            metadata.get("session_id", ""),
            metadata.get("agent_id", ""),
            metadata.get("parent_chain_id", ""),
            str(metadata.get("step_number", 0))
        ]
        return "_".join(filter(None, key_components))
    
    def _generate_fallback_metadata(self, template: MetadataTemplate,
                                   context: ReasoningContext,
                                   error: str) -> Dict[str, Any]:
        """Generate minimal fallback metadata on error."""
        return {
            "fallback": True,
            "template_attempted": template.value,
            "reasoning_type": context.reasoning_type.value if context else "unknown",
            "generation_error": error,
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata_id": str(uuid.uuid4()),
            "confidence_level": 0.0
        }
    
    def validate_metadata(self, metadata: Dict[str, Any],
                         template: MetadataTemplate) -> Dict[str, Any]:
        """
        Validate metadata against template requirements and consistency rules.
        
        Args:
            metadata: Metadata to validate
            template: Template used for generation
            
        Returns:
            Validation result with status and warnings
        """
        result = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check required fields for template
        template_config = self.templates[template]
        for required_field in template_config["required_fields"]:
            if required_field not in metadata or metadata[required_field] is None:
                result["warnings"].append(f"Missing required field: {required_field}")
        
        # Check field constraints
        for field, value in metadata.items():
            if field in self.validation_rules["field_constraints"]:
                constraints = self.validation_rules["field_constraints"][field]
                
                # Check max length
                if "max_length" in constraints and isinstance(value, str):
                    if len(value) > constraints["max_length"]:
                        result["warnings"].append(
                            f"Field {field} exceeds max length: {len(value)} > {constraints['max_length']}"
                        )
                
                # Check value range
                if "min" in constraints and isinstance(value, (int, float)):
                    if value < constraints["min"]:
                        result["warnings"].append(
                            f"Field {field} below minimum: {value} < {constraints['min']}"
                        )
                if "max" in constraints and isinstance(value, (int, float)):
                    if value > constraints["max"]:
                        result["warnings"].append(
                            f"Field {field} above maximum: {value} > {constraints['max']}"
                        )
        
        # Check consistency rules
        if "step_number" in metadata and metadata.get("step_number", 1) > 1:
            if not metadata.get("previous_thought_id"):
                result["warnings"].append("Chain continuity broken: missing previous_thought_id for step > 1")
        
        if metadata.get("source_agent") == metadata.get("target_agent"):
            result["warnings"].append("Invalid handoff: source and target agents are the same")
        
        # Set valid to False if there are errors
        if result["errors"]:
            result["valid"] = False
            
        return result
    
    def enrich_with_chain_context(self, metadata: Dict[str, Any],
                                 chain_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Enrich metadata with chain context and relationships.
        
        Args:
            metadata: Base metadata to enrich
            chain_data: Historical chain data for context
            
        Returns:
            Enriched metadata with chain relationships
        """
        if not chain_data:
            return metadata
            
        # Add chain statistics
        metadata["chain_context"] = {
            "chain_length": len(chain_data),
            "total_decisions": sum(len(t.get("decision_points", [])) for t in chain_data),
            "confidence_progression": [t.get("confidence_level", 0.0) for t in chain_data],
            "reasoning_types": list(set(t.get("reasoning_type", "unknown") for t in chain_data))
        }
        
        # Identify chain patterns
        patterns = self._identify_chain_patterns(chain_data)
        if patterns:
            metadata["chain_patterns"] = patterns
            
        # Add relationship graph
        metadata["chain_relationships"] = self._build_relationship_graph(chain_data)
        
        return metadata
    
    def _identify_chain_patterns(self, chain_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify patterns in reasoning chain."""
        patterns = {}
        
        # Check for iterative refinement
        reasoning_types = [t.get("reasoning_type") for t in chain_data]
        if reasoning_types.count("iterative_refinement") > 1:
            patterns["iterative_refinement"] = True
            patterns["refinement_cycles"] = reasoning_types.count("iterative_refinement")
            
        # Check for error recovery
        if any(t.get("error_recovery") for t in chain_data):
            patterns["error_recovery_present"] = True
            patterns["recovery_points"] = [
                i for i, t in enumerate(chain_data) if t.get("error_recovery")
            ]
            
        # Check for parallel reasoning
        parallel_chains = set()
        for t in chain_data:
            if t.get("parallel_chains"):
                parallel_chains.update(t["parallel_chains"])
        if parallel_chains:
            patterns["parallel_reasoning"] = True
            patterns["parallel_chain_count"] = len(parallel_chains)
            
        return patterns
    
    def _build_relationship_graph(self, chain_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build relationship graph from chain data."""
        graph = {
            "nodes": [],
            "edges": [],
            "clusters": []
        }
        
        # Create nodes
        for i, thought in enumerate(chain_data):
            graph["nodes"].append({
                "id": thought.get("ulid_id", f"node_{i}"),
                "type": thought.get("reasoning_type", "unknown"),
                "confidence": thought.get("confidence_level", 0.0),
                "step": thought.get("step_number", i + 1)
            })
        
        # Create edges
        for i in range(len(chain_data) - 1):
            graph["edges"].append({
                "from": chain_data[i].get("ulid_id", f"node_{i}"),
                "to": chain_data[i + 1].get("ulid_id", f"node_{i+1}"),
                "type": "sequential"
            })
        
        # Identify clusters (parallel reasoning groups)
        parallel_groups = {}
        for thought in chain_data:
            if thought.get("parent_chain_id"):
                parent = thought["parent_chain_id"]
                if parent not in parallel_groups:
                    parallel_groups[parent] = []
                parallel_groups[parent].append(thought.get("ulid_id"))
                
        for parent, children in parallel_groups.items():
            graph["clusters"].append({
                "parent": parent,
                "children": children,
                "type": "parallel_reasoning"
            })
            
        return graph
    
    async def ensure_metadata_consistency(self, metadata: Dict[str, Any],
                                         transaction_id: str) -> Dict[str, Any]:
        """
        Ensure metadata consistency across atomic transactions.
        
        Args:
            metadata: Metadata to check
            transaction_id: Atomic transaction ID
            
        Returns:
            Consistency check result
        """
        consistency_result = {
            "consistent": True,
            "transaction_id": transaction_id,
            "databases_checked": [],
            "inconsistencies": []
        }
        
        if not self.db_manager:
            logger.warning("No database manager available for consistency check")
            return consistency_result
            
        try:
            # Check each database for metadata consistency
            databases = ["sqlite", "neo4j", "redis", "faiss"]
            
            for db_name in databases:
                if hasattr(self.db_manager, db_name):
                    db_status = await self._check_database_consistency(
                        db_name, metadata, transaction_id
                    )
                    consistency_result["databases_checked"].append(db_name)
                    
                    if not db_status["consistent"]:
                        consistency_result["consistent"] = False
                        consistency_result["inconsistencies"].append({
                            "database": db_name,
                            "issue": db_status["issue"]
                        })
                        
        except Exception as e:
            logger.error(f"Consistency check failed: {e}")
            consistency_result["consistent"] = False
            consistency_result["error"] = str(e)
            
        return consistency_result
    
    async def _check_database_consistency(self, db_name: str,
                                         metadata: Dict[str, Any],
                                         transaction_id: str) -> Dict[str, Any]:
        """Check consistency for specific database."""
        # This would be implemented with actual database checks
        # For now, return a placeholder that indicates consistency
        return {
            "consistent": True,
            "database": db_name,
            "transaction_id": transaction_id,
            "metadata_stored": True
        }
    
    def generate_template_from_context(self, context: Dict[str, Any]) -> MetadataTemplate:
        """
        Automatically determine best template from context.
        
        Args:
            context: Context dictionary with reasoning information
            
        Returns:
            Best matching metadata template
        """
        # Check for specific context indicators
        if context.get("handoff") or context.get("source_agent"):
            return MetadataTemplate.AGENT_HANDOFF
            
        if context.get("error_recovery") or context.get("corrections_applied"):
            return MetadataTemplate.ERROR_RECOVERY
            
        if context.get("parallel_chains") or context.get("parallel_reasoning"):
            return MetadataTemplate.PARALLEL_REASONING
            
        if context.get("previous_thought_id") and context.get("step_number", 1) > 1:
            return MetadataTemplate.CHAIN_CONTINUATION
            
        if context.get("conclusion") or context.get("conclusion_type"):
            return MetadataTemplate.CONCLUSION_SUMMARY
            
        if context.get("session_init") or context.get("step_number", 1) == 1:
            return MetadataTemplate.SESSION_INIT
            
        # Default to autonomous reasoning
        return MetadataTemplate.AUTONOMOUS_REASONING
    
    def generate_ai_enhanced_metadata(self, content: str, 
                                     session_context: Dict[str, Any],
                                     chain_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Generate AI-enhanced metadata with intelligent pattern detection.
        
        This is the main Phase 2B enhancement - provides rich AI reasoning context
        for autonomous agents through intelligent content analysis.
        
        Args:
            content: Thought content to analyze
            session_context: Current session context
            chain_history: Optional chain history for depth analysis
            
        Returns:
            Enhanced metadata with AI reasoning intelligence
        """
        start_time = time.time()
        
        try:
            # Analyze thought content for patterns
            thought_patterns = self._reasoning_analyzer.analyze_thought_content(
                content, session_context
            )
            
            # Classify reasoning type from patterns
            reasoning_type = self._reasoning_analyzer.classify_reasoning_type(
                content, thought_patterns
            )
            
            # Calculate reasoning depth if chain history available
            reasoning_depth = None
            if chain_history:
                current_step = session_context.get("step_number", len(chain_history) + 1)
                reasoning_depth = self._reasoning_analyzer.calculate_reasoning_depth(
                    chain_history, current_step
                )
            
            # Identify agent capabilities if history available
            agent_capability = None
            agent_id = session_context.get("agent_id")
            if agent_id and chain_history:
                # Check cache first
                if agent_id in self._agent_registry:
                    agent_capability = self._agent_registry[agent_id]
                else:
                    agent_capability = self._reasoning_analyzer.identify_agent_capabilities(
                        agent_id, chain_history
                    )
                    self._agent_registry[agent_id] = agent_capability
            
            # Build semantic context from content analysis
            semantic_context = self._build_semantic_context(content, thought_patterns)
            
            # Extract hypothesis chain if present
            hypothesis_chain = self._extract_hypothesis_chain(content, chain_history)
            
            # Create enhanced reasoning context
            reasoning_context = ReasoningContext(
                reasoning_type=reasoning_type,
                confidence_level=session_context.get("confidence", 0.8),
                decision_points=session_context.get("decision_points", []),
                parent_chain_id=session_context.get("parent_chain_id"),
                parallel_chains=session_context.get("parallel_chains", []),
                error_corrections=session_context.get("error_corrections", []),
                agent_id=agent_id,
                caller_agent=session_context.get("caller_agent"),
                handoff_context=session_context.get("handoff_context"),
                thought_patterns=thought_patterns,
                agent_capability=agent_capability,
                reasoning_depth=reasoning_depth,
                semantic_context=semantic_context,
                hypothesis_chain=hypothesis_chain
            )
            
            # Select appropriate template
            template = self.generate_template_from_context(session_context)
            
            # Build enrichment data
            enrichment = MetadataEnrichment(
                timestamp=datetime.now(timezone.utc).isoformat(),
                generation_method='ai_enhanced_analysis',
                extraction_sources=['content_analysis', 'pattern_detection', 'chain_analysis'],
                context_confidence=min(1.0, sum(p.confidence for p in thought_patterns) / max(1, len(thought_patterns))),
                validation_status='ai_validated',
                reasoning_trace=self._build_ai_reasoning_trace(thought_patterns, reasoning_type)
            )
            
            # Generate the enhanced metadata
            metadata = self.generate_metadata(
                template=template,
                context=reasoning_context,
                enrichment=enrichment,
                custom_fields=session_context
            )
            
            # Add performance metrics
            generation_time_ms = (time.time() - start_time) * 1000
            metadata["ai_enhancement"] = {
                "generation_time_ms": generation_time_ms,
                "patterns_detected": len(thought_patterns),
                "reasoning_classification": reasoning_type.value,
                "complexity_score": max(p.complexity_score for p in thought_patterns) if thought_patterns else 0.0,
                "sla_compliant": generation_time_ms < 200  # 200ms SLA
            }
            
            # Log performance
            if generation_time_ms > 200:
                logger.warning(f"AI metadata generation exceeded SLA: {generation_time_ms:.1f}ms")
            else:
                logger.debug(f"AI metadata generated in {generation_time_ms:.1f}ms")
            
            return metadata
            
        except Exception as e:
            logger.error(f"AI-enhanced metadata generation failed: {e}")
            # Fallback to basic generation
            return self._generate_fallback_ai_metadata(content, session_context, str(e))
    
    def _build_semantic_context(self, content: str, patterns: List[ThoughtPattern]) -> Dict[str, Any]:
        """Build semantic context from content and patterns."""
        # Extract key concepts (simplified - could use NLP for better extraction)
        concepts = []
        concept_indicators = ["concept", "idea", "principle", "theory", "model"]
        for indicator in concept_indicators:
            if indicator in content.lower():
                # Extract surrounding context
                concepts.append(indicator)
        
        # Build semantic relationships
        relationships = []
        if "because" in content.lower() or "therefore" in content.lower():
            relationships.append("causal")
        if "similar" in content.lower() or "like" in content.lower():
            relationships.append("analogical")
        if "however" in content.lower() or "but" in content.lower():
            relationships.append("contrastive")
        
        return {
            "concepts": concepts,
            "relationships": relationships,
            "pattern_summary": [p.pattern_type for p in patterns],
            "semantic_complexity": max(p.complexity_score for p in patterns) if patterns else 0.0
        }
    
    def _extract_hypothesis_chain(self, content: str, 
                                 chain_history: Optional[List[Dict]]) -> List[Dict[str, Any]]:
        """Extract hypothesis chain from content and history."""
        hypothesis_chain = []
        
        # Check for hypothesis indicators in content
        hypothesis_keywords = ["hypothesis", "assume", "suppose", "if", "predict"]
        for keyword in hypothesis_keywords:
            if keyword in content.lower():
                hypothesis_chain.append({
                    "type": "hypothesis",
                    "keyword": keyword,
                    "step": len(chain_history) + 1 if chain_history else 1
                })
        
        # Check history for hypothesis evolution
        if chain_history:
            for i, thought in enumerate(chain_history):
                thought_content = thought.get("content", "").lower()
                if any(kw in thought_content for kw in hypothesis_keywords):
                    hypothesis_chain.append({
                        "type": "historical_hypothesis",
                        "step": thought.get("step_number", i + 1),
                        "thought_id": thought.get("ulid_id")
                    })
        
        return hypothesis_chain
    
    def _build_ai_reasoning_trace(self, patterns: List[ThoughtPattern],
                                 reasoning_type: ReasoningType) -> List[Dict[str, Any]]:
        """Build AI reasoning trace from analysis results."""
        trace = []
        
        # Add pattern detection steps
        for pattern in patterns:
            trace.append({
                "step": "pattern_detection",
                "pattern": pattern.pattern_type,
                "confidence": pattern.confidence,
                "complexity": pattern.complexity_score
            })
        
        # Add reasoning classification
        trace.append({
            "step": "reasoning_classification",
            "type": reasoning_type.value,
            "method": "ai_analysis"
        })
        
        return trace
    
    def _generate_fallback_ai_metadata(self, content: str,
                                      session_context: Dict[str, Any],
                                      error: str) -> Dict[str, Any]:
        """Generate fallback metadata when AI enhancement fails."""
        return {
            "fallback": True,
            "ai_enhancement_error": error,
            "session_id": session_context.get("session_id"),
            "agent_id": session_context.get("agent_id"),
            "step_number": session_context.get("step_number", 1),
            "content_preview": content[:100] if content else "",
            "generation_timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata_id": str(uuid.uuid4()),
            "confidence_level": 0.5
        }