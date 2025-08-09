# Updated Taskmaster Integration Plan

This plan has been updated to incorporate the best ideas from memory-bank-mcp into our existing "Taskmaster" concept for LTMC. The goal is to create a robust system with two parallel sources of truth: a machine-readable code blueprint (Neo4j) and human-readable project documentation (Markdown files).

## Phase 1: Blueprint and Documentation Foundation 🧭📜

This phase combines the creation of the code graph with a structured documentation system, ensuring a complete and synchronized project map.

### Step 1.1: Enhance the Blueprint Database Schema

The Neo4j database schema from our previous plan will remain the core for mapping code dependencies.

**Action:** Ensure the Neo4j adapter is capable of handling the node and relationship types we defined earlier, such as `(:Function)-[:CALLS]->(:Function)` and `(:Module)-[:IMPORTS]->(:Module)`.

### Step 1.2: Establish a Structured Documentation System

We will create a directory for structured project documentation. This mirrors the memory-bank-mcp approach and provides a human-readable blueprint.

**Action:** Create a new directory, e.g., `ltms/docs/blueprint/`.

**Action:** Inside this directory, create the following core Markdown files:

- `productContext.md`: Describes the project's high-level goals and user needs.
- `systemArchitecture.md`: Outlines the project's architecture, including components, data flow, and technologies.
- `decisionLog.md`: A log of key technical decisions and their justifications.
- `progress.md`: A high-level overview of current tasks and milestones.

### Step 1.3: Update MCP Tools for Dual Management

The BlueprintTools class from our previous plan will be updated to manage both the Neo4j graph and the Markdown files.

**File to Modify:** `ltms/tools/blueprint_tools.py`

**Code to Add:** Add a new method to manage the documentation files.

```python
# ltms/tools/blueprint_tools.py
# ... existing imports and BlueprintTools class ...

def update_docs(self, doc_name: str, new_content: str, change_type: str) -> Dict[str, Any]:
    """
    Updates a specific documentation file with new content.

    Args:
        doc_name: The name of the Markdown file (e.g., 'systemArchitecture.md').
        new_content: The updated content for the file.
        change_type: The type of change (e.g., 'architecture', 'bugfix').
    """
    doc_path = os.path.join("ltms/docs/blueprint", doc_name)
    with open(doc_path, 'w') as f:
        f.write(new_content)

    # In a real implementation, you would also validate the content
    # or log the change type to a separate history file.

    return {"status": f"Documentation file '{doc_name}' updated for change type: '{change_type}'."}
```

**Action:** Register this new `update_docs` tool in `ltms/mcp_server.py`.

## Phase 2: Enforce Rules with a Dual-Source Check ✅

The TaskmasterEnforcement tool will be significantly enhanced to validate proposed changes against both the code blueprint (Neo4j) and the documentation files.

### Step 2.1: Update the TaskmasterEnforcement Tool

The `enforce_changes` method will now perform a more comprehensive validation.

**File to Modify:** `ltms/tools/taskmaster_enforcement.py`

**Action:** Modify the `enforce_changes` method to include checks for both sources of truth.

**Code to Modify:**

```python
# ltms/tools/taskmaster_enforcement.py
# ... existing imports and TaskmasterEnforcement class ...

def enforce_changes(self, proposed_changes: Dict[str, Any], change_type: str) -> Dict[str, Any]:
    """
    Validates proposed changes against the code blueprint and documentation.
    """
    print("Enforcing changes against Taskmaster Blueprint and Docs...")

    # Step 1: Code-level validation against Neo4j blueprint (from original plan)
    # We assume this logic would check function signatures, imports, etc.
    if not self._validate_code_against_blueprint(proposed_changes):
        return {"error": "Code changes violate the application blueprint."}

    # Step 2: Documentation validation (new logic)
    # This checks if the change_type is valid and if relevant docs are updated.
    if change_type in ["architecture", "feature"] and not self._check_documentation_updates(proposed_changes, change_type):
        return {"error": "Documentation update is required for this type of change."}

    return {"status": "Proposed changes successfully validated."}

def _check_documentation_updates(self, proposed_changes: Dict, change_type: str) -> bool:
    """
    Placeholder to check if the proposed change requires documentation updates.
    A real implementation would check if the relevant docs were also part of the change.
    """
    # Example logic:
    # if 'systemArchitecture.md' not in proposed_changes:
    #     return False
    return True
```

**Why:** This dual-source validation is the key to preventing context drift. The AI is now forced to not only write syntactically correct, blueprint-compliant code but also to document its changes in a structured, human-readable format.

## Phase 3: Refined AI Workflow 🧠

The final workflow for an AI agent will be more robust and disciplined, leveraging the full power of the integrated system.

### Step 3.1: Finalized AI Workflow

The AI's plan to implement a new feature would now look like this:

**Request:** "Add a new feature to the ltmc/ codebase that does X. Make sure to update the application blueprint and documentation."

**AI Plan:**

1. `query_blueprint`: "Analyze the code graph to find the best place to add the new code."

2. `query_docs`: "Read productContext.md and systemArchitecture.md to ensure the feature aligns with the project goals."

3. `enforce_changes`: "Validate the proposed code and documentation changes to ensure they are consistent and compliant with the Taskmaster's rules."

4. `write_file`: "Write the new code."

5. `update_docs`: "Update the systemArchitecture.md and progress.md files, specifying change_type: feature."

6. `update_blueprint`: "Update the Neo4j graph with the new module and function."

This updated plan creates a comprehensive, self-documenting, and error-preventing development pipeline that directly addresses your concerns about context drift and uncoordinated changes.