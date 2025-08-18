#!/bin/bash

# LTMC CI/CD Setup Script
# Configures Jenkins on Raspberry Pi (192.168.1.119) for LTMC MCP Server

set -e

echo "🚀 LTMC CI/CD Setup for Jenkins (192.168.1.119)"
echo "================================================"

# Configuration
JENKINS_HOST="192.168.1.119"
JENKINS_PORT="8080"
JENKINS_USER="feanor"
JENKINS_PASSWORD="2113"
LOCAL_GIT_SERVER="192.168.1.119"
PROJECT_NAME="ltmc-mcp-server"

echo "📋 Configuration:"
echo "  Jenkins: http://${JENKINS_HOST}:${JENKINS_PORT}"
echo "  Git Server: ${LOCAL_GIT_SERVER}"
echo "  Project: ${PROJECT_NAME}"
echo ""

# Test Jenkins connectivity
echo "🔍 Testing Jenkins connectivity..."
if curl -s -f "http://${JENKINS_HOST}:${JENKINS_PORT}" >/dev/null; then
    echo "✅ Jenkins is accessible at http://${JENKINS_HOST}:${JENKINS_PORT}"
else
    echo "❌ Cannot reach Jenkins at http://${JENKINS_HOST}:${JENKINS_PORT}"
    echo "Please ensure Jenkins is running on the Raspberry Pi"
    exit 1
fi

# Test Docker registry connectivity
echo "🐳 Testing Docker registry..."
if curl -s -f "http://${JENKINS_HOST}:5000/v2/_catalog" >/dev/null 2>&1; then
    echo "✅ Docker registry is accessible at ${JENKINS_HOST}:5000"
else
    echo "⚠️  Docker registry at ${JENKINS_HOST}:5000 may not be running"
    echo "    This is optional for basic CI/CD functionality"
fi

# Create Jenkins job configuration
echo "📝 Creating Jenkins job configuration..."

cat > jenkins-job-config.xml << 'EOF'
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job@2.40">
  <actions/>
  <description>LTMC MCP Server CI/CD Pipeline - Automated testing, building, and deployment pipeline for the Long-Term Memory and Context MCP server</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <com.coravy.hudson.plugins.github.GithubProjectProperty plugin="github@1.34.4">
      <projectUrl>https://github.com/user/ltmc/</projectUrl>
    </com.coravy.hudson.plugins.github.GithubProjectProperty>
    <hudson.plugins.jiraext.view.JiraExtBuildDetails plugin="jira-ext@0.8">
      <issueStrategyEnum>NONE</issueStrategyEnum>
    </hudson.plugins.jiraext.view.JiraExtBuildDetails>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.BooleanParameterDefinition>
          <name>SKIP_TESTS</name>
          <description>Skip test execution (for emergency deployments only)</description>
          <defaultValue>false</defaultValue>
        </hudson.model.BooleanParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>DOCKER_TAG</name>
          <description>Custom Docker tag (defaults to build number)</description>
          <defaultValue></defaultValue>
          <trim>true</trim>
        </hudson.model.StringParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers>
        <hudson.triggers.SCMTrigger>
          <spec>H/5 * * * *</spec>
          <ignorePostCommitHooks>false</ignorePostCommitHooks>
        </hudson.triggers.SCMTrigger>
      </triggers>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps@2.87">
    <scm class="hudson.plugins.git.GitSCM" plugin="git@4.8.2">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>git@192.168.1.119:ltmc.git</url>
          <credentialsId>ltmc-git-credentials</credentialsId>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>*/main</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
      <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
      <submoduleCfg class="list"/>
      <extensions/>
    </scm>
    <scriptPath>Jenkinsfile.simple</scriptPath>
    <lightweight>true</lightweight>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
EOF

echo "✅ Jenkins job configuration created: jenkins-job-config.xml"

# Create deployment script
echo "🚀 Creating deployment automation script..."

cat > deploy_to_jenkins.sh << 'EOF'
#!/bin/bash

# Deploy LTMC Pipeline to Jenkins
set -e

JENKINS_URL="http://192.168.1.119:8080"
JOB_NAME="ltmc-mcp-server"

echo "🚀 Deploying LTMC Pipeline to Jenkins..."

# Create or update Jenkins job
if curl -s -f "${JENKINS_URL}/job/${JOB_NAME}/config.xml" >/dev/null 2>&1; then
    echo "🔄 Updating existing Jenkins job: ${JOB_NAME}"
    curl -X POST "${JENKINS_URL}/job/${JOB_NAME}/config.xml" \
         --data-binary "@jenkins-job-config.xml" \
         -H "Content-Type: text/xml"
else
    echo "✨ Creating new Jenkins job: ${JOB_NAME}"
    curl -X POST "${JENKINS_URL}/createItem?name=${JOB_NAME}" \
         --data-binary "@jenkins-job-config.xml" \
         -H "Content-Type: text/xml"
fi

echo "✅ Jenkins job deployed successfully!"
echo "🔗 Job URL: ${JENKINS_URL}/job/${JOB_NAME}/"

EOF

chmod +x deploy_to_jenkins.sh
echo "✅ Deployment script created: deploy_to_jenkins.sh"

# Create local Git setup script
echo "📁 Creating local Git repository setup..."

cat > setup_local_git.sh << 'EOF'
#!/bin/bash

# Setup Local Git Repository on Jenkins Server
set -e

echo "📁 Setting up local Git repository for LTMC..."

# SSH to Jenkins server and create Git repository
ssh feanor@192.168.1.119 << 'REMOTE_SCRIPT'
    # Create Git repositories directory
    mkdir -p /home/feanor/git-repos
    cd /home/feanor/git-repos
    
    # Initialize bare Git repository for LTMC
    if [ ! -d "ltmc.git" ]; then
        git init --bare ltmc.git
        echo "✅ Created bare Git repository: ltmc.git"
    else
        echo "📁 Git repository already exists: ltmc.git"
    fi
    
    # Set permissions
    chmod -R 755 ltmc.git
    
    echo "✅ Local Git repository ready at: feanor@192.168.1.119:/home/feanor/git-repos/ltmc.git"
REMOTE_SCRIPT

echo "✅ Local Git repository setup completed"

EOF

chmod +x setup_local_git.sh
echo "✅ Git setup script created: setup_local_git.sh"

# Create README for CI/CD setup
cat > CI_CD_SETUP_README.md << 'EOF'
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
EOF

echo "✅ Documentation created: CI_CD_SETUP_README.md"

echo ""
echo "🎉 LTMC CI/CD Setup Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Review CI_CD_SETUP_README.md for detailed instructions"
echo "2. Run ./setup_local_git.sh to create Git repository"  
echo "3. Run ./deploy_to_jenkins.sh to deploy pipeline"
echo "4. Push code to local Git to trigger first build"
echo ""
echo "📋 Files created:"
echo "  - jenkins-job-config.xml (Jenkins job definition)"
echo "  - deploy_to_jenkins.sh (Deploy pipeline to Jenkins)"
echo "  - setup_local_git.sh (Setup local Git repository)"
echo "  - CI_CD_SETUP_README.md (Complete documentation)"
echo ""
echo "🔗 Jenkins URL: http://${JENKINS_HOST}:${JENKINS_PORT}/"
echo "📊 After setup, monitor builds at: http://${JENKINS_HOST}:${JENKINS_PORT}/job/${PROJECT_NAME}/"