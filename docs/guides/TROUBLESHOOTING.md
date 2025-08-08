# LTMC Troubleshooting Guide

## Server Startup Issues

### Server Won't Start
1. **Check Ports**
   ```bash
   lsof -i :5050  # HTTP port
   lsof -i :6381  # Redis port
   lsof -i :7687  # Neo4j port
   ```

2. **Review Logs**
   ```bash
   tail -f logs/ltmc_http.log
   tail -f logs/ltmc_mcp.log
   tail -f logs/ltmc_server.log
   ```

### Dependency Problems
- Ensure all dependencies are installed
  ```bash
  poetry install --with dev
  poetry run pip check
  ```

## Database Issues

### Database Initialization Errors
```bash
# Recreate database
rm ltmc.db
poetry run python -c "from ltms.database.schema import create_tables; create_tables()"
```

### Vector ID Constraint Errors
```bash
# Check VectorIdSequence table
sqlite3 ltmc.db ".schema VectorIdSequence"
```

## Performance and Resource Management

### Memory Constraints
- Increase system swap or RAM
- Monitor memory usage:
  ```bash
  free -h
  top
  ```

### High CPU Usage
- Check running processes
  ```bash
  htop
  ```
- Adjust concurrency settings in configuration

## Networking and Transport

### HTTP Transport Issues
```bash
# Test HTTP connectivity
curl http://localhost:5050/health

# Verify tool availability
curl http://localhost:5050/tools
```

### Stdio Transport Debugging
```bash
# Use MCP dev tool
poetry run mcp dev ltmc_mcp_server.py
```

## Security and Permissions

### Permission Errors
```bash
# Check file permissions
ls -l ltmc.db
ls -l logs/

# Fix permissions if needed
chmod 600 ltmc.db
chmod 755 logs/
```

## Service Dependencies

### Redis Connection Problems
```bash
# Check Redis server status
sudo systemctl status redis-server

# Test Redis connection
redis-cli ping
```

### Neo4j Connection Issues
```bash
# Check Neo4j server status
sudo systemctl status neo4j

# Test Neo4j connection
cypher-shell
```

## Common Error Messages

### `Connection Refused`
- Ensure services are running
- Check firewall settings
- Verify port configurations

### `Permission Denied`
- Run with `sudo` or adjust file permissions
- Check user and group ownership

### `Resource Constraints`
- Increase system resources
- Optimize memory usage
- Consider horizontal scaling

## Logging and Monitoring

### Log Rotation
- Logs are stored in `logs/` directory
- Implement log rotation to manage disk space

### Performance Metrics
```bash
# Monitor server performance
poetry run python tools/performance_monitor.py
```

## Emergency Recovery

### Complete Reset
```bash
# Stop all services
./stop_server.sh

# Remove all generated data
rm -rf ltmc.db faiss_index logs/* redis_data/*

# Reinitialize
poetry run python -c "from ltms.database.schema import create_tables; create_tables()"
./start_server.sh
```

## Getting Help

1. Check [GitHub Issues](https://github.com/your-org/ltmc/issues)
2. Consult [Documentation](/docs/README.md)
3. Create a new GitHub issue with:
   - Detailed error message
   - Log files
   - System configuration

## Contributing Fixes

1. Reproduce the issue
2. Create a minimal test case
3. Submit a pull request with the fix

## Disclaimer

This troubleshooting guide covers most common issues. Always maintain recent backups and exercise caution when performing system-level operations.