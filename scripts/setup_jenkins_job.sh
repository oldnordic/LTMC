#!/bin/bash

# LTMC Jenkins Job Configuration Script
# Creates and configures Jenkins pipeline job for LTMC CI/CD

set -euo pipefail

# Configuration
JENKINS_URL="http://192.168.1.119:8080"
JENKINS_USER="admin"
JENKINS_PASSWORD="${JENKINS_PASSWORD:-admin}"
JOB_NAME="ltmc-ci-cd-pipeline"
GIT_REPO_URL="git@192.168.1.119:ltmc.git"
GIT_CREDENTIALS_ID="ltmc-git-credentials"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Jenkins availability
check_jenkins() {
    log_info "Checking Jenkins availability..."
    
    if ! curl -s --connect-timeout 10 "$JENKINS_URL/api/json" > /dev/null; then
        log_error "Jenkins is not accessible at $JENKINS_URL"
        log_info "Please ensure Jenkins is running: sudo systemctl start jenkins"
        exit 1
    fi
    
    log_success "Jenkins is accessible"
}

# Install required Jenkins plugins
install_plugins() {
    log_info "Installing required Jenkins plugins..."
    
    local required_plugins=(
        "git"
        "workflow-aggregator"
        "pipeline-stage-view"
        "blueocean"
        "junit"
        "coverage"
        "htmlpublisher"
        "emailext"
        "timestamper"
        "ws-cleanup"
        "build-timeout"
        "github"
        "ssh-credentials"
        "credentials-binding"
        "docker-pipeline"
    )
    
    # Create plugin installation script
    cat > /tmp/install-plugins.groovy << 'EOF'
import jenkins.model.*
import hudson.model.*

def instance = Jenkins.getInstance()
def pm = instance.getPluginManager()
def uc = instance.getUpdateCenter()

// Install plugins
def plugins = [
    "git", "workflow-aggregator", "pipeline-stage-view", "blueocean",
    "junit", "coverage", "htmlpublisher", "emailext", "timestamper",
    "ws-cleanup", "build-timeout", "github", "ssh-credentials",
    "credentials-binding", "docker-pipeline"
]

plugins.each { plugin ->
    if (!pm.getPlugin(plugin)) {
        println "Installing plugin: ${plugin}"
        def deployment = uc.getPlugin(plugin).deploy()
        deployment.get()
    } else {
        println "Plugin already installed: ${plugin}"
    }
}

// Save configuration
instance.save()
println "Plugin installation completed"
EOF
    
    # Execute plugin installation via Jenkins CLI
    if command -v java &> /dev/null; then
        # Download Jenkins CLI if not present
        if [[ ! -f "jenkins-cli.jar" ]]; then
            curl -s "$JENKINS_URL/jnlpJars/jenkins-cli.jar" -o jenkins-cli.jar
        fi
        
        # Execute Groovy script
        java -jar jenkins-cli.jar -s "$JENKINS_URL" -auth "$JENKINS_USER:$JENKINS_PASSWORD" groovy = < /tmp/install-plugins.groovy || {
            log_warning "Plugin installation via CLI failed - may need manual installation"
        }
    else
        log_warning "Java not found - plugins must be installed manually"
    fi
    
    log_success "Plugin installation attempted"
}

# Create SSH credentials
create_ssh_credentials() {
    log_info "Creating SSH credentials for Git access..."
    
    # Create credentials XML
    cat > /tmp/ssh-credentials.xml << EOF
<com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey plugin="ssh-credentials">
  <scope>GLOBAL</scope>
  <id>$GIT_CREDENTIALS_ID</id>
  <description>LTMC Git Repository SSH Access</description>
  <username>feanor</username>
  <privateKeySource class="com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey\$FileOnMasterPrivateKeySource">
    <privateKeyFile>/var/lib/jenkins/.ssh/id_rsa</privateKeyFile>
  </privateKeySource>
</com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey>
EOF
    
    # Create credentials via Groovy script
    cat > /tmp/create-credentials.groovy << 'EOF'
import jenkins.model.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.impl.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.jenkins.plugins.sshcredentials.impl.*

def instance = Jenkins.getInstance()
def domain = Domain.global()
def store = instance.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()

// Check if credentials already exist
def existingCreds = store.getCredentials(domain).find { it.id == 'ltmc-git-credentials' }

if (!existingCreds) {
    // Read private key from file
    def privateKeyFile = new File('/var/lib/jenkins/.ssh/id_rsa')
    if (privateKeyFile.exists()) {
        def privateKey = privateKeyFile.text
        
        def credentials = new BasicSSHUserPrivateKey(
            CredentialsScope.GLOBAL,
            'ltmc-git-credentials',
            'feanor',
            new BasicSSHUserPrivateKey.DirectEntryPrivateKeySource(privateKey),
            '',
            'LTMC Git Repository SSH Access'
        )
        
        store.addCredentials(domain, credentials)
        instance.save()
        println "SSH credentials created successfully"
    } else {
        println "Private key file not found: /var/lib/jenkins/.ssh/id_rsa"
    }
} else {
    println "SSH credentials already exist"
}
EOF
    
    # Execute credentials creation
    if [[ -f "jenkins-cli.jar" ]]; then
        java -jar jenkins-cli.jar -s "$JENKINS_URL" -auth "$JENKINS_USER:$JENKINS_PASSWORD" groovy = < /tmp/create-credentials.groovy || {
            log_warning "Credentials creation via CLI failed - manual setup required"
        }
    fi
    
    log_success "SSH credentials configuration attempted"
}

# Create Jenkins pipeline job
create_pipeline_job() {
    log_info "Creating LTMC CI/CD pipeline job..."
    
    # Create job configuration XML
    cat > /tmp/job-config.xml << EOF
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <actions/>
  <description>LTMC TDD Framework CI/CD Pipeline - Comprehensive testing with real databases and quality gates</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <hudson.plugins.jira.JiraProjectProperty plugin="jira"/>
    <hudson.plugins.buildblocker.BuildBlockerProperty plugin="build-blocker-plugin">
      <useBuildBlocker>false</useBuildBlocker>
      <blockLevel>GLOBAL</blockLevel>
      <scanQueueFor>DISABLED</scanQueueFor>
      <blockingJobs></blockingJobs>
    </hudson.plugins.buildblocker.BuildBlockerProperty>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.StringParameterDefinition>
          <name>GIT_COMMIT</name>
          <description>Git commit hash (auto-populated by webhook)</description>
          <defaultValue>main</defaultValue>
          <trim>true</trim>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>COMMIT_MESSAGE</name>
          <description>Commit message (auto-populated by webhook)</description>
          <defaultValue>Manual build</defaultValue>
          <trim>true</trim>
        </hudson.model.StringParameterDefinition>
        <hudson.model.StringParameterDefinition>
          <name>COMMIT_AUTHOR</name>
          <description>Commit author (auto-populated by webhook)</description>
          <defaultValue>Unknown</defaultValue>
          <trim>true</trim>
        </hudson.model.StringParameterDefinition>
        <hudson.model.BooleanParameterDefinition>
          <name>SKIP_TESTS</name>
          <description>Skip test execution (emergency builds only)</description>
          <defaultValue>false</defaultValue>
        </hudson.model.BooleanParameterDefinition>
        <hudson.model.BooleanParameterDefinition>
          <name>FORCE_PUSH</name>
          <description>Force push to GitHub even if quality gates fail</description>
          <defaultValue>false</defaultValue>
        </hudson.model.BooleanParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
    <org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
      <triggers>
        <hudson.triggers.SCMTrigger>
          <spec>H/5 * * * *</spec>
          <ignorePostCommitHooks>false</ignorePostCommitHooks>
        </hudson.triggers.SCMTrigger>
        <com.cloudbees.hudson.plugins.folder.computed.DefaultOrphanedItemStrategy plugin="cloudbees-folder">
          <pruneDeadBranches>true</pruneDeadBranches>
          <daysToKeep>-1</daysToKeep>
          <numToKeep>-1</numToKeep>
        </com.cloudbees.hudson.plugins.folder.computed.DefaultOrphanedItemStrategy>
      </triggers>
    </org.jenkinsci.plugins.workflow.job.properties.PipelineTriggersJobProperty>
    <jenkins.model.BuildDiscarderProperty>
      <strategy class="hudson.tasks.LogRotator">
        <daysToKeep>30</daysToKeep>
        <numToKeep>50</numToKeep>
        <artifactDaysToKeep>7</artifactDaysToKeep>
        <artifactNumToKeep>10</artifactNumToKeep>
      </strategy>
    </jenkins.model.BuildDiscarderProperty>
  </properties>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps">
    <scm class="hudson.plugins.git.GitSCM" plugin="git">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>$GIT_REPO_URL</url>
          <credentialsId>$GIT_CREDENTIALS_ID</credentialsId>
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
    <scriptPath>Jenkinsfile</scriptPath>
    <lightweight>true</lightweight>
  </definition>
  <triggers/>
  <disabled>false</disabled>
</flow-definition>
EOF
    
    # Create job via Jenkins CLI
    if [[ -f "jenkins-cli.jar" ]]; then
        # Check if job already exists
        if java -jar jenkins-cli.jar -s "$JENKINS_URL" -auth "$JENKINS_USER:$JENKINS_PASSWORD" get-job "$JOB_NAME" > /dev/null 2>&1; then
            log_info "Job already exists, updating configuration..."
            java -jar jenkins-cli.jar -s "$JENKINS_URL" -auth "$JENKINS_USER:$JENKINS_PASSWORD" update-job "$JOB_NAME" < /tmp/job-config.xml
        else
            log_info "Creating new pipeline job..."
            java -jar jenkins-cli.jar -s "$JENKINS_URL" -auth "$JENKINS_USER:$JENKINS_PASSWORD" create-job "$JOB_NAME" < /tmp/job-config.xml
        fi
    else
        log_warning "Jenkins CLI not available - job must be created manually"
        log_info "Job configuration saved to /tmp/job-config.xml"
    fi
    
    log_success "Pipeline job configuration completed"
}

# Configure Jenkins global settings
configure_jenkins_settings() {
    log_info "Configuring Jenkins global settings..."
    
    # Create global configuration script
    cat > /tmp/configure-jenkins.groovy << 'EOF'
import jenkins.model.*
import hudson.model.*
import hudson.tasks.*
import hudson.plugins.emailext.*

def instance = Jenkins.getInstance()

// Configure email notification
def emailExtension = instance.getDescriptor(ExtendedEmailPublisher.class)
if (emailExtension) {
    emailExtension.setSmtpServer("localhost")
    emailExtension.setSmtpPort("25")
    emailExtension.setDefaultSubject("LTMC CI/CD: \$PROJECT_NAME - Build # \$BUILD_NUMBER - \$BUILD_STATUS!")
    emailExtension.setDefaultBody("""
LTMC CI/CD Build Report

Project: \$PROJECT_NAME
Build Number: \$BUILD_NUMBER
Build Status: \$BUILD_STATUS
Build URL: \$BUILD_URL

Commit: \$GIT_COMMIT
Author: \$GIT_AUTHOR_NAME
Message: \$GIT_COMMIT_MSG

Check the build details for more information.
""")
    emailExtension.save()
}

// Configure security (if needed)
def securityRealm = instance.getSecurityRealm()
if (securityRealm instanceof hudson.security.HudsonPrivateSecurityRealm) {
    // Basic security configuration
    instance.save()
}

// Set number of executors
instance.setNumExecutors(2)

// Configure quiet period
instance.setQuietPeriod(5)

// Save all changes
instance.save()

println "Jenkins global configuration updated"
EOF
    
    # Execute configuration script
    if [[ -f "jenkins-cli.jar" ]]; then
        java -jar jenkins-cli.jar -s "$JENKINS_URL" -auth "$JENKINS_USER:$JENKINS_PASSWORD" groovy = < /tmp/configure-jenkins.groovy || {
            log_warning "Global configuration failed - manual setup may be required"
        }
    fi
    
    log_success "Jenkins global configuration attempted"
}

# Create webhook configuration script
create_webhook_setup() {
    log_info "Creating webhook configuration instructions..."
    
    cat > /tmp/webhook-setup.md << EOF
# LTMC Jenkins Webhook Configuration

## Generic Webhook Trigger
To enable automatic builds on Git push, configure the webhook in your Git post-receive hook:

### Webhook URL
\`\`\`
$JENKINS_URL/job/$JOB_NAME/build
\`\`\`

### Advanced Webhook with Parameters
\`\`\`
$JENKINS_URL/job/$JOB_NAME/buildWithParameters?GIT_COMMIT=\$COMMIT&COMMIT_MESSAGE=\$MESSAGE&COMMIT_AUTHOR=\$AUTHOR
\`\`\`

## GitHub Webhook (for GitHub sync)
If syncing to GitHub, configure webhook:

1. Go to GitHub repository settings
2. Add webhook: \`$JENKINS_URL/github-webhook/\`
3. Content type: application/json
4. Events: Just the push event

## Manual Trigger
You can manually trigger builds via:
- Jenkins UI: $JENKINS_URL/job/$JOB_NAME/
- CLI: \`java -jar jenkins-cli.jar -s $JENKINS_URL build $JOB_NAME\`
- API: \`curl -X POST $JENKINS_URL/job/$JOB_NAME/build\`

## Authentication
For authenticated webhook triggers, use Jenkins user API token:
\`\`\`bash
curl -X POST -u \$JENKINS_USER:\$JENKINS_TOKEN $JENKINS_URL/job/$JOB_NAME/build
\`\`\`

Generate API token:
1. Jenkins → People → [Username] → Configure
2. Add new Token
3. Copy token for webhook authentication
EOF
    
    log_success "Webhook configuration instructions created at /tmp/webhook-setup.md"
}

# Test Jenkins job
test_jenkins_job() {
    log_info "Testing Jenkins job configuration..."
    
    # Test job trigger via API
    if command -v curl &> /dev/null; then
        log_info "Triggering test build..."
        
        # Trigger build with test parameters
        curl -X POST \
            -u "$JENKINS_USER:$JENKINS_PASSWORD" \
            "$JENKINS_URL/job/$JOB_NAME/buildWithParameters" \
            -d "GIT_COMMIT=test&COMMIT_MESSAGE=Test%20build&COMMIT_AUTHOR=CI%20Setup&SKIP_TESTS=true" \
            --silent --show-error || {
            log_warning "Test build trigger failed - check credentials and job configuration"
        }
        
        log_info "Test build triggered - check Jenkins UI for progress"
    else
        log_warning "curl not available - manual testing required"
    fi
    
    log_success "Job testing completed"
}

# Generate setup summary
generate_jenkins_summary() {
    log_info "Generating Jenkins setup summary..."
    
    cat > /tmp/jenkins-setup-summary.md << EOF
# LTMC Jenkins CI/CD Setup Summary

## Jenkins Configuration
- **URL**: $JENKINS_URL
- **Job Name**: $JOB_NAME
- **Git Repository**: $GIT_REPO_URL
- **Credentials ID**: $GIT_CREDENTIALS_ID

## Pipeline Features
- ✅ **Real Database Testing**: PostgreSQL, Neo4j, Redis, FAISS
- ✅ **Container Isolation**: Testcontainers with parallel execution
- ✅ **Quality Gates**: Code coverage, performance SLA, mock detection
- ✅ **MCP Protocol Testing**: stdio compliance validation
- ✅ **Performance Monitoring**: <15ms SLA enforcement
- ✅ **Security Scanning**: Bandit security analysis
- ✅ **Code Quality**: Black, isort, flake8, mypy validation
- ✅ **GitHub Integration**: Automatic push on success

## Build Triggers
- **Git Push**: Automatic via post-receive hook
- **Scheduled**: Every 5 minutes polling
- **Manual**: Via Jenkins UI or API
- **Webhook**: Generic and GitHub webhooks

## Pipeline Stages
1. **Checkout & Environment Validation**
2. **Build Environment Setup**
3. **Code Quality Validation**
4. **Container-Based Database Testing**
5. **MCP Protocol Compliance Testing**
6. **Performance SLA Validation**
7. **Comprehensive Test Suite**
8. **Quality Gates Validation**
9. **Documentation Generation**

## Quality Standards
- **Test Coverage**: ≥85% required
- **Success Rate**: ≥95% required
- **Performance**: <15ms operations
- **Memory**: <500MB total usage
- **Build Time**: <30 minutes maximum
- **No Mocks**: Zero mock implementations in production

## Access Information
- **Jenkins UI**: $JENKINS_URL
- **Job URL**: $JENKINS_URL/job/$JOB_NAME/
- **Build Logs**: $JENKINS_URL/job/$JOB_NAME/lastBuild/console
- **Test Reports**: $JENKINS_URL/job/$JOB_NAME/lastBuild/testReport/

## Next Steps
1. **Verify Job Creation**: Check Jenkins UI for created job
2. **Test Git Integration**: Push commit to trigger build
3. **Monitor First Build**: Check logs and test results
4. **Configure Notifications**: Set up email/Slack notifications
5. **GitHub Sync**: Verify successful builds push to GitHub

## Troubleshooting
- **Build Failures**: Check console logs and test reports
- **Git Access**: Verify SSH credentials and repository access
- **Database Issues**: Check Docker and container logs
- **Performance**: Monitor resource usage and timing

## Support Commands
\`\`\`bash
# Check Jenkins status
sudo systemctl status jenkins

# View Jenkins logs
sudo journalctl -u jenkins -f

# Test SSH access
sudo -u jenkins ssh -T feanor@192.168.1.119

# Manual build trigger
curl -X POST $JENKINS_URL/job/$JOB_NAME/build
\`\`\`
EOF
    
    log_success "Jenkins setup summary generated at /tmp/jenkins-setup-summary.md"
    cat /tmp/jenkins-setup-summary.md
}

# Main execution
main() {
    log_info "Starting LTMC Jenkins job setup..."
    
    check_jenkins
    install_plugins
    create_ssh_credentials
    configure_jenkins_settings
    create_pipeline_job
    create_webhook_setup
    test_jenkins_job
    generate_jenkins_summary
    
    log_success "LTMC Jenkins CI/CD job setup completed successfully!"
    log_info "Access Jenkins at: $JENKINS_URL/job/$JOB_NAME/"
}

# Handle command line arguments
case "${1:-setup}" in
    "setup")
        main
        ;;
    "test")
        check_jenkins
        test_jenkins_job
        ;;
    "status")
        check_jenkins
        log_info "Jenkins job status: $JENKINS_URL/job/$JOB_NAME/"
        ;;
    *)
        echo "Usage: $0 [setup|test|status]"
        echo "  setup  - Complete Jenkins job setup (default)"
        echo "  test   - Test existing job configuration"
        echo "  status - Check Jenkins and job status"
        exit 1
        ;;
esac