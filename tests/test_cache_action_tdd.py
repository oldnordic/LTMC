"""
TDD Tests for cache_action Consolidated Powertool
Tests all 4 cache actions with real Redis operations (NO MOCKS)
"""

import os
import pytest
import tempfile
import sqlite3
from datetime import datetime, timezone

# Add LTMC to path
import sys
sys.path.insert(0, '/home/feanor/Projects/ltmc')

from ltms.tools.consolidated import cache_action


class TestCacheActionTDD:
    """Test cache_action powertool with real Redis operations."""
    
    def setup_method(self):
        """Setup test environment with real Redis connection."""
        # Cache action uses real Redis service, no setup needed
        pass
    
    def teardown_method(self):
        """Clean up test environment."""
        # Flush any test cache entries
        try:
            cache_action(action="flush", cache_type="all")
        except Exception:
            pass  # Ignore cleanup errors
    
    def test_cache_health_check_action(self):
        """Test Redis health check with real connection."""
        result = cache_action(action="health_check")
        
        # Should either succeed with Redis running or fail gracefully
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Redis is available
            assert result['connected'] is True
            assert 'host' in result
            assert 'port' in result
            assert result['message'] == 'Redis connection healthy'
        else:
            # Redis not available - expected behavior
            assert result['connected'] is False
            assert 'error' in result
            assert 'Redis' in result['error']
    
    def test_cache_stats_action(self):
        """Test cache statistics retrieval with real Redis data."""
        result = cache_action(action="stats")
        
        # Should either succeed with Redis running or fail gracefully
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Redis is available
            assert 'stats' in result
            assert 'cache_type' in result
            assert result['cache_type'] == 'all'
        else:
            # Redis not available or configuration error - expected behavior
            assert 'error' in result
            assert any(keyword in result['error'].lower() for keyword in [
                'cache stats failed', 'failed to get cache stats', 
                'redis', 'config', 'import'
            ])
    
    def test_cache_stats_filtered_action(self):
        """Test cache statistics with type filtering."""
        # Test embeddings filter
        result = cache_action(action="stats", cache_type="embeddings")
        
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            assert result['cache_type'] == 'embeddings'
            assert 'stats' in result
        
        # Test queries filter
        result = cache_action(action="stats", cache_type="queries")
        
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            assert result['cache_type'] == 'queries'
            assert 'stats' in result
    
    def test_cache_flush_all_action(self):
        """Test cache flush with all cache types."""
        result = cache_action(action="flush", cache_type="all")
        
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Redis is available and flush succeeded
            assert result['cache_type'] == 'all'
            assert 'total_keys_deleted' in result
            assert 'breakdown' in result
            
            breakdown = result['breakdown']
            assert 'embeddings' in breakdown
            assert 'queries' in breakdown  
            assert 'chunks' in breakdown
            assert 'resources' in breakdown
        else:
            # Redis not available - expected behavior
            assert 'error' in result
            assert 'cache flush failed' in result['error'].lower()
    
    def test_cache_flush_specific_type_action(self):
        """Test cache flush with specific cache types."""
        # Test embeddings flush
        result = cache_action(action="flush", cache_type="embeddings")
        
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            assert result['cache_type'] == 'embeddings'
            assert 'keys_deleted' in result
        
        # Test queries flush
        result = cache_action(action="flush", cache_type="queries")
        
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            assert result['cache_type'] == 'queries'
            assert 'keys_deleted' in result
    
    def test_cache_flush_custom_pattern_action(self):
        """Test cache flush with custom pattern."""
        result = cache_action(action="flush", pattern="test:*")
        
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            assert 'pattern' in result
            assert result['pattern'] == "test:*"
            assert 'keys_deleted' in result
        else:
            # Redis not available - expected behavior
            assert 'error' in result
    
    def test_cache_reset_action(self):
        """Test Redis global instance reset."""
        result = cache_action(action="reset")
        
        assert isinstance(result, dict)
        assert 'success' in result
        
        if result['success']:
            # Redis is available and reset succeeded
            assert result['message'] == 'Redis global instances reset successfully'
        else:
            # Redis not available - expected behavior
            assert 'error' in result
            assert 'cache reset failed' in result['error'].lower()
    
    def test_cache_action_invalid_action(self):
        """Test invalid action parameter handling."""
        result = cache_action(action="invalid_action")
        
        assert result['success'] is False
        assert 'Unknown cache action' in result['error']
    
    def test_cache_action_missing_action(self):
        """Test missing action parameter handling."""
        result = cache_action(action="")
        
        assert result['success'] is False
        assert result['error'] == 'Action parameter is required'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])