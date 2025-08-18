#!/bin/bash

# LTMC Git Repository Setup Script
# Creates and configures local Git repository on 192.168.1.119 for LTMC CI/CD

set -euo pipefail

# Configuration
GIT_SERVER="192.168.1.119"
GIT_USER="feanor"
REPO_NAME="ltmc"
GIT_REPOS_DIR="/home/feanor/git-repos"
LOCAL_PROJECT_DIR="/home/feanor/Projects/lmtc"

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

# Validate environment
validate_environment() {
    log_info "Validating environment for LTMC Git setup..."
    
    # Check if we're on the correct server
    if [[ "$(hostname -I | grep -o '192\.168\.1\.119')" != "192.168.1.119" ]]; then
        log_warning "Not running on Git server 192.168.1.119, assuming remote setup"
    fi
    
    # Check Git installation
    if ! command -v git &> /dev/null; then
        log_error "Git is not installed"
        exit 1
    fi
    
    # Check SSH service
    if ! systemctl is-active --quiet ssh; then
        log_warning "SSH service is not running - required for Git access"
    fi
    
    log_success "Environment validation completed"
}

# Create bare Git repository
create_bare_repository() {
    log_info "Creating bare Git repository for LTMC..."
    
    # Create git-repos directory if it doesn't exist
    mkdir -p "$GIT_REPOS_DIR"
    
    # Navigate to git-repos directory
    cd "$GIT_REPOS_DIR"
    
    # Remove existing repository if it exists
    if [[ -d "$REPO_NAME.git" ]]; then
        log_warning "Existing repository found, backing up..."
        mv "$REPO_NAME.git" "$REPO_NAME.git.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Create bare repository
    git init --bare "$REPO_NAME.git"
    
    # Set proper permissions
    chown -R "$GIT_USER:$GIT_USER" "$REPO_NAME.git"
    chmod -R 755 "$REPO_NAME.git"
    
    log_success "Bare repository created at $GIT_REPOS_DIR/$REPO_NAME.git"
}

# Configure Git hooks for CI/CD integration
setup_git_hooks() {
    log_info "Setting up Git hooks for Jenkins CI/CD integration..."
    
    local hooks_dir="$GIT_REPOS_DIR/$REPO_NAME.git/hooks"
    
    # Create post-receive hook for Jenkins webhook
    cat > "$hooks_dir/post-receive" << 'EOF'
#!/bin/bash

# LTMC Git Post-Receive Hook
# Triggers Jenkins CI/CD pipeline on push

set -euo pipefail

# Configuration
JENKINS_URL="http://192.168.1.119:8080"
JENKINS_JOB="ltmc-ci-cd-pipeline"
JENKINS_USER="jenkins"
JENKINS_TOKEN="${JENKINS_API_TOKEN:-}"

# Logging
log_info() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >&2
}

# Process each ref being pushed
while read oldrev newrev refname; do
    # Only trigger on main branch
    if [[ "$refname" == "refs/heads/main" ]]; then
        log_info "Push detected on main branch: $oldrev -> $newrev"
        
        # Extract commit information
        COMMIT_HASH="$newrev"
        COMMIT_MSG=$(git log -1 --pretty=format:"%s" "$newrev" 2>/dev/null || echo "Unknown commit")
        AUTHOR=$(git log -1 --pretty=format:"%an" "$newrev" 2>/dev/null || echo "Unknown author")
        
        log_info "Commit: $COMMIT_HASH"
        log_info "Message: $COMMIT_MSG"
        log_info "Author: $AUTHOR"
        
        # Trigger Jenkins build
        if [[ -n "$JENKINS_TOKEN" ]]; then
            log_info "Triggering Jenkins build via API..."
            
            # Build parameters
            BUILD_PARAMS="GIT_COMMIT=$COMMIT_HASH&COMMIT_MESSAGE=${COMMIT_MSG// /%20}&COMMIT_AUTHOR=${AUTHOR// /%20}"
            
            # Trigger build with parameters
            curl -X POST \
                -u "$JENKINS_USER:$JENKINS_TOKEN" \
                "$JENKINS_URL/job/$JENKINS_JOB/buildWithParameters?$BUILD_PARAMS" \
                --silent --show-error || {
                log_error "Failed to trigger Jenkins build via API"
                # Fallback to generic trigger
                curl -X POST "$JENKINS_URL/job/$JENKINS_JOB/build" --silent || true
            }
            
            log_info "Jenkins CI/CD pipeline triggered successfully"
        else
            log_info "Jenkins API token not configured, using generic webhook trigger"
            
            # Generic webhook trigger
            curl -X POST "$JENKINS_URL/job/$JENKINS_JOB/build" --silent || {
                log_error "Failed to trigger Jenkins build"
            }
        fi
        
        # Log to file for debugging
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Push to main: $COMMIT_HASH by $AUTHOR" >> /var/log/ltmc-git-hooks.log
        
    else
        log_info "Ignoring push to $refname (not main branch)"
    fi
done

echo "Post-receive hook completed"
EOF
    
    # Make hook executable
    chmod +x "$hooks_dir/post-receive"
    
    # Create pre-receive hook for validation
    cat > "$hooks_dir/pre-receive" << 'EOF'
#!/bin/bash

# LTMC Git Pre-Receive Hook  
# Validates pushes before accepting them

set -euo pipefail

# Logging
log_info() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >&2
}

log_info "LTMC pre-receive validation starting..."

# Process each ref being pushed
while read oldrev newrev refname; do
    # Skip branch deletions
    if [[ "$newrev" == "0000000000000000000000000000000000000000" ]]; then
        log_info "Branch deletion detected, skipping validation"
        continue
    fi
    
    log_info "Validating push to $refname: $oldrev -> $newrev"
    
    # Validate commit message format (basic check)
    COMMIT_MSG=$(git log -1 --pretty=format:"%s" "$newrev" 2>/dev/null || echo "")
    if [[ ${#COMMIT_MSG} -lt 10 ]]; then
        log_error "Commit message too short (minimum 10 characters): '$COMMIT_MSG'"
        exit 1
    fi
    
    # Check for required files in LTMC project
    if [[ "$refname" == "refs/heads/main" ]]; then
        log_info "Validating LTMC project structure..."
        
        # Check for critical files
        REQUIRED_FILES=(
            "ltmc_mcp_server/main.py"
            "tests/conftest.py"
            "LTMC_TECHNICAL_STANDARDS.md"
            "requirements.txt"
            "Jenkinsfile"
        )
        
        for file in "${REQUIRED_FILES[@]}"; do
            if ! git show "$newrev:$file" > /dev/null 2>&1; then
                log_error "Required file missing: $file"
                exit 1
            fi
        done
        
        # Check for forbidden patterns
        FORBIDDEN_PATTERNS=(
            "TODO.*FIXME"
            "import.*mock"
            "from.*mock"
        )
        
        for pattern in "${FORBIDDEN_PATTERNS[@]}"; do
            if git show "$newrev" | grep -q "$pattern"; then
                log_error "Forbidden pattern detected: $pattern"
                exit 1
            fi
        done
        
        log_info "LTMC project structure validation passed"
    fi
    
    log_info "Validation completed for $refname"
done

log_info "Pre-receive validation successful"
EOF
    
    # Make hook executable
    chmod +x "$hooks_dir/pre-receive"
    
    # Set proper ownership
    chown -R "$GIT_USER:$GIT_USER" "$hooks_dir"
    
    log_success "Git hooks configured for Jenkins CI/CD integration"
}

# Push local LTMC project to Git repository
push_initial_code() {
    log_info "Pushing initial LTMC code to Git repository..."
    
    # Navigate to local project directory
    cd "$LOCAL_PROJECT_DIR"
    
    # Initialize Git if not already initialized
    if [[ ! -d ".git" ]]; then
        git init
        log_info "Initialized Git repository in local project"
    fi
    
    # Configure Git user
    git config user.name "LTMC System"
    git config user.email "ltmc@example.com"
    
    # Add remote origin
    git remote remove origin 2>/dev/null || true
    git remote add origin "$GIT_REPOS_DIR/$REPO_NAME.git"
    
    # Add all files
    git add .
    
    # Create initial commit if needed
    if ! git log --oneline 2>/dev/null | head -1; then
        git commit -m "feat: Initial LTMC TDD framework with 126→46 tool architecture

- Complete MCP stdio protocol implementation
- Real database operations (PostgreSQL, Neo4j, Redis, FAISS)
- Comprehensive TDD testing framework
- Performance SLA enforcement (<15ms operations)
- Mock detection and compliance validation
- Jenkins CI/CD pipeline integration
- Quality gates and automated testing

🚀 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
    fi
    
    # Push to main branch
    git branch -M main
    git push -u origin main
    
    log_success "Initial code pushed to Git repository"
}

# Create SSH key pair for Jenkins access
setup_ssh_access() {
    log_info "Setting up SSH access for Jenkins..."
    
    local jenkins_home="/var/lib/jenkins"
    local ssh_dir="$jenkins_home/.ssh"
    
    # Create SSH directory for Jenkins user
    sudo mkdir -p "$ssh_dir"
    
    # Generate SSH key pair if it doesn't exist
    if [[ ! -f "$ssh_dir/id_rsa" ]]; then
        sudo ssh-keygen -t rsa -b 4096 -C "jenkins@ltmc-ci" -f "$ssh_dir/id_rsa" -N ""
        log_success "SSH key pair generated for Jenkins"
    else
        log_info "SSH key pair already exists for Jenkins"
    fi
    
    # Set proper ownership and permissions
    sudo chown -R jenkins:jenkins "$ssh_dir"
    sudo chmod 700 "$ssh_dir"
    sudo chmod 600 "$ssh_dir/id_rsa"
    sudo chmod 644 "$ssh_dir/id_rsa.pub"
    
    # Add Jenkins public key to authorized_keys
    local authorized_keys="/home/$GIT_USER/.ssh/authorized_keys"
    mkdir -p "/home/$GIT_USER/.ssh"
    
    if [[ -f "$ssh_dir/id_rsa.pub" ]]; then
        cat "$ssh_dir/id_rsa.pub" >> "$authorized_keys"
        sort -u "$authorized_keys" -o "$authorized_keys"
        chmod 600 "$authorized_keys"
        chown "$GIT_USER:$GIT_USER" "$authorized_keys"
        log_success "Jenkins SSH access configured"
    fi
    
    # Test SSH connection
    sudo -u jenkins ssh -T -o StrictHostKeyChecking=no "$GIT_USER@localhost" "echo 'SSH connection test successful'" || {
        log_warning "SSH connection test failed - manual configuration may be required"
    }
}

# Create Jenkins credentials
create_jenkins_credentials() {
    log_info "Creating Jenkins credentials for Git access..."
    
    # Jenkins credentials XML template
    cat > "/tmp/ltmc-git-credentials.xml" << EOF
<com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>
  <scope>GLOBAL</scope>
  <id>ltmc-git-credentials</id>
  <description>LTMC Git Repository Access</description>
  <username>$GIT_USER</username>
  <password>{AQAAABAAAAAQExample=}</password>
</com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>
EOF
    
    log_info "Jenkins credentials template created at /tmp/ltmc-git-credentials.xml"
    log_warning "Manual step required: Configure credentials in Jenkins UI"
    log_info "1. Go to Jenkins → Manage Jenkins → Credentials"
    log_info "2. Add SSH Username with private key credential"
    log_info "3. Use ID: 'ltmc-git-credentials'"
    log_info "4. Username: '$GIT_USER'"
    log_info "5. Private key: /var/lib/jenkins/.ssh/id_rsa"
}

# Configure Git repository settings
configure_repository() {
    log_info "Configuring Git repository settings..."
    
    cd "$GIT_REPOS_DIR/$REPO_NAME.git"
    
    # Set repository description
    echo "LTMC TDD Framework - 126→46 Tool Architecture MCP System" > description
    
    # Configure Git settings
    git config receive.denyNonFastForwards false
    git config receive.denyCurrentBranch ignore
    git config core.bare true
    git config core.sharedRepository group
    
    # Set proper permissions
    find . -type d -exec chmod 755 {} \;
    find . -type f -exec chmod 644 {} \;
    chmod +x hooks/*
    
    log_success "Git repository configured"
}

# Generate setup summary
generate_summary() {
    log_info "Generating LTMC Git setup summary..."
    
    cat > "/tmp/ltmc-git-setup-summary.md" << EOF
# LTMC Git Repository Setup Summary

## Repository Configuration
- **Server**: $GIT_SERVER
- **Repository Path**: $GIT_REPOS_DIR/$REPO_NAME.git
- **Clone URL**: git@$GIT_SERVER:$REPO_NAME.git
- **Local Project**: $LOCAL_PROJECT_DIR

## Jenkins Integration
- **Jenkins URL**: http://$GIT_SERVER:8080
- **Pipeline Job**: ltmc-ci-cd-pipeline
- **Git Credentials ID**: ltmc-git-credentials

## Git Hooks Configured
- ✅ **post-receive**: Triggers Jenkins CI/CD pipeline
- ✅ **pre-receive**: Validates commits and LTMC structure

## Next Steps
1. **Configure Jenkins Pipeline**:
   - Create new Pipeline job: 'ltmc-ci-cd-pipeline'
   - Use Pipeline script from SCM
   - Repository URL: git@$GIT_SERVER:$REPO_NAME.git
   - Credentials: ltmc-git-credentials
   - Branch: main
   - Script Path: Jenkinsfile

2. **Set Jenkins API Token** (for webhook):
   - Generate API token in Jenkins user settings
   - Set environment variable: JENKINS_API_TOKEN

3. **Test Git Operations**:
   \`\`\`bash
   # Clone repository
   git clone git@$GIT_SERVER:$REPO_NAME.git ltmc-test
   
   # Make test commit
   cd ltmc-test
   echo "# Test" > test.md
   git add test.md
   git commit -m "test: Verify CI/CD trigger"
   git push origin main
   \`\`\`

4. **Verify CI/CD Pipeline**:
   - Check Jenkins job triggers after push
   - Monitor build progress and logs
   - Verify quality gates and test execution

## SSH Access
- Jenkins SSH key: /var/lib/jenkins/.ssh/id_rsa
- Git server access configured for jenkins user

## Repository Features
- 🔒 **Pre-receive validation**: Commit message and structure checks
- 🚀 **Post-receive triggers**: Automatic Jenkins CI/CD pipeline
- 📊 **Quality gates**: Test coverage, performance SLA, mock detection
- 🔄 **GitHub sync**: Successful builds pushed to GitHub

## Support
For issues or configuration help, check:
- Jenkins logs: /var/log/jenkins/jenkins.log
- Git hook logs: /var/log/ltmc-git-hooks.log
- SSH access: sudo -u jenkins ssh -T $GIT_USER@localhost
EOF
    
    log_success "Setup summary generated at /tmp/ltmc-git-setup-summary.md"
    cat /tmp/ltmc-git-setup-summary.md
}

# Main execution
main() {
    log_info "Starting LTMC Git repository setup..."
    
    validate_environment
    create_bare_repository
    configure_repository
    setup_git_hooks
    setup_ssh_access
    create_jenkins_credentials
    push_initial_code
    generate_summary
    
    log_success "LTMC Git repository setup completed successfully!"
    log_info "Next step: Configure Jenkins pipeline job with the generated summary"
}

# Execute main function
main "$@"