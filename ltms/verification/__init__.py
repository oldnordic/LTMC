"""
LTMC Source Code Truth Verification Package

This package implements a comprehensive system for preventing false claims about
the codebase by enforcing mandatory source code verification before any
quantitative or factual claims can be made.

Components:
- source_truth_verification_system: Core verification engine
- behavioral_enforcement_rules: Rules for detecting and blocking false claims  
- ltmc_memory_truth_integration: Integration with LTMC long-term memory
- automated_truth_workflows: Pre-commit hooks and continuous monitoring

NO MOCKS, NO STUBS, NO PLACEHOLDERS - 100% REAL IMPLEMENTATION
"""

from .source_truth_verification_system import (
    SourceTruthVerificationEngine,
    VerificationResult,
    VerificationMethod,
    TruthClaim,
    require_source_verification
)

from .behavioral_enforcement_rules import (
    BehavioralEnforcementEngine,
    QuantitativeClaimDetector,
    BehavioralViolation,
    ViolationSeverity,
    ClaimType,
    get_enforcement_engine,
    enforce_source_truth
)

from .ltmc_memory_truth_integration import (
    LTMCTruthIntegrationManager,
    TruthVerificationRecord,
    BehavioralPattern,
    get_ltmc_truth_manager,
    ensure_source_truth_compliance,
    ensure_source_truth_compliance_sync
)

from .automated_truth_workflows import (
    PreCommitTruthHook,
    ContinuousMonitoringWorkflow,
    QualityGateOrchestrator,
    QualityGateResult
)

__all__ = [
    # Core verification
    "SourceTruthVerificationEngine",
    "VerificationResult", 
    "VerificationMethod",
    "TruthClaim",
    "require_source_verification",
    
    # Behavioral enforcement
    "BehavioralEnforcementEngine",
    "QuantitativeClaimDetector",
    "BehavioralViolation",
    "ViolationSeverity",
    "ClaimType",
    "get_enforcement_engine",
    "enforce_source_truth",
    
    # LTMC integration
    "LTMCTruthIntegrationManager",
    "TruthVerificationRecord",
    "BehavioralPattern",
    "get_ltmc_truth_manager",
    "ensure_source_truth_compliance",
    "ensure_source_truth_compliance_sync",
    
    # Automated workflows
    "PreCommitTruthHook",
    "ContinuousMonitoringWorkflow", 
    "QualityGateOrchestrator",
    "QualityGateResult"
]

# Package version
__version__ = "1.0.0"

# Package metadata
__author__ = "LTMC Development Team"
__description__ = "Source Code Truth Verification System for preventing false claims"
__license__ = "MIT"