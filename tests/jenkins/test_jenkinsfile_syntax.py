#!/usr/bin/env python3
"""
TDD Test Suite: Jenkinsfile Syntax Validation with LTMC Integration
==================================================================

Professional test suite for validating Jenkins pipeline syntax issues and 
ensuring professional Groovy-only implementation.

Uses LTMC pattern analysis tools to detect syntax mixing and validate structure.
"""

import pytest
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, NamedTuple
from dataclasses import dataclass

# Add LTMC to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ltms.tools.pattern_tools import PatternAnalyzer
from ltms.tools.memory_tools import MemoryManager
from ltms.tools.unix_tools import UnixToolManager

class SyntaxIssue(NamedTuple):
    """Professional syntax issue representation"""
    line_number: int
    issue_type: str
    description: str
    severity: str
    fix_suggestion: str

@dataclass
class JenkinsfileSyntaxAnalysis:
    """Professional analysis results"""
    file_path: str
    total_lines: int
    groovy_shell_mixing: List[SyntaxIssue]
    path_errors: List[SyntaxIssue]
    error_handling_missing: List[SyntaxIssue]
    ltmc_integration_missing: List[SyntaxIssue]
    is_production_ready: bool
    overall_score: float

class JenkinsfileSyntaxValidator:
    """Professional Jenkins syntax validator with LTMC integration"""
    
    def __init__(self):
        self.pattern_analyzer = PatternAnalyzer()
        self.memory_manager = MemoryManager()
        self.unix_tools = UnixToolManager()
        self.jenkinsfile_path = Path(__file__).parent.parent.parent / "Jenkinsfile.simple"
        
    def analyze_jenkinsfile(self) -> JenkinsfileSyntaxAnalysis:
        """
        Professional syntax analysis using LTMC pattern tools.
        
        Returns comprehensive analysis with specific line-by-line issues.
        """
        if not self.jenkinsfile_path.exists():
            raise FileNotFoundError(f"Jenkinsfile not found: {self.jenkinsfile_path}")
            
        content = self.jenkinsfile_path.read_text()
        lines = content.split('\n')
        
        # Use LTMC pattern analysis
        groovy_patterns = self.pattern_analyzer.extract_patterns(
            content, 
            language="groovy",
            pattern_type="syntax_issues"
        )
        
        analysis = JenkinsfileSyntaxAnalysis(
            file_path=str(self.jenkinsfile_path),
            total_lines=len(lines),
            groovy_shell_mixing=[],
            path_errors=[],
            error_handling_missing=[],
            ltmc_integration_missing=[],
            is_production_ready=False,
            overall_score=0.0
        )
        
        # Analyze line by line
        for line_num, line in enumerate(lines, 1):
            # Check for Groovy/Shell mixing (CRITICAL ISSUE)
            if self._has_groovy_shell_mixing(line):
                analysis.groovy_shell_mixing.append(SyntaxIssue(
                    line_number=line_num,
                    issue_type="GROOVY_SHELL_MIXING",
                    description=f"Shell and Groovy syntax mixed: {line.strip()}",
                    severity="CRITICAL",
                    fix_suggestion="Use pure Groovy script block or separate shell command"
                ))
            
            # Check for path errors
            if "lmtc" in line and "ltmc" not in line:
                analysis.path_errors.append(SyntaxIssue(
                    line_number=line_num,
                    issue_type="PATH_TYPO",
                    description=f"Path typo 'lmtc' should be 'ltmc': {line.strip()}",
                    severity="HIGH",
                    fix_suggestion="Replace 'lmtc' with 'ltmc'"
                ))
            
            # Check for missing error handling
            if line.strip().startswith("sh ") and "try" not in content[max(0, content.find(line)-200):content.find(line)]:
                analysis.error_handling_missing.append(SyntaxIssue(
                    line_number=line_num,
                    issue_type="NO_ERROR_HANDLING",
                    description=f"Shell command without error handling: {line.strip()}",
                    severity="MEDIUM",
                    fix_suggestion="Wrap in try-catch block with LTMC error storage"
                ))
        
        # Check for LTMC integration
        ltmc_integrations = self._analyze_ltmc_integration(content)
        if len(ltmc_integrations) < 5:  # Should have at least 5 LTMC tool integrations
            analysis.ltmc_integration_missing.append(SyntaxIssue(
                line_number=0,
                issue_type="INSUFFICIENT_LTMC_INTEGRATION",
                description=f"Only {len(ltmc_integrations)} LTMC tool integrations found, need at least 5",
                severity="HIGH",
                fix_suggestion="Add memory, todo, cache, pattern, and error handling integrations"
            ))
        
        # Calculate production readiness
        analysis.is_production_ready = (
            len(analysis.groovy_shell_mixing) == 0 and
            len(analysis.path_errors) == 0 and
            len(analysis.ltmc_integration_missing) == 0
        )
        
        # Calculate overall score
        total_issues = (
            len(analysis.groovy_shell_mixing) * 10 +  # Critical weight
            len(analysis.path_errors) * 5 +           # High weight
            len(analysis.error_handling_missing) * 2 + # Medium weight
            len(analysis.ltmc_integration_missing) * 5  # High weight
        )
        analysis.overall_score = max(0, 100 - total_issues)
        
        # Store analysis in LTMC memory
        self.memory_manager.store_memory(
            content=f"Jenkins syntax analysis: {len(analysis.groovy_shell_mixing)} critical issues, score: {analysis.overall_score}",
            memory_type="technical",
            tags=["jenkins", "syntax-analysis", "tdd", "validation"],
            metadata={
                "file_path": str(self.jenkinsfile_path),
                "critical_issues": len(analysis.groovy_shell_mixing),
                "total_issues": total_issues,
                "score": analysis.overall_score,
                "production_ready": analysis.is_production_ready
            }
        )
        
        return analysis
    
    def _has_groovy_shell_mixing(self, line: str) -> bool:
        """Detect Groovy/Shell syntax mixing - the root cause of our failures"""
        line = line.strip()
        
        # CRITICAL: Groovy ternary operator in shell context
        if re.search(r'\$\{[^}]*\?\s*:[^}]*\}', line):
            return True
            
        # CRITICAL: currentBuild.* in shell string
        if re.search(r'\$\{currentBuild\.[^}]*\}', line) and any(shell_indicator in line for shell_indicator in ['sh """', "sh '''", "sh '"]):
            return True
            
        # CRITICAL: Complex nested substitutions
        if re.search(r'\$\(\[.*\$\{.*\}.*\]\)', line):
            return True
            
        return False
    
    def _analyze_ltmc_integration(self, content: str) -> List[str]:
        """Analyze LTMC tool integration using pattern analysis"""
        ltmc_patterns = [
            "ltms.tools.memory_tools",
            "ltms.tools.todo_tools", 
            "ltms.tools.cache_tools",
            "ltms.tools.pattern_tools",
            "ltms.tools.graph_tools",
            "ltms.tools.blueprint_tools",
            "ltms.tools.documentation_tools",
            "ltms.tools.chat_tools",
            "ltms.tools.config_tools",
            "ltms.tools.unix_tools",
            "ltms.tools.sync_tools"
        ]
        
        found_integrations = []
        for pattern in ltmc_patterns:
            if pattern in content or pattern.replace("ltms.tools.", "").replace("_tools", "_") in content:
                found_integrations.append(pattern)
                
        return found_integrations


class TestJenkinsfileSyntaxValidation:
    """
    Professional TDD test suite for Jenkins pipeline syntax validation.
    
    RED-GREEN-REFACTOR approach with LTMC integration.
    """
    
    @pytest.fixture
    def syntax_validator(self):
        """Professional test fixture with LTMC integration"""
        return JenkinsfileSyntaxValidator()
    
    def test_jenkinsfile_exists(self, syntax_validator):
        """TDD: Ensure Jenkinsfile exists before analysis"""
        assert syntax_validator.jenkinsfile_path.exists(), f"Jenkinsfile not found: {syntax_validator.jenkinsfile_path}"
        assert syntax_validator.jenkinsfile_path.stat().st_size > 0, "Jenkinsfile is empty"
    
    def test_critical_groovy_shell_mixing_detected(self, syntax_validator):
        """
        TDD RED: This test MUST FAIL initially - we have known syntax mixing issues.
        
        Validates detection of the root cause: Groovy ternary operators in shell context.
        This is the "Bad substitution" error source.
        """
        analysis = syntax_validator.analyze_jenkinsfile()
        
        # RED: This should currently FAIL - we have known issues
        assert len(analysis.groovy_shell_mixing) > 0, "Should detect existing Groovy/Shell mixing issues"
        
        # Verify we detect the specific problematic line (364)
        line_364_issue = any(issue.line_number == 364 for issue in analysis.groovy_shell_mixing)
        assert line_364_issue, "Should detect line 364 Groovy ternary operator issue"
        
        # Verify severity classification
        critical_issues = [issue for issue in analysis.groovy_shell_mixing if issue.severity == "CRITICAL"]
        assert len(critical_issues) > 0, "Should classify mixing as CRITICAL severity"
    
    def test_path_typo_detection(self, syntax_validator):
        """
        TDD RED: This test MUST FAIL initially - we have known path typos.
        
        Validates detection of lmtc vs ltmc path errors.
        """
        analysis = syntax_validator.analyze_jenkinsfile()
        
        # RED: This should currently FAIL - we have path typos
        path_typos = [issue for issue in analysis.path_errors if "lmtc" in issue.description]
        assert len(path_typos) > 0, "Should detect path typo 'lmtc' instead of 'ltmc'"
        
        # Verify fix suggestions are provided
        for issue in path_typos:
            assert "ltmc" in issue.fix_suggestion, f"Fix suggestion should mention 'ltmc': {issue.fix_suggestion}"
    
    def test_ltmc_integration_insufficient(self, syntax_validator):
        """
        TDD RED: This test MUST FAIL initially - insufficient LTMC integration.
        
        Validates that current Jenkinsfile lacks proper LTMC tool integration.
        """
        analysis = syntax_validator.analyze_jenkinsfile()
        
        # RED: This should currently FAIL - insufficient LTMC integration
        ltmc_issues = [issue for issue in analysis.ltmc_integration_missing if "LTMC" in issue.issue_type]
        assert len(ltmc_issues) > 0, "Should detect insufficient LTMC tool integration"
        
        # Verify it recommends specific tools
        ltmc_issue = ltmc_issues[0]
        assert any(tool in ltmc_issue.fix_suggestion for tool in ["memory", "todo", "cache"]), \
            "Should suggest specific LTMC tools"
    
    def test_error_handling_missing(self, syntax_validator):
        """
        TDD RED: This test MUST FAIL initially - missing error handling.
        
        Validates detection of shell commands without proper error handling.
        """
        analysis = syntax_validator.analyze_jenkinsfile()
        
        # RED: This should currently FAIL - missing error handling
        error_handling_issues = analysis.error_handling_missing
        assert len(error_handling_issues) > 0, "Should detect shell commands without error handling"
        
        # Verify fix suggestions mention try-catch
        for issue in error_handling_issues:
            assert "try-catch" in issue.fix_suggestion or "error" in issue.fix_suggestion, \
                f"Should suggest error handling: {issue.fix_suggestion}"
    
    def test_production_readiness_fails(self, syntax_validator):
        """
        TDD RED: This test MUST FAIL initially - not production ready.
        
        Validates that current Jenkinsfile is NOT production ready.
        """
        analysis = syntax_validator.analyze_jenkinsfile()
        
        # RED: This should currently FAIL - not production ready
        assert analysis.is_production_ready == False, "Current Jenkinsfile should NOT be production ready"
        assert analysis.overall_score < 80, f"Quality score should be low: {analysis.overall_score}"
    
    def test_ltmc_memory_storage_integration(self, syntax_validator):
        """
        TDD: Validate LTMC memory integration works correctly.
        
        Ensures analysis results are properly stored in LTMC memory.
        """
        analysis = syntax_validator.analyze_jenkinsfile()
        
        # Verify analysis was stored in LTMC memory
        # This validates our LTMC integration is working
        memory_stored = syntax_validator.memory_manager.retrieve_memory(
            query="Jenkins syntax analysis",
            memory_type="technical"
        )
        
        assert len(memory_stored) > 0, "Analysis should be stored in LTMC memory"
        
        # Verify metadata is preserved
        latest_analysis = memory_stored[0]  # Most recent
        assert "critical_issues" in latest_analysis.metadata, "Should store critical issue count"
        assert "production_ready" in latest_analysis.metadata, "Should store production readiness"

    def test_specific_line_364_detection(self, syntax_validator):
        """
        TDD: Specific test for the exact line causing "Bad substitution" error.
        
        This is the professional root cause analysis test.
        """
        analysis = syntax_validator.analyze_jenkinsfile()
        
        # Find the specific problematic pattern
        line_364_issues = [issue for issue in analysis.groovy_shell_mixing if issue.line_number == 364]
        
        assert len(line_364_issues) > 0, "Should detect line 364 as problematic"
        
        issue = line_364_issues[0]
        assert "?:" in issue.description or "ternary" in issue.description, \
            f"Should identify ternary operator issue: {issue.description}"
        assert issue.severity == "CRITICAL", f"Line 364 should be CRITICAL severity: {issue.severity}"

    def test_professional_fix_suggestions(self, syntax_validator):
        """
        TDD: Validate that fix suggestions are professional and actionable.
        
        Ensures we provide specific, implementable solutions.
        """
        analysis = syntax_validator.analyze_jenkinsfile()
        
        all_issues = (
            analysis.groovy_shell_mixing + 
            analysis.path_errors + 
            analysis.error_handling_missing + 
            analysis.ltmc_integration_missing
        )
        
        assert len(all_issues) > 0, "Should find issues to validate fix suggestions"
        
        for issue in all_issues:
            # Professional requirements for fix suggestions
            assert len(issue.fix_suggestion) > 10, f"Fix suggestion too short: {issue.fix_suggestion}"
            assert not issue.fix_suggestion.startswith("TODO"), "No TODO placeholders allowed"
            assert not issue.fix_suggestion.startswith("Fix"), "Should be specific, not generic 'Fix'"
            
            # Should mention specific techniques
            if issue.issue_type == "GROOVY_SHELL_MIXING":
                assert any(technique in issue.fix_suggestion for technique in ["script block", "Groovy", "separate"]), \
                    f"Should suggest specific Groovy technique: {issue.fix_suggestion}"


if __name__ == "__main__":
    # Professional test execution with LTMC integration
    validator = JenkinsfileSyntaxValidator()
    analysis = validator.analyze_jenkinsfile()
    
    print("🔍 JENKINS SYNTAX ANALYSIS RESULTS")
    print("==================================")
    print(f"File: {analysis.file_path}")
    print(f"Lines: {analysis.total_lines}")
    print(f"Production Ready: {analysis.is_production_ready}")
    print(f"Quality Score: {analysis.overall_score}/100")
    print()
    
    if analysis.groovy_shell_mixing:
        print("❌ CRITICAL: Groovy/Shell Mixing Issues")
        for issue in analysis.groovy_shell_mixing:
            print(f"  Line {issue.line_number}: {issue.description}")
            print(f"    Fix: {issue.fix_suggestion}")
    
    if analysis.path_errors:
        print("❌ HIGH: Path Errors")
        for issue in analysis.path_errors:
            print(f"  Line {issue.line_number}: {issue.description}")
    
    if analysis.ltmc_integration_missing:
        print("❌ HIGH: LTMC Integration Missing")
        for issue in analysis.ltmc_integration_missing:
            print(f"  {issue.description}")
    
    print(f"\n✅ Analysis stored in LTMC memory")
    
    # Run pytest if available
    try:
        import subprocess
        result = subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"], 
                              capture_output=True, text=True)
        print(f"\n🧪 TDD Test Results:")
        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")
    except Exception as e:
        print(f"⚠️ Could not run pytest: {e}")