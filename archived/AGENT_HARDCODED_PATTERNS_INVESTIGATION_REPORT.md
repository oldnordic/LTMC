# Agent Hardcoded Patterns Investigation Report

**Issue Investigated:** Whether agents use the same hardcoded patterns that cause violations
**Investigation Date:** August 12, 2025
**Scope:** All global and project-specific agent files

## Executive Summary

🔴 **CRITICAL VIOLATIONS FOUND:** Multiple agents contain hardcoded references and patterns that violate global behavioral standards
⚠️ **WIDESPREAD ISSUE:** Both global and project-specific agents contain hardcoded technology references
🔧 **ACTION REQUIRED:** Systematic update needed to remove hardcoded patterns and align with centralized configuration

## Investigation Findings

### 1. Hardcoded Technology References Detected

#### ❌ **Model References** (Violates Centralized Model Configuration)
```
expert-tester.md:4:model: sonnet
software-architect.md:4:model: sonnet  
project-manager.md:4:model: sonnet
expert-planner.md:4:model: sonnet
expert-coder.md:4:model: sonnet
```

**Problem:** Agents specify hardcoded models instead of using centralized model configuration.

#### ❌ **Technology Stack Hardcoding** (Multiple Files)
```
- "Ollama DeepSeek-R1" references in 12+ agent files
- "DeepSeek reasoning integration" in agent descriptions
- Specific LLM model names embedded in agent logic
- Hardcoded service integration assumptions
```

**Example Violations:**
```markdown
# From expert-documenter.md
- **LLM Integration Patterns** - Ollama DeepSeek reasoning integration and streaming responses

# From expert-tester.md
- **LLM Integration Testing**: Validate Ollama DeepSeek integration and streaming responses
- **Real LLM Integration**: Testing with actual Ollama DeepSeek responses, not mocks

# From ai-engineer.md
- **LLMs**: Ollama DeepSeek-R1 (primary), OpenAI, Anthropic, Llama, Mistral
- **Unified Ollama Client** (`/core/unified_ollama_client.py`) - LLM integration hub
```

### 2. Hardcoded Pattern Categories Found

#### **Category 1: Model Configuration Hardcoding**
- **Files Affected:** 5+ core agent files
- **Pattern:** `model: sonnet` in YAML frontmatter
- **Violation:** Should use centralized model configuration system
- **Impact:** Prevents dynamic model switching, creates tech debt

#### **Category 2: Technology Stack Assumptions**
- **Files Affected:** 12+ engineering and expert agent files
- **Pattern:** Direct references to "Ollama DeepSeek-R1", "DeepSeek reasoning"
- **Violation:** Hardcoded technology choices instead of configurable options
- **Impact:** Makes agents unusable if technology stack changes

#### **Category 3: Service Integration Hardcoding**
- **Files Affected:** 8+ agents with LLM integration references
- **Pattern:** Specific service names and integration patterns
- **Violation:** Should use abstracted service interfaces
- **Impact:** Tight coupling to specific implementations

#### **Category 4: Architecture Assumptions**
- **Files Affected:** Multiple agent files
- **Pattern:** References to specific file paths, service names, protocols
- **Violation:** Should use environment-based configuration
- **Impact:** Agents break when deployment context changes

### 3. Specific Violation Examples

#### **From expert-coder.md:**
```markdown
- **No Hardcoded Heuristics**: All intelligent behavior must use Ollama DeepSeek reasoning
- **Support AI Engineer**: Implement agent coordination features and Ollama integration code
```
**Problem:** Mentions "No Hardcoded Heuristics" while hardcoding DeepSeek references.

#### **From ai-engineer.md:**
```markdown
- **LLMs**: Ollama DeepSeek-R1 (primary), OpenAI, Anthropic, Llama, Mistral
- **Unified Ollama Client** (`/core/unified_ollama_client.py`) - LLM integration hub
- LLM reasoning MUST use centralized Ollama client with DeepSeek-R1 model
- **No Hardcoded Heuristics** - All reasoning uses Ollama DeepSeek instead of static logic
```
**Problem:** Contradictory - claims "No Hardcoded Heuristics" while specifying exact models and file paths.

#### **From software-architect.md:**
```markdown
model: sonnet
- Ensure all architecture supports KWE's Ollama DeepSeek reasoning integration
- **LLM Integration Patterns** - Consistent patterns for Ollama DeepSeek reasoning integration
```
**Problem:** Hardcoded model specification and technology assumptions.

### 4. Impact Analysis

#### **High Impact Issues:**
1. **Model Configuration Conflicts:** Agents specify models that override centralized configuration
2. **Technology Lock-in:** Agents unusable if LLM provider changes
3. **Deployment Fragility:** Hardcoded paths and services break in different environments
4. **Maintenance Overhead:** Updates require changing multiple files instead of central config

#### **Medium Impact Issues:**
1. **Inconsistent Behavior:** Some agents use different models than global configuration
2. **Documentation Drift:** Agent docs reference outdated or incorrect technology stack
3. **Testing Issues:** Hardcoded references make testing with different setups difficult

### 5. Comparison with Global CLAUDE.md Standards

#### **Global Standards Require:**
✅ Centralized model configuration via environment variables
✅ No hardcoded technology references
✅ Configurable service integration
✅ Environment-agnostic agents

#### **Current Agent Implementation:**
❌ Hardcoded model specifications in YAML frontmatter
❌ Direct technology stack references (Ollama, DeepSeek)
❌ Specific service integration assumptions
❌ Environment-specific file paths and configurations

### 6. Agent Files Requiring Updates

#### **Critical Updates Needed:**
1. `expert-tester.md` - Remove `model: sonnet`, DeepSeek references
2. `expert-coder.md` - Remove `model: sonnet`, Ollama hardcoding  
3. `software-architect.md` - Remove `model: sonnet`, tech stack assumptions
4. `project-manager.md` - Remove `model: sonnet`, technology references
5. `expert-planner.md` - Remove `model: sonnet`
6. `ai-engineer.md` - Abstract LLM provider references
7. `devops-automator.md` - Remove Ollama-specific deployment references
8. `backend-architect.md` - Remove specific service integration assumptions

#### **Medium Priority Updates:**
- All engineering category agents with LLM integration references
- Documentation agents with technology-specific patterns
- Rapid prototyper with hardcoded integration examples

### 7. Recommended Fixes

#### **Immediate Actions:**
1. **Remove Model Specifications:** Delete `model: sonnet` from all agent YAML frontmatter
2. **Abstract Technology References:** Replace "Ollama DeepSeek" with "configured LLM provider"
3. **Use Environment Variables:** Reference `${LLM_PROVIDER}`, `${PRIMARY_MODEL}` instead of hardcoded values
4. **Update Integration Patterns:** Use configurable service interfaces

#### **Pattern Replacement Examples:**
```markdown
# BEFORE (Hardcoded):
model: sonnet
- LLM Integration Testing: Validate Ollama DeepSeek integration
- All reasoning uses Ollama DeepSeek instead of static logic

# AFTER (Configurable):
# No model specification (uses centralized config)
- LLM Integration Testing: Validate configured LLM provider integration  
- All reasoning uses centralized LLM client instead of static logic
```

#### **Configuration Integration:**
```markdown
# Reference centralized configuration instead of hardcoded values:
- Use project's centralized model configuration system
- Follow KWE_PRIMARY_MODEL environment variable for model selection
- Abstract service integration through configurable interfaces
```

## Conclusion

**The agents DO use the same hardcoded patterns that violate global behavioral standards.**

### **Key Problems:**
1. **Model Configuration Violations:** 5+ agents hardcode `model: sonnet`
2. **Technology Stack Hardcoding:** 12+ agents reference specific LLM providers
3. **Service Integration Assumptions:** Multiple agents assume specific implementations
4. **Architecture Coupling:** Agents tied to specific deployment contexts

### **Required Actions:**
1. **Systematic Agent Update:** Remove all hardcoded references from agent files
2. **Centralized Configuration Integration:** Make agents use global configuration system
3. **Abstract Service References:** Replace hardcoded integrations with configurable interfaces
4. **Documentation Alignment:** Update agent documentation to reflect configurable approach

### **Priority Level:** 🔴 **HIGH** - These violations directly contradict established global behavioral standards and create technical debt that undermines the centralized configuration system.

The irony is that several agents explicitly mention "No Hardcoded Heuristics" while containing multiple hardcoded technology references themselves. This inconsistency must be resolved through systematic agent file updates.