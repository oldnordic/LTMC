# LTMC MCP Server Production Deployment Guide

## Overview

This guide covers the complete production deployment of the LTMC MCP Server with all 126 tools (102 LTMC + 24 Mermaid) using Docker containerization and Kubernetes orchestration.

## Prerequisites

- Docker 20.10+
- Kubernetes 1.21+
- kubectl configured for target cluster
- Helm 3.0+ (optional, for monitoring stack)

## Quick Start

### 1. Build and Push Container Image

```bash
# Build production image
docker build -f Dockerfile.production -t ltmc-mcp-server:latest .

# Tag for registry
docker tag ltmc-mcp-server:latest your-registry/ltmc-mcp-server:latest

# Push to registry
docker push your-registry/ltmc-mcp-server:latest
```

### 2. Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace ltmc-production

# Apply all manifests
kubectl apply -f k8s/ -n ltmc-production

# Verify deployment
kubectl get pods -n ltmc-production
```

### 3. Verify Deployment

```bash
# Check service status
kubectl get svc -n ltmc-production

# Port forward for testing
kubectl port-forward svc/ltmc-mcp-service 8080:80 -n ltmc-production

# Test health endpoint
curl http://localhost:8080/health
```

## Performance Validation

Based on Week 4 Phase 2 load testing results:
- **Sustained Throughput**: 104+ operations/second
- **Success Rate**: 97.3% under peak load
- **Response Time**: <150ms P95 under normal conditions

## Scaling Configuration

The deployment includes Horizontal Pod Autoscaler:
- **Min Replicas**: 2
- **Max Replicas**: 10
- **CPU Target**: 70% utilization

## Security Configuration

Production security features:
- Non-root container execution
- Read-only root filesystem
- Security context restrictions
- Kubernetes secrets for credentials

## Monitoring and Observability

Comprehensive monitoring stack includes:
- Prometheus metrics collection
- Grafana dashboards
- Jaeger distributed tracing
- Structured logging

Access Grafana dashboard: `http://grafana.your-domain.com`

## Troubleshooting

For common issues, see [TROUBLESHOOTING_GUIDE.md](TROUBLESHOOTING_GUIDE.md)
