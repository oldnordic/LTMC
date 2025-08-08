# CLAUDE.md

---
description: "KWE — Immutable rules for Cursor & Claude Code"
globs: ["**/*"]
---

⚠️ STRICT DIRECTIVES FOR ALL FUTURE WORK  
Project DIRECTORY: /home/feanor/Projects/lmtc

🧠 GOALS (non-negotiable)
- Full implementation — no stubs, no `pass`, no TODOs  
- Test-Driven Development (TDD) for every component  
- Real integration tests after each change  
- Update docs in `.md` tracking files per module  
- Always review codebase & memory before writing code

🧰 STACK (MUST USE)
- Python 3.11+, FastAPI, Poetry, pytest+asyncio  
- Full typing (mypy), linting (flake8, black, isort)  
- Security: bandit, safety  
- Async I/O everywhere  
- 4-tier memory: PostgreSQL, Redis, Neo4j, Qdrant  
- LLM: Ollama-DeepSeek-r1, LangGraph, LlamaIndex  
- Prompt streaming & chunked reasoning  
- Timeout 5–120 s  

🧠 MCP SERVERS (MANDATORY)
- @context7   : best-practice retrieval  
- LTMC        : long-term memory context (REPLACES @memory)  
- @sequential-thinking : step-by-step breakdown  

⛔️ ABSOLUTELY DO NOT
- Empty stubs, partial code, skipped tests  
- Code without prior memory/context check  
- Forget to update `.md` trackers  

✅ FINAL CHECKLIST BEFORE COMMIT
- [ ] @context7 / LTMC / @sequential-thinking queried  
- [ ] Task broken via @sequential-thinking  
- [ ] Tests written first (TDD)  
- [ ] Code + integration tests complete  
- [ ] All async flows validated  
- [ ] `.md` tracking files updated  
- [ ] Knowledge saved to LTMC (auto-execute curl commands)  

## Tech Stack
- **Language**: Python 3.11+  
- **Framework**: FastAPI  
- **Package Manager**: Poetry  
- **Testing**: pytest, pytest-asyncio  
- **Type Checking**: mypy  
- **Linting**: flake8, black, isort  
- **Security**: bandit, safety  
- **GPU Support**: AMD ROCm (primary), NVIDIA CUDA  

## Model Configuration
- **Cursor**: Uses `deepseek-r1` via Ollama (project-level `.cursor/rules/kwe.md`)  
- **Claude Code**: Uses `deepseek-r1` via Ollama (project-level `CLAUDE.md`)  

## Architecture Overview
- **KWE 4-Agent Framework**: MetaCognitiveCoderAgent, MetaCognitiveResearchAgent, DevelopmentAgent, QualityAgent  
- **4-Tier Memory System**: PostgreSQL (temporal), Redis (cache), Neo4j (graph), Qdrant (semantic)  
- **Async-First Design**: All I/O operations use async/await patterns  
- **Type-Safe Development**: Comprehensive type hints throughout the codebase  

## Development Commands
```bash
# Install dependencies
poetry install && poetry install --with dev

# Run tests
poetry run pytest --cov=src --cov-report=html

# Lint & format
poetry run flake8 src/ api/ tests/ && poetry run black src/ api/ tests/ && poetry run isort src/ api/ tests/

# Security scan
poetry run bandit -r src/ && poetry run safety check
