# LTMC Installation Guide

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 22.04+ recommended)
- **Python Version**: 3.11+
- **CPU**: 4 cores
- **RAM**: 16GB+
- **Disk Space**: 10GB free

### Required Services
1. **Redis Server**
   - Version: 7.0+
   - Port: 6381
   - Installation:
     ```bash
     sudo apt update
     sudo apt install redis-server
     sudo systemctl start redis-server
     sudo systemctl enable redis-server
     ```

2. **Neo4j Server**
   - Version: 5.x Community Edition
   - Port: 7687 (Bolt)
   - Installation:
     ```bash
     wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
     echo 'deb https://debian.neo4j.com stable latest' | sudo tee -a /etc/apt/sources.list.d/neo4j.list
     sudo apt-get update
     sudo apt-get install neo4j
     sudo systemctl start neo4j
     sudo systemctl enable neo4j
     ```

## Installation Steps

### 1. Clone Repository
```bash
git clone https://github.com/your-org/ltmc.git
cd ltmc
```

### 2. Install Poetry
```bash
pip install poetry
poetry env use python3.11
poetry shell
```

### 3. Install Dependencies
```bash
poetry install
poetry install --with dev
```

### 4. Configure Environment
```bash
cp ltmc_config.env.example ltmc_config.env
# Edit ltmc_config.env with your specific settings
```

### 5. Initialize Database
```bash
poetry run python -c "from ltms.database.schema import create_tables; create_tables()"
```

### 6. Start Dual Transport Server
```bash
./start_server.sh
```

## Post-Installation Verification

### Check Server Status
```bash
./status_server.sh
```

### Run Health Check
```bash
curl http://localhost:5050/health
```

### Test MCP Tools
```bash
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "store_memory",
      "arguments": {
        "file_name": "test.md",
        "content": "Installation test"
      }
    },
    "id": 1
  }'
```

## Troubleshooting

### Common Installation Issues
- Ensure Python 3.11+ is installed
- Check Redis and Neo4j service status
- Verify all dependencies are installed
- Review logs in `logs/` directory

### Logging
Check installation and runtime logs:
- `logs/ltmc_http.log`
- `logs/ltmc_mcp.log`
- `logs/ltmc_server.log`

## Optional: Docker Deployment

A Dockerfile is provided for containerized deployment. Build and run with:

```bash
docker build -t ltmc .
docker run -p 5050:5050 ltmc
```

## Uninstallation

To completely remove LTMC:
```bash
./stop_server.sh
poetry env remove --all
rm -rf ltmc.db faiss_index logs/
```

## Additional Resources
- [Architecture Overview](/docs/architecture/systemArchtecture.md)
- [API Reference](/docs/api/README.md)
- [Troubleshooting Guide](/docs/guides/TROUBLESHOOTING.md)