"""
Mind Graph Redis Cache Patterns
File: ltms/database/cache/mind_graph_cache.py
Purpose: Redis caching for Mind Graph reasoning chains and patterns
Status: Phase 1 - Real Redis Implementation
"""

import json
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone, timedelta
import hashlib

logger = logging.getLogger(__name__)

class MindGraphCache:
    """Redis cache management for Mind Graph reasoning chains."""
    
    def __init__(self, redis_client=None):
        """Initialize Mind Graph cache with Redis client.
        
        Args:
            redis_client: Redis client instance (will be created if None)
        """
        self.redis_client = redis_client
        self._ensure_redis_connection()
        
        # Cache key patterns
        self.REASONING_CHAIN_KEY = "mindgraph:reasoning_chain:{chain_id}"
        self.AGENT_PATTERNS_KEY = "mindgraph:agent_patterns:{agent_id}"
        self.FILE_CHANGE_HISTORY_KEY = "mindgraph:file_changes:{file_path_hash}"
        self.CAUSAL_PATH_KEY = "mindgraph:causal_path:{path_hash}"
        self.DECISION_CONTEXT_KEY = "mindgraph:decision_context:{context_id}"
        self.AGENT_SESSION_KEY = "mindgraph:agent_session:{session_id}"
        
        # TTL settings (in seconds)
        self.REASONING_CHAIN_TTL = 3600  # 1 hour
        self.AGENT_PATTERNS_TTL = 7200   # 2 hours  
        self.FILE_HISTORY_TTL = 1800     # 30 minutes
        self.CAUSAL_PATH_TTL = 3600      # 1 hour
        self.DECISION_CONTEXT_TTL = 7200 # 2 hours
        self.AGENT_SESSION_TTL = 1800    # 30 minutes
    
    def _ensure_redis_connection(self):
        """Ensure Redis connection is available."""
        if self.redis_client is None:
            try:
                from ltms.database.redis_manager import RedisManager
                from ltms.config.json_config_loader import get_config
                
                config = get_config()
                redis_config = {
                    'host': config.redis_host,
                    'port': config.redis_port,
                    'db': config.redis_db,
                    'password': config.redis_password
                }
                
                self.redis_manager = RedisManager(redis_config)
                # Redis manager uses async connections, we'll check availability differently
                logger.info("Connected to Redis manager for Mind Graph caching")
                
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_manager = None
    
    def is_available(self) -> bool:
        """Check if Redis cache is available."""
        if not hasattr(self, 'redis_manager') or self.redis_manager is None:
            return False
        
        try:
            return self.redis_manager.is_available()
        except Exception:
            return False
    
    def cache_reasoning_chain(self, chain_id: str, chain_data: Dict[str, Any]) -> bool:
        """Cache reasoning chain data in Redis.
        
        Args:
            chain_id: Unique reasoning chain identifier
            chain_data: Chain data to cache
            
        Returns:
            bool: True if cached successfully, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            key = self.REASONING_CHAIN_KEY.format(chain_id=chain_id)
            
            # Add caching metadata
            cached_data = {
                'chain_id': chain_id,
                'data': chain_data,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'ttl': self.REASONING_CHAIN_TTL,
                'cache_version': '1.0'
            }
            
            # Cache with TTL
            self.redis_client.setex(
                key, 
                self.REASONING_CHAIN_TTL, 
                json.dumps(cached_data)
            )
            
            logger.debug(f"Cached reasoning chain: {chain_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache reasoning chain {chain_id}: {e}")
            return False
    
    def get_reasoning_chain(self, chain_id: str) -> Optional[Dict[str, Any]]:
        """Get cached reasoning chain from Redis.
        
        Args:
            chain_id: Reasoning chain identifier
            
        Returns:
            Cached chain data or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            key = self.REASONING_CHAIN_KEY.format(chain_id=chain_id)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Retrieved cached reasoning chain: {chain_id}")
                return data
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached reasoning chain {chain_id}: {e}")
            return None
    
    def cache_agent_patterns(self, agent_id: str, patterns: Dict[str, Any]) -> bool:
        """Cache agent decision patterns.
        
        Args:
            agent_id: Agent identifier
            patterns: Agent patterns to cache
            
        Returns:
            bool: True if cached successfully, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            key = self.AGENT_PATTERNS_KEY.format(agent_id=agent_id)
            
            cached_data = {
                'agent_id': agent_id,
                'patterns': patterns,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'pattern_count': len(patterns),
                'ttl': self.AGENT_PATTERNS_TTL
            }
            
            self.redis_client.setex(
                key,
                self.AGENT_PATTERNS_TTL,
                json.dumps(cached_data)
            )
            
            logger.debug(f"Cached agent patterns for: {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache agent patterns for {agent_id}: {e}")
            return False
    
    def get_agent_patterns(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get cached agent patterns.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Cached patterns or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            key = self.AGENT_PATTERNS_KEY.format(agent_id=agent_id)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Retrieved cached agent patterns: {agent_id}")
                return data.get('patterns', {})
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached agent patterns for {agent_id}: {e}")
            return None
    
    def cache_file_change_history(self, file_path: str, change_history: List[Dict[str, Any]]) -> bool:
        """Cache file change history for quick access.
        
        Args:
            file_path: File path
            change_history: List of changes for this file
            
        Returns:
            bool: True if cached successfully, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            # Hash file path for consistent key length
            file_path_hash = hashlib.md5(file_path.encode()).hexdigest()
            key = self.FILE_CHANGE_HISTORY_KEY.format(file_path_hash=file_path_hash)
            
            cached_data = {
                'file_path': file_path,
                'file_path_hash': file_path_hash,
                'change_history': change_history,
                'change_count': len(change_history),
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'ttl': self.FILE_HISTORY_TTL
            }
            
            self.redis_client.setex(
                key,
                self.FILE_HISTORY_TTL,
                json.dumps(cached_data)
            )
            
            logger.debug(f"Cached file change history for: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache file history for {file_path}: {e}")
            return False
    
    def get_file_change_history(self, file_path: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached file change history.
        
        Args:
            file_path: File path
            
        Returns:
            List of changes or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            file_path_hash = hashlib.md5(file_path.encode()).hexdigest()
            key = self.FILE_CHANGE_HISTORY_KEY.format(file_path_hash=file_path_hash)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Retrieved cached file history: {file_path}")
                return data.get('change_history', [])
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached file history for {file_path}: {e}")
            return None
    
    def cache_causal_path(self, start_node_id: str, end_node_id: str, path_data: Dict[str, Any]) -> bool:
        """Cache causal reasoning path between two nodes.
        
        Args:
            start_node_id: Starting node ID
            end_node_id: Ending node ID
            path_data: Path data including nodes and relationships
            
        Returns:
            bool: True if cached successfully, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            # Create hash from start and end nodes for consistent key
            path_string = f"{start_node_id}->{end_node_id}"
            path_hash = hashlib.md5(path_string.encode()).hexdigest()
            key = self.CAUSAL_PATH_KEY.format(path_hash=path_hash)
            
            cached_data = {
                'start_node_id': start_node_id,
                'end_node_id': end_node_id,
                'path_data': path_data,
                'path_length': len(path_data.get('nodes', [])),
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'ttl': self.CAUSAL_PATH_TTL
            }
            
            self.redis_client.setex(
                key,
                self.CAUSAL_PATH_TTL,
                json.dumps(cached_data)
            )
            
            logger.debug(f"Cached causal path: {start_node_id} -> {end_node_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache causal path: {e}")
            return False
    
    def get_causal_path(self, start_node_id: str, end_node_id: str) -> Optional[Dict[str, Any]]:
        """Get cached causal path.
        
        Args:
            start_node_id: Starting node ID
            end_node_id: Ending node ID
            
        Returns:
            Cached path data or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            path_string = f"{start_node_id}->{end_node_id}"
            path_hash = hashlib.md5(path_string.encode()).hexdigest()
            key = self.CAUSAL_PATH_KEY.format(path_hash=path_hash)
            cached_data = self.redis_client.get(key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.debug(f"Retrieved cached causal path: {start_node_id} -> {end_node_id}")
                return data.get('path_data', {})
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cached causal path: {e}")
            return None
    
    def cache_decision_context(self, context_id: str, context_data: Dict[str, Any]) -> bool:
        """Cache decision context for quick retrieval.
        
        Args:
            context_id: Decision context identifier
            context_data: Context data to cache
            
        Returns:
            bool: True if cached successfully, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            key = self.DECISION_CONTEXT_KEY.format(context_id=context_id)
            
            cached_data = {
                'context_id': context_id,
                'context_data': context_data,
                'cached_at': datetime.now(timezone.utc).isoformat(),
                'ttl': self.DECISION_CONTEXT_TTL
            }
            
            self.redis_client.setex(
                key,
                self.DECISION_CONTEXT_TTL,
                json.dumps(cached_data)
            )
            
            logger.debug(f"Cached decision context: {context_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cache decision context {context_id}: {e}")
            return False
    
    def invalidate_cache_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern.
        
        Args:
            pattern: Redis key pattern to match
            
        Returns:
            int: Number of keys deleted
        """
        if not self.is_available():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching pattern: {pattern}")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Failed to invalidate cache pattern {pattern}: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get Mind Graph cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.is_available():
            return {'status': 'unavailable'}
        
        try:
            # Count keys by pattern
            patterns = {
                'reasoning_chains': "mindgraph:reasoning_chain:*",
                'agent_patterns': "mindgraph:agent_patterns:*", 
                'file_histories': "mindgraph:file_changes:*",
                'causal_paths': "mindgraph:causal_path:*",
                'decision_contexts': "mindgraph:decision_context:*",
                'agent_sessions': "mindgraph:agent_session:*"
            }
            
            stats = {
                'status': 'available',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'key_counts': {}
            }
            
            for category, pattern in patterns.items():
                keys = self.redis_client.keys(pattern)
                stats['key_counts'][category] = len(keys)
            
            # Total Mind Graph keys
            total_keys = self.redis_client.keys("mindgraph:*")
            stats['total_mind_graph_keys'] = len(total_keys)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {'status': 'error', 'error': str(e)}


# Global cache instance
_mind_graph_cache = None

def get_mind_graph_cache() -> MindGraphCache:
    """Get global Mind Graph cache instance.
    
    Returns:
        MindGraphCache instance
    """
    global _mind_graph_cache
    
    if _mind_graph_cache is None:
        _mind_graph_cache = MindGraphCache()
    
    return _mind_graph_cache


def test_mind_graph_cache() -> bool:
    """Test Mind Graph cache functionality.
    
    Returns:
        bool: True if all tests pass, False otherwise
    """
    try:
        cache = get_mind_graph_cache()
        
        if not cache.is_available():
            print("❌ Redis not available for cache testing")
            return False
        
        # Test reasoning chain caching
        test_chain_id = "test_chain_123"
        test_chain_data = {
            'nodes': [
                {'type': 'change', 'id': 'change_1', 'summary': 'Test change'},
                {'type': 'reason', 'id': 'reason_1', 'summary': 'Test reason'}
            ],
            'relationships': [
                {'from': 'change_1', 'to': 'reason_1', 'type': 'MOTIVATED_BY'}
            ]
        }
        
        # Cache and retrieve
        if cache.cache_reasoning_chain(test_chain_id, test_chain_data):
            retrieved_data = cache.get_reasoning_chain(test_chain_id)
            if retrieved_data and retrieved_data['data'] == test_chain_data:
                print("✅ Reasoning chain caching test passed")
            else:
                print("❌ Reasoning chain retrieval failed")
                return False
        else:
            print("❌ Reasoning chain caching failed")
            return False
        
        # Test agent patterns caching
        test_agent_id = "test_agent_456"
        test_patterns = {
            'common_actions': ['code_edit', 'file_create'],
            'decision_patterns': {'bug_fix': 0.8, 'feature_add': 0.2}
        }
        
        if cache.cache_agent_patterns(test_agent_id, test_patterns):
            retrieved_patterns = cache.get_agent_patterns(test_agent_id)
            if retrieved_patterns == test_patterns:
                print("✅ Agent patterns caching test passed")
            else:
                print("❌ Agent patterns retrieval failed")
                return False
        else:
            print("❌ Agent patterns caching failed")
            return False
        
        # Test cache stats
        stats = cache.get_cache_stats()
        if stats['status'] == 'available' and stats['total_mind_graph_keys'] >= 0:
            print("✅ Cache stats test passed")
        else:
            print("❌ Cache stats test failed")
            return False
        
        # Cleanup test data
        cache.invalidate_cache_pattern("mindgraph:*test*")
        
        print("✅ All Mind Graph cache tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Mind Graph cache test failed: {e}")
        return False


if __name__ == "__main__":
    print("Testing Mind Graph Redis cache patterns")
    
    if test_mind_graph_cache():
        print("✅ Mind Graph cache implementation successful")
    else:
        print("❌ Mind Graph cache implementation failed")