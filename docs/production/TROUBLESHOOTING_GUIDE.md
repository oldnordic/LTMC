# LTMC MCP Server Troubleshooting Guide

## Common Issues and Solutions

### Pod Startup Issues

#### Issue: Pod stuck in `Pending` state
**Diagnosis**: Resource constraints or scheduling issues
```bash
kubectl describe pod <pod-name> -n ltmc-production
```

**Solutions**:
- Check resource requests vs cluster capacity
- Verify persistent volume availability
- Check node selectors and taints

#### Issue: Pod crashes during startup
**Diagnosis**: Configuration or dependency issues
```bash
kubectl logs <pod-name> -n ltmc-production --previous
```

**Solutions**:
- Check environment variables and secrets
- Verify dependency services are running
- Review health check configuration

### Performance Issues

#### Issue: High response times
**Indicators**: P95 > 500ms, users reporting slowness

**Investigation Steps**:
1. Check current resource utilization:
   ```bash
   kubectl top pods -n ltmc-production
   ```
2. Review application logs for bottlenecks
3. Check database connection pool status
4. Monitor dependency services performance

**Solutions**:
- Scale deployment if CPU/memory constrained
- Optimize database queries
- Increase connection pool sizes
- Review caching strategy

#### Issue: High memory usage
**Indicators**: Memory usage approaching limits

**Investigation**:
```bash
kubectl exec -it <pod-name> -n ltmc-production -- ps aux --sort=-%mem
```

**Solutions**:
- Increase memory limits
- Check for memory leaks in application logs
- Review caching configurations
- Consider pod restarts to clear memory

### Connectivity Issues

#### Issue: Unable to connect to Redis
**Symptoms**: Connection timeout errors in logs

**Diagnosis**:
```bash
kubectl exec -it <pod-name> -n ltmc-production -- redis-cli -h redis ping
```

**Solutions**:
- Check Redis pod status
- Verify network policies
- Check service endpoints
- Review Redis authentication

#### Issue: Neo4j connection failures
**Symptoms**: Bolt protocol errors

**Diagnosis**:
```bash
kubectl exec -it <pod-name> -n ltmc-production -- cypher-shell -a bolt://neo4j:7687
```

**Solutions**:
- Check Neo4j service availability
- Verify authentication credentials
- Review network connectivity
- Check Neo4j logs for issues

### Tool-Specific Issues

#### Issue: MCP tool execution failures
**Symptoms**: Tool timeout or execution errors

**Investigation**:
- Check specific tool logs in application output
- Verify tool dependencies are available
- Review resource limits for tool execution

**Solutions**:
- Increase timeout values
- Check tool-specific configurations
- Verify required libraries are installed
- Review tool resource requirements

## Diagnostic Commands

### Cluster Health
```bash
kubectl get nodes
kubectl top nodes
kubectl get events --sort-by='.lastTimestamp' -n ltmc-production
```

### Application Health
```bash
kubectl get pods -n ltmc-production -o wide
kubectl describe deployment ltmc-mcp-server -n ltmc-production
kubectl logs -f deployment/ltmc-mcp-server -n ltmc-production --tail=100
```

### Resource Usage
```bash
kubectl top pods -n ltmc-production
kubectl describe hpa ltmc-hpa -n ltmc-production
```

## Emergency Procedures

### Emergency Rollback
```bash
kubectl rollout undo deployment/ltmc-mcp-server -n ltmc-production
kubectl rollout status deployment/ltmc-mcp-server -n ltmc-production
```

### Scale Down for Maintenance
```bash
kubectl scale deployment ltmc-mcp-server --replicas=0 -n ltmc-production
```

### Complete Service Restart
```bash
kubectl rollout restart deployment/ltmc-mcp-server -n ltmc-production
kubectl rollout restart deployment/redis -n ltmc-production
kubectl rollout restart deployment/neo4j -n ltmc-production
```
