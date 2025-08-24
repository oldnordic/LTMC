"""
Jenkins TDD Test Suite for LTMC Pipeline Groovy Refactor
=========================================================

Professional test suite package for comprehensive Jenkins pipeline testing
with full LTMC integration and TDD methodology.

Test Modules:
- test_jenkinsfile_syntax: Syntax validation with LTMC pattern analysis
- test_ltmc_integration: All 11 LTMC tools validation  
- test_error_handling: Error handling framework with LTMC integration
- test_utilities: Jenkins test utilities with LTMC unix tools

NON-NEGOTIABLE Requirements:
- All 11 LTMC tools must be validated
- TDD approach with RED-GREEN-REFACTOR
- Comprehensive error handling testing
- Professional production-ready code only
"""

__version__ = "1.0.0"
__author__ = "LTMC Development Team"

# Import all test modules for easy access
from .test_jenkinsfile_syntax import JenkinsfileSyntaxValidator, TestJenkinsfileSyntaxValidation
from .test_ltmc_integration import LTMCIntegrationValidator, TestLTMCIntegration  
from .test_error_handling import JenkinsErrorHandlingFramework, TestJenkinsErrorHandling
from .test_utilities import JenkinsTestUtilities

__all__ = [
    "JenkinsfileSyntaxValidator",
    "TestJenkinsfileSyntaxValidation", 
    "LTMCIntegrationValidator",
    "TestLTMCIntegration",
    "JenkinsErrorHandlingFramework", 
    "TestJenkinsErrorHandling",
    "JenkinsTestUtilities"
]