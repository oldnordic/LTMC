LTMC Integration & Fix Plan (TDD)

Status baseline
- Memory core: FAISS + SQLite operational; embeddings via MiniLM; retrieval working
- Context logging: Chat history + ContextLinks working; minor JSON response shaping
- Todos: add/search/list working
- MCP: 19 tools exposed over stdio and HTTP; JSON-RPC healthy

Goals
- Fix current MCP tool inconsistencies (no breaking behavior for clients)
- Add high-impact features: hybrid ranking, auto-summary ingestion, graph query, SSE streaming
- Prepare for durability and multi-agent observability: TTL/archival and agent tracing
- Keep changes additive, small, and fully covered by tests (TDD)

Priorities
1) High: Advanced retrieval ranking; Auto-summary ingestion
2) Medium: SSE streaming for context; Graph query (read-only)
3) Medium/High (if HTTP beyond localhost): API auth (token)
4) Later: TTL/archival; Dashboard
Optional: Agent trace logging; Tool discovery enrichment

Cross-cutting rules
- Tests-first (pytest) for every feature; no mocks/stubs/placeholders
- Full error handling; validated inputs; stable, documented responses
- Schema migrations are idempotent; run on boot; versioned via schema_version table
- No breaking changes to existing endpoints or MCP tool contracts unless explicitly noted

Work items (with design, files, tests, acceptance)

0) MCP tool fixes and response shaping
- Design
  - link_resources: unify to {source_id: str, target_id: str, relation: str, properties?: dict}
  - log_chat: return {success: true, message_id: int}; keep current behavior; shape JSON consistently
  - Add describe_tool(name) in MCP or enrich /api/v1/tools to return tool names + parameter hints
- Files
  - ltms/mcp_server.py: adjust tool signatures and return shapes; add optional describe_tool logic
  - ltms/mcp_server_http.py: expose GET /api/v1/tools with schemas/hints if feasible
  - docs/guides/tools.md: document signatures and examples
- Tests
  - tests/mcp/test_mcp_server.py: validate signatures, error handling, and JSON shapes
  - tests/test_run.py: GET /tools returns 200 and expected schema
- Acceptance
  - link_resources accepts source/target/relation and returns success payload
  - log_chat returns message_id consistently
  - /tools (HTTP) and tools/list (JSON-RPC) provide discoverable interface

1) Advanced retrieval ranking (hybrid scoring)
- Design
  - Compute score = α*similarity + β*recency + γ*frequency + δ*length_boost + ε*type_boost
  - Over-fetch top K×R from FAISS, then re-rank in Python with metadata from SQLite
  - Expose tunables via config (defaults: α=1.0, β=0.2, γ=0.1, δ=0.05, ε=0.1)
- Files
  - ltms/config.py: add RANKING_WEIGHTS and overfetch factor
  - tools/retrieve.py: return raw similarity scores; add hybrid ranker; deterministic ordering
  - vector/ or faiss store module: ensure raw scores are returned to retriever
- Tests
  - tests/test_retrieve.py: verify ranker ordering vs cosine-only; deterministic with fixed times
- Acceptance
  - Retrieval returns better-ranked results on mixed-age/frequency fixtures
  - No regression in latency beyond configured budget

2) Auto-summary ingestion (external summaries)
- Design
  - Dedicated table Summaries(id, resource_id, doc_id, summary_text, model, created_at)
  - Service: store_summary(resource_or_doc, text, model)
  - HTTP: POST /api/v1/summaries with SummaryRequest{doc_id|resource_id, summary_text, model?}
- Files
  - ltms/database/schema.py (or migration): CREATE TABLE IF NOT EXISTS Summaries(...); indexes
  - ltms/services/resource_service.py: store_summary()
  - ltms/api/main.py or ltms/mcp_server_http.py: POST /api/v1/summaries
  - docs/api/summaries.md: route spec + examples
- Tests
  - tests/test_summaries.py: POST persists; GET by doc/resource returns inserted rows
- Acceptance
  - Agents can push summaries; persisted and queryable; idempotent behavior documented

3) Graph query (Neo4j) – read-only
- Design
  - Add search_relations(entity_id, relationship_type=None) wrapper over query_relationships
  - HTTP: POST /api/v1/graph/query accepts restricted Cypher or structured params; enforce read-only
  - Reject CREATE/MERGE/DELETE/SET; allow MATCH/RETURN only
- Files
  - ltms/database/neo4j_store.py: search_relations()
  - ltms/api/main.py or ltms/mcp_server_http.py: POST /api/v1/graph/query
  - docs/graph_examples.md: sample MATCH patterns and results
- Tests
  - tests/test_neo4j_integration.py: query returns 200 and no side effects
- Acceptance
  - Safe query route; returns relationships; blocked on write attempts (400/403)

4) SSE streaming for context retrieval (HTTP)
- Design
  - When Accept: text/event-stream or transport=sse, stream results incrementally with StreamingResponse
  - Chunk large lists into events; include progress metadata
- Files
  - ltms/api/main.py or ltms/mcp_server_http.py: update /api/v1/context to support SSE
  - ltms/config.py: ENABLE_SSE=True flag
- Tests
  - tests/test_run.py: request SSE and assert streamed chunks arrive in order
- Acceptance
  - Large retrievals do not block; clients receive incremental events; non-SSE behavior unchanged

5) Memory TTL / archival (deferred if needed)
- Design
  - Add ResourceChunks.archived INTEGER DEFAULT 0; ensure created_at exists
  - Retrieval: over-fetch then post-filter archived=0 and created_at >= cutoff
- Files
  - ltms/database/schema.py: migration for archived and created_at (if missing)
  - tools/retrieve.py: apply TTL filter and re-rank
- Tests
  - tests/test_retrieve_ttl.py: archived chunks excluded; cutoff respected
- Acceptance
  - TTL policy enforced without impacting FAISS index operations

6) Agent trace logging (optional but useful)
- Design
  - Add ChatHistory.agent_name TEXT, metadata JSON
  - log_chat accepts agent_name and metadata
- Files
  - ltms/database/schema.py: migration for columns
  - ltms/mcp_server.py: extend log_chat tool parameters and validation
- Tests
  - tests/test_log_chat.py: fields persisted; defaults handled
- Acceptance
  - Distinguish agents and capture tool/model metadata for analytics

7) API authentication (if exposed beyond localhost)
- Design
  - Simple token auth via LTMC_API_TOKEN header; feature flag ENABLE_AUTH
  - Apply to write endpoints: store_memory, log_chat, summaries, link_resources
- Files
  - ltms/config.py: ENABLE_AUTH and token
  - ltms/api/main.py or ltms/mcp_server_http.py: dependency that validates token
- Tests
  - tests/test_auth.py: 401 without token; 200 with valid token
- Acceptance
  - Unauthorized access blocked; localhost dev flows documented

8) Dashboard (later)
- Design
  - Minimal read-only UI to inspect resources, chats, relationships, todos
  - Consider fastapi-admin or static React served by FastAPI
- Files
  - dashboard/ (new) and run_dashboard.py (optional)
  - docs/guides/dashboard.md
- Tests
  - Basic route tests; defer E2E until MVP
- Acceptance
  - Non-blocking for agents; added after core APIs stabilize

Schema migrations plan (SQLite)
- Create schema_version table if missing
- For each change, apply CREATE/ALTER IF NOT EXISTS; record version bump
- Validate indices: Summaries(resource_id, doc_id), ResourceChunks(created_at, archived)

Rollout checklist
- Write tests for each item, then implement until tests pass
- Run lints and tests locally
- Apply migrations automatically on app startup
- Start dual transport: ./start_server.sh
- Verify: /health, /tools, /jsonrpc tools/list, /api/v1/context (SSE), /api/v1/summaries, /api/v1/graph/query
- Document features in docs/ and link from docs/README.md

cURL test snippets
- Health: curl http://localhost:5050/health
- Tools: curl http://localhost:5050/tools
- JSON-RPC tools: curl -X POST http://localhost:5050/jsonrpc -H 'Content-Type: application/json' -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
- Summaries: curl -X POST http://localhost:5050/api/v1/summaries -H 'Content-Type: application/json' -d '{"doc_id":"doc_1","summary_text":"...","model":"claude-3"}'
- Graph query (read-only): curl -X POST http://localhost:5050/api/v1/graph/query -H 'Content-Type: application/json' -d '{"entity_id":"doc_1"}'
- Context (SSE): curl -N -H 'Accept: text/event-stream' 'http://localhost:5050/api/v1/context?conversation_id=1&query=hello&transport=sse'

Risks & mitigations
- Neo4j write-protection: enforce read-only Cypher; reject writes
- Performance: bound over-fetch and stream chunked responses
- Backward compatibility: keep existing contracts; version any breaking change explicitly
- Security: enable token auth if binding beyond localhost; avoid sensitive logs

Success criteria
- Tests pass (unit + API + integration)
- No linter errors; clear docstrings and type hints
- Features deliver measurable UX benefits (faster perceived retrieval, better ranking, easy graph inspection)
- Dual transport remains stable; HTTP health and JSON-RPC tools listing remain green


