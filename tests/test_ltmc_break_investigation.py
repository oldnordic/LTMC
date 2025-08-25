#!/usr/bin/env python3
"""TDD investigation to find exactly what broke in LTMC."""

import sys
import os
import unittest
import subprocess
import sqlite3
from pathlib import Path

class TestLTMCBreakInvestigation(unittest.TestCase):
    """Systematically test what broke in LTMC."""

    def setUp(self):
        """Set up test environment."""
        self.ltmc_dir = Path('/home/feanor/Projects/ltmc')
        self.venv_python = self.ltmc_dir / 'venv' / 'bin' / 'python'
        
    def test_01_python_environment_works(self):
        """Test that Python environment is functional."""
        result = subprocess.run([str(self.venv_python), '--version'], 
                              capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, f"Python environment broken: {result.stderr}")
        self.assertIn('Python', result.stdout)

    def test_02_basic_imports_work(self):
        """Test that basic Python imports still work."""
        cmd = [str(self.venv_python), '-c', 'import sys; print("imports work")']
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.ltmc_dir))
        self.assertEqual(result.returncode, 0, f"Basic imports broken: {result.stderr}")

    def test_03_ltms_package_imports(self):
        """Test that LTMS package can be imported."""
        cmd = [str(self.venv_python), '-c', 'import ltms; print("ltms imports work")']
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.ltmc_dir))
        if result.returncode != 0:
            self.fail(f"LTMS package import broken: {result.stderr}")

    def test_04_ltms_tools_import(self):
        """Test that LTMS tools can be imported."""
        cmd = [str(self.venv_python), '-c', 'from ltms.tools import ALL_TOOLS; print("tools import work")']
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.ltmc_dir))
        if result.returncode != 0:
            self.fail(f"LTMS tools import broken: {result.stderr}")

    def test_05_embedding_service_imports(self):
        """Test that embedding service can be imported."""
        cmd = [str(self.venv_python), '-c', 
               'from ltms.services.embedding_service import create_embedding_model; print("embedding service works")']
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.ltmc_dir))
        if result.returncode != 0:
            self.fail(f"Embedding service import broken: {result.stderr}")

    def test_06_database_connection_works(self):
        """Test that database connection works."""
        cmd = [str(self.venv_python), '-c', '''
from ltms.database.connection import get_db_connection
conn = get_db_connection()
print("database connection works")
conn.close()
''']
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.ltmc_dir))
        if result.returncode != 0:
            self.fail(f"Database connection broken: {result.stderr}")

    def test_07_mcp_server_can_start(self):
        """Test that MCP server can be started."""
        cmd = [str(self.venv_python), '-m', 'ltms.mcp_server', '--help']
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.ltmc_dir), timeout=10)
        if result.returncode != 0:
            self.fail(f"MCP server broken: {result.stderr}")

    def test_08_main_entry_point_works(self):
        """Test that main entry point works."""
        cmd = [str(self.venv_python), '-m', 'ltms.main', '--help']
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.ltmc_dir), timeout=10)
        if result.returncode != 0:
            self.fail(f"Main entry point broken: {result.stderr}")

    def test_09_git_status_shows_what_changed(self):
        """Check what git thinks changed."""
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd=str(self.ltmc_dir))
        print(f"Git status shows: {result.stdout}")
        # This is informational, not a failure

    def test_10_check_critical_files_exist(self):
        """Check that critical files still exist."""
        critical_files = [
            'ltms/__init__.py',
            'ltms/main.py', 
            'ltms/mcp_server.py',
            'ltms/services/embedding_service.py',
            'ltms/tools/__init__.py'
        ]
        
        for file_path in critical_files:
            full_path = self.ltmc_dir / file_path
            self.assertTrue(full_path.exists(), f"Critical file missing: {file_path}")

if __name__ == '__main__':
    print("Starting TDD investigation of LTMC breakage...")
    unittest.main(verbosity=2)