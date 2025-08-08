# LTMC Deployment Guide

## Overview

This guide provides comprehensive deployment instructions for the LTMC Multi-Agent Coordination Platform across different environments, from development setup to production deployment.

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows 10+
- **Python**: 3.11 or higher
- **Memory**: Minimum 2GB RAM, recommended 4GB+
- **Storage**: Minimum 1GB free space for databases and indexes
- **Network**: Internet access for package installation

### Required Services
- **Redis**: Version 6.0+ (for orchestration and caching)
- **Neo4j**: Version 4.4+ (for knowledge graph, optional but recommended)

## Quick Start (Development)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd lmtc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or using Poetry
poetry install
```

### 2. Environment Configuration

Create a `.env` file:

```bash
# Core Configuration
DB_PATH=ltmc.db
FAISS_INDEX_PATH=faiss_index
LOG_LEVEL=INFO

# Transport Configuration  
HTTP_HOST=localhost
HTTP_PORT=5050

# Redis Configuration (for orchestration)
REDIS_HOST=localhost
REDIS_PORT=6381
REDIS_PASSWORD=ltmc_cache_2025
REDIS_ENABLED=true

# Orchestration Configuration
ORCHESTRATION_MODE=basic  # Options: basic, full, debug, disabled
CACHE_ENABLED=true
BUFFER_ENABLED=true
SESSION_STATE_ENABLED=true

# Advanced ML Integration
ML_INTEGRATION_ENABLED=true
ML_LEARNING_COORDINATION=true
ML_KNOWLEDGE_SHARING=true
ML_ADAPTIVE_RESOURCES=true
ML_OPTIMIZATION_INTERVAL=15

# Neo4j Configuration (optional)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=ltmc_graph_2025
NEO4J_ENABLED=false  # Set to true if Neo4j is available
```

### 3. Start Required Services

#### Start Redis (Required for orchestration)
```bash
# Using the included Redis setup script
./setup_redis.sh

# Or manually
redis-server --port 6381 --requirepass ltmc_cache_2025

# Or using Docker
docker run -d --name ltmc-redis \
  -p 6381:6381 \
  redis:7-alpine redis-server --port 6381 --requirepass ltmc_cache_2025
```

#### Start Neo4j (Optional but recommended)
```bash
# Using Docker
docker run -d --name ltmc-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/ltmc_graph_2025 \
  neo4j:5

# Or install locally and configure
# Set NEO4J_ENABLED=true in .env after setup
```

### 4. Initialize Database

```bash
# Create SQLite database and tables
python -c "
from ltms.database.schema import create_tables
import sqlite3
conn = sqlite3.connect('ltmc.db')
create_tables(conn)
conn.close()
print('Database initialized successfully')
"
```

### 5. Start LTMC Server

```bash
# Start dual transport (HTTP + stdio)
./start_server.sh

# Or start individual transports
# HTTP only
python -m uvicorn ltms.mcp_server_http:app --host localhost --port 5050

# MCP (stdio) only  
python ltmc_mcp_server.py
```

### 6. Verify Installation

```bash
# Check server status
./status_server.sh

# Test HTTP endpoint
curl http://localhost:5050/health

# Test orchestration
curl http://localhost:5050/orchestration/health

# Test ML integration
curl http://localhost:5050/ml/status

# Test tool functionality
curl -X POST http://localhost:5050/jsonrpc \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call", 
    "params": {
      "name": "store_memory",
      "arguments": {
        "file_name": "test.md",
        "content": "Test deployment successful!"
      }
    },
    "id": 1
  }'
```

## Production Deployment

### Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data/logs

# Set environment variables
ENV DB_PATH=/data/ltmc.db
ENV FAISS_INDEX_PATH=/data/faiss_index
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 5050

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5050/health || exit 1

# Start command
CMD ["python", "-m", "uvicorn", "ltms.mcp_server_http:app", "--host", "0.0.0.0", "--port", "5050"]
```

#### 2. Docker Compose Configuration

```yaml
version: '3.8'

services:
  ltmc:
    build: .
    ports:
      - "5050:5050"
    environment:
      - DB_PATH=/data/ltmc.db
      - FAISS_INDEX_PATH=/data/faiss_index
      - REDIS_HOST=redis
      - REDIS_PORT=6381
      - REDIS_PASSWORD=ltmc_cache_2025
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=ltmc_graph_2025
      - ORCHESTRATION_MODE=full
      - ML_INTEGRATION_ENABLED=true
    volumes:
      - ./data:/data
      - ./logs:/app/logs
    depends_on:
      - redis
      - neo4j
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5050/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6381:6381"
    command: redis-server --port 6381 --requirepass ltmc_cache_2025
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "-p", "6381", "-a", "ltmc_cache_2025", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/ltmc_graph_2025
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "ltmc_graph_2025", "RETURN 1"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  redis_data:
  neo4j_data:
  neo4j_logs:
```

#### 3. Deploy with Docker Compose

```bash
# Build and start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f ltmc

# Scale LTMC instances (load balancing)
docker-compose up -d --scale ltmc=3
```

### Kubernetes Deployment

#### 1. ConfigMap and Secrets

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ltmc-config
data:
  HTTP_HOST: "0.0.0.0"
  HTTP_PORT: "5050"
  LOG_LEVEL: "INFO"
  ORCHESTRATION_MODE: "full"
  ML_INTEGRATION_ENABLED: "true"

---
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ltmc-secrets
type: Opaque
data:
  redis-password: bHRtY19jYWNoZV8yMDI1  # base64 encoded
  neo4j-password: bHRtY19ncmFwaF8yMDI1   # base64 encoded
```

#### 2. Deployment Configuration

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ltmc-deployment
  labels:
    app: ltmc
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ltmc
  template:
    metadata:
      labels:
        app: ltmc
    spec:
      containers:
      - name: ltmc
        image: ltmc:latest
        ports:
        - containerPort: 5050
        env:
        - name: REDIS_HOST
          value: "redis-service"
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ltmc-secrets
              key: redis-password
        - name: NEO4J_URI
          value: "bolt://neo4j-service:7687"
        - name: NEO4J_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ltmc-secrets
              key: neo4j-password
        envFrom:
        - configMapRef:
            name: ltmc-config
        volumeMounts:
        - name: data-volume
          mountPath: /data
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi" 
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5050
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 5050
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: ltmc-data-pvc

---
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ltmc-service
spec:
  selector:
    app: ltmc
  ports:
  - protocol: TCP
    port: 5050
    targetPort: 5050
  type: LoadBalancer

---
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ltmc-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
```

#### 3. Deploy to Kubernetes

```bash
# Apply configurations
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml

# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/ltmc-deployment

# Port forward for testing
kubectl port-forward service/ltmc-service 5050:5050
```

### Cloud Deployment

#### AWS ECS Deployment

```json
{
  "family": "ltmc-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "ltmc",
      "image": "your-registry/ltmc:latest",
      "portMappings": [
        {
          "containerPort": 5050,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "REDIS_HOST",
          "value": "your-redis-cluster.cache.amazonaws.com"
        },
        {
          "name": "ORCHESTRATION_MODE",
          "value": "full"
        }
      ],
      "secrets": [
        {
          "name": "REDIS_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:ltmc/redis-password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ltmc",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Google Cloud Run Deployment

```yaml
# service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ltmc-service
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cpu: "1000m"
        run.googleapis.com/memory: "2Gi"
        run.googleapis.com/max-scale: "10"
    spec:
      containers:
      - image: gcr.io/your-project/ltmc:latest
        ports:
        - containerPort: 5050
        env:
        - name: REDIS_HOST
          value: "your-redis-instance"
        - name: ORCHESTRATION_MODE
          value: "full"
        resources:
          limits:
            cpu: "1000m"
            memory: "2Gi"
```

```bash
# Deploy to Cloud Run
gcloud run deploy ltmc-service \
  --image gcr.io/your-project/ltmc:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Load Balancing and High Availability

### Nginx Load Balancer Configuration

```nginx
# /etc/nginx/sites-available/ltmc
upstream ltmc_backend {
    least_conn;
    server ltmc1:5050 max_fails=3 fail_timeout=30s;
    server ltmc2:5050 max_fails=3 fail_timeout=30s;
    server ltmc3:5050 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name ltmc.your-domain.com;
    
    location / {
        proxy_pass http://ltmc_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    location /health {
        access_log off;
        proxy_pass http://ltmc_backend/health;
    }
}
```

### HAProxy Configuration

```
# /etc/haproxy/haproxy.cfg
global
    daemon
    maxconn 4096

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms

frontend ltmc_frontend
    bind *:80
    default_backend ltmc_backend

backend ltmc_backend
    balance roundrobin
    option httpchk GET /health
    server ltmc1 ltmc1:5050 check
    server ltmc2 ltmc2:5050 check
    server ltmc3 ltmc3:5050 check
```

## Monitoring and Observability

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ltmc'
    static_configs:
      - targets: ['ltmc1:5050', 'ltmc2:5050', 'ltmc3:5050']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "LTMC Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ltmc_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(ltmc_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

## Security Configuration

### SSL/TLS Setup

```nginx
server {
    listen 443 ssl http2;
    server_name ltmc.your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://ltmc_backend;
        # ... other proxy settings
    }
}
```

### Firewall Configuration

```bash
# UFW (Ubuntu Firewall)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 5050/tcp    # LTMC (if direct access needed)
sudo ufw enable
```

## Backup and Recovery

### Database Backup

```bash
#!/bin/bash
# backup_ltmc.sh

BACKUP_DIR="/backups/ltmc"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup SQLite database
cp ltmc.db $BACKUP_DIR/ltmc_$DATE.db

# Backup FAISS index
tar -czf $BACKUP_DIR/faiss_index_$DATE.tar.gz faiss_index/

# Backup Redis data (if persistent)
redis-cli -p 6381 -a ltmc_cache_2025 --rdb $BACKUP_DIR/redis_$DATE.rdb

# Backup Neo4j data
docker exec ltmc-neo4j neo4j-admin backup --backup-dir=/backups --name=graph_$DATE

# Clean old backups (keep 30 days)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.rdb" -mtime +30 -delete
```

### Automated Backup with Cron

```bash
# crontab -e
# Backup every 6 hours
0 */6 * * * /path/to/backup_ltmc.sh >> /var/log/ltmc_backup.log 2>&1
```

## Troubleshooting Deployment Issues

### Common Issues and Solutions

#### Port Already in Use
```bash
# Check what's using the port
sudo netstat -tulpn | grep 5050
sudo lsof -i :5050

# Kill process if needed
sudo kill -9 <PID>
```

#### Redis Connection Issues
```bash
# Test Redis connection
redis-cli -h localhost -p 6381 -a ltmc_cache_2025 ping

# Check Redis logs
docker logs ltmc-redis

# Restart Redis
docker restart ltmc-redis
```

#### Database Permission Issues
```bash
# Fix SQLite permissions
chmod 664 ltmc.db
chown ltmc:ltmc ltmc.db
```

#### Memory Issues
```bash
# Check memory usage
free -h
docker stats

# Increase Docker memory limits
docker run -m 4g ltmc:latest
```

## Performance Tuning

### SQLite Optimization

```sql
-- SQLite performance settings
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;
```

### Redis Optimization

```
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
tcp-keepalive 60
timeout 300
```

### System-Level Optimization

```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize network settings
echo "net.core.somaxconn = 65535" >> /etc/sysctl.conf
sysctl -p
```

## Next Steps

- [Performance Tuning Guide](PERFORMANCE_TUNING.md) - Advanced optimization techniques
- [Monitoring Guide](MONITORING.md) - Comprehensive monitoring setup
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions
- [API Reference](../api/API_REFERENCE.md) - Complete API documentation