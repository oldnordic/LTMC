# LTMC Agent Coordination System

## Overview

The `.ltmc-coordination/` directory implements external file-based coordination to solve the parallel isolation problem identified in Task tool agents. Based on TaskMaster design patterns, this system enables true multi-agent collaboration through persistent file coordination.

## Directory Structure

### `agent-handoffs/`
Contains individual handoff files between agents. Each handoff file includes:
- Source agent identification
- Target agent identification  
- Complete context and analysis results
- Instructions and expectations
- Validation criteria for handoff completion

**Naming Convention**: `{source-agent-id}_to_{target-agent-id}_{timestamp}.json`

### `workflow-states/`
JSON state machine files for coordination workflows. Tracks:
- Current workflow state
- Available transitions
- Timestamps for state changes
- Agent responsibilities at each state
- Completion criteria

**Naming Convention**: `{workflow-id}_state.json`

### `shared-context/`
Cross-agent context and session data that multiple agents can access:
- Shared analysis results
- Common documentation
- Cross-agent reference materials
- Session persistence data

**Naming Convention**: `{context-type}_{session-id}.json`

### `coordination-history/`
Audit trail of all coordination activities:
- Agent registration logs
- Handoff execution logs
- State transition history
- Error and recovery logs

**Naming Convention**: `{date}_{activity-type}_log.json`

## Coordination Commands

### Core Commands
- `ltmc-coord store-analysis [agent-id] [file]` - Store analysis results for handoff
- `ltmc-coord retrieve-handoff [target-agent]` - Get pending handoff for specific agent  
- `ltmc-coord update-status [workflow] [status]` - Update workflow state
- `ltmc-coord list-pending` - Show all pending handoffs
- `ltmc-coord create-workflow [workflow-id]` - Initialize new coordination workflow

### Implementation Location
MCP tool: `ltms/tools/coordination/coordination_actions.py`
Tool name: `coordination_action` (follows LTMC consolidated tool patterns)

## Coordination Principles

1. **External State Persistence**: Store coordination data in files, not agent memory
2. **Simple Command Interface**: Basic commands that read/write external state
3. **Immediate Visibility**: Changes instantly visible to all agents
4. **Human Debuggable**: Coordination files can be inspected and modified
5. **Context Preservation**: Structured files maintain full context across handoffs

## Expected Benefits

- ✅ Solves parallel isolation problem
- ✅ Immediate persistence across agent boundaries
- ✅ Simple API any agent can perform
- ✅ Human debuggable coordination state
- ✅ Scalable for complex multi-agent workflows
- ✅ Context preservation across handoffs

## Integration with LTMC Tools

This coordination system integrates with existing LTMC consolidated tools:
- Uses `memory_action` for persistence
- Uses `chat_action` for logging
- Uses `todo_action` for tracking
- Uses `graph_action` for dependencies

## Usage Example

```json
// Example handoff file: research_agent_to_docs_agent_20250828_104000.json
{
  "handoff_id": "research_to_docs_001",
  "source_agent": "research_agent",
  "target_agent": "documentation_agent", 
  "timestamp": "2025-08-28T10:40:00Z",
  "context": {
    "analysis_results": "...",
    "key_findings": ["...", "..."],
    "next_actions": "..."
  },
  "instructions": "Create comprehensive documentation based on analysis",
  "validation_criteria": [
    "Documentation includes all key findings",
    "Format follows project standards",
    "Technical accuracy verified"
  ],
  "status": "pending"
}
```