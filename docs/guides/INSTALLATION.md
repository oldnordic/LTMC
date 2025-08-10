# LTMC Installation Guide

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 22.04+ recommended)
- **Python Version**: 3.11+
- **CPU**: 4 cores
- **RAM**: 16GB+
- **Disk Space**: 10GB free

### Required Services
1. **Redis Server** (Required for Orchestration)
   - Version: 7.0+
   - Port: 6381 (dedicated LTMC Redis instance)
   - Installation:
     ```bash
     sudo apt update
     sudo apt install redis-server
     
     # Configure LTMC Redis instance
     sudo cp /etc/redis/redis.conf /etc/redis/redis-ltmc.conf
     sudo sed -i 's/port 6379/port 6381/' /etc/redis/redis-ltmc.conf
     sudo sed -i 's/# requirepass foobared/requirepass ltmc_cache_2025/' /etc/redis/redis-ltmc.conf
     
     # Start LTMC Redis instance
     sudo systemctl start redis-server@ltmc
     sudo systemctl enable redis-server@ltmc
     ```

2. **Neo4j Server** (Optional - for advanced graph operations)
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

## Orchestration Configuration

### Enable Redis Orchestration
Create environment configuration for orchestration:

```bash
# Copy example configuration
cp ltmc_config.env.example ltmc_config.env

# Configure orchestration mode
echo "ORCHESTRATION_MODE=basic" >> ltmc_config.env
echo "REDIS_ENABLED=true" >> ltmc_config.env
echo "REDIS_PORT=6381" >> ltmc_config.env
```

### Start with Orchestration
```bash
# Start LTMC with orchestration enabled
ORCHESTRATION_MODE=basic ./start_server.sh
```

### Orchestration Modes
- `disabled`: No orchestration (original LTMC behavior)
- `basic`: Core coordination services (recommended)
- `full`: All orchestration features with advanced analytics
- `debug`: Full mode with detailed logging

## Post-Installation Verification

### Check Server Status
```bash
./status_server.sh
```

### Verify MCP Server Status
```bash
# Check if MCP server process is running
ps aux | grep ltmc_mcp_server

# Server should show as running on stdio transport
# No HTTP endpoints - all communication via stdio MCP protocol
```

### Test MCP Tools via Claude Code
```python
# Test via Claude Code MCP integration (recommended)
mcp__ltmc__store_memory(
  file_name="test.md",
  content="Test installation successful"
)

# Verify storage worked
mcp__ltmc__retrieve_memory(
  query="test installation"
)
```

### Direct stdio JSON-RPC Test (Advanced)
```bash
# Test direct stdio communication
echo '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"store_memory","arguments":{"file_name":"test.md","content":"Test"}},"id":1}' | ./run_modular_stdio.sh
        "content": "Installation test"
      }
    },
    "id": 1
  }'
```

### Test Orchestration Features
```bash
# Run orchestration demonstration
python simple_orchestration_demo.py

# Run integration tests
python tests/orchestration/run_integration_tests.py
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