# LTMC Configuration Guide

Complete configuration guide for the LTMC (Long-Term Memory and Context) MCP server.

## Environment Variables

### Core Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PATH` | `ltmc.db` | SQLite database path |
| `FAISS_INDEX_PATH` | `faiss_index` | FAISS vector index path |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |
| `MCP_TRANSPORT` | `stdio` | MCP transport protocol (stdio only) |
| `MCP_LOG_LEVEL` | `WARNING` | MCP logging level for stdio |
| `ORCHESTRATION_MODE` | `basic` | Redis Orchestration mode (basic/full/debug) |
| `AGENT_REGISTRY_ENABLED` | `true` | Enable Agent Registry Service |
| `CONTEXT_COORDINATION_ENABLED` | `true` | Enable Context Coordination Service |
| `MEMORY_LOCKING_STRATEGY` | `optimistic` | Memory locking strategy (optimistic/pessimistic) |

### Redis Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis server host |
| `REDIS_PORT` | `6381` | Redis server port |
| `REDIS_PASSWORD` | `ltmc_cache_2025` | Redis password |
| `REDIS_DB` | `0` | Redis database number |

### Neo4j Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `kwe_password` | Neo4j password |
| `NEO4J_DATABASE` | `neo4j` | Neo4j database name |

### Authentication (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_AUTH` | `0` | Enable API authentication (0/1) |
| `LTMC_API_TOKEN` | - | API authentication token |

## Configuration Files

### Environment File (.env)

Create a `.env` file in the project root:

```bash
# Core Configuration
DB_PATH=ltmc.db
FAISS_INDEX_PATH=faiss_index
LOG_LEVEL=INFO
HTTP_HOST=localhost
HTTP_PORT=5050

# Redis Configuration  
REDIS_HOST=localhost
REDIS_PORT=6381
REDIS_PASSWORD=ltmc_cache_2025
REDIS_DB=0

# Orchestration Configuration
ORCHESTRATION_MODE=full
AGENT_REGISTRY_ENABLED=true
CONTEXT_COORDINATION_ENABLED=true
MEMORY_LOCKING_STRATEGY=optimistic

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j

# Optional Authentication
ENABLE_AUTH=0
# LTMC_API_TOKEN=your_secure_token_here
```

### Server Scripts Configuration

The server management scripts can be configured by editing the script files:

#### start_server.sh
- Modify environment variable exports
- Adjust process management settings
- Configure log file locations

#### stop_server.sh
- Customize cleanup procedures
- Configure graceful shutdown timeouts

#### redis_control.sh
- Adjust Redis server settings
- Configure data persistence options

## Database Configuration

### SQLite Settings

SQLite database is automatically initialized with the following tables:
- `Resources`: Main content storage
- `ResourceChunks`: Chunked content with embeddings
- `VectorIdSequence`: Vector ID management
- `ChatHistory`: Conversation logs
- `Todos`: Task management
- `CodePatterns`: Code pattern storage

**Performance Tuning:**
```sql
-- Enable WAL mode for better concurrency
PRAGMA journal_mode = WAL;

-- Optimize cache size
PRAGMA cache_size = -64000; -- 64MB cache

-- Enable foreign keys
PRAGMA foreign_keys = ON;
```

### FAISS Index Configuration

Vector index settings:
- **Dimension**: 384 (SentenceTransformers all-MiniLM-L6-v2)
- **Index Type**: IndexFlatL2 (exact search)
- **Metric**: L2 (Euclidean distance)

For large datasets, consider switching to IndexIVFFlat:
```python
# In ltms/services/embedding_service.py
import faiss
index = faiss.IndexIVFFlat(quantizer, 384, ncentroids)
```

## Service Dependencies

### Redis Orchestration Configuration

### Orchestration Modes

| Mode | Description | Typical Use Case |
|------|-------------|-----------------|
| `basic` | Minimal service coordination | Lightweight deployments |
| `full` | Complete service integration | Complex multi-agent scenarios |
| `debug` | Enhanced logging and tracing | Development and troubleshooting |

### Orchestration Service Configuration

| Service | Variable | Default | Description |
|---------|----------|---------|-------------|
| Agent Registry | `AGENT_REGISTRY_ENABLED` | `true` | Enable/disable agent tracking |
| Context Coordination | `CONTEXT_COORDINATION_ENABLED` | `true` | Enable/disable context sharing |
| Memory Locking | `MEMORY_LOCKING_STRATEGY` | `optimistic` | Concurrency control strategy |

**Service Activation Example:**
```bash
# Configure orchestration mode and services
export ORCHESTRATION_MODE=full
export AGENT_REGISTRY_ENABLED=true
export CONTEXT_COORDINATION_ENABLED=true
export MEMORY_LOCKING_STRATEGY=optimistic
```

## Redis Server Configuration

**Installation & Setup:**
```bash
# Ubuntu/Debian
sudo apt install redis-server

# macOS
brew install redis

# Configure Redis for LTMC
sudo nano /etc/redis/redis.conf
```

**Redis Configuration (`/etc/redis/redis.conf`):**
```conf
# Bind to localhost only (security)
bind 127.0.0.1

# Set port for LTMC (avoid conflicts)
port 6381

# Enable password authentication
requirepass ltmc_cache_2025

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000
```

**Start Redis:**
```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### Neo4j Server Configuration

**Installation:**
```bash
# Add Neo4j repository
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j

# macOS
brew install neo4j
```

**Neo4j Configuration (`/etc/neo4j/neo4j.conf`):**
```conf
# Network connector configuration
dbms.default_listen_address=0.0.0.0
dbms.connector.bolt.listen_address=:7687
dbms.connector.http.listen_address=:7474

# Security
dbms.security.auth_enabled=true

# Memory settings
dbms.memory.heap.initial_size=512m
dbms.memory.heap.max_size=1G
dbms.memory.pagecache.size=1G

# Database location
dbms.directories.data=/var/lib/neo4j/data
```

**Initialize Neo4j:**
```bash
sudo systemctl start neo4j
sudo systemctl enable neo4j

# Set initial password
cypher-shell -u neo4j -p neo4j
ALTER USER neo4j SET PASSWORD 'kwe_password';
```

## Performance Optimization

### Memory Usage

**SQLite Optimization:**
```bash
# Enable memory mapping
export SQLITE_TMPDIR=/tmp/ltmc_sqlite
mkdir -p $SQLITE_TMPDIR
```

**Python Memory:**
```bash
# Increase Python memory limit
export PYTHONMALLOC=malloc
export MALLOC_ARENA_MAX=4
```

### Concurrent Connections

**HTTP Server:**
```bash
# Increase uvicorn workers (in production)
uvicorn ltms.mcp_server_http:app --workers 4 --port 5050
```

**Database Connections:**
- SQLite: Uses connection pooling
- Redis: Connection pool size = 10
- Neo4j: Session pool managed by driver

### Embedding Performance

**CPU Optimization:**
```bash
# Use all CPU cores for embeddings
export OMP_NUM_THREADS=$(nproc)
export MKL_NUM_THREADS=$(nproc)
```

**GPU Support (Optional):**
```python
# In ltms/services/embedding_service.py
device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
```

## Security Configuration

### Network Security

**Firewall Rules:**
```bash
# Allow LTMC HTTP port
sudo ufw allow 5050/tcp

# Restrict database ports to localhost
sudo ufw deny 6381/tcp  # Redis
sudo ufw deny 7687/tcp  # Neo4j Bolt
sudo ufw deny 7474/tcp  # Neo4j HTTP
```

### Authentication

**Enable API Authentication:**
```bash
export ENABLE_AUTH=1
export LTMC_API_TOKEN=$(openssl rand -hex 32)
echo "API Token: $LTMC_API_TOKEN"
```

**MCP Client Authentication:**
```python
# Authentication handled via MCP server process security
# No HTTP tokens required - stdio transport is secure by design
server_params = StdioServerParameters(
    command="python",
    args=["ltmc_stdio_wrapper.py"],
    env={"LTMC_SECURE_MODE": "true"}
)
```

### Data Encryption

**Redis Encryption (Optional):**
```conf
# In redis.conf
tls-port 6380
tls-cert-file /path/to/cert.pem
tls-key-file /path/to/key.pem
```

## Monitoring & Logging

### Log Configuration

**Log Levels:**
- `DEBUG`: Detailed debugging information
- `INFO`: General information (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages only

**Log Files:**
- HTTP Transport: `logs/ltmc_http.log`
- Stdio Transport: `logs/ltmc_mcp.log`
- Server General: `logs/ltmc_server.log`

### Health Monitoring

**Health Check via MCP:**
```python
# Check LTMC system health via MCP tools
health_status = await session.call_tool("get_performance_report")
redis_health = await session.call_tool("redis_health_check")
print(f"LTMC Status: {health_status['status']}")
```

**System Status:**
```bash
./status_server.sh
```

## Backup & Recovery

### Database Backup

**SQLite Backup:**
```bash
# Hot backup
sqlite3 ltmc.db ".backup ltmc_backup.db"

# Scheduled backup
0 2 * * * sqlite3 /path/to/ltmc.db ".backup /backups/ltmc_$(date +\%Y\%m\%d).db"
```

**FAISS Index Backup:**
```bash
cp -r faiss_index faiss_index_backup_$(date +%Y%m%d)
```

### Redis Backup

**Manual Backup:**
```bash
redis-cli -p 6381 -a ltmc_cache_2025 BGSAVE
cp /var/lib/redis/dump.rdb /backups/redis_ltmc_$(date +%Y%m%d).rdb
```

### Neo4j Backup

**Database Export:**
```bash
neo4j-admin dump --database=neo4j --to=/backups/neo4j_ltmc_$(date +%Y%m%d).dump
```

## Troubleshooting

For detailed troubleshooting information, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

### Quick Diagnostics

**Check All Services:**
```bash
./status_server.sh
```

**Test Database Connectivity:**
```bash
python -c "
import sqlite3
conn = sqlite3.connect('ltmc.db')
print('SQLite: OK')
conn.close()

import redis
r = redis.Redis(host='localhost', port=6381, password='ltmc_cache_2025')
r.ping()
print('Redis: OK')

from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'kwe_password'))
driver.verify_connectivity()
print('Neo4j: OK')
"
```

**Validate Configuration:**
```bash
python -c "
import os
from ltms.services.redis_service import get_redis_manager
from ltms.database.connection import get_db_connection

print('Environment Variables:')
for var in ['DB_PATH', 'REDIS_PORT', 'NEO4J_URI']:
    print(f'  {var}: {os.getenv(var, \"Not Set\")}')
"
```

---

For installation instructions, see [INSTALLATION.md](INSTALLATION.md).
For architecture details, see [Architecture Overview](../architecture/systemArchtecture.md).