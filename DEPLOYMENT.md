# LTMC Deployment Guide

## Overview

This guide provides comprehensive deployment instructions for LTMC (Long-Term Memory and Context) from development to production environments. LTMC's **11 consolidated tools** architecture enables flexible deployment options with robust multi-database integration.

## Deployment Architecture

### **System Components**
- **LTMC Core**: 11 consolidated MCP tools with stdio protocol
- **Database Layer**: SQLite + Neo4j + Redis + FAISS
- **Orchestration Layer**: Agent coordination and workflow management
- **Monitoring Layer**: Performance metrics and health checks

### **Deployment Patterns**
1. **Single-Node Deployment** - All services on one server
2. **Multi-Node Deployment** - Services distributed across nodes
3. **Container Deployment** - Docker and Kubernetes orchestration
4. **Cloud Deployment** - AWS, GCP, Azure configurations

## Prerequisites

### **System Requirements**
```bash
# Minimum Requirements
OS: Linux (Ubuntu 20.04+), macOS (10.15+), Windows 10+ with WSL2
Python: 3.9+ (Recommended: 3.11+)
Memory: 4GB RAM minimum, 8GB recommended
Storage: 2GB minimum, 10GB+ recommended for production
CPU: 2+ cores recommended

# Production Requirements  
OS: Linux (Ubuntu 22.04+ or CentOS 8+)
Python: 3.11+
Memory: 16GB RAM minimum
Storage: 50GB+ SSD storage
CPU: 4+ cores
Network: Stable internet connection, dedicated network recommended
```

### **Software Dependencies**
```bash
# Core Dependencies
python3.11
python3.11-venv
python3.11-dev
build-essential
git

# Database Dependencies
redis-server
neo4j
sqlite3

# Container Dependencies (Optional)
docker
docker-compose
kubectl (for Kubernetes)
```

## Development Deployment

### **Local Development Setup**
```bash
# 1. Clone and setup LTMC
git clone https://github.com/your-org/ltmc.git
cd ltmc

# UV method (recommended - 3-50x faster)
uv venv venv --python 3.11.9
source venv/bin/activate
uv pip install -r requirements.txt
uv pip install -e .

# Traditional method (fallback)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# 2. Install and configure databases
sudo apt update && sudo apt install redis-server

# Install Neo4j
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 4.4' | sudo tee -a /etc/apt/sources.list.d/neo4j.list
sudo apt update && sudo apt install neo4j

# Start services
sudo systemctl start redis-server neo4j
sudo systemctl enable redis-server neo4j

# 3. Configure LTMC
cat > ltmc_config.json << 'EOF'
{
  "database": {
    "neo4j": {
      "uri": "bolt://localhost:7687",
      "user": "neo4j", 
      "password": "dev_password",
      "database": "ltmc_dev"
    },
    "redis": {
      "host": "localhost",
      "port": 6379,
      "db": 1
    },
    "sqlite": {
      "path": "data/ltmc_dev.db"
    }
  },
  "vector_store": {
    "faiss": {
      "index_path": "data/faiss_dev_index",
      "dimension": 384
    }
  },
  "logging": {
    "level": "DEBUG",
    "file": "logs/ltmc_dev.log"
  }
}
EOF

# 4. Initialize and test
mkdir -p data logs
python -m ltms --init
python -m ltms tools/list
```

### **Development with Docker**
```bash
# Create development Docker Compose
cat > docker-compose.dev.yml << 'EOF'
version: '3.8'
services:
  ltmc-dev:
    build: 
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./ltms:/app/ltms
      - ./data:/app/data
      - ./logs:/app/logs
      - ./ltmc_config.json:/app/ltmc_config.json
    depends_on:
      - redis-dev
      - neo4j-dev
    environment:
      - LTMC_ENV=development
      - LTMC_DEBUG=true
    ports:
      - "8000:8000"

  redis-dev:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-dev-data:/data

  neo4j-dev:
    image: neo4j:5.11
    environment:
      - NEO4J_AUTH=neo4j/dev_password
    ports:
      - "7474:7474"
      - "7687:7687" 
    volumes:
      - neo4j-dev-data:/data

volumes:
  redis-dev-data:
  neo4j-dev-data:
EOF

# Development Dockerfile
cat > Dockerfile.dev << 'EOF'
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt
# For UV optimization (add UV installation step before this):
# RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# RUN /root/.local/bin/uv pip install -r requirements.txt

COPY . .
RUN pip install -e .
# UV alternative:
# RUN /root/.local/bin/uv pip install -e .

CMD ["python", "-m", "ltms"]
EOF

# Start development environment
docker-compose -f docker-compose.dev.yml up -d
```

## Production Deployment

### **Single-Node Production Deployment**

#### **Server Preparation**
```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
sudo apt install -y python3.11 python3.11-venv python3.11-dev \
    build-essential git nginx supervisor fail2ban ufw

# 3. Configure firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# 4. Create LTMC user
sudo useradd -m -s /bin/bash ltmc
sudo usermod -aG sudo ltmc

# 5. Install databases
# Redis
sudo apt install -y redis-server
sudo systemctl enable redis-server

# Neo4j
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 4.4' | sudo tee -a /etc/apt/sources.list.d/neo4j.list
sudo apt update && sudo apt install -y neo4j
sudo systemctl enable neo4j
```

#### **LTMC Application Deployment**
```bash
# Switch to LTMC user
sudo su - ltmc

# 1. Deploy application
git clone https://github.com/your-org/ltmc.git /opt/ltmc
cd /opt/ltmc
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# 2. Configure production settings
cat > /opt/ltmc/ltmc_config.json << 'EOF'
{
  "database": {
    "neo4j": {
      "uri": "bolt://localhost:7687",
      "user": "neo4j",
      "password": "SECURE_PRODUCTION_PASSWORD",
      "database": "ltmc_production",
      "connection_pool": {
        "max_pool_size": 100,
        "connection_timeout": 30
      }
    },
    "redis": {
      "host": "localhost",
      "port": 6379,
      "db": 0,
      "password": "REDIS_SECURE_PASSWORD",
      "connection_pool": {
        "max_connections": 50
      }
    },
    "sqlite": {
      "path": "/opt/ltmc/data/ltmc_production.db",
      "journal_mode": "WAL",
      "synchronous": "NORMAL",
      "cache_size": 20000
    }
  },
  "vector_store": {
    "faiss": {
      "index_path": "/opt/ltmc/data/faiss_production_index",
      "dimension": 384,
      "backup": {
        "enabled": true,
        "interval": 3600
      }
    }
  },
  "logging": {
    "level": "INFO",
    "file": "/opt/ltmc/logs/ltmc_production.log",
    "rotation": {
      "max_size": "100MB",
      "backup_count": 10
    }
  },
  "performance": {
    "max_concurrent_operations": 20,
    "memory_limit": "4GB",
    "cache_ttl": 7200
  },
  "security": {
    "authentication": {
      "enabled": true,
      "token_file": "/opt/ltmc/security/.ltmc_token"
    },
    "encryption": {
      "at_rest": true,
      "key_file": "/opt/ltmc/security/encryption.key"
    }
  }
}
EOF

# 3. Create directories and set permissions
sudo mkdir -p /opt/ltmc/{data,logs,security,backups}
sudo chown -R ltmc:ltmc /opt/ltmc
chmod 700 /opt/ltmc/security

# 4. Initialize production database
cd /opt/ltmc
source venv/bin/activate
python -m ltms --init --config /opt/ltmc/ltmc_config.json
```

#### **Service Configuration**
```bash
# 1. Create systemd service
sudo cat > /etc/systemd/system/ltmc.service << 'EOF'
[Unit]
Description=LTMC Long-Term Memory and Context Service
After=network.target redis.service neo4j.service
Requires=redis.service neo4j.service

[Service]
Type=simple
User=ltmc
Group=ltmc
WorkingDirectory=/opt/ltmc
Environment=PATH=/opt/ltmc/venv/bin
Environment=LTMC_CONFIG=/opt/ltmc/ltmc_config.json
Environment=LTMC_ENV=production
ExecStart=/opt/ltmc/venv/bin/python -m ltms
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/ltmc/data /opt/ltmc/logs

[Install]
WantedBy=multi-user.target
EOF

# 2. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ltmc
sudo systemctl start ltmc

# 3. Check service status
sudo systemctl status ltmc
journalctl -u ltmc -f
```

### **Multi-Node Production Deployment**

#### **Architecture Overview**
```
┌─────────────────────────────────────────────┐
│                Load Balancer                │
│              (nginx/HAProxy)                │
└─────────────────┬───────────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
┌───▼───┐    ┌────▼───┐    ┌────▼───┐
│LTMC-1 │    │LTMC-2  │    │LTMC-3  │
│Node   │    │Node    │    │Node    │
└───┬───┘    └────┬───┘    └────┬───┘
    │             │             │
    └─────────────┼─────────────┘
                  │
    ┌─────────────▼─────────────┐
    │      Shared Database      │
    │  Redis Cluster + Neo4j    │
    │      + Shared Storage     │
    └───────────────────────────┘
```

#### **Node Configuration**
```bash
# Node-specific configuration
cat > ltmc_config_node.json << 'EOF'
{
  "node": {
    "id": "${NODE_ID}",
    "role": "worker",
    "cluster_mode": true
  },
  "database": {
    "neo4j": {
      "uri": "bolt://db-cluster-lb:7687",
      "user": "ltmc_cluster",
      "password": "${NEO4J_CLUSTER_PASSWORD}"
    },
    "redis": {
      "cluster_mode": true,
      "nodes": [
        {"host": "redis-1", "port": 7000},
        {"host": "redis-2", "port": 7000}, 
        {"host": "redis-3", "port": 7000}
      ]
    },
    "sqlite": {
      "path": "/shared/data/ltmc_${NODE_ID}.db"
    }
  },
  "coordination": {
    "distributed": true,
    "leader_election": true,
    "heartbeat_interval": 30
  }
}
EOF
```

### **Container Deployment (Docker)**

#### **Production Docker Configuration**
```bash
# Production Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

# Add labels
LABEL maintainer="LTMC Team"
LABEL version="1.0"
LABEL description="LTMC Long-Term Memory and Context Service"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LTMC_ENV=production

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# UV alternative (faster builds):
# RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# RUN /root/.local/bin/uv pip install --no-cache -r requirements.txt

# Copy application code
COPY ltms/ ltms/
COPY ltmc_config.json .

# Install LTMC
RUN pip install -e .
# UV alternative:
# RUN /root/.local/bin/uv pip install -e .

# Create non-root user
RUN adduser --disabled-password --gecos '' ltmc
RUN mkdir -p /app/data /app/logs /app/security
RUN chown -R ltmc:ltmc /app

USER ltmc

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "from ltms.tools.consolidated import memory_action; memory_action(action='status')" || exit 1

# Expose port (if needed for HTTP interface)
EXPOSE 8000

CMD ["python", "-m", "ltms"]
EOF

# Production Docker Compose
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  ltmc:
    build: 
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    depends_on:
      - redis
      - neo4j
    environment:
      - LTMC_ENV=production
      - LTMC_CONFIG=/app/ltmc_config.json
    volumes:
      - ltmc-data:/app/data
      - ltmc-logs:/app/logs
      - ltmc-security:/app/security
      - ./ltmc_config.json:/app/ltmc_config.json:ro
    networks:
      - ltmc-network
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '0.5'
          memory: 1G

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - ltmc-network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  neo4j:
    image: neo4j:5.11
    restart: unless-stopped
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
      - NEO4J_PLUGINS=["apoc"]
      - NEO4J_apoc_export_file_enabled=true
      - NEO4J_apoc_import_file_enabled=true
      - NEO4J_apoc_import_file_use__neo4j__config=true
    volumes:
      - neo4j-data:/data
      - neo4j-logs:/logs
    networks:
      - ltmc-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - ltmc
    networks:
      - ltmc-network

volumes:
  ltmc-data:
  ltmc-logs:
  ltmc-security:
  redis-data:
  neo4j-data:
  neo4j-logs:

networks:
  ltmc-network:
    driver: bridge
EOF

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

### **Kubernetes Deployment**

#### **Kubernetes Manifests**
```yaml
# ltmc-namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: ltmc-production
  labels:
    name: ltmc-production

---
# ltmc-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ltmc-config
  namespace: ltmc-production
data:
  ltmc_config.json: |
    {
      "database": {
        "neo4j": {
          "uri": "bolt://neo4j-service:7687",
          "user": "neo4j",
          "password": "${NEO4J_PASSWORD}"
        },
        "redis": {
          "host": "redis-service",
          "port": 6379,
          "password": "${REDIS_PASSWORD}"
        },
        "sqlite": {
          "path": "/app/data/ltmc_k8s.db"
        }
      },
      "logging": {
        "level": "INFO",
        "console": true
      },
      "performance": {
        "max_concurrent_operations": 20
      }
    }

---
# ltmc-secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: ltmc-secrets
  namespace: ltmc-production
type: Opaque
data:
  neo4j-password: <base64-encoded-password>
  redis-password: <base64-encoded-password>

---
# ltmc-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ltmc-deployment
  namespace: ltmc-production
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
        - containerPort: 8000
        env:
        - name: LTMC_ENV
          value: "production"
        - name: LTMC_CONFIG
          value: "/app/config/ltmc_config.json"
        - name: NEO4J_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ltmc-secrets
              key: neo4j-password
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ltmc-secrets
              key: redis-password
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: data
          mountPath: /app/data
        - name: logs
          mountPath: /app/logs
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          exec:
            command:
            - python
            - -c
            - "from ltms.tools.consolidated import memory_action; memory_action(action='status')"
          initialDelaySeconds: 60
          periodSeconds: 30
        readinessProbe:
          exec:
            command:
            - python
            - -c
            - "from ltms.tools.consolidated import memory_action; memory_action(action='status')"
          initialDelaySeconds: 30
          periodSeconds: 10
      volumes:
      - name: config
        configMap:
          name: ltmc-config
      - name: data
        persistentVolumeClaim:
          claimName: ltmc-data-pvc
      - name: logs
        persistentVolumeClaim:
          claimName: ltmc-logs-pvc

---
# ltmc-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: ltmc-service
  namespace: ltmc-production
spec:
  selector:
    app: ltmc
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP

---
# ltmc-hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ltmc-hpa
  namespace: ltmc-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ltmc-deployment
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

#### **Deploy to Kubernetes**
```bash
# Create namespace and deploy
kubectl apply -f ltmc-namespace.yaml
kubectl apply -f ltmc-configmap.yaml
kubectl apply -f ltmc-secrets.yaml
kubectl apply -f ltmc-deployment.yaml
kubectl apply -f ltmc-service.yaml
kubectl apply -f ltmc-hpa.yaml

# Check deployment status
kubectl get pods -n ltmc-production
kubectl logs -f deployment/ltmc-deployment -n ltmc-production
```

## Cloud Deployment

### **AWS Deployment**

#### **ECS Fargate Deployment**
```yaml
# ecs-task-definition.json
{
  "family": "ltmc-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/ltmc-task-role",
  "containerDefinitions": [
    {
      "name": "ltmc",
      "image": "your-account.dkr.ecr.region.amazonaws.com/ltmc:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "LTMC_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "NEO4J_PASSWORD",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:ltmc/neo4j-password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ltmc",
          "awslogs-region": "us-west-2",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "python -c \"from ltms.tools.consolidated import memory_action; memory_action(action='status')\" || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

#### **Terraform Configuration**
```hcl
# main.tf
provider "aws" {
  region = var.aws_region
}

# VPC and networking
resource "aws_vpc" "ltmc_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "ltmc-vpc"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "ltmc_cluster" {
  name = "ltmc-cluster"
  
  capacity_providers = ["FARGATE"]
  
  default_capacity_provider_strategy {
    capacity_provider = "FARGATE"
  }
}

# ECS Service
resource "aws_ecs_service" "ltmc_service" {
  name            = "ltmc-service"
  cluster         = aws_ecs_cluster.ltmc_cluster.id
  task_definition = aws_ecs_task_definition.ltmc_task.arn
  desired_count   = 3
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets          = aws_subnet.ltmc_private_subnets[*].id
    security_groups  = [aws_security_group.ltmc_sg.id]
    assign_public_ip = false
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.ltmc_tg.arn
    container_name   = "ltmc"
    container_port   = 8000
  }
  
  depends_on = [aws_lb_listener.ltmc_listener]
}

# Application Load Balancer
resource "aws_lb" "ltmc_alb" {
  name               = "ltmc-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.ltmc_alb_sg.id]
  subnets            = aws_subnet.ltmc_public_subnets[*].id
  
  enable_deletion_protection = true
}

# RDS for PostgreSQL (alternative to local databases)
resource "aws_rds_cluster" "ltmc_postgres" {
  cluster_identifier      = "ltmc-postgres"
  engine                  = "aurora-postgresql"
  engine_version          = "13.7"
  availability_zones      = data.aws_availability_zones.available.names
  database_name           = "ltmc"
  master_username         = "ltmc_admin"
  manage_master_user_password = true
  backup_retention_period = 7
  preferred_backup_window = "07:00-09:00"
  
  vpc_security_group_ids = [aws_security_group.ltmc_rds_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.ltmc_db_subnet_group.name
  
  storage_encrypted = true
  
  tags = {
    Name = "ltmc-postgres"
  }
}

# ElastiCache for Redis
resource "aws_elasticache_replication_group" "ltmc_redis" {
  replication_group_id       = "ltmc-redis"
  description                = "Redis cluster for LTMC"
  
  node_type                  = "cache.t3.micro"
  port                       = 6379
  parameter_group_name       = "default.redis7"
  
  num_cache_clusters         = 2
  automatic_failover_enabled = true
  multi_az_enabled          = true
  
  subnet_group_name = aws_elasticache_subnet_group.ltmc_cache_subnet.name
  security_group_ids = [aws_security_group.ltmc_redis_sg.id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  tags = {
    Name = "ltmc-redis"
  }
}
```

### **Google Cloud Platform (GCP) Deployment**

#### **GKE Deployment**
```yaml
# gke-deployment.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ltmc-config
data:
  ltmc_config.json: |
    {
      "database": {
        "neo4j": {
          "uri": "bolt://neo4j-service:7687"
        },
        "redis": {
          "host": "redis-service"
        }
      },
      "cloud": {
        "provider": "gcp",
        "project_id": "${PROJECT_ID}",
        "region": "${REGION}"
      }
    }

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ltmc-deployment
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
      serviceAccountName: ltmc-service-account
      containers:
      - name: ltmc
        image: gcr.io/PROJECT_ID/ltmc:latest
        ports:
        - containerPort: 8000
        env:
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: /var/secrets/google/key.json
        volumeMounts:
        - name: google-cloud-key
          mountPath: /var/secrets/google
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "4Gi"
            cpu: "2"
      volumes:
      - name: google-cloud-key
        secret:
          secretName: google-cloud-key
```

## Monitoring and Observability

### **Prometheus Monitoring**
```yaml
# prometheus-config.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "ltmc_rules.yml"

scrape_configs:
  - job_name: 'ltmc'
    static_configs:
      - targets: ['ltmc:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s
    
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### **Grafana Dashboard**
```json
{
  "dashboard": {
    "title": "LTMC Production Dashboard",
    "panels": [
      {
        "title": "Tool Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "ltmc_tool_duration_seconds{tool=\"memory_action\"}",
            "legend": "Memory Action Response Time"
          }
        ]
      },
      {
        "title": "Database Performance", 
        "type": "graph",
        "targets": [
          {
            "expr": "ltmc_database_operation_duration_seconds",
            "legend": "Database Operations"
          }
        ]
      },
      {
        "title": "Agent Coordination",
        "type": "graph", 
        "targets": [
          {
            "expr": "ltmc_coordination_operations_total",
            "legend": "Coordination Operations"
          }
        ]
      }
    ]
  }
}
```

## Backup and Recovery

### **Database Backup Strategy**
```bash
#!/bin/bash
# backup-ltmc.sh

BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/ltmc/backups/$BACKUP_DATE"
mkdir -p $BACKUP_DIR

# SQLite backup
cp /opt/ltmc/data/ltmc_production.db $BACKUP_DIR/

# Neo4j backup
neo4j-admin dump --database=ltmc_production --to=$BACKUP_DIR/neo4j_dump.dump

# Redis backup
redis-cli --rdb $BACKUP_DIR/redis_dump.rdb

# FAISS backup
cp -r /opt/ltmc/data/faiss_production_index $BACKUP_DIR/

# Compress backup
tar -czf $BACKUP_DIR.tar.gz -C /opt/ltmc/backups $BACKUP_DATE
rm -rf $BACKUP_DIR

# Upload to cloud storage (optional)
aws s3 cp $BACKUP_DIR.tar.gz s3://ltmc-backups/

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

### **Automated Backup Scheduling**
```bash
# Add to crontab
# Daily backups at 2 AM
0 2 * * * /opt/ltmc/scripts/backup-ltmc.sh

# Weekly full backup at Sunday 1 AM  
0 1 * * 0 /opt/ltmc/scripts/full-backup-ltmc.sh
```

## Security Hardening

### **Production Security Checklist**
- [ ] Change default database passwords
- [ ] Enable SSL/TLS for all database connections
- [ ] Configure firewall rules (only necessary ports)
- [ ] Enable authentication and authorization
- [ ] Set up SSL certificates for HTTPS
- [ ] Configure fail2ban for intrusion prevention
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] Network segmentation

### **SSL/TLS Configuration**
```bash
# Generate SSL certificate (Let's Encrypt)
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# Or use custom certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/ltmc.key \
    -out /etc/ssl/certs/ltmc.crt
```

### **nginx SSL Configuration**
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/ssl/certs/ltmc.crt;
    ssl_certificate_key /etc/ssl/private/ltmc.key;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### **Common Deployment Issues**

#### **Database Connection Issues**
```bash
# Test database connections
python -c "
import redis
r = redis.Redis(host='localhost', port=6379)
print(f'Redis: {r.ping()}')

from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))
with driver.session() as session:
    result = session.run('RETURN 1')
    print(f'Neo4j: {result.single()[0] == 1}')
driver.close()
"
```

#### **Performance Issues**
```bash
# Monitor system resources
htop
iostat -x 1
netstat -tulpn

# Check LTMC logs
tail -f /opt/ltmc/logs/ltmc_production.log

# Monitor database performance
redis-cli monitor
neo4j-admin report
```

#### **Container Issues**
```bash
# Docker troubleshooting
docker logs ltmc-container
docker exec -it ltmc-container bash
docker stats ltmc-container

# Kubernetes troubleshooting
kubectl logs -f deployment/ltmc-deployment
kubectl describe pod ltmc-pod-name
kubectl get events --sort-by=.metadata.creationTimestamp
```

## Performance Tuning

### **Production Optimization**
```bash
# System-level optimizations
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'net.core.somaxconn=65535' >> /etc/sysctl.conf
echo 'fs.file-max=2097152' >> /etc/sysctl.conf

# Database optimizations
# Redis
echo 'maxmemory 2gb' >> /etc/redis/redis.conf
echo 'maxmemory-policy allkeys-lru' >> /etc/redis/redis.conf

# Neo4j (neo4j.conf)
echo 'server.memory.heap.initial_size=2g' >> /etc/neo4j/neo4j.conf
echo 'server.memory.heap.max_size=4g' >> /etc/neo4j/neo4j.conf
echo 'server.memory.pagecache.size=2g' >> /etc/neo4j/neo4j.conf
```

### **LTMC-Specific Optimizations**
```json
{
  "performance": {
    "max_concurrent_operations": 20,
    "memory_limit": "4GB",
    "cache_ttl": 7200,
    "batch_size": 200,
    "connection_pool_sizes": {
      "sqlite": 30,
      "neo4j": 100,
      "redis": 50
    }
  }
}
```

## Maintenance Procedures

### **Regular Maintenance Tasks**
```bash
#!/bin/bash
# ltmc-maintenance.sh

# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Check disk space
df -h | grep -E "(80|90|95)%" && echo "Warning: High disk usage"

# 3. Clean old logs
find /opt/ltmc/logs -name "*.log.*" -mtime +30 -delete

# 4. Optimize databases
sqlite3 /opt/ltmc/data/ltmc_production.db "VACUUM;"
neo4j-admin database optimize ltmc_production

# 5. Update LTMC
cd /opt/ltmc
git pull
source venv/bin/activate  
pip install -r requirements.txt

# 6. Restart services
sudo systemctl restart ltmc

# 7. Health check
sleep 30
python -m ltms tools/list || echo "ERROR: LTMC health check failed"
```

### **Monitoring Alerts**
```yaml
# alerting-rules.yml
groups:
  - name: ltmc
    rules:
      - alert: LTMCHighResponseTime
        expr: ltmc_tool_duration_seconds > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "LTMC tool response time is high"
          
      - alert: LTMCDatabaseConnectionFailure
        expr: ltmc_database_connection_failures_total > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "LTMC database connection failure"
```

## Deployment Summary

### **Deployment Options Comparison**

| Deployment Type | Complexity | Scalability | Cost | Recommended For |
|-----------------|------------|-------------|------|----------------|
| **Single Node** | Low | Limited | Low | Development, Small Teams |
| **Multi-Node** | Medium | High | Medium | Medium Teams, High Availability |
| **Container** | Medium | High | Medium | Modern Infrastructure |
| **Kubernetes** | High | Very High | Medium-High | Large Teams, Enterprise |
| **Cloud Managed** | Low | Very High | High | Enterprise, Managed Services |

### **Performance Expectations**

| Environment | Response Time | Throughput | Concurrent Users |
|-------------|---------------|------------|-----------------|
| **Development** | <1s | 10 ops/sec | 1-5 |
| **Production Single** | <500ms | 100 ops/sec | 10-50 |
| **Production Multi** | <200ms | 1000+ ops/sec | 50-500 |
| **Cloud Scaling** | <100ms | 10k+ ops/sec | 500+ |

---

**LTMC is now ready for production deployment with comprehensive monitoring, backup, and scaling capabilities. The 11 consolidated tools architecture provides excellent performance and maintainability across all deployment scenarios.**

*Deployment Guide - LTMC Project Team - August 25, 2025*