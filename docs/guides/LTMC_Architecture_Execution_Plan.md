# LTMC MCP Server - Full Architecture and Execution Plan

## 🧠 Design Principles
- **Model-Agnostic**: LTMC performs no inference or summarization itself
- **Summarization Is External**: Tools like Cursor, Claude, Gemini, and VSCode are responsible for generating summaries using their models
- **Multi-Agent Friendly**: Supports MCP stdio and HTTP transports to allow different agents to access the memory
- **Separation of Concerns**: Retrieval, chunking, embedding, linking, and storage are modular and interchangeable
- **Transparent Context**: Contexts returned are raw chunks with full metadata and scores; summaries are optional
- **Extendable Memory**: Future-ready with Neo4j-based relationships and ToDo memory support

---

## ✅ Completed Modules
- [x] SQLite schema + connection + DAL layer
- [x] FAISS vector index (IndexFlatIP) and persistent storage
- [x] SentenceTransformer embedding (MiniLM 384-d)
- [x] Modular config loading from `.env`
- [x] Ingestion pipeline: documents, code, chat, todos
- [x] FastAPI server (`/api/v1/resources`, `/api/v1/context`, `/health`)
- [x] FastMCP server with `store_memory`, `retrieve_memory`, `ask_with_context`
- [x] Pydantic models for request/response validation
- [x] Test suite with `pytest` structure for all layers

---

## 🔄 In Progress / Incomplete Modules

### 🧩 Retrieval & Context Tools
- [ ] `tools/retrieve.py`: Clean retrieval with metadata + score
- [ ] MCP: `retrieve_memory(conversation_id, query, top_k)`
- [ ] `/context` supports `type` filters (e.g., only `code` or `todos`)
- [ ] Add ranking + context window builder
- [ ] Return format: raw, scored chunks (JSON-serializable)

### 💬 Chat Logging & ContextLinking
- [ ] `log_chat(conversation_id, role, content)` → stores message
- [ ] `store_context_links(message_id, chunk_ids)` → traces what memory was used
- [ ] MCP exposes both as tools
- [ ] Logs stored in `ChatHistory` and `ContextLinks`

### 🧠 Neo4j Integration (Graph Memory)
- [ ] Module: `neo4j_store.py` with `GraphDatabase.driver`
- [ ] Support auto-linking between related documents
- [ ] Manual linking tool `link_resources(a, b, relation)`
- [ ] Relationship discovery: `query_graph(entity, relation_type)`
- [ ] Expose graph context as optional retrieval backend

### 🌐 HTTP & SSE MCP Transport
- [ ] Add `FastMCP(..., transport='http')` support
- [ ] Launch MCP HTTP server at `http://localhost:5050`
- [ ] Enable streaming memory responses with SSE or chunked JSON

### 📤 Summarization Handling
- [x] Removed all internal summarization (OpenAI, etc.)
- [ ] Retrieval returns raw chunks
- [ ] Optionally: expose a tool `store_summary(doc_id, summary)` for clients
- [ ] Summaries are stored as part of document metadata, not generated

### ✅ ToDo System
- [x] Store todos as memory entries (with type='todo')
- [ ] Expose as MCP tools:
  - `add_todo(title, description)`
  - `list_todos(completed: bool)`
  - `complete_todo(todo_id)`
  - `search_todos(query)`

---

## 🛠 Final Tool Summary (via MCP)

### ✅ Core Memory Tools
- `store_memory(file_name, content, resource_type)`
- `retrieve_memory(conversation_id, query, top_k)`

### 🔜 Chat Logging + Linking
- `log_chat(conversation_id, role, content)`
- `store_context_links(message_id, chunk_ids)`

### 🔜 Summary Ingestion
- `store_summary(doc_id, summary)` (external summaries only)

### 🔜 Graph Memory (Neo4j)
- `link_resources(doc_id_a, doc_id_b, relation)`
- `query_graph(entity, relation_type)`

### 🔜 ToDo Memory
- `add_todo(title, description)`
- `list_todos(completed)`
- `complete_todo(todo_id)`
- `search_todos(query)`

---

## 🔌 API Interface
- `/api/v1/resources` → Document/code/chat/todo ingestion
- `/api/v1/context` → Retrieve memory with top_k + filters
- `/health` → App status for orchestration or self-checks

---

## 🧪 Test Plan
- [ ] End-to-end tests (ingestion → retrieval → context links)
- [ ] REST API contract tests (`requests`, `httpx`)
- [ ] FAISS integration tests (index load/save/search)
- [ ] SQLite DAL tests
- [ ] Neo4j relationship tests
- [ ] MCP tools over stdio and HTTP
- [ ] Memory format compliance for Claude/Cursor/Gemini/VSCode

---

## 📦 Deployment Modes
- Local Python CLI (for Cursor or Claude agents)
- REST API for plugins / IDEs
- MCP Server (stdio and HTTP transports)
- Docker support (production/staging)
- Systemd service for long-term deployment

---

## 🧠 LTMC System Role
> **LTMC is the hippocampus.**
>
> It doesn't summarize, hallucinate, or answer questions. It stores, retrieves, and tracks memory faithfully.
>
> Different AI agents bring their own cortex. LTMC just helps them remember.

---

## ✅ Status Overview
| Component         | Status  |
|------------------|---------|
| Ingestion         | ✅ Done |
| Vector Search     | ✅ Done |
| Summarization     | ✅ External Only |
| Retrieval         | 🔄 In Progress |
| Chat History      | ⬜ Missing |
| Context Linking   | ⬜ Missing |
| Neo4j Graph       | ⬜ Missing |
| ToDo Tools        | ⬜ Partial |
| HTTP Transport    | ⬜ Missing |
| Testing           | 🔄 Ongoing |

---

*Last Updated: 2025-08-07*
*Maintainer: @LTMC Architect*
