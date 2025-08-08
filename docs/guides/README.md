# Long-Term Memory Core (LTMC)

A complete Long-Term Memory Core system that provides semantic search and context retrieval capabilities through a REST API.

## Features

- **Resource Ingestion**: Add documents and text content to the memory core
- **Semantic Search**: Find relevant context using vector similarity search
- **Chat History**: Track conversations and link them to retrieved context
- **REST API**: Full HTTP interface for external clients
- **Vector Storage**: FAISS-based similarity search
- **SQLite Database**: Persistent storage for resources and metadata

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Start the Server

```bash
# Start server with default settings
./start_server.sh

# Or start manually
python run.py
```

### 3. Use the API

```bash
# Health check
curl http://localhost:8000/health

# Add a resource
curl -X POST http://localhost:8000/api/v1/resources \
  -H "Content-Type: application/json" \
  -d '{
    "file_name": "document.txt",
    "resource_type": "document",
    "content": "This is a sample document about machine learning."
  }'

# Get context for a query
curl -X POST http://localhost:8000/api/v1/context \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv123",
    "query": "What is machine learning?",
    "top_k": 3
  }'
```

## Server Management Scripts

### Start Server

```bash
./start_server.sh
```

**Features:**
- Automatic virtual environment activation
- Environment variable configuration
- Process management with PID file
- Logging to `logs/ltmc_server.log`
- Health checks and error handling

**Environment Variables:**
- `DB_PATH`: Database file path (default: `ltmc.db`)
- `FAISS_INDEX_PATH`: Vector index path (default: `faiss_index`)
- `HOST`: Server host (default: `0.0.0.0`)
- `PORT`: Server port (default: `8000`)
- `RELOAD`: Enable auto-reload (default: `false`)

### Stop Server

```bash
./stop_server.sh
```

**Features:**
- Graceful shutdown with SIGTERM
- Force kill with SIGKILL if needed
- PID file cleanup
- Status checking

### Check Server Status

```bash
./status_server.sh
```

**Features:**
- Process status verification
- Recent log entries display
- HTTP response checking
- Process information display

## API Endpoints

### Health Check
```
GET /health
```
Returns server status and timestamp.

### Add Resource
```
POST /api/v1/resources
```
Add a new document or text resource to the memory core.

**Request Body:**
```json
{
  "file_name": "document.txt",
  "resource_type": "document",
  "content": "Text content to store..."
}
```

**Response:**
```json
{
  "success": true,
  "resource_id": 1,
  "chunk_count": 3
}
```

### Get Context
```
POST /api/v1/context
```
Retrieve relevant context for a query.

**Request Body:**
```json
{
  "conversation_id": "conv123",
  "query": "What is machine learning?",
  "top_k": 3
}
```

**Response:**
```json
{
  "success": true,
  "context": "Machine learning is a subset of artificial intelligence...",
  "retrieved_chunks": [
    {
      "chunk_id": 1,
      "resource_id": 1,
      "file_name": "document.txt",
      "score": 0.85
    }
  ]
}
```

## System Architecture

### Data Flow 1: Resource Ingestion
1. **HTTP Request** → API receives file_name, type, content
2. **Text Chunking** → Split into semantically coherent chunks
3. **Embedding Generation** → Convert chunks to 384-dimensional vectors
4. **Database Storage** → Store resource and chunks in SQLite
5. **Vector Storage** → Add embeddings to FAISS index
6. **Response** → Return resource_id and chunk_count

### Data Flow 2: Context Retrieval
1. **HTTP Request** → API receives query and conversation_id
2. **Query Embedding** → Convert query to vector
3. **Similarity Search** → Find similar chunks in FAISS index
4. **Context Assembly** → Retrieve full text and metadata
5. **Chat Logging** → Store query in conversation history
6. **Response** → Return context and chunk metadata

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PATH` | `ltmc.db` | SQLite database file path |
| `FAISS_INDEX_PATH` | `faiss_index` | FAISS vector index file path |
| `HOST` | `0.0.0.0` | Server host address |
| `PORT` | `8000` | Server port number |
| `RELOAD` | `false` | Enable auto-reload for development |

### Database Schema

- **Resources**: Store document metadata
- **ResourceChunks**: Store text chunks with vector IDs
- **ChatHistory**: Store conversation messages
- **ContextLinks**: Link messages to used chunks

## Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/database/ -v
python -m pytest tests/services/ -v
python -m pytest tests/api/ -v
```

### Project Structure

```
lmtc/
├── ltms/                    # Main application package
│   ├── api/                # FastAPI endpoints
│   ├── database/           # Database layer
│   ├── services/           # Business logic
│   └── vector_store/       # FAISS vector operations
├── tests/                  # Test suite
├── logs/                   # Server logs
├── start_server.sh         # Server start script
├── stop_server.sh          # Server stop script
├── status_server.sh        # Server status script
├── run.py                  # Server entry point
└── requirements.txt        # Python dependencies
```

## Troubleshooting

### Common Issues

1. **Server won't start**
   - Check if port 8000 is available
   - Verify virtual environment is activated
   - Check log file for errors

2. **Import errors**
   - Ensure all requirements are installed: `pip install -r requirements.txt`
   - Activate virtual environment

3. **Database errors**
   - Check file permissions for database directory
   - Verify SQLite is available

4. **Vector search not working**
   - Check FAISS index file permissions
   - Verify sentence-transformers is installed

### Log Files

- **Server logs**: `logs/ltmc_server.log`
- **PID file**: `ltmc_server.pid`

### Manual Server Control

```bash
# Start server manually
python run.py

# Check if server is running
ps aux | grep python

# Kill server manually
pkill -f "python run.py"
```

## License

This project is part of the Long-Term Memory Core system.
