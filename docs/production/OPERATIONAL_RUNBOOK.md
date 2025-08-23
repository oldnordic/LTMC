# LTMC MCP Server Operational Runbook

## Daily Operations

### Health Checks
- Monitor Grafana dashboards for key metrics
- Check Prometheus alerts for any firing alerts
- Verify all pods are running: `kubectl get pods -n ltmc-production`

### Performance Monitoring
- Request rate should be consistent with expected load
- P95 response time should remain <150ms
- Error rate should stay below 2%

## Common Operational Tasks

### Scaling Operations

Manual scaling:
```bash
kubectl scale deployment ltmc-mcp-server --replicas=5 -n ltmc-production
```

Check HPA status:
```bash
kubectl get hpa -n ltmc-production
```

### Log Analysis

View application logs:
```bash
kubectl logs -f deployment/ltmc-mcp-server -n ltmc-production
```

Search for errors:
```bash
kubectl logs deployment/ltmc-mcp-server -n ltmc-production | grep ERROR
```

### Configuration Updates

Update ConfigMap:
```bash
kubectl edit configmap ltmc-config -n ltmc-production
```

Restart deployment to pick up changes:
```bash
kubectl rollout restart deployment/ltmc-mcp-server -n ltmc-production
```

## Alert Response Procedures

### High Response Time Alert
1. Check current load and scale if necessary
2. Examine application logs for bottlenecks
3. Check dependency services (Redis, Neo4j, PostgreSQL)

### High Error Rate Alert
1. Immediately check application logs
2. Verify dependency connectivity
3. Consider emergency rollback if needed

### Service Down Alert
1. Check pod status and events
2. Verify cluster resources availability
3. Check node health and capacity

## Backup and Recovery

### Database Backups
- PostgreSQL: Daily automated backups configured
- Neo4j: Weekly graph database exports
- Redis: Persistent data with AOF enabled

### Application Data
- Persistent volumes backed up daily
- Configuration stored in version control

## Maintenance Windows

### Regular Maintenance
- Monthly security updates
- Quarterly dependency updates
- Semi-annual performance reviews

### Emergency Maintenance
- Immediate security patches
- Critical bug fixes
- Infrastructure issues
