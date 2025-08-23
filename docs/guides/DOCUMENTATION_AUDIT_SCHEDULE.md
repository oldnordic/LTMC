# LTMC Documentation Audit Schedule

## Overview

This document outlines the automated weekly documentation audit schedule for the LTMC project to ensure documentation consistency and quality across all modules.

## Audit Schedule

### **Frequency**: Weekly (Every Friday)
### **Next Scheduled Run**: August 29, 2025
### **Estimated Duration**: 15-20 minutes

## Audit Tasks

### 1. Documentation Consistency Scoring
**Tool**: `mcp__ltmc__sync_action` with `score` action  
**Target Files**:
- `ltms/main.py`
- `ltms/tools/consolidated.py`  
- `ltms/tools/consolidated_real.py`
- Additional key modules

**Success Criteria**: All files maintain 70%+ consistency score

### 2. Documentation Drift Detection  
**Tool**: `mcp__ltmc__sync_action` with `drift` action  
**Purpose**: Identify files modified without corresponding documentation updates  
**Alert Threshold**: Files modified within 48 hours

### 3. Architecture Diagram Updates
**Tool**: `mcp__ltmc__documentation_action` with `generate_architecture_diagram`  
**Purpose**: Ensure diagrams reflect current system architecture  
**Output**: Updated PlantUML diagrams

### 4. API Documentation Sync
**Tool**: `mcp__ltmc__sync_action` with `code` action  
**Purpose**: Sync code changes with API documentation  
**Target**: All major modules with public APIs

## Audit Execution Commands

### Manual Execution
```bash
# 1. Run consistency scoring
mcp__ltmc__sync_action score --project_id ltmc --file_path ltms/main.py
mcp__ltmc__sync_action score --project_id ltmc --file_path ltms/tools/consolidated.py
mcp__ltmc__sync_action score --project_id ltmc --file_path ltms/tools/consolidated_real.py

# 2. Check for drift
mcp__ltmc__sync_action drift --project_id ltmc --file_path ltms/main.py --doc_path docs

# 3. Generate architecture diagrams
mcp__ltmc__documentation_action generate_architecture_diagram --project_id ltmc --source_path ltms
```

## Success Metrics

### Target Consistency Scores
- **Excellent**: 90%+ consistency
- **Good**: 70-89% consistency  
- **Needs Improvement**: <70% consistency

### Drift Detection
- **Acceptable**: <24 hours since last doc update
- **Warning**: 24-72 hours since last doc update
- **Critical**: >72 hours since last doc update

## Automated Scheduling

### LTMC Task Management
The audit tasks are scheduled in the LTMC task management system:
- **Task ID 31**: Weekly Documentation Consistency Audit (Parent)
- **Task ID 32**: Run consistency scoring on all main modules
- **Task ID 33**: Check documentation drift detection  
- **Task ID 34**: Generate updated architecture diagrams

### Recurring Schedule
Each audit creates new tasks for the following week, ensuring continuous documentation quality monitoring.

## Reporting

### Weekly Audit Report Template
```markdown
# Weekly Documentation Audit Report - [Date]

## Consistency Scores
- ltms/main.py: [X.X]% ([Status])
- ltms/tools/consolidated.py: [X.X]% ([Status])  
- ltms/tools/consolidated_real.py: [X.X]% ([Status])

## Drift Detection
- Files with recent changes: [Count]
- Documentation updates needed: [Count]

## Actions Required
- [ ] Update documentation for: [Files]
- [ ] Review consistency for: [Files] 
- [ ] Architecture updates: [Changes]

## Next Audit
- Scheduled: [Next Friday]
- Focus Areas: [Specific concerns]
```

## Troubleshooting

### Common Issues
1. **Consistency scores dropping**: Review recent code changes for missing docstrings
2. **Drift warnings**: Check if recent changes included documentation updates
3. **Tool failures**: Verify database connectivity and MCP server status

### Escalation
- **Critical consistency drops** (>10% decrease): Immediate review required
- **Persistent drift warnings**: Development process review needed
- **Tool failures**: Technical infrastructure investigation required

---

**Last Updated**: August 22, 2025  
**Next Review**: August 29, 2025