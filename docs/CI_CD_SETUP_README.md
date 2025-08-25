# LTMC CI/CD Setup Instructions

## Overview
This directory contains scripts to set up the complete CI/CD pipeline for LTMC MCP Server using Jenkins on Raspberry Pi (192.168.1.119).

## Components
- **Jenkins Server**: 192.168.1.119:8080
- **Docker Registry**: 192.168.1.119:5000
- **Local Git Server**: feanor@192.168.1.119:/home/feanor/git-repos/ltmc.git

## Setup Steps

### 1. Setup Local Git Repository
```bash
./setup_local_git.sh
```

### 2. Configure Local Git Remote
```bash
# Add local Git remote
git remote add local git@192.168.1.119:ltmc.git

# Push current code to local Git
git push local main
```

### 3. Deploy Jenkins Pipeline
```bash
./deploy_to_jenkins.sh
```

### 4. Trigger First Build
```bash
# Push changes to trigger CI/CD
git push local main

# Or trigger manually via Jenkins web interface:
# http://192.168.1.119:8080/job/ltmc-mcp-server/
```

## CI/CD Workflow

1. **Developer pushes to local Git** (192.168.1.119)
2. **Jenkins detects changes** (polls every 5 minutes)
3. **Pipeline executes quality gates**:
   - ✅ Security framework validation
   - ✅ Mock detection and compliance
   - ✅ Database integration testing
   - ✅ Performance SLA validation
   - ✅ Docker image build and push
4. **If all gates pass**: Prepare for GitHub deployment
5. **If gates fail**: Keep changes local for fixes

## Quality Gates
- **Security**: Framework validation, injection prevention
- **Compliance**: No mock implementations in production code
- **Database**: Real integration with SQLite, Redis, Neo4j, PostgreSQL, FAISS
- **Performance**: <500ms for tools/list, <2000ms for tools/call
- **Docker**: Containerized build and registry push

## Monitoring
- **Jenkins Dashboard**: http://192.168.1.119:8080/
- **Build Logs**: Full console output for debugging
- **Docker Images**: Available at 192.168.1.119:5000
- **Artifacts**: Build reports and deployment summaries

## Troubleshooting

### Jenkins Not Accessible
```bash
# SSH to Raspberry Pi and check Jenkins
ssh feanor@192.168.1.119
sudo systemctl status jenkins
sudo systemctl start jenkins  # if needed
```

### Git Authentication Issues
```bash
# Generate SSH key if needed
ssh-keygen -t rsa -b 4096 -C "ci@ltmc.local"

# Copy public key to Jenkins server
ssh-copy-id feanor@192.168.1.119
```

### Docker Registry Issues
```bash
# Check Docker registry on Jenkins server
ssh feanor@192.168.1.119
docker ps | grep registry
```

## Next Steps
Once CI/CD is working locally, configure GitHub integration:
1. Add GitHub remote to Jenkins job
2. Configure GitHub webhooks
3. Set up deployment keys
4. Enable automatic GitHub pushes on successful builds
