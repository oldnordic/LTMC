# Contributing to LTMC

Thank you for your interest in contributing to LTMC (Long-Term Memory and Context) MCP Server! We welcome contributions from the community.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Git
- Redis (for caching functionality)
- Neo4j (for knowledge graph functionality, optional)

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/ltmc-mcp-server.git
   cd ltmc-mcp-server
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Development dependencies
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

5. **Verify Installation**
   ```bash
   python -m ltms.mcp_server --help
   ```

## How to Contribute

### Reporting Bugs
1. Check existing issues to avoid duplicates
2. Use the bug report template
3. Include:
   - LTMC version
   - Python version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs/screenshots

### Suggesting Features
1. Check existing feature requests
2. Use the feature request template  
3. Describe:
   - Use case and motivation
   - Proposed solution
   - Alternative solutions considered
   - Impact on existing functionality

### Code Contributions
1. Create a feature branch from `main`
2. Make your changes following our coding standards
3. Add tests for new functionality
4. Update documentation as needed
5. Submit a pull request

## Coding Standards

### Python Style
- **Formatter**: Black with line length 88
- **Import Sorting**: isort with Black profile
- **Linting**: flake8 with these ignore rules: E203, W503
- **Type Checking**: mypy for gradual typing
- **Security**: bandit for security analysis

### Code Organization
- **File Size**: Maximum 300 lines per file
- **Functions**: Single responsibility, clear naming
- **Classes**: Follow Python naming conventions
- **Constants**: ALL_CAPS with underscores

### MCP Tool Development
When adding new tools:

```python
@mcp.tool(name="mcp__ltmc__your_action")
async def your_action(
    action: str,
    # ... other parameters
) -> dict:
    """
    Your tool description.
    
    Args:
        action: Action to perform (create, read, update, delete, etc.)
        
    Returns:
        dict: Success/error response with results
    """
    try:
        # Implementation here
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Action-Based Dispatch Pattern
All tools use action-based dispatch:

```python
if action == "create":
    # Handle creation
elif action == "read":  
    # Handle reading
elif action == "update":
    # Handle updates
else:
    return {"success": False, "error": f"Unknown action: {action}"}
```

## Testing

### Test Structure
```
tests/
├── unit/           # Unit tests for individual functions
├── integration/    # Integration tests with databases
├── mcp/           # MCP protocol compliance tests
└── performance/   # Performance and load tests
```

### Running Tests
```bash
# All tests
pytest

# Specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/mcp/

# With coverage
pytest --cov=ltms --cov-report=html

# Performance tests
pytest tests/performance/ -v
```

### Writing Tests
```python
import pytest
from ltms.tools.consolidated import memory_action

@pytest.mark.asyncio
async def test_memory_store():
    result = await memory_action(
        action="store",
        file_name="test.md",
        content="Test content"
    )
    assert result["success"] is True
    assert "doc_id" in result
```

### Test Requirements
- **Coverage**: Minimum 85% code coverage
- **Real Functionality**: No mocks for core functionality
- **Database Tests**: Test with real database connections
- **Error Cases**: Test error handling and edge cases

## Documentation

### Documentation Standards
- **API Documentation**: All tools must have complete API documentation
- **Code Comments**: Focus on "why" rather than "what"
- **Docstrings**: Use Google-style docstrings
- **Examples**: Include working code examples
- **Architecture**: Update architecture docs for significant changes

### Documentation Files
- **API Reference**: `/docs/api/API_REFERENCE.md`
- **User Guide**: `/docs/guides/USER_GUIDE.md`
- **Architecture**: `/docs/architecture/SYSTEM_ARCHITECTURE.md`
- **Deployment**: `/docs/guides/DEPLOYMENT.md`

### Documentation Verification
All documentation must be:
- **Reality-Aligned**: Match actual implementation
- **Tested**: All code examples must work
- **Current**: Updated with any changes
- **Complete**: Cover all functionality

## Pull Request Process

### Before Submitting
1. **Sync with main**: Rebase your branch on latest main
2. **Run tests**: Ensure all tests pass
3. **Check quality**: Run linting and formatting tools
4. **Update docs**: Update relevant documentation
5. **Test examples**: Verify all code examples work

### PR Requirements
- **Description**: Clear description of changes and motivation
- **Tests**: Include tests for new functionality
- **Documentation**: Update relevant documentation
- **Backwards Compatibility**: Maintain compatibility or document breaking changes
- **Performance**: Consider performance impact of changes

### Quality Gates
All PRs must pass:
- ✅ All automated tests
- ✅ Code quality checks (black, flake8, mypy, bandit)
- ✅ Documentation verification
- ✅ Performance regression tests
- ✅ Security scan
- ✅ Manual code review

### Review Process
1. **Automated Checks**: CI/CD pipeline runs all quality gates
2. **Code Review**: Maintainer reviews code and design
3. **Testing**: Manual testing of new functionality
4. **Documentation Review**: Verify documentation accuracy
5. **Approval**: At least one maintainer approval required

## Development Workflow

### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages
Follow conventional commits:
```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`

Examples:
```
feat(memory): add vector similarity search
fix(database): resolve connection pool timeout
docs(api): update tool reference examples
test(integration): add comprehensive MCP tests
```

### Development Commands

```bash
# Code formatting
black ltms/ tests/
isort ltms/ tests/

# Linting
flake8 ltms/ tests/
mypy ltms/

# Security scan
bandit -r ltms/

# Run development server
python -m ltms.mcp_server

# Build documentation
cd docs && make html

# Performance profiling
python -m cProfile -o profile.stats -m ltms.mcp_server
```

## Architecture Contributions

### Design Principles
- **Simplicity**: Prefer simple, clear solutions
- **Performance**: Optimize for <500ms response times
- **Reliability**: Comprehensive error handling and testing
- **Maintainability**: Clear code organization and documentation
- **Security**: Follow security best practices

### Database Design
- **SQLite**: Primary storage, ACID compliance
- **FAISS**: Vector search, optimized for performance
- **Redis**: Caching and session state
- **Neo4j**: Knowledge graphs, optional graceful degradation

### Tool Design
All tools should:
- Use action-based dispatch pattern
- Provide comprehensive error handling
- Include parameter validation
- Return consistent response format
- Support async operation
- Include performance monitoring

## Getting Help

### Communication Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **Documentation**: Comprehensive guides in `/docs/`

### Maintainer Contact
- Review the maintainer list in README.md
- Tag maintainers in issues for urgent matters
- Use GitHub discussions for general questions

## Recognition

Contributors are recognized in:
- **CHANGELOG.md**: Major contributions noted in release notes
- **README.md**: Contributors section
- **GitHub**: Contributor graphs and statistics

## License

By contributing to LTMC, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to LTMC! Your contributions help make this project better for everyone.