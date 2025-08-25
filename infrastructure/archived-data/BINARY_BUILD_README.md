# LTMC Binary Build Guide

## 🚀 Building a Standalone LTMC Binary with PyInstaller

This guide explains how to create a standalone binary that includes all 126 MCP tools and reads configuration files without requiring Python installation.

## 📋 Prerequisites

- Python 3.8+ with pip
- PyInstaller 6.0+
- All LTMC dependencies installed
- Linux/macOS/Windows environment

## 🔧 Build Methods

### Method 1: Using the Advanced Build Script (Recommended)

```bash
# Make the script executable
chmod +x build_ltmc_binary_advanced.sh

# Run the build script
./build_ltmc_binary_advanced.sh
```

**Features:**
- ✅ Automatically includes all 126 MCP tools
- ✅ Bundles configuration files
- ✅ Creates user config directory
- ✅ Installs binary to system PATH
- ✅ Comprehensive testing and verification

### Method 2: Using PyInstaller Spec File

```bash
# Build using the spec file
pyinstaller ltmc_binary.spec

# Install the binary
cp dist/ltmc ~/.local/bin/
chmod +x ~/.local/bin/ltmc
```

### Method 3: Direct PyInstaller Command

```bash
pyinstaller \
    --onefile \
    --name="ltmc" \
    --console \
    --add-data="ltmc_config.json:." \
    --add-data="ltmc_mcp_server:ltmc_mcp_server" \
    --add-data="ltms:ltms" \
    --hidden-import="mcp.server.fastmcp" \
    --collect-all="ltmc_mcp_server" \
    --collect-all="ltms" \
    ltmc_binary_main.py
```

## 📁 Binary Features

### 🛠️ All 126 MCP Tools Included
- **Memory Tools**: 3 tools (store_memory, retrieve_memory, retrieve_by_type)
- **Redis Tools**: 7 tools (cache operations, health checks)
- **Chat Tools**: 5 tools (log_chat, ask_with_context, etc.)
- **Todo Tools**: 4 tools (add_todo, list_todos, etc.)
- **Context Tools**: 10 tools (build_context, link_resources, etc.)
- **Code Patterns**: 3 tools (log_code_attempt, get_code_patterns, etc.)
- **System Tools**: 8 tools (security, connection metrics, etc.)
- **Mermaid Tools**: 24 tools (diagram generation, analysis)
- **Blueprint Tools**: 6 tools (create, update, validate blueprints)
- **Documentation Tools**: 8 tools (sync, validation, monitoring)
- **Taskmaster Tools**: 4 tools (task management, analysis)
- **Advanced Tools**: 3 tools (context search, statistics)
- **Unified Tools**: 1 tool (performance reporting)
- **Utility Tools**: 46 tools (documentation, validation, etc.)

### ⚙️ Configuration Management
The binary automatically reads configuration from multiple sources in priority order:

1. **Environment Variable**: `LTMC_CONFIG_PATH=/path/to/config.json`
2. **User Config**: `~/.config/ltmc/ltmc_config.json`
3. **Current Directory**: `./ltmc_config.json`
4. **Bundled Config**: Default configuration included in binary

### 🔧 Command Line Options
```bash
ltmc                    # Run with default config
ltmc --config /path    # Use custom config file
ltmc --help           # Show help information
ltmc --version        # Show version information
```

## 📊 Configuration File Format

```json
{
  "base_data_dir": "/home/user/Projects/Data",
  "database_path": "/home/user/Projects/Data/ltmc.db",
  "log_level": "INFO",
  "redis_enabled": true,
  "redis_host": "localhost",
  "redis_port": 6379,
  "redis_password": "your_password",
  "neo4j_enabled": true,
  "neo4j_uri": "bolt://localhost:7687",
  "neo4j_user": "neo4j",
  "neo4j_password": "your_password",
  "postgres_enabled": false
}
```

## 🚀 Usage Examples

### Basic Usage
```bash
# Run with default configuration
ltmc

# Run with custom configuration
ltmc --config /path/to/ltmc_config.json

# Set configuration via environment variable
export LTMC_CONFIG_PATH=/path/to/config.json
ltmc
```

### MCP Client Integration
```json
// .cursor/mcp.json
{
  "mcpServers": {
    "ltmc": {
      "command": "ltmc",
      "args": [],
      "env": {
        "LTMC_CONFIG_PATH": "/path/to/ltmc_config.json"
      }
    }
  }
}
```

### Systemd Service (Linux)
```ini
# /etc/systemd/system/ltmc.service
[Unit]
Description=LTMC MCP Server
After=network.target

[Service]
Type=simple
User=your_user
ExecStart=/usr/local/bin/ltmc
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Binary Not Found
```bash
# Check if binary is in PATH
which ltmc

# Check installation location
ls -la ~/.local/bin/ltmc
ls -la /usr/local/bin/ltmc
```

#### 2. Configuration File Issues
```bash
# Check config file locations
ls -la ~/.config/ltmc/
ls -la ./ltmc_config.json

# Test configuration loading
ltmc --help
ltmc --version
```

#### 3. Permission Issues
```bash
# Fix binary permissions
chmod +x ~/.local/bin/ltmc

# Fix config directory permissions
chmod 755 ~/.config/ltmc/
chmod 644 ~/.config/ltmc/ltmc_config.json
```

#### 4. Missing Dependencies
```bash
# Check if all dependencies are installed
pip install -r requirements.txt

# Verify PyInstaller installation
pip show pyinstaller
```

### Debug Mode
```bash
# Run with verbose logging
export LTMC_LOG_LEVEL=DEBUG
ltmc

# Check binary information
file ~/.local/bin/ltmc
ldd ~/.local/bin/ltmc  # Linux
otool -L ~/.local/bin/ltmc  # macOS
```

## 📈 Performance Optimization

### Binary Size Optimization
- Use `--onefile` for single executable
- Use `--upx` for compression (requires UPX)
- Exclude unnecessary modules with `--exclude`

### Runtime Optimization
- Set appropriate log levels
- Use connection pooling for databases
- Enable Redis caching when possible

## 🔒 Security Considerations

### File Permissions
```bash
# Secure configuration files
chmod 600 ~/.config/ltmc/ltmc_config.json

# Secure binary
chmod 755 ~/.local/bin/ltmc
```

### Environment Variables
```bash
# Use environment variables for sensitive data
export LTMC_REDIS_PASSWORD="your_password"
export LTMC_NEO4J_PASSWORD="your_password"
```

## 📚 Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/fastmcp/fastmcp)
- [LTMC Project Repository](https://github.com/your-org/ltmc)

## 🤝 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your configuration file format
3. Check system permissions and PATH
4. Review the build logs for errors
5. Open an issue on the project repository

## 🎉 Success Indicators

Your binary is working correctly when:

- ✅ `ltmc --help` shows comprehensive help
- ✅ `ltmc --version` shows version information
- ✅ `ltmc` starts without errors
- ✅ All 126 tools are available
- ✅ Configuration files are loaded correctly
- ✅ MCP clients can connect successfully
