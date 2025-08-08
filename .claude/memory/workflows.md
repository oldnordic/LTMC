# KWE Development Workflows

## Development Workflow Patterns

### Standard Development Cycle
1. **Context Retrieval**
   - Query @context7 for best practices
   - Retrieve project context from @memory
   - Use @sequential-thinking for task breakdown

2. **Task Planning**
   - Create detailed task decomposition
   - Identify dependencies and potential challenges
   - Define clear acceptance criteria

3. **Implementation**
   - Write tests first (TDD approach)
   - Implement with full typing
   - Follow async patterns
   - Maintain code quality standards

4. **Validation**
   - Run comprehensive test suite
   - Execute quality checks
   - Review code with agents
   - Update documentation

5. **Finalization**
   - Commit changes
   - Update @memory with implementation details
   - Prepare for code review

## Git Workflow

### Branching Strategy
- **Main Branch**: `main` (production-ready)
- **Development Branch**: `develop`
- **Feature Branches**: `feature/[description]`
- **Hotfix Branches**: `hotfix/[issue]`

### Commit Message Conventions
- Use imperative mood
- Provide context and reasoning
- Reference issue numbers
- Keep messages concise

### Pull Request Process
1. Create feature branch from `develop`
2. Implement feature with tests
3. Run quality checks
4. Create pull request to `develop`
5. Mandatory code review
6. Squash and merge

## Issue Tracking

### Issue Categories
- **Bug**: Defects in existing functionality
- **Feature**: New capabilities
- **Enhancement**: Improvements to existing features
- **Documentation**: Doc updates and clarifications
- **Performance**: Optimization tasks

### Workflow Markers
- `todo`: Not started
- `in_progress`: Active development
- `review`: Awaiting code review
- `blocked`: Requires external intervention
- `done`: Completed and merged

## Code Review Standards

### Review Checklist
- Verify test coverage
- Check type annotations
- Validate async patterns
- Review error handling
- Assess performance implications
- Confirm documentation updates

### Agent-Assisted Reviews
- MetaCognitiveCoderAgent: Code quality check
- QualityAgent: Comprehensive validation
- MetaCognitiveResearchAgent: Context and best practices review

## Development Environment

### Concurrent Development
```bash
# Terminal 1: Backend
python test_server.py

# Terminal 2: Frontend
cd frontend && npm run tauri dev
```

## Continuous Learning

### Knowledge Capture
- Document lessons learned
- Update @memory after significant changes
- Share insights across agent framework
- Maintain living documentation

## Troubleshooting Workflow

### Problem Resolution Steps
1. Reproduce the issue
2. Isolate the problem
3. Create minimal test case
4. Investigate root cause
5. Develop fix with tests
6. Validate across multiple scenarios
7. Document resolution strategy

## Collaboration Principles

### Cross-Agent Collaboration
- Share context transparently
- Use unified memory system
- Maintain clear communication protocols
- Leverage collective intelligence

### Documentation Philosophy
- Document decisions, not just code
- Maintain up-to-date knowledge base
- Create reusable knowledge artifacts
- Prioritize clarity and brevity