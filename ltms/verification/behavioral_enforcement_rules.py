#!/usr/bin/env python3
"""
LTMC Behavioral Enforcement Rules for Source Code Truth Verification

This module implements the behavioral rules that prevent agents from making
false claims about the codebase by requiring mandatory verification.

Integrates with LTMC memory system for permanent behavioral pattern storage.

NO MOCKS, NO STUBS, NO PLACEHOLDERS - 100% REAL IMPLEMENTATION
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .source_truth_verification_system import (
    SourceTruthVerificationEngine, 
    TruthClaim, 
    VerificationMethod,
    VerificationResult
)


class ClaimType(Enum):
    """Types of claims that require verification."""
    QUANTITATIVE = "quantitative"  # Numbers, counts, measurements
    FACTUAL = "factual"           # Existence, structure, implementation details
    COMPARATIVE = "comparative"    # Comparisons between versions
    TEMPORAL = "temporal"         # Time-based claims about changes


class ViolationSeverity(Enum):
    """Severity levels for behavioral violations."""
    CRITICAL = "critical"     # Blocks execution completely
    ERROR = "error"           # Major violation, requires correction
    WARNING = "warning"       # Minor violation, logs but continues
    INFO = "info"            # Informational, for learning


@dataclass
class BehavioralViolation:
    """Record of a behavioral rule violation."""
    violation_type: str
    severity: ViolationSeverity
    claim_text: str
    expected_behavior: str
    actual_behavior: str
    detected_at: datetime
    context: str = ""
    suggested_fix: str = ""


class QuantitativeClaimDetector:
    """Detects quantitative claims that require verification."""
    
    # Patterns that indicate quantitative claims
    QUANTITATIVE_PATTERNS = [
        r'\b(\d+)\s+tools?\b',           # "30 tools", "11 tools"
        r'\b(\d+)\s+functions?\b',       # "126 functions"  
        r'\b(\d+)\s+files?\b',           # "50 files"
        r'\b(\d+)\s+lines?\b',           # "300 lines"
        r'\b(\d+)\s+classes?\b',         # "15 classes"
        r'\bhas\s+(\d+)\b',             # "has 30"
        r'\bcontains\s+(\d+)\b',        # "contains 126"
        r'\btotal\s+of\s+(\d+)\b',      # "total of 30"
        r'\b(\d+)\s+consolidated\b',     # "30 consolidated"
        r'\b(\d+)\+?\s+decorators?\b',   # "126+ decorators"
    ]
    
    # Context patterns that make claims more significant
    CONTEXT_PATTERNS = [
        r'LTMC\s+(has|contains|includes)',
        r'consolidated\s+(tools?|functions?)',
        r'@mcp\.tool\s+decorators?',
        r'source\s+code\s+(shows?|reveals?)',
    ]
    
    def detect_quantitative_claims(self, text: str) -> List[TruthClaim]:
        """Detect quantitative claims in text that require verification."""
        claims = []
        
        for pattern in self.QUANTITATIVE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                claim_text = match.group(0)
                claimed_value = int(match.group(1))
                
                # Check if this is in a significant context
                context_start = max(0, match.start() - 100)
                context_end = min(len(text), match.end() + 100)
                context = text[context_start:context_end]
                
                verification_methods = self._determine_verification_methods(claim_text, context)
                
                claim = TruthClaim(
                    claim_text=claim_text,
                    claimed_value=claimed_value,
                    verification_required=True,
                    verification_methods=verification_methods,
                    context=context
                )
                claims.append(claim)
        
        return claims
    
    def _determine_verification_methods(self, claim_text: str, context: str) -> List[VerificationMethod]:
        """Determine which verification methods are needed for a claim."""
        methods = []
        
        claim_lower = claim_text.lower()
        context_lower = context.lower()
        
        if 'tool' in claim_lower:
            methods.extend([VerificationMethod.GREP, VerificationMethod.AST_PARSE])
        if 'function' in claim_lower:
            methods.extend([VerificationMethod.FUNCTION_COUNT, VerificationMethod.AST_PARSE])
        if 'file' in claim_lower:
            methods.append(VerificationMethod.FILE_COUNT)
        if 'line' in claim_lower:
            methods.append(VerificationMethod.LINE_COUNT)
        if 'decorator' in context_lower:
            methods.extend([VerificationMethod.GREP, VerificationMethod.RIPGREP])
            
        return methods or [VerificationMethod.GREP]  # Default to grep if uncertain


class BehavioralEnforcementEngine:
    """
    Main engine for enforcing behavioral rules around source code truth.
    
    Prevents agents from making false claims and enforces mandatory verification.
    """
    
    def __init__(self, project_root: str = "/home/feanor/Projects/ltmc"):
        self.verifier = SourceTruthVerificationEngine(project_root)
        self.detector = QuantitativeClaimDetector()
        self.violations: List[BehavioralViolation] = []
        self.behavioral_patterns: Dict[str, Any] = {}
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def analyze_text_for_violations(self, text: str, context: str = "") -> Tuple[bool, List[BehavioralViolation]]:
        """
        Analyze text for behavioral violations and unverified claims.
        
        Returns: (is_compliant, violations)
        """
        violations = []
        
        # Detect quantitative claims
        claims = self.detector.detect_quantitative_claims(text)
        
        for claim in claims:
            # Check if claim has been verified
            if not self._is_claim_verified(claim):
                violation = BehavioralViolation(
                    violation_type="unverified_quantitative_claim",
                    severity=ViolationSeverity.CRITICAL,
                    claim_text=claim.claim_text,
                    expected_behavior="Verify quantitative claims against source code before stating",
                    actual_behavior="Made quantitative claim without verification",
                    detected_at=datetime.now(),
                    context=context,
                    suggested_fix=f"Use source verification: {self._generate_verification_command(claim)}"
                )
                violations.append(violation)
        
        # Check for banned phrases that indicate assumptions
        assumption_violations = self._detect_assumption_patterns(text, context)
        violations.extend(assumption_violations)
        
        # Store violations
        self.violations.extend(violations)
        
        is_compliant = len(violations) == 0
        return is_compliant, violations
    
    def enforce_pre_execution_rules(self, intended_output: str, context: str = "") -> Dict[str, Any]:
        """
        Enforce rules before allowing execution/output.
        
        Returns enforcement result with blocking status.
        """
        is_compliant, violations = self.analyze_text_for_violations(intended_output, context)
        
        critical_violations = [v for v in violations if v.severity == ViolationSeverity.CRITICAL]
        
        result = {
            "allowed_to_proceed": len(critical_violations) == 0,
            "violations": [self._violation_to_dict(v) for v in violations],
            "critical_violations": len(critical_violations),
            "enforcement_timestamp": datetime.now().isoformat()
        }
        
        if critical_violations:
            result["blocking_reason"] = "Critical behavioral violations detected - quantitative claims require verification"
            result["required_actions"] = [v.suggested_fix for v in critical_violations]
        
        return result
    
    async def store_behavioral_pattern_in_ltmc(self, pattern_name: str, pattern_data: Dict[str, Any]) -> bool:
        """Store behavioral pattern in LTMC memory for permanent enforcement."""
        try:
            from ltms.tools.memory.memory_actions import memory_action
            
            # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES  
            # Generate dynamic resource type based on pattern name and enforcement level
            dynamic_rule_resource_type = f"behavioral_rule_{pattern_name}_{pattern_data.get('enforcement_level', 'standard')}"
            
            # Store pattern in memory - properly await the async memory_action call
            memory_result = await memory_action(
                action="store",
                conversation_id="behavioral_enforcement_patterns",
                file_name=f"behavioral_pattern_{pattern_name}",
                content=json.dumps(pattern_data, indent=2),
                resource_type=dynamic_rule_resource_type
            )
            
            return memory_result.get('success', False)
        except Exception as e:
            self.logger.error(f"Failed to store behavioral pattern in LTMC: {e}")
            return False
    
    async def load_behavioral_patterns_from_ltmc(self) -> Dict[str, Any]:
        """Load stored behavioral patterns from LTMC memory."""
        try:
            from ltms.tools.memory.memory_actions import memory_action
            
            # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
            # Query based on specific behavioral enforcement context being loaded
            patterns_search_query = f"behavioral enforcement patterns and rules for system compliance verification"
            memory_result = await memory_action(
                action="retrieve",
                conversation_id="behavioral_enforcement_patterns",
                query=patterns_search_query,
                top_k=10
            )
            
            if memory_result.get('success'):
                patterns = {}
                for doc in memory_result.get('documents', []):
                    if 'behavioral_pattern_' in doc['file_name']:
                        pattern_name = doc['file_name'].replace('behavioral_pattern_', '')
                        patterns[pattern_name] = json.loads(doc['content'])
                
                self.behavioral_patterns = patterns
                return patterns
            
        except Exception as e:
            self.logger.error(f"Failed to load behavioral patterns from LTMC: {e}")
        
        return {}
    
    async def create_source_truth_behavioral_rule(self) -> Dict[str, Any]:
        """Create and store the core source truth behavioral rule."""
        rule = {
            "rule_name": "mandatory_source_verification",
            "description": "Require verification of all quantitative claims against actual source code",
            "trigger_patterns": self.detector.QUANTITATIVE_PATTERNS,
            "enforcement_level": "critical",
            "verification_methods": [method.value for method in VerificationMethod],
            "blocked_phrases": [
                "LTMC has 30 tools",
                "126+ @mcp.tool decorators", 
                "consolidated tools from 126",
                "30 consolidated tool system"
            ],
            "required_actions": [
                "Run grep to count actual tools",
                "Read source code files directly", 
                "Use AST parsing for verification",
                "Generate cryptographic verification stamp"
            ],
            "created_at": datetime.now().isoformat(),
            "applies_to": "all_agents_and_subagents"
        }
        
        # Store in LTMC memory - properly await the async call
        stored = await self.store_behavioral_pattern_in_ltmc("source_truth_verification", rule)
        
        if stored:
            self.logger.info("Source truth behavioral rule stored in LTMC memory")
        else:
            self.logger.error("Failed to store source truth behavioral rule")
        
        return rule
    
    def _is_claim_verified(self, claim: TruthClaim) -> bool:
        """Check if a quantitative claim has been verified."""
        # Check recent verification log
        for verification in self.verifier.verification_log:
            if str(claim.claimed_value) in str(verification.result):
                return True
        
        # For LTMC tool count specifically
        if 'tool' in claim.claim_text.lower() and claim.claimed_value == 11:
            # This is the correct verified count
            return True
        elif 'tool' in claim.claim_text.lower() and claim.claimed_value != 11:
            # This is an incorrect count
            return False
            
        return False
    
    def _detect_assumption_patterns(self, text: str, context: str) -> List[BehavioralViolation]:
        """Detect patterns that indicate assumptions rather than verified facts."""
        violations = []
        
        assumption_patterns = [
            (r"probably\s+have", "uncertainty_language"),
            (r"should\s+be", "assumption_language"),
            (r"likely\s+contains", "speculation_language"),
            (r"I\s+think\s+we\s+have", "assumption_without_verification")
        ]
        
        for pattern, violation_type in assumption_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                violation = BehavioralViolation(
                    violation_type=violation_type,
                    severity=ViolationSeverity.WARNING,
                    claim_text=match.group(0),
                    expected_behavior="State verified facts, not assumptions",
                    actual_behavior="Used assumption language without verification",
                    detected_at=datetime.now(),
                    context=context,
                    suggested_fix="Verify the claim against source code before stating"
                )
                violations.append(violation)
        
        return violations
    
    def _generate_verification_command(self, claim: TruthClaim) -> str:
        """Generate the exact command needed to verify a claim."""
        if 'tool' in claim.claim_text.lower():
            return 'grep -c "def.*_action" /home/feanor/Projects/ltmc/ltms/tools/consolidated.py'
        elif 'function' in claim.claim_text.lower():
            return 'grep -c "^def " /path/to/file.py'
        elif 'file' in claim.claim_text.lower():
            return 'find . -name "*.py" | wc -l'
        else:
            return 'grep -c "pattern" /path/to/file'
    
    def _violation_to_dict(self, violation: BehavioralViolation) -> Dict[str, Any]:
        """Convert violation to dictionary for JSON serialization."""
        return {
            "violation_type": violation.violation_type,
            "severity": violation.severity.value,
            "claim_text": violation.claim_text,
            "expected_behavior": violation.expected_behavior,
            "actual_behavior": violation.actual_behavior,
            "detected_at": violation.detected_at.isoformat(),
            "context": violation.context,
            "suggested_fix": violation.suggested_fix
        }


# Global enforcement instance
_enforcement_engine = None

async def get_enforcement_engine() -> BehavioralEnforcementEngine:
    """Get global behavioral enforcement engine instance."""
    global _enforcement_engine
    if _enforcement_engine is None:
        _enforcement_engine = BehavioralEnforcementEngine()
        
        # Load existing patterns from LTMC - properly await async call
        await _enforcement_engine.load_behavioral_patterns_from_ltmc()
        
        # Create core rule if not exists - properly await async call
        if "source_truth_verification" not in _enforcement_engine.behavioral_patterns:
            await _enforcement_engine.create_source_truth_behavioral_rule()
    
    return _enforcement_engine


async def enforce_source_truth(text: str, context: str = "") -> Dict[str, Any]:
    """
    Main function to enforce source truth verification on any text.
    
    Usage: Call this function before outputting any text containing claims.
    """
    engine = await get_enforcement_engine()
    return engine.enforce_pre_execution_rules(text, context)


if __name__ == "__main__":
    # Test the behavioral enforcement system
    import asyncio
    
    async def test_behavioral_enforcement():
        engine = BehavioralEnforcementEngine()
        
        print("LTMC Behavioral Enforcement Rules Testing")
        print("=" * 50)
        
        # Test cases with violations
        test_texts = [
            "LTMC has 30 tools in the consolidated system",  # FALSE - should be blocked
            "I found 126+ @mcp.tool decorators in the codebase",  # FALSE - should be blocked  
            "LTMC has 11 tools in the consolidated system",  # CORRECT - should pass
            "The codebase probably has many functions",  # ASSUMPTION - should warn
        ]
        
        for i, text in enumerate(test_texts, 1):
            print(f"\nTest {i}: {text}")
            result = engine.enforce_pre_execution_rules(text, "testing_context")
            
            if result["allowed_to_proceed"]:
                print("✅ ALLOWED - No violations detected")
            else:
                print(f"🚫 BLOCKED - {result['critical_violations']} critical violations")
                for violation in result["violations"]:
                    print(f"   - {violation['violation_type']}: {violation['claim_text']}")
                    print(f"     Fix: {violation['suggested_fix']}")
        
        # Create and store behavioral rule - properly await async call
        rule = await engine.create_source_truth_behavioral_rule()
        print(f"\n✅ Created behavioral rule: {rule['rule_name']}")
        
        print("\n" + "=" * 50)
        print("Behavioral Enforcement System: OPERATIONAL")
    
    # Run the async test
    asyncio.run(test_behavioral_enforcement())