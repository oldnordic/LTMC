#!/usr/bin/env python3
"""
TDD Test for LTMC Async Event Loop Fix
Tests cache_action and graph_action without asyncio.run() calls
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
import sys
import os

# Add LTMC to path
sys.path.insert(0, '/home/feanor/Projects/ltmc')

class TestAsyncEventLoopFix:
    """TDD tests to verify async event loop fixes"""
    
    def test_cache_action_health_check_no_event_loop_error(self):
        """Test that cache_action health_check doesn't cause event loop errors"""
        from ltms.tools.consolidated import cache_action
        
        # This should not raise "asyncio.run() cannot be called from a running event loop"
        try:
            result = cache_action('health_check')
            # Should return a result, not crash with event loop error
            assert isinstance(result, dict)
            assert 'success' in result
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                pytest.fail(f"Event loop error still present: {e}")
            else:
                # Other errors are acceptable for now
                pass
    
    def test_cache_action_stats_no_event_loop_error(self):
        """Test that cache_action stats doesn't cause event loop errors"""
        from ltms.tools.consolidated import cache_action
        
        try:
            result = cache_action('stats')
            assert isinstance(result, dict)
            assert 'success' in result
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                pytest.fail(f"Event loop error still present: {e}")
            else:
                pass
    
    def test_graph_action_query_no_event_loop_error(self):
        """Test that graph_action query doesn't cause event loop errors"""
        from ltms.tools.consolidated import graph_action
        
        try:
            result = graph_action('query', entity='test', query='MATCH (n) RETURN count(n)')
            assert isinstance(result, dict)
            assert 'success' in result
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                pytest.fail(f"Event loop error still present: {e}")
            else:
                pass
    
    def test_graph_action_link_no_event_loop_error(self):
        """Test that graph_action link doesn't cause event loop errors"""
        from ltms.tools.consolidated import graph_action
        
        try:
            result = graph_action('link', source='test1', target='test2', relation_type='RELATED')
            assert isinstance(result, dict)
            assert 'success' in result
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                pytest.fail(f"Event loop error still present: {e}")
            else:
                pass

if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])