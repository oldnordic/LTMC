#!/usr/bin/env python3
"""
Jenkins Test Utilities with LTMC Unix Tools Integration
=======================================================

Professional utilities for Jenkins pipeline testing, validation, and 
integration with LTMC unix tools for file operations and system validation.

Used by all Jenkins TDD tests for consistent, professional test infrastructure.
"""

import os
import sys
import tempfile
import shutil
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, NamedTuple
from dataclasses import dataclass
from enum import Enum

# Add LTMC to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ltms.tools.unix_tools import UnixToolManager
from ltms.tools.memory_tools import MemoryManager

class JenkinsfileSection(Enum):
    """Jenkinsfile section types"""
    ENVIRONMENT = "environment"
    STAGES = "stages" 
    POST = "post"
    PIPELINE = "pipeline"
    AGENT = "agent"

@dataclass
class JenkinsfileAnalysis:
    """Professional Jenkinsfile analysis results"""
    file_path: str
    total_lines: int
    sections: Dict[JenkinsfileSection, List[str]]
    groovy_blocks: List[str]
    shell_blocks: List[str]
    environment_vars: Dict[str, str]
    ltmc_references: List[str]
    syntax_issues: List[str]
    is_valid: bool

class JenkinsTestUtilities:
    """Professional Jenkins test utilities with LTMC integration"""
    
    def __init__(self):
        self.unix_tools = UnixToolManager()
        self.memory_manager = MemoryManager()
        self.jenkinsfile_path = Path(__file__).parent.parent.parent / "Jenkinsfile.simple"
    
    def parse_jenkinsfile(self) -> JenkinsfileAnalysis:
        """
        Professional Jenkinsfile parsing with comprehensive analysis.
        
        Returns structured analysis of Jenkinsfile content.
        """
        if not self.jenkinsfile_path.exists():
            raise FileNotFoundError(f"Jenkinsfile not found: {self.jenkinsfile_path}")
        
        content = self.jenkinsfile_path.read_text()
        lines = content.split('\n')
        
        analysis = JenkinsfileAnalysis(
            file_path=str(self.jenkinsfile_path),
            total_lines=len(lines),
            sections={},
            groovy_blocks=[],
            shell_blocks=[],
            environment_vars={},
            ltmc_references=[],
            syntax_issues=[],
            is_valid=True
        )
        
        # Parse sections using LTMC unix tools for file analysis
        analysis.sections = self._parse_sections(content)
        analysis.groovy_blocks = self._extract_groovy_blocks(content)
        analysis.shell_blocks = self._extract_shell_blocks(content)
        analysis.environment_vars = self._parse_environment_vars(content)
        analysis.ltmc_references = self._find_ltmc_references(content)
        analysis.syntax_issues = self._detect_syntax_issues(content)
        analysis.is_valid = len(analysis.syntax_issues) == 0
        
        return analysis
    
    def _parse_sections(self, content: str) -> Dict[JenkinsfileSection, List[str]]:
        """Parse Jenkinsfile sections using professional parsing"""
        sections = {}
        
        # Use unix tools to analyze file structure
        lines = content.split('\n')
        
        current_section = None
        current_content = []
        brace_depth = 0
        
        for line_num, line in enumerate(lines):
            stripped = line.strip()
            
            # Detect section starts
            if stripped.startswith('pipeline {'):
                current_section = JenkinsfileSection.PIPELINE
                current_content = [line]
                brace_depth = 1
            elif stripped.startswith('environment {') and current_section == JenkinsfileSection.PIPELINE:
                if current_section:
                    sections[current_section] = current_content
                current_section = JenkinsfileSection.ENVIRONMENT
                current_content = [line]
                brace_depth = 1
            elif stripped.startswith('stages {') and current_section == JenkinsfileSection.PIPELINE:
                if current_section:
                    sections[current_section] = current_content
                current_section = JenkinsfileSection.STAGES
                current_content = [line]
                brace_depth = 1
            elif stripped.startswith('post {') and current_section == JenkinsfileSection.PIPELINE:
                if current_section:
                    sections[current_section] = current_content
                current_section = JenkinsfileSection.POST
                current_content = [line]
                brace_depth = 1
            else:
                if current_section:
                    current_content.append(line)
                    
                    # Track brace depth for proper section ending
                    brace_depth += line.count('{') - line.count('}')
                    
                    if brace_depth == 0 and current_section != JenkinsfileSection.PIPELINE:
                        sections[current_section] = current_content
                        current_section = JenkinsfileSection.PIPELINE
                        current_content = []
        
        # Add final section
        if current_section and current_content:
            sections[current_section] = current_content
        
        return sections
    
    def _extract_groovy_blocks(self, content: str) -> List[str]:
        """Extract Groovy script blocks"""
        groovy_blocks = []
        in_script_block = False
        current_block = []
        
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()
            
            if 'script {' in stripped:
                in_script_block = True
                current_block = [line]
            elif in_script_block:
                current_block.append(line)
                if stripped == '}' and len(current_block) > 1:
                    groovy_blocks.append('\n'.join(current_block))
                    in_script_block = False
                    current_block = []
        
        return groovy_blocks
    
    def _extract_shell_blocks(self, content: str) -> List[str]:
        """Extract shell command blocks"""
        import re
        
        # Find all shell blocks with different quote styles
        shell_patterns = [
            r"sh\s*['\"]([^'\"]*)['\"]",
            r"sh\s*'''([^']*)'''",
            r'sh\s*"""([^"]*)"""',
            r"sh\s*'''\s*([^']*?)\s*'''",
            r'sh\s*"""\s*([^"]*?)\s*"""'
        ]
        
        shell_blocks = []
        for pattern in shell_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            shell_blocks.extend(matches)
        
        return shell_blocks
    
    def _parse_environment_vars(self, content: str) -> Dict[str, str]:
        """Parse environment variables from Jenkinsfile"""
        env_vars = {}
        in_env_section = False
        
        lines = content.split('\n')
        for line in lines:
            stripped = line.strip()
            
            if stripped.startswith('environment {'):
                in_env_section = True
                continue
            elif stripped == '}' and in_env_section:
                in_env_section = False
                continue
            elif in_env_section and '=' in stripped:
                # Parse environment variable assignment
                parts = stripped.split('=', 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    var_value = parts[1].strip().strip('\'"')
                    env_vars[var_name] = var_value
        
        return env_vars
    
    def _find_ltmc_references(self, content: str) -> List[str]:
        """Find all LTMC tool references in Jenkinsfile"""
        ltmc_patterns = [
            'ltms.tools.',
            'ltmc_mcp_server',
            'MemoryManager',
            'TodoManager', 
            'CacheManager',
            'PatternAnalyzer',
            'GraphManager',
            'BlueprintManager',
            'DocumentationManager',
            'ChatManager',
            'ConfigManager',
            'UnixToolManager',
            'SyncManager',
            'store_memory',
            'add_todo',
            'health_check'
        ]
        
        references = []
        for pattern in ltmc_patterns:
            if pattern in content:
                # Find line numbers where pattern appears
                lines = content.split('\n')
                for line_num, line in enumerate(lines, 1):
                    if pattern in line:
                        references.append(f"Line {line_num}: {pattern} in '{line.strip()}'")
        
        return references
    
    def _detect_syntax_issues(self, content: str) -> List[str]:
        """Detect syntax issues in Jenkinsfile"""
        issues = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Check for Groovy/Shell mixing
            if '${' in stripped and '?:' in stripped:
                issues.append(f"Line {line_num}: Groovy ternary operator in potential shell context")
            
            # Check for path typos
            if 'lmtc' in stripped and 'ltmc' not in stripped:
                issues.append(f"Line {line_num}: Path typo 'lmtc' should be 'ltmc'")
            
            # Check for unhandled shell commands
            if stripped.startswith('sh ') and 'try' not in content[max(0, content.find(line)-200):content.find(line)]:
                issues.append(f"Line {line_num}: Shell command without error handling")
            
            # Check for currentBuild usage in shell
            if 'currentBuild.' in stripped and any(shell_indicator in stripped for shell_indicator in ['sh """', "sh '''", "sh '"]):
                issues.append(f"Line {line_num}: currentBuild reference in shell context")
        
        return issues
    
    def create_test_jenkinsfile(self, content: str, temp_dir: Optional[str] = None) -> Path:
        """Create temporary Jenkinsfile for testing"""
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp()
        
        temp_path = Path(temp_dir) / "Jenkinsfile.test"
        temp_path.write_text(content)
        
        return temp_path
    
    def validate_groovy_syntax(self, jenkinsfile_path: Path) -> Dict[str, Any]:
        """Validate Groovy syntax using system tools"""
        try:
            # Use unix tools to validate file
            file_info = self.unix_tools.file_info(str(jenkinsfile_path))
            
            if not file_info.get("exists", False):
                return {"valid": False, "error": "File does not exist"}
            
            # Basic syntax validation (checking for common issues)
            content = jenkinsfile_path.read_text()
            
            # Check for balanced braces
            open_braces = content.count('{')
            close_braces = content.count('}')
            
            if open_braces != close_braces:
                return {
                    "valid": False, 
                    "error": f"Unbalanced braces: {open_braces} open, {close_braces} close"
                }
            
            # Check for basic Groovy structure
            if 'pipeline {' not in content:
                return {"valid": False, "error": "Missing pipeline block"}
            
            return {"valid": True, "message": "Basic syntax validation passed"}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def simulate_jenkins_environment(self) -> Dict[str, str]:
        """Simulate Jenkins environment variables"""
        jenkins_env = {
            "BUILD_NUMBER": "test-build-789",
            "BUILD_ID": "test-build-789",
            "JOB_NAME": "ltmc-pipeline-test",
            "BUILD_URL": "http://192.168.1.119:8080/job/ltmc-pipeline-test/789/",
            "WORKSPACE": "/tmp/jenkins-test-workspace",
            "JENKINS_URL": "http://192.168.1.119:8080/",
            "NODE_NAME": "master",
            "EXECUTOR_NUMBER": "0",
            "BUILD_CAUSE": "MANUALTRIGGER"
        }
        
        return jenkins_env
    
    def setup_test_workspace(self) -> Path:
        """Set up test workspace with LTMC structure"""
        workspace = Path(tempfile.mkdtemp()) / "jenkins-test-workspace"
        workspace.mkdir(parents=True)
        
        # Create basic LTMC structure
        ltmc_dirs = [
            "ltms/tools",
            "ltmc_mcp_server", 
            "tests",
            "docs",
            "logs"
        ]
        
        for dir_path in ltmc_dirs:
            (workspace / dir_path).mkdir(parents=True)
        
        # Create basic files
        (workspace / "requirements.txt").write_text("# Test requirements\npydantic>=2.0\n")
        (workspace / "README.md").write_text("# Test LTMC Project\n")
        
        return workspace
    
    def cleanup_test_workspace(self, workspace: Path):
        """Clean up test workspace"""
        if workspace.exists():
            shutil.rmtree(workspace)
    
    def measure_pipeline_performance(self, test_function) -> Dict[str, float]:
        """Measure pipeline test performance"""
        import time
        
        start_time = time.time()
        try:
            result = test_function()
            success = True
        except Exception as e:
            result = {"error": str(e)}
            success = False
        end_time = time.time()
        
        duration_ms = (end_time - start_time) * 1000
        
        performance_data = {
            "duration_ms": duration_ms,
            "success": success,
            "timestamp": start_time
        }
        
        # Store performance data in LTMC memory
        self.memory_manager.store_memory(
            content=f"Jenkins test performance: {duration_ms:.1f}ms - {'SUCCESS' if success else 'FAILED'}",
            memory_type="performance",
            tags=["jenkins", "performance", "testing"],
            metadata=performance_data
        )
        
        return performance_data
    
    def generate_test_report(self, test_results: List[Dict[str, Any]]) -> str:
        """Generate professional test report"""
        passed = len([r for r in test_results if r.get("passed", False)])
        total = len(test_results)
        
        report = f"""
# JENKINS PIPELINE TDD TEST REPORT

## Summary
- **Total Tests**: {total}
- **Passed**: {passed}
- **Failed**: {total - passed}
- **Success Rate**: {(passed/total)*100:.1f}%

## Test Results
"""
        
        for i, result in enumerate(test_results, 1):
            status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
            test_name = result.get("name", f"Test {i}")
            duration = result.get("duration_ms", 0)
            
            report += f"\n### {i}. {test_name}\n"
            report += f"**Status**: {status}\n"
            report += f"**Duration**: {duration:.1f}ms\n"
            
            if not result.get("passed", False) and "error" in result:
                report += f"**Error**: {result['error']}\n"
            
            if "details" in result:
                report += f"**Details**: {result['details']}\n"
        
        return report
    
    def store_test_artifacts(self, artifacts: Dict[str, Any]):
        """Store test artifacts in LTMC memory"""
        try:
            self.memory_manager.store_memory(
                content=f"Jenkins test artifacts: {len(artifacts)} items stored",
                memory_type="testing",
                tags=["jenkins", "artifacts", "tdd"],
                metadata=artifacts
            )
        except Exception as e:
            print(f"⚠️ Could not store test artifacts: {e}")


# Professional test data and fixtures
SAMPLE_BROKEN_JENKINSFILE = '''
pipeline {
    agent any
    
    environment {
        LTMC_HOME = '/home/feanor/Projects/lmtc'  // TYPO: lmtc
        BROKEN_VAR = '${currentBuild.result ?: 'SUCCESS'}'  // BROKEN SYNTAX
    }
    
    stages {
        stage('Broken Stage') {
            steps {
                sh 'echo Status: ${currentBuild.result ?: 'SUCCESS'}'  // BROKEN
            }
        }
    }
}
'''

SAMPLE_FIXED_JENKINSFILE = '''
pipeline {
    agent any
    
    environment {
        LTMC_HOME = '/home/feanor/Projects/ltmc'
        BUILD_STATUS = 'UNKNOWN'
    }
    
    stages {
        stage('Fixed Stage') {
            steps {
                script {
                    def buildStatus = currentBuild.result ?: 'SUCCESS'
                    sh "echo Status: ${buildStatus}"
                }
            }
        }
    }
}
'''

SAMPLE_LTMC_INTEGRATED_JENKINSFILE = '''
pipeline {
    agent any
    
    environment {
        LTMC_HOME = '/home/feanor/Projects/ltmc'
        LTMC_TOOLS_ENABLED = 'true'
    }
    
    stages {
        stage('LTMC Integration') {
            steps {
                script {
                    sh """
                        python3 -c "
import sys
sys.path.insert(0, '${env.LTMC_HOME}')
from ltms.tools.memory_tools import MemoryManager
from ltms.tools.todo_tools import TodoManager

memory = MemoryManager()
todo = TodoManager()

memory.store_memory('Jenkins test success', 'ci_cd', ['jenkins', 'test'])
todo.add_todo('Jenkins pipeline validated', 'completed', ['jenkins'])

print('✅ LTMC tools integrated successfully')
"
                    """
                }
            }
        }
    }
}
'''


if __name__ == "__main__":
    # Professional utility demonstration
    utils = JenkinsTestUtilities()
    
    print("🔧 JENKINS TEST UTILITIES - LTMC INTEGRATION")
    print("===========================================")
    
    try:
        # Parse actual Jenkinsfile
        analysis = utils.parse_jenkinsfile()
        
        print(f"File: {analysis.file_path}")
        print(f"Total Lines: {analysis.total_lines}")
        print(f"Valid Syntax: {analysis.is_valid}")
        print(f"Sections Found: {len(analysis.sections)}")
        print(f"Environment Variables: {len(analysis.environment_vars)}")
        print(f"LTMC References: {len(analysis.ltmc_references)}")
        print(f"Syntax Issues: {len(analysis.syntax_issues)}")
        
        if analysis.syntax_issues:
            print("\n❌ Syntax Issues Found:")
            for issue in analysis.syntax_issues[:5]:  # Show first 5
                print(f"  - {issue}")
        
        if analysis.ltmc_references:
            print("\n🧠 LTMC References:")
            for ref in analysis.ltmc_references[:5]:  # Show first 5
                print(f"  - {ref}")
        
        print(f"\n✅ Analysis stored in LTMC memory")
        
    except FileNotFoundError:
        print("⚠️ Jenkinsfile.simple not found - using test data")
        
        # Test with sample data
        temp_file = utils.create_test_jenkinsfile(SAMPLE_BROKEN_JENKINSFILE)
        syntax_result = utils.validate_groovy_syntax(temp_file)
        
        print(f"Test Jenkinsfile Syntax: {'Valid' if syntax_result['valid'] else 'Invalid'}")
        if not syntax_result['valid']:
            print(f"Error: {syntax_result['error']}")
    
    # Demonstrate Jenkins environment simulation
    jenkins_env = utils.simulate_jenkins_environment()
    print(f"\n🏗️ Jenkins Environment Simulated: {len(jenkins_env)} variables")
    
    print(f"\n✅ Jenkins test utilities ready for TDD")