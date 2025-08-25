#!/bin/bash

# LTMC CI/CD Quality Gates Integration Script
# Integrates quality gates with Jenkins CI/CD pipeline

set -euo pipefail

# Configuration
LTMC_ROOT="/home/feanor/Projects/lmtc"
QUALITY_GATES_DIR="$LTMC_ROOT/quality-gates"
REPORTS_DIR="$LTMC_ROOT/quality-reports"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Setup reports directory
setup_reports() {
    log_info "Setting up quality reports directory..."
    mkdir -p "$REPORTS_DIR"
    cd "$LTMC_ROOT"
}

# Run quality gates for CI/CD
run_quality_gates() {
    log_info "Running LTMC quality gates for CI/CD..."
    
    # Set CI environment variables
    export LTMC_CI_MODE=true
    export LTMC_QUALITY_GATES=strict
    
    # Run comprehensive quality gates
    python3 "$QUALITY_GATES_DIR/run_quality_gates.py" \
        --project-root "$LTMC_ROOT" \
        --output "$REPORTS_DIR/quality_gates_report.json"
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "All quality gates passed"
        return 0
    else
        log_error "Quality gates failed"
        return 1
    fi
}

# Generate CI/CD summary report
generate_cicd_summary() {
    log_info "Generating CI/CD quality summary..."
    
    local quality_report="$REPORTS_DIR/quality_gates_report.json"
    
    if [ -f "$quality_report" ]; then
        # Extract key metrics using jq if available
        if command -v jq &> /dev/null; then
            local overall_passed=$(jq -r '.overall_passed' "$quality_report")
            local passed_gates=$(jq -r '.passed_gates' "$quality_report")
            local total_gates=$(jq -r '.total_gates' "$quality_report")
            local overall_score=$(jq -r '.overall_score' "$quality_report")
            
            local build_status
            if [ "$overall_passed" = "true" ]; then
                build_status="✅ PASSED"
            else
                build_status="❌ FAILED"
            fi
            
            local recommendations
            if [ "$overall_passed" = "true" ]; then
                recommendations="All quality standards met. Ready for deployment."
            else
                recommendations="Quality issues detected. Review failed gates before deployment."
            fi
            
            local gate_results
            gate_results=$(jq -r '.gate_results[] | "- " + (if .passed then "✅" else "❌" end) + " " + .name + ": " + .message' "$quality_report")
            
            {
                echo "# LTMC CI/CD Quality Gates Summary"
                echo ""
                echo "**Build Status**: ${build_status}"
                echo "**Quality Score**: ${overall_score}/100"
                echo "**Gates Passed**: ${passed_gates}/${total_gates}"
                echo ""
                echo "## Quality Gate Results"
                echo "${gate_results}"
                echo ""
                echo "## Recommendations"
                echo "${recommendations}"
                echo ""
                echo "**Generated**: $(date)"
                echo "**Report**: quality_gates_report.json"
            } > "$REPORTS_DIR/cicd_summary.md"
        else
            echo "# LTMC CI/CD Quality Gates Summary" > "$REPORTS_DIR/cicd_summary.md"
            echo "Quality gates report generated at: $quality_report" >> "$REPORTS_DIR/cicd_summary.md"
        fi
        
        log_success "CI/CD summary generated"
    else
        log_warning "Quality gates report not found"
    fi
}

# Main execution for different CI/CD stages
case "${1:-run}" in
    "setup")
        setup_reports
        ;;
    "run")
        setup_reports
        run_quality_gates
        generate_cicd_summary
        ;;
    "mock-only")
        setup_reports
        python3 "$QUALITY_GATES_DIR/run_quality_gates.py" --gate mock --project-root "$LTMC_ROOT"
        ;;
    "performance-only")
        setup_reports
        python3 "$QUALITY_GATES_DIR/run_quality_gates.py" --gate performance --project-root "$LTMC_ROOT"
        ;;
    "coverage-only")
        setup_reports
        python3 "$QUALITY_GATES_DIR/run_quality_gates.py" --gate coverage --project-root "$LTMC_ROOT"
        ;;
    *)
        echo "Usage: $0 [setup|run|mock-only|performance-only|coverage-only]"
        echo "  setup    - Setup reports directory"
        echo "  run      - Run all quality gates (default)"
        echo "  mock-only - Run only mock detection"
        echo "  performance-only - Run only performance SLA check"
        echo "  coverage-only - Run only coverage check"
        exit 1
        ;;
esac
    
    chmod +x "$SCRIPTS_DIR/cicd_quality_gates.sh"
    log_success "CI/CD integration script created"
}

# Generate quality gates documentation
generate_documentation() {
    log_info "Generating quality gates documentation..."
    
    cat > "$QUALITY_CONFIG_DIR/QUALITY_GATES_GUIDE.md" << 'EOF'
# LTMC Quality Gates Implementation Guide

## Overview

The LTMC Quality Gates system enforces comprehensive quality standards for the LTMC TDD framework, ensuring zero-tolerance for mock implementations, performance SLA compliance, and comprehensive testing coverage.

## Quality Standards

### 1. Mock Detection (Zero Tolerance)
- **Requirement**: No mock implementations in production code
- **Validator**: `validators/mock_detector.py`
- **Threshold**: 0 violations
- **Scope**: `ltmc_mcp_server/`, `ltms/` directories

### 2. Test Coverage
- **Requirement**: Minimum 85% code coverage
- **Tool**: pytest-cov
- **Threshold**: ≥85%
- **Scope**: All production code

### 3. Test Success Rate
- **Requirement**: Minimum 95% test success rate
- **Tool**: pytest with JUnit output
- **Threshold**: ≥95%
- **Scope**: All test suites

### 4. Performance SLA
- **Requirement**: <15ms operation response time
- **Monitor**: `monitors/performance_sla.py`
- **Thresholds**:
  - Database operations: <15ms
  - Vector search: <25ms
  - Graph queries: <20ms
  - Cache operations: <5ms

### 5. Code Quality
- **Requirements**:
  - Black formatting compliance
  - isort import sorting
  - flake8 linting (max-line-length=88)
- **Threshold**: 8.0/10 quality score

### 6. Security Compliance
- **Tool**: Bandit security scanner
- **Requirement**: 0 high-severity issues
- **Threshold**: 0 high-severity vulnerabilities

## Usage

### Command Line Interface

```bash
# Run all quality gates
python quality-gates/run_quality_gates.py

# Run specific gate
python quality-gates/run_quality_gates.py --gate mock
python quality-gates/run_quality_gates.py --gate coverage
python quality-gates/run_quality_gates.py --gate performance

# Generate report
python quality-gates/run_quality_gates.py --output quality_report.json
```

### CI/CD Integration

```bash
# In Jenkins pipeline
scripts/cicd_quality_gates.sh run

# Individual gates for debugging
scripts/cicd_quality_gates.sh mock-only
scripts/cicd_quality_gates.sh performance-only
```

### Docker Integration

```dockerfile
# Add to Dockerfile for CI
RUN python quality-gates/run_quality_gates.py --output /reports/quality.json
```

## Quality Gate Results

### Success Criteria
All quality gates must pass for successful CI/CD pipeline completion:

```json
{
  "overall_passed": true,
  "passed_gates": 6,
  "total_gates": 6,
  "overall_score": 95.5
}
```

### Failure Handling
Failed quality gates prevent deployment and require fixes:

```json
{
  "overall_passed": false,
  "failed_gates": 1,
  "gate_results": [
    {
      "name": "Mock Detection",
      "passed": false,
      "message": "Mock violations: 3"
    }
  ]
}
```

## Configuration

### Threshold Configuration
Edit thresholds in `run_quality_gates.py`:

```python
THRESHOLDS = {
    'test_coverage': 85.0,
    'test_success_rate': 95.0,
    'performance_sla_ms': 15,
    'mock_violations': 0,
    'security_high_issues': 0,
    'code_quality_score': 8.0,
}
```

### Tool Configuration
- pytest: `configs/pytest.ini`
- Black: `configs/pyproject.toml`
- flake8: `configs/.flake8`
- Bandit: `configs/.bandit`

## Jenkins Integration

### Pipeline Stage
```groovy
stage('Quality Gates Validation') {
    steps {
        script {
            sh '''
                scripts/cicd_quality_gates.sh run
            '''
        }
    }
    post {
        always {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: 'quality-reports',
                reportFiles: 'cicd_summary.md',
                reportName: 'Quality Gates Report'
            ])
        }
    }
}
```

### Quality Gate Failure Handling
```groovy
post {
    failure {
        script {
            if (fileExists('quality-reports/quality_gates_report.json')) {
                // Parse and display specific failures
                def qualityReport = readJSON file: 'quality-reports/quality_gates_report.json'
                def failedGates = qualityReport.gate_results.findAll { !it.passed }
                
                echo "Failed Quality Gates:"
                failedGates.each { gate ->
                    echo "❌ ${gate.name}: ${gate.message}"
                }
            }
        }
    }
}
```

## Troubleshooting

### Common Issues

1. **Mock Detection False Positives**
   - Check exclusion patterns in `mock_detector.py`
   - Verify test files are properly excluded

2. **Coverage Below Threshold**
   - Add missing tests for uncovered code
   - Check coverage report: `htmlcov/index.html`

3. **Performance SLA Violations**
   - Review database connection pooling
   - Check for blocking operations
   - Monitor resource usage

4. **Code Quality Issues**
   - Run `black ltmc_mcp_server/ ltms/` to fix formatting
   - Run `isort ltmc_mcp_server/ ltms/` to fix imports
   - Address flake8 warnings

### Debug Commands

```bash
# Verbose quality gate run
python quality-gates/run_quality_gates.py --output debug_report.json

# Individual tool runs
python -m pytest --cov=ltmc_mcp_server --cov-report=html
python -m black --check --diff ltmc_mcp_server/
python -m flake8 ltmc_mcp_server/
python -m bandit -r ltmc_mcp_server/ -f json
```

## Monitoring and Metrics

### Quality Metrics Dashboard
- Overall quality score trending
- Individual gate pass/fail rates
- Performance SLA compliance over time
- Coverage progression

### Alerts
- Quality gate failures trigger immediate alerts
- Performance SLA violations logged for analysis
- Security issue notifications

## Best Practices

1. **Run Quality Gates Locally**
   ```bash
   # Before committing
   scripts/cicd_quality_gates.sh run
   ```

2. **Incremental Improvements**
   - Gradually increase coverage thresholds
   - Continuously monitor performance metrics
   - Regular security audits

3. **Quality Culture**
   - Team training on quality standards
   - Regular quality reviews
   - Continuous improvement processes

## Support

For quality gate issues:
1. Check logs in `quality-reports/`
2. Review individual tool outputs
3. Consult LTMC Technical Standards document
4. Contact development team for threshold adjustments

---

**Remember**: Quality gates are designed to maintain LTMC's high standards. All gates must pass for production deployment.
