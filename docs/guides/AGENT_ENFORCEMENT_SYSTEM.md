# LTMC Agent Enforcement & Anti-Tech Stack Drift System

## Overview

LTMC includes a **production-grade agent enforcement system** designed to prevent AI agent behavioral drift, tech stack inconsistencies, and false claims about codebases. This system ensures agents maintain behavioral compliance and technical accuracy across all operations.

## Core Components

### 🛡️ **Behavioral Enforcement Engine**
**Location**: `ltms/verification/behavioral_enforcement_rules.py`

**Purpose**: Prevents agents from making false claims by requiring mandatory source code verification.

**Key Features**:
- **Quantitative Claim Detection**: Automatically detects numerical claims requiring verification
- **Violation Severity Levels**: CRITICAL, ERROR, WARNING, INFO classifications
- **Real-time Verification**: Integrates with source code truth verification
- **LTMC Memory Integration**: Permanent behavioral pattern storage

```python
from ltms.verification.behavioral_enforcement_rules import BehavioralEnforcementEngine

# Initialize enforcement
enforcer = BehavioralEnforcementEngine("/path/to/project")

# Analyze text for violations
is_compliant, violations = enforcer.analyze_text_for_violations(
    "LTMC has 30 tools",  # This would be flagged as false claim
    "agent_response"
)
```

### ⚖️ **Tech Stack Alignment Agent**
**Location**: `ltms/coordination/tech_stack_alignment_agent.py`

**Purpose**: Multi-agent coordination for tech stack consistency enforcement across development workflows.

**Key Features**:
- **Real agent-to-agent communication** with stack consistency enforcement
- **Cross-agent conflict detection** and resolution coordination
- **Performance-optimized coordination** (<500ms SLA)
- **Full LTMC integration** for persistent coordination state

```python
from ltms.coordination.tech_stack_alignment_agent import TechStackAlignmentAgent

# Initialize alignment agent
alignment_agent = TechStackAlignmentAgent(
    coordination_mode=CoordinationMode.HIERARCHICAL,
    project_path="/path/to/project"
)

# Coordinate tech stack validation across agents
result = await alignment_agent.coordinate_validation_across_agents([
    "development_agent",
    "testing_agent", 
    "review_agent"
])
```

### 🔍 **Tech Stack Conflict Detector**
**Location**: `ltms/coordination/tech_stack/conflict_detector.py`

**Purpose**: Detects conflicts between different frameworks (FastAPI/MCP) and prevents event loop conflicts.

**Key Features**:
- **Framework conflict analysis** (FastAPI vs MCP)
- **Event loop conflict detection**
- **Import conflict analysis**
- **Port binding issue detection**

```python
from ltms.coordination.tech_stack.conflict_detector import detect_framework_conflicts

# Detect conflicts in project directory
conflicts = await detect_framework_conflicts(validator, project_directory)
for conflict in conflicts:
    print(f"Conflict: {conflict.message}")
    print(f"Severity: {conflict.severity}")
```

### 🎯 **Consistency Validation Engine**
**Location**: `ltms/services/consistency_validation_engine.py`

**Purpose**: Comprehensive validation of blueprint-code alignment with automated remediation.

**Key Features**:
- **Blueprint-code consistency validation**
- **Real-time change validation**  
- **Automated consistency enforcement**
- **Intelligent violation detection**
- **Smart automated remediation**

**Performance SLA**:
- Validation operations: <10ms per validation
- Change detection: <5ms per change
- Enforcement actions: <15ms per action
- Violation detection: <8ms per scan
- Remediation operations: <20ms per fix

### 📊 **Source Code Truth Verification System**
**Location**: `ltms/verification/source_truth_verification_system.py`

**Purpose**: Prevents false quantitative claims about the codebase by enforcing mandatory verification.

**Key Features**:
- **Multi-method verification** (grep, AST parsing, ripgrep)
- **Cryptographic verification stamps**
- **Blocked claim tracking**
- **Real-time source code analysis**

## Anti-Tech Stack Drift Architecture

### 1. **Stack Registry System**
**Location**: `ltms/coordination/tech_stack/registry.py`

Maintains canonical tech stack definitions and validates compatibility:

```python
class StackRegistry:
    """
    Central registry for tech stack components and compatibility rules.
    
    Features:
    - Component version tracking
    - Compatibility matrix management  
    - Dependency conflict detection
    - Upgrade path validation
    """
```

### 2. **Pattern Detector**
**Location**: `ltms/coordination/tech_stack/pattern_detector.py`

Detects anti-patterns and tech stack violations:

```python
# Detects patterns that indicate tech stack drift
patterns = await pattern_detector.analyze_codebase_patterns(project_path)
for pattern in patterns:
    if pattern.is_anti_pattern:
        await enforcer.flag_violation(pattern)
```

### 3. **Resolution Generator**
**Location**: `ltms/coordination/tech_stack/resolution_generator.py`

Generates automated fixes for tech stack conflicts:

```python
# Generate resolution for detected conflicts
resolution = await resolution_generator.generate_resolution(conflict)
if resolution.auto_applicable:
    await resolution.apply_fix()
```

### 4. **Event Loop Monitor** 
**Location**: `ltms/coordination/tech_stack/monitor.py`

Monitors for event loop conflicts and async/await inconsistencies:

```python
# Monitor for event loop conflicts
monitor = EventLoopMonitor()
conflicts = await monitor.detect_event_loop_conflicts(codebase_path)
```

## Behavioral Enforcement Rules

### Rule Categories

#### 1. **Quantitative Claims Detection**
**Patterns Monitored**:
- `\b(\d+)\s+tools?\b` - "30 tools", "11 tools"
- `\b(\d+)\s+functions?\b` - "126 functions"  
- `\b(\d+)\s+files?\b` - "50 files"
- `\bhas\s+(\d+)\b` - "has 30"
- `\b(\d+)\+?\s+decorators?\b` - "126+ decorators"

#### 2. **Context-Aware Analysis**
**Enhanced Detection For**:
- LTMC-specific claims
- Consolidated tool references
- @mcp.tool decorator counts
- Source code structure claims

#### 3. **Violation Severity Classification**

```python
class ViolationSeverity(Enum):
    CRITICAL = "critical"     # Blocks execution completely
    ERROR = "error"           # Major violation, requires correction
    WARNING = "warning"       # Minor violation, logs but continues
    INFO = "info"            # Informational, for learning
```

## Anti-Drift Workflow Patterns

### 1. **Continuous Validation Pattern**
```python
async def continuous_tech_stack_validation():
    """Continuously validate tech stack consistency."""
    
    validator = TechStackValidator()
    monitor = EventLoopMonitor()
    
    while True:
        # Validate current tech stack
        validation_results = await validator.validate_tech_stack(project_path)
        
        # Check for event loop conflicts
        loop_conflicts = await monitor.detect_conflicts()
        
        # Apply automated fixes for minor issues
        for result in validation_results:
            if result.severity == ValidationSeverity.WARNING:
                await apply_automated_fix(result)
        
        # Alert for critical issues
        critical_issues = [r for r in validation_results if r.severity == ValidationSeverity.CRITICAL]
        if critical_issues:
            await alert_critical_issues(critical_issues)
        
        await asyncio.sleep(60)  # Check every minute
```

### 2. **Pre-Commit Enforcement Pattern**
```python
async def pre_commit_enforcement():
    """Enforce tech stack consistency before commits."""
    
    # Analyze staged changes
    staged_files = await get_staged_files()
    
    # Validate changes don't introduce drift
    for file in staged_files:
        violations = await consistency_engine.validate_file_consistency(file)
        
        # Block commit if critical violations found
        critical_violations = [v for v in violations if v.severity == SeverityLevel.CRITICAL]
        if critical_violations:
            raise CommitBlockedException("Critical tech stack violations detected")
    
    # Auto-fix minor violations
    minor_violations = [v for v in violations if v.severity == SeverityLevel.MINOR]
    for violation in minor_violations:
        await auto_remediate_violation(violation)
```

### 3. **Cross-Agent Coordination Pattern**
```python
async def cross_agent_drift_prevention():
    """Coordinate drift prevention across multiple agents."""
    
    coordination_agent = TechStackAlignmentAgent()
    
    # Define coordination workflow
    workflow = {
        "agents": ["development", "testing", "review", "deployment"],
        "validation_checkpoints": [
            "code_analysis",
            "dependency_check", 
            "integration_test",
            "deployment_validation"
        ],
        "drift_prevention_rules": [
            "no_new_frameworks_without_approval",
            "maintain_existing_patterns",
            "validate_against_tech_stack_registry"
        ]
    }
    
    # Execute coordinated validation
    result = await coordination_agent.coordinate_drift_prevention(workflow)
    return result
```

## Integration with LTMC Tools

### Memory Integration
```python
# Store enforcement patterns in LTMC memory
await memory_action(
    action="store",
    content=enforcement_pattern,
    tags=["behavioral_enforcement", "tech_stack_validation"]
)

# Retrieve historical violation patterns
violations = await memory_action(
    action="retrieve",
    query="tech stack violations last 30 days"
)
```

### Graph Integration
```python
# Store tech stack relationships in Neo4j
await graph_action(
    action="link",
    source_entity="FastAPI",
    target_entity="MCP_Protocol",
    relationship="conflicts_with",
    metadata={"conflict_type": "event_loop", "severity": "critical"}
)
```

## Configuration

### Environment Setup
```bash
# Enable behavioral enforcement
export LTMC_BEHAVIORAL_ENFORCEMENT=enabled
export LTMC_TECH_STACK_VALIDATION=strict
export LTMC_DRIFT_PREVENTION=active
export LTMC_ENFORCEMENT_SLA_MS=500
```

### Enforcement Configuration
```python
# ltms/config/enforcement_config.py
ENFORCEMENT_CONFIG = {
    "quantitative_claims_detection": True,
    "tech_stack_drift_prevention": True,
    "auto_remediation_enabled": True,
    "enforcement_sla_ms": 500,
    "violation_retention_days": 90,
    "critical_violation_alerts": True
}
```

## Monitoring and Metrics

### Enforcement Metrics
```python
from ltms.verification.behavioral_enforcement_rules import get_enforcement_metrics

metrics = await get_enforcement_metrics()
print(f"Claims blocked: {metrics['claims_blocked']}")
print(f"Violations detected: {metrics['violations_detected']}")
print(f"Auto-remediations: {metrics['auto_remediations']}")
print(f"Tech stack drift incidents: {metrics['drift_incidents']}")
```

### Performance Monitoring
```python
# Monitor enforcement performance
performance_metrics = await enforcement_engine.get_performance_metrics()
print(f"Average validation time: {performance_metrics['avg_validation_ms']}ms")
print(f"SLA compliance: {performance_metrics['sla_compliance_pct']}%")
```

## Examples

### Basic Enforcement Setup
```python
#!/usr/bin/env python3
"""Basic LTMC Agent Enforcement Example"""

import asyncio
from ltms.verification.behavioral_enforcement_rules import BehavioralEnforcementEngine
from ltms.coordination.tech_stack_alignment_agent import TechStackAlignmentAgent

async def setup_enforcement():
    """Set up comprehensive agent enforcement."""
    
    # Initialize behavioral enforcement
    behavioral_enforcer = BehavioralEnforcementEngine("/path/to/ltmc")
    
    # Initialize tech stack alignment
    tech_stack_agent = TechStackAlignmentAgent()
    
    # Configure enforcement rules
    enforcement_config = {
        "block_false_claims": True,
        "verify_quantitative_claims": True,
        "prevent_tech_stack_drift": True,
        "auto_remediate_minor_violations": True
    }
    
    # Start enforcement monitoring
    await behavioral_enforcer.start_monitoring(enforcement_config)
    await tech_stack_agent.start_coordination()
    
    print("✅ LTMC Agent Enforcement System Active")
    print("🛡️ Behavioral compliance monitoring enabled")
    print("⚖️ Tech stack drift prevention active")
    
    return {
        "behavioral_enforcer": behavioral_enforcer,
        "tech_stack_agent": tech_stack_agent
    }

# Run enforcement setup
if __name__ == "__main__":
    asyncio.run(setup_enforcement())
```

### Advanced Drift Prevention
```python
async def advanced_drift_prevention_example():
    """Advanced tech stack drift prevention workflow."""
    
    from ltms.services.consistency_validation_engine import ConsistencyValidationEngine
    from ltms.coordination.tech_stack.conflict_detector import detect_framework_conflicts
    
    # Initialize components
    consistency_engine = ConsistencyValidationEngine()
    
    # Comprehensive project analysis
    project_analysis = await consistency_engine.analyze_project_consistency("/path/to/project")
    
    # Detect framework conflicts
    conflicts = await detect_framework_conflicts(validator, project_directory)
    
    # Generate remediation plan
    if conflicts:
        remediation_plan = await consistency_engine.generate_remediation_plan(conflicts)
        
        # Apply automated fixes
        for fix in remediation_plan.automated_fixes:
            await fix.apply()
        
        # Report manual intervention needed
        if remediation_plan.manual_fixes:
            print("Manual intervention required for:")
            for manual_fix in remediation_plan.manual_fixes:
                print(f"  - {manual_fix.description}")
    
    return project_analysis
```

## Troubleshooting

### Common Issues

#### 1. False Positive Claim Detection
```python
# Configure claim detection sensitivity
enforcer.configure_detection_sensitivity({
    "quantitative_threshold": 0.8,  # Reduce false positives
    "context_weight": 0.7,
    "pattern_strictness": "moderate"
})
```

#### 2. Performance Impact from Enforcement
```python
# Optimize enforcement performance
enforcer.configure_performance({
    "async_validation": True,
    "batch_processing": True,
    "cache_validation_results": True,
    "max_concurrent_validations": 5
})
```

#### 3. Tech Stack Conflict Resolution
```python
# Manual conflict resolution
conflicts = await detect_framework_conflicts(validator, project_dir)
for conflict in conflicts:
    if conflict.auto_resolvable:
        await conflict.apply_resolution()
    else:
        await conflict.escalate_to_human()
```

## Best Practices

### 1. **Enforcement Strategy**
- Start with WARNING severity for new projects
- Gradually increase to ERROR/CRITICAL as team adapts
- Use automated remediation for minor violations
- Maintain audit trail for all enforcement actions

### 2. **Tech Stack Management**
- Define clear tech stack registry
- Regular validation of stack consistency
- Automated conflict detection in CI/CD
- Version compatibility management

### 3. **Performance Optimization**
- Monitor enforcement overhead
- Use async validation for large codebases
- Implement caching for repeated validations
- Batch process multiple violations

### 4. **Team Integration**
- Train team on enforcement rules
- Provide clear violation explanations
- Implement gradual enforcement rollout
- Regular review of enforcement effectiveness

## API Reference

### Core Classes
- `BehavioralEnforcementEngine` - Main enforcement orchestrator
- `TechStackAlignmentAgent` - Cross-agent coordination
- `ConsistencyValidationEngine` - Blueprint-code consistency
- `QuantitativeClaimDetector` - Claim detection and validation
- `TechStackValidator` - Tech stack validation and enforcement

### Key Methods
- `analyze_text_for_violations()` - Analyze text for behavioral violations
- `coordinate_validation_across_agents()` - Multi-agent validation coordination
- `validate_tech_stack()` - Comprehensive tech stack validation
- `detect_framework_conflicts()` - Framework conflict analysis
- `generate_remediation_plan()` - Automated remediation planning

---

*This documentation covers LTMC's advanced agent enforcement and anti-tech stack drift capabilities. These systems ensure AI agents maintain behavioral compliance and technical accuracy across all development workflows.*