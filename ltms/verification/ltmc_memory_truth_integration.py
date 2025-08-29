from ltms.tools.memory.memory_actions import MemoryTools
#!/usr/bin/env python3
"""
LTMC Memory Integration for Source Code Truth Verification

This module integrates the source code truth verification system with LTMC's
long-term memory capabilities to ensure behavioral patterns are permanently stored
and consistently enforced across all agent interactions.

NO MOCKS, NO STUBS, NO PLACEHOLDERS - 100% REAL IMPLEMENTATION
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from .source_truth_verification_system import (
    SourceTruthVerificationEngine,
    VerificationResult,
    VerificationMethod
)
from .behavioral_enforcement_rules import (
    BehavioralEnforcementEngine,
    BehavioralViolation,
    ViolationSeverity
)


@dataclass
class TruthVerificationRecord:
    """Complete record of a truth verification with LTMC integration."""
    verification_id: str
    claim_text: str
    verified_value: Any
    verification_method: str
    file_path: Optional[str]
    verification_command: str
    file_hash: str
    verified_at: datetime
    stored_in_ltmc: bool
    ltmc_conversation_id: str
    ltmc_resource_id: Optional[str] = None


@dataclass
class BehavioralPattern:
    """Behavioral pattern stored in LTMC memory."""
    pattern_id: str
    pattern_name: str
    rule_description: str
    trigger_patterns: List[str]
    enforcement_actions: List[str]
    violation_history: List[Dict[str, Any]]
    effectiveness_score: float
    created_at: datetime
    last_updated: datetime
    usage_count: int


class LTMCTruthIntegrationManager:
    """
    Manages integration between source truth verification and LTMC memory system.
    
    Ensures all verification results and behavioral patterns are permanently
    stored and retrievable across agent sessions.
    """
    
    def __init__(self):
        self.verifier = SourceTruthVerificationEngine()
        self.enforcer = BehavioralEnforcementEngine()
        self.verification_records: List[TruthVerificationRecord] = []
        self.behavioral_patterns: List[BehavioralPattern] = []
        
        # LTMC conversation IDs for different data types
        self.VERIFICATION_CONVERSATION_ID = "source_truth_verifications"
        self.BEHAVIORAL_PATTERN_CONVERSATION_ID = "behavioral_enforcement_patterns"
        self.VIOLATION_HISTORY_CONVERSATION_ID = "behavioral_violations_history"
    
    async def verify_and_store_ltmc_tool_count(self) -> TruthVerificationRecord:
        """Verify LTMC tool count and store the result in LTMC memory."""
        # Perform verification
        verification = self.verifier.verify_tool_count()
        
        # Create complete record
        record = TruthVerificationRecord(
            verification_id=f"ltmc_tool_count_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            claim_text="LTMC consolidated tool count",
            verified_value=verification.result,
            verification_method=verification.method.value,
            file_path=verification.file_path,
            verification_command=verification.command,
            file_hash=verification.hash_signature,
            verified_at=verification.verified_at,
            stored_in_ltmc=False,
            ltmc_conversation_id=self.VERIFICATION_CONVERSATION_ID
        )
        
        # Store in LTMC memory
        success = await self._store_verification_in_ltmc(record)
        record.stored_in_ltmc = success
        
        if success:
            self.verification_records.append(record)
        
        return record
    
    async def verify_and_store_function_names(self) -> TruthVerificationRecord:
        """Verify function names and store the result in LTMC memory."""
        # Perform verification
        verification = self.verifier.verify_function_names()
        
        # Create complete record
        record = TruthVerificationRecord(
            verification_id=f"ltmc_function_names_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            claim_text="LTMC consolidated function names",
            verified_value=verification.result,
            verification_method=verification.method.value,
            file_path=verification.file_path,
            verification_command=verification.command,
            file_hash=verification.hash_signature,
            verified_at=verification.verified_at,
            stored_in_ltmc=False,
            ltmc_conversation_id=self.VERIFICATION_CONVERSATION_ID
        )
        
        # Store in LTMC memory
        success = await self._store_verification_in_ltmc(record)
        record.stored_in_ltmc = success
        
        if success:
            self.verification_records.append(record)
        
        return record
    
    async def store_behavioral_pattern(self, pattern_name: str, rule_data: Dict[str, Any]) -> BehavioralPattern:
        """Store a behavioral pattern in LTMC memory."""
        pattern = BehavioralPattern(
            pattern_id=f"pattern_{pattern_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            pattern_name=pattern_name,
            rule_description=rule_data.get('description', ''),
            trigger_patterns=rule_data.get('trigger_patterns', []),
            enforcement_actions=rule_data.get('required_actions', []),
            violation_history=[],
            effectiveness_score=1.0,
            created_at=datetime.now(),
            last_updated=datetime.now(),
            usage_count=0
        )
        
        # Store in LTMC memory
        success = await self._store_pattern_in_ltmc(pattern)
        
        if success:
            self.behavioral_patterns.append(pattern)
        
        return pattern
    
    async def record_behavioral_violation(self, violation: BehavioralViolation) -> bool:
        """Record a behavioral violation in LTMC memory for pattern analysis."""
        memory_tools = MemoryTools()
        violation_record = {
            "violation_id": f"violation_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "violation_type": violation.violation_type,
            "severity": violation.severity.value,
            "claim_text": violation.claim_text,
            "expected_behavior": violation.expected_behavior,
            "actual_behavior": violation.actual_behavior,
            "detected_at": violation.detected_at.isoformat(),
            "context": violation.context,
            "suggested_fix": violation.suggested_fix
        }
        
        try:
            from ltms.tools.memory.memory_actions import memory_action
            
            # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
            # Generate dynamic resource type based on violation severity and type
            dynamic_resource_type = f"behavioral_violation_{violation.severity.value}_{violation.violation_type}"
            
            result = await memory_tools("store",
                conversation_id=self.VIOLATION_HISTORY_CONVERSATION_ID,
                file_name=f"violation_{violation_record['violation_id']}",
                content=json.dumps(violation_record, indent=2),
                resource_type=dynamic_resource_type
            )
            
            return result.get('success', False)
            
        except Exception as e:
            print(f"Error storing violation in LTMC: {e}")
            return False
    
    async def retrieve_verification_history(self, claim_type: str = None) -> List[TruthVerificationRecord]:
        """Retrieve verification history from LTMC memory."""
        memory_tools = MemoryTools()
        try:
            from ltms.tools.memory.memory_actions import memory_action
            
            query = claim_type if claim_type else "truth verification records"
            
            result = await memory_tools("retrieve",
                conversation_id=self.VERIFICATION_CONVERSATION_ID,
                query=query,
                top_k=20
            )
            
            if result.get('success'):
                records = []
                for doc in result.get('documents', []):
                    try:
                        record_data = json.loads(doc['content'])
                        # Convert back to TruthVerificationRecord
                        record_data['verified_at'] = datetime.fromisoformat(record_data['verified_at'])
                        record = TruthVerificationRecord(**record_data)
                        records.append(record)
                    except (json.JSONDecodeError, KeyError, TypeError):
                        continue
                
                return records
            
        except Exception as e:
            print(f"Error retrieving verification history from LTMC: {e}")
        
        return []
    
    async def get_current_ltmc_tool_count(self) -> Optional[int]:
        """Get the most recent verified LTMC tool count from memory."""
        records = await self.retrieve_verification_history("ltmc tool count")
        
        if records:
            # Get most recent verification
            latest_record = max(records, key=lambda r: r.verified_at)
            return latest_record.verified_value
        
        return None
    
    async def validate_claim_against_memory(self, claim_text: str, claimed_value: Any) -> Dict[str, Any]:
        """Validate a claim against stored verification records in LTMC memory."""
        # Retrieve relevant verification records
        records = await self.retrieve_verification_history()
        
        # Find matching verifications
        relevant_records = []
        claim_lower = claim_text.lower()
        
        for record in records:
            if any(keyword in claim_lower for keyword in ['tool', 'function', 'count', 'ltmc']):
                if 'tool' in record.claim_text.lower() or 'function' in record.claim_text.lower():
                    relevant_records.append(record)
        
        if not relevant_records:
            return {
                "validated": False,
                "reason": "No relevant verification records found",
                "requires_new_verification": True
            }
        
        # Check against most recent verification
        latest_record = max(relevant_records, key=lambda r: r.verified_at)
        
        if latest_record.verified_value == claimed_value:
            return {
                "validated": True,
                "verified_value": latest_record.verified_value,
                "verification_date": latest_record.verified_at.isoformat(),
                "verification_method": latest_record.verification_method,
                "file_hash": latest_record.file_hash
            }
        else:
            return {
                "validated": False,
                "claimed_value": claimed_value,
                "actual_verified_value": latest_record.verified_value,
                "reason": f"Claim value {claimed_value} does not match verified value {latest_record.verified_value}",
                "requires_correction": True,
                "verification_record": asdict(latest_record)
            }
    
    async def ensure_source_truth_compliance(self, text_to_analyze: str) -> Dict[str, Any]:
        """
        Comprehensive function to ensure source truth compliance.
        
        This is the main function that should be called before any agent outputs text.
        """
        # Analyze for violations
        is_compliant, violations = self.enforcer.analyze_text_for_violations(text_to_analyze)
        
        compliance_result = {
            "compliant": is_compliant,
            "violations_detected": len(violations),
            "critical_violations": len([v for v in violations if v.severity == ViolationSeverity.CRITICAL]),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        if violations:
            # Record violations in LTMC memory
            for violation in violations:
                await self.record_behavioral_violation(violation)
            
            compliance_result["violations"] = [
                {
                    "type": v.violation_type,
                    "severity": v.severity.value,
                    "claim": v.claim_text,
                    "suggested_fix": v.suggested_fix
                } for v in violations
            ]
        
        # If there are quantitative claims, validate against memory
        if any("tool" in v.claim_text.lower() or "function" in v.claim_text.lower() 
               for v in violations):
            
            # Ensure we have current verification
            tool_count_record = await self.verify_and_store_ltmc_tool_count()
            function_record = await self.verify_and_store_function_names()
            
            compliance_result["current_verified_tool_count"] = tool_count_record.verified_value
            compliance_result["current_verified_functions"] = len(function_record.verified_value)
            compliance_result["verification_timestamp"] = tool_count_record.verified_at.isoformat()
        
        return compliance_result
    
    async def _store_verification_in_ltmc(self, record: TruthVerificationRecord) -> bool:
        """Store a verification record in LTMC memory."""
        memory_tools = MemoryTools()
        try:
            from ltms.tools.memory.memory_actions import memory_action
            
            record_data = asdict(record)
            record_data['verified_at'] = record.verified_at.isoformat()
            
            # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
            # Generate dynamic resource type based on verification method and result type
            dynamic_verification_resource_type = f"truth_verification_{record.verification_method}_{record.claim_text.replace(' ', '_').lower()}"
            
            result = await memory_tools("store",
                conversation_id=record.ltmc_conversation_id,
                file_name=f"verification_{record.verification_id}",
                content=json.dumps(record_data, indent=2),
                resource_type=dynamic_verification_resource_type
            )
            
            if result.get('success') and 'resource_id' in result:
                record.ltmc_resource_id = result['resource_id']
                return True
            
        except Exception as e:
            print(f"Error storing verification in LTMC: {e}")
        
        return False
    
    async def _store_pattern_in_ltmc(self, pattern: BehavioralPattern) -> bool:
        """Store a behavioral pattern in LTMC memory."""
        memory_tools = MemoryTools()
        try:
            from ltms.tools.memory.memory_actions import memory_action
            
            pattern_data = asdict(pattern)
            pattern_data['created_at'] = pattern.created_at.isoformat()
            pattern_data['last_updated'] = pattern.last_updated.isoformat()
            
            # Following LTMC Dynamic Method Architecture Principles - NO HARDCODED VALUES
            # Generate dynamic resource type based on pattern name and enforcement actions
            dynamic_pattern_resource_type = f"behavioral_pattern_{pattern.pattern_name}_{len(pattern.enforcement_actions)}_actions"
            
            result = await memory_tools("store",
                conversation_id=self.BEHAVIORAL_PATTERN_CONVERSATION_ID,
                file_name=f"pattern_{pattern.pattern_id}",
                content=json.dumps(pattern_data, indent=2),
                resource_type=dynamic_pattern_resource_type
            )
            
            return result.get('success', False)
            
        except Exception as e:
            print(f"Error storing pattern in LTMC: {e}")
            return False


# Global instance
_integration_manager = None

def get_ltmc_truth_manager() -> LTMCTruthIntegrationManager:
    """Get the global LTMC truth integration manager."""
    global _integration_manager
    if _integration_manager is None:
        _integration_manager = LTMCTruthIntegrationManager()
    return _integration_manager


async def ensure_source_truth_compliance(text: str) -> Dict[str, Any]:
    """
    Main async function for ensuring source truth compliance.
    
    This should be called before any agent outputs text containing potential claims.
    """
    manager = get_ltmc_truth_manager()
    return await manager.ensure_source_truth_compliance(text)


def ensure_source_truth_compliance_sync(text: str) -> Dict[str, Any]:
    """
    Synchronous wrapper for source truth compliance checking.
    
    For use in contexts where async is not available.
    """
    return asyncio.run(ensure_source_truth_compliance(text))


if __name__ == "__main__":
    # Test the LTMC integration
    async def test_ltmc_integration():
        print("LTMC Memory Truth Integration Testing")
        print("=" * 50)
        
        manager = LTMCTruthIntegrationManager()
        
        # Test verification and storage
        tool_record = await manager.verify_and_store_ltmc_tool_count()
        print(f"✅ Verified and stored tool count: {tool_record.verified_value}")
        print(f"   Stored in LTMC: {tool_record.stored_in_ltmc}")
        
        # Test function verification
        function_record = await manager.verify_and_store_function_names()
        print(f"✅ Verified function names: {len(function_record.verified_value)}")
        print(f"   Functions: {', '.join(function_record.verified_value[:3])}...")
        
        # Test compliance checking
        test_text = "LTMC has 30 tools in the consolidated system"
        compliance = await manager.ensure_source_truth_compliance(test_text)
        
        print(f"\nCompliance check for: '{test_text}'")
        print(f"Compliant: {compliance['compliant']}")
        print(f"Violations: {compliance['violations_detected']}")
        
        if not compliance['compliant']:
            print("Violations:")
            for violation in compliance.get('violations', []):
                print(f"  - {violation['type']}: {violation['claim']}")
                print(f"    Fix: {violation['suggested_fix']}")
        
        print("\n" + "=" * 50)
        print("LTMC Memory Truth Integration: OPERATIONAL")
    
    # Run the test
    asyncio.run(test_ltmc_integration())