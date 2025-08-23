"""
Centralized configuration for the KWE project.

This module provides a nested configuration structure that matches 
the expected access patterns throughout the KWE codebase.

Uses dynamic path detection to eliminate hardcoded paths and make
the system completely self-contained and portable.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any, List

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv(override=True)
except ImportError:
    # python-dotenv not available, environment variables must be set manually
    import warnings
    import logging

    # Set up logging for configuration warnings
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Check if .env files exist but dotenv can't load them
    env_files = [".env", ".env.local", ".env.production", ".env.development"]
    existing_env_files = [f for f in env_files if os.path.exists(f)]

    if existing_env_files:
        warning_msg = (
            f"python-dotenv package is not installed, but .env files exist: {', '.join(existing_env_files)}. "
            f"Environment variables from these files will NOT be loaded automatically. "
            f"To fix this: 1) Install python-dotenv: 'pip install python-dotenv' or "
            f"2) Set environment variables manually using your shell or system configuration."
        )
        warnings.warn(warning_msg, UserWarning)
        logger.warning(warning_msg)
    else:
        logger.info(
            "python-dotenv package not installed. Environment variables must be set manually "
            "using your shell or system configuration. To use .env files, install python-dotenv: "
            "'pip install python-dotenv'"
        )

# Handle both relative and absolute imports
try:
    from path_utils import (
        get_project_root,
        get_kwe_server_root,
        get_workspace_directory,
    )
except ImportError:
    # Fallback for when running as script
    try:
        from path_utils import (
            get_project_root,
            get_kwe_server_root,
            get_workspace_directory,
        )
    except ImportError:
        # Final fallback - define minimal versions
        from pathlib import Path

        def get_project_root():
            return Path(__file__).parent.parent

        def get_kwe_server_root():
            return Path(__file__).parent

        def get_workspace_directory(name="test_runs"):
            return get_project_root() / name


# Set environment variables
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"


def _get_redis_health_check_interval() -> int:
    """
    Get Redis health check interval from environment with validation.

    Validates range (5-300 seconds) with fallback to default 30 seconds.

    Returns:
        int: Health check interval in seconds (5-300)
    """
    try:
        interval_str = os.getenv("KWE_REDIS_HEALTH_CHECK_INTERVAL", "30")

        # Handle empty string case
        if not interval_str or interval_str.strip() == "":
            return 30

        interval = int(interval_str)

        # Validate range: 5-300 seconds
        if 5 <= interval <= 300:
            return interval
        else:
            # Log warning for out-of-range values
            import warnings

            warnings.warn(
                f"KWE_REDIS_HEALTH_CHECK_INTERVAL value {interval} is outside valid range (5-300 seconds). "
                f"Using default value 30 seconds.",
                UserWarning,
            )
            return 30

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_REDIS_HEALTH_CHECK_INTERVAL value '{interval_str}'. "
            f"Must be an integer between 5 and 300 seconds. Using default value 30 seconds.",
            UserWarning,
        )
        return 30


def _get_connection_pool_size(env_var: str, default: int) -> int:
    """
    Get connection pool size from environment with validation.

    Validates range (1-1000 connections) with fallback to provided default.

    Args:
        env_var: Environment variable name
        default: Default value to use

    Returns:
        int: Connection pool size (1-1000)
    """
    try:
        pool_size_str = os.getenv(env_var, str(default))

        # Handle empty string case
        if not pool_size_str or pool_size_str.strip() == "":
            return default

        pool_size = int(pool_size_str)

        # Validate range: 1-1000 connections
        if 1 <= pool_size <= 1000:
            return pool_size
        else:
            # Log warning for out-of-range values
            import warnings

            warnings.warn(
                f"{env_var} value {pool_size} is outside valid range (1-1000 connections). "
                f"Using default value {default} connections.",
                UserWarning,
            )
            return default

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid {env_var} value '{pool_size_str}'. "
            f"Must be an integer between 1 and 1000 connections. Using default value {default} connections.",
            UserWarning,
        )
        return default


def _get_postgresql_connection_pool_size() -> int:
    """Get PostgreSQL connection pool size from environment with validation."""
    return _get_connection_pool_size("KWE_POSTGRESQL_CONNECTION_POOL_SIZE", 10)


def _get_redis_connection_pool_size() -> int:
    """Get Redis connection pool size from environment with validation."""
    return _get_connection_pool_size("KWE_REDIS_CONNECTION_POOL_SIZE", 20)


def _get_neo4j_connection_pool_size() -> int:
    """Get Neo4j connection pool size from environment with validation."""
    return _get_connection_pool_size("KWE_NEO4J_CONNECTION_POOL_SIZE", 15)


def _get_memory_state_manager_pool_size() -> int:
    """Get Memory State Manager pool size from environment with validation."""
    return _get_connection_pool_size("KWE_MEMORY_STATE_MANAGER_POOL_SIZE", 50)


def _get_redis_max_connections() -> int:
    """Get Redis max connections from environment with validation."""
    return _get_connection_pool_size("KWE_REDIS_MAX_CONNECTIONS", 50)


def _get_memory_bridge_pool_size() -> int:
    """Get Memory Bridge pool size from environment with validation.
    
    MED-045: Configurable connection pool sizes for memory bridge optimization
    """
    return _get_connection_pool_size("KWE_MEMORY_BRIDGE_POOL_SIZE", 10)


def _get_state_manager_max_pool_size() -> int:
    """Get State Manager max pool size from environment with validation.
    
    MED-045: Configurable connection pool sizes for state manager
    """
    return _get_connection_pool_size("KWE_STATE_MANAGER_MAX_POOL_SIZE", 100)


def _get_memory_aware_pool_size() -> int:
    """Get Memory Aware pool size from environment with validation.
    
    MED-045: Configurable connection pool sizes for memory aware state manager
    """
    return _get_connection_pool_size("KWE_MEMORY_AWARE_POOL_SIZE", 50)


def _get_redis_protocol() -> str:
    """
    Get Redis protocol from environment with validation.

    Validates protocol values ('redis' or 'rediss') with fallback to 'redis'.

    Returns:
        str: Redis protocol ('redis' for standard, 'rediss' for SSL/TLS)
    """
    try:
        protocol_str = os.getenv("KWE_REDIS_PROTOCOL", "redis")

        # Handle empty string case
        if not protocol_str or protocol_str.strip() == "":
            return "redis"

        protocol = protocol_str.strip().lower()

        # Validate protocol: only 'redis' or 'rediss' allowed
        if protocol in ["redis", "rediss"]:
            return protocol
        else:
            # Log warning for invalid protocol values
            import warnings

            warnings.warn(
                f"KWE_REDIS_PROTOCOL value '{protocol}' is invalid. "
                f"Must be 'redis' or 'rediss'. Using default value 'redis'.",
                UserWarning,
            )
            return "redis"

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_REDIS_PROTOCOL value '{protocol_str}'. "
            f"Must be 'redis' or 'rediss'. Using default value 'redis'.",
            UserWarning,
        )
        return "redis"


def _get_qdrant_host() -> str:
    """
    Get Qdrant host from environment with validation.

    Returns:
        str: Qdrant host address
    """
    host_str = os.getenv("KWE_QDRANT_HOST", "localhost")

    # Handle empty string case
    if not host_str or host_str.strip() == "":
        return "localhost"

    return host_str.strip()


def _get_qdrant_port() -> int:
    """
    Get Qdrant port from environment with validation.

    Validates range (1-65535) with fallback to default 6333.

    Returns:
        int: Qdrant port (1-65535)
    """
    try:
        port_str = os.getenv("KWE_QDRANT_PORT", "6333")

        # Handle empty string case
        if not port_str or port_str.strip() == "":
            return 6333

        port = int(port_str)

        # Validate range: 1-65535
        if 1 <= port <= 65535:
            return port
        else:
            # Log warning for out-of-range values
            import warnings

            warnings.warn(
                f"KWE_QDRANT_PORT value {port} is outside valid range (1-65535). "
                f"Using default value 6333.",
                UserWarning,
            )
            return 6333

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_QDRANT_PORT value '{port_str}'. "
            f"Must be an integer between 1 and 65535. Using default value 6333.",
            UserWarning,
        )
        return 6333


def _get_qdrant_api_key() -> str:
    """Get Qdrant API key from environment."""
    return os.getenv("KWE_QDRANT_API_KEY", "")


def _get_service_host() -> str:
    """
    Get service host from environment with validation.

    Returns:
        str: Service host address
    """
    host_str = os.getenv("KWE_SERVICE_HOST", "localhost")

    # Handle empty string case
    if not host_str or host_str.strip() == "":
        return "localhost"

    return host_str.strip()


def _get_service_port() -> int:
    """
    Get service port from environment with validation.

    Validates range (1-65535) with fallback to default 8000.

    Returns:
        int: Service port (1-65535)
    """
    try:
        port_str = os.getenv("KWE_SERVICE_PORT", "8000")

        # Handle empty string case
        if not port_str or port_str.strip() == "":
            return 8000

        port = int(port_str)

        # Validate range: 1-65535
        if 1 <= port <= 65535:
            return port
        else:
            # Log warning for out-of-range values
            import warnings

            warnings.warn(
                f"KWE_SERVICE_PORT value {port} is outside valid range (1-65535). "
                f"Using default value 8000.",
                UserWarning,
            )
            return 8000

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_SERVICE_PORT value '{port_str}'. "
            f"Must be an integer between 1 and 65535. Using default value 8000.",
            UserWarning,
        )
        return 8000


def _get_service_workers() -> int:
    """
    Get service workers from environment with validation.

    Validates range (1-100) with fallback to default 4.

    Returns:
        int: Service workers count (1-100)
    """
    try:
        workers_str = os.getenv("KWE_SERVICE_WORKERS", "4")

        # Handle empty string case
        if not workers_str or workers_str.strip() == "":
            return 4

        workers = int(workers_str)

        # Validate range: 1-100
        if 1 <= workers <= 100:
            return workers
        else:
            # Log warning for out-of-range values
            import warnings

            warnings.warn(
                f"KWE_SERVICE_WORKERS value {workers} is outside valid range (1-100). "
                f"Using default value 4.",
                UserWarning,
            )
            return 4

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_SERVICE_WORKERS value '{workers_str}'. "
            f"Must be an integer between 1 and 100. Using default value 4.",
            UserWarning,
        )
        return 4


def _get_service_timeout() -> int:
    """
    Get service timeout from environment with validation.

    Validates range (1-3600) with fallback to default 300.

    Returns:
        int: Service timeout in seconds (1-3600)
    """
    try:
        timeout_str = os.getenv("KWE_SERVICE_TIMEOUT", "300")

        # Handle empty string case
        if not timeout_str or timeout_str.strip() == "":
            return 300

        timeout = int(timeout_str)

        # Validate range: 1-3600 seconds (1 hour max)
        if 1 <= timeout <= 3600:
            return timeout
        else:
            # Log warning for out-of-range values
            import warnings

            warnings.warn(
                f"KWE_SERVICE_TIMEOUT value {timeout} is outside valid range (1-3600 seconds). "
                f"Using default value 300 seconds.",
                UserWarning,
            )
            return 300

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_SERVICE_TIMEOUT value '{timeout_str}'. "
            f"Must be an integer between 1 and 3600 seconds. Using default value 300 seconds.",
            UserWarning,
        )
        return 300


def _get_docs_path() -> str:
    """
    Get documentation path from environment with validation.

    Uses KWE server root to construct portable default path.

    Returns:
        str: Documentation path (absolute or relative)
    """
    try:
        docs_path_str = os.getenv("KWE_DOCS_PATH", "")

        # Handle empty string case - use KWE server root default
        if not docs_path_str or docs_path_str.strip() == "":
            # Use dynamic KWE server root for portability (where docs/ directory is located)
            kwe_root = get_kwe_server_root()
            return str(kwe_root / "docs")

        # Return the custom path as-is (user is responsible for validity)
        return docs_path_str.strip()

    except Exception:
        # Fallback to KWE server root default on any error
        try:
            kwe_root = get_kwe_server_root()
            return str(kwe_root / "docs")
        except Exception:
            # Final fallback if KWE server root detection fails
            return "/tmp/kwe_docs"


def _get_memory_feedback_endpoint() -> str:
    """
    Get memory feedback endpoint from environment with validation.

    Environment Variable: KWE_MEMORY_FEEDBACK_ENDPOINT
    Default: http://localhost:8766/memory/feedback

    Returns:
        str: Memory feedback endpoint URL
    
    MED-044: Enhanced URL validation for configurable service endpoints
    """
    try:
        endpoint_str = os.getenv("KWE_MEMORY_FEEDBACK_ENDPOINT", "")

        # Handle empty string case - use default endpoint
        if not endpoint_str or endpoint_str.strip() == "":
            return "http://localhost:8766/memory/feedback"

        # Enhanced URL validation and normalization
        endpoint = endpoint_str.strip()

        # Enhanced validation for invalid protocols and malformed URLs
        if not endpoint.startswith(("http://", "https://")):
            # Log warning for invalid URL format
            import warnings
            warnings.warn(
                f"KWE_MEMORY_FEEDBACK_ENDPOINT value '{endpoint}' does not appear to be a valid URL. "
                f"Using default endpoint 'http://localhost:8766/memory/feedback'.",
                UserWarning,
            )
            return "http://localhost:8766/memory/feedback"
        
        # Check for incomplete URLs (e.g., "http://")
        if endpoint in ("http://", "https://"):
            import warnings
            warnings.warn(
                f"KWE_MEMORY_FEEDBACK_ENDPOINT value '{endpoint}' does not appear to be a valid URL. "
                f"Using default endpoint 'http://localhost:8766/memory/feedback'.",
                UserWarning,
            )
            return "http://localhost:8766/memory/feedback"
        
        # Endpoint URLs preserve their paths (no trailing slash removal)
        return endpoint

    except Exception:
        # Fallback to default endpoint on any error
        return "http://localhost:8766/memory/feedback"


def _get_template_cache_size() -> int:
    """
    Get template cache size from environment with validation.

    Validates positive integer with fallback to default 1000.

    Returns:
        int: Template cache size (positive integer)
    """
    try:
        cache_size_str = os.getenv("KWE_TEMPLATE_CACHE_SIZE", "1000")

        # Handle empty string case
        if not cache_size_str or cache_size_str.strip() == "":
            return 1000

        cache_size = int(float(cache_size_str))  # Handle float strings

        # Validate positive integer
        if cache_size > 0:
            return cache_size
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"KWE_TEMPLATE_CACHE_SIZE value {cache_size} must be positive. "
                f"Using default value 1000.",
                UserWarning,
            )
            return 1000

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_TEMPLATE_CACHE_SIZE value '{cache_size_str}'. "
            f"Must be a positive integer. Using default value 1000.",
            UserWarning,
        )
        return 1000


def _get_performance_cache_size() -> int:
    """
    Get performance cache size from environment with validation.

    Validates positive integer with fallback to default 500.

    Returns:
        int: Performance cache size (positive integer)
    """
    try:
        cache_size_str = os.getenv("KWE_PERFORMANCE_CACHE_SIZE", "500")

        # Handle empty string case
        if not cache_size_str or cache_size_str.strip() == "":
            return 500

        cache_size = int(float(cache_size_str))  # Handle float strings

        # Validate positive integer
        if cache_size > 0:
            return cache_size
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"KWE_PERFORMANCE_CACHE_SIZE value {cache_size} must be positive. "
                f"Using default value 500.",
                UserWarning,
            )
            return 500

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_PERFORMANCE_CACHE_SIZE value '{cache_size_str}'. "
            f"Must be a positive integer. Using default value 500.",
            UserWarning,
        )
        return 500


def _get_adaptation_history_size() -> int:
    """
    Get adaptation history cache size from environment with validation.

    Validates positive integer with fallback to default 200.

    Returns:
        int: Adaptation history cache size (positive integer)
    """
    try:
        cache_size_str = os.getenv("KWE_ADAPTATION_HISTORY_SIZE", "200")

        # Handle empty string case
        if not cache_size_str or cache_size_str.strip() == "":
            return 200

        cache_size = int(float(cache_size_str))  # Handle float strings

        # Validate positive integer
        if cache_size > 0:
            return cache_size
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"KWE_ADAPTATION_HISTORY_SIZE value {cache_size} must be positive. "
                f"Using default value 200.",
                UserWarning,
            )
            return 200

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_ADAPTATION_HISTORY_SIZE value '{cache_size_str}'. "
            f"Must be a positive integer. Using default value 200.",
            UserWarning,
        )
        return 200


def _get_prediction_cache_size() -> int:
    """
    Get prediction cache size from environment with validation.

    Validates positive integer with fallback to default 1000.

    Returns:
        int: Prediction cache size (positive integer)
    """
    try:
        cache_size_str = os.getenv("KWE_PREDICTION_CACHE_SIZE", "1000")

        # Handle empty string case
        if not cache_size_str or cache_size_str.strip() == "":
            return 1000

        cache_size = int(float(cache_size_str))  # Handle float strings

        # Validate positive integer
        if cache_size > 0:
            return cache_size
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"KWE_PREDICTION_CACHE_SIZE value {cache_size} must be positive. "
                f"Using default value 1000.",
                UserWarning,
            )
            return 1000

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_PREDICTION_CACHE_SIZE value '{cache_size_str}'. "
            f"Must be a positive integer. Using default value 1000.",
            UserWarning,
        )
        return 1000


def _get_redis_cache_size_mb() -> int:
    """
    Get Redis cache size in MB from environment with validation.

    Validates positive integer with fallback to default 512MB.

    Returns:
        int: Redis cache size in MB (positive integer)
    """
    try:
        cache_size_str = os.getenv("KWE_REDIS_CACHE_SIZE_MB", "512")

        # Handle empty string case
        if not cache_size_str or cache_size_str.strip() == "":
            return 512

        cache_size = int(float(cache_size_str))  # Handle float strings

        # Validate positive integer
        if cache_size > 0:
            return cache_size
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"KWE_REDIS_CACHE_SIZE_MB value {cache_size} must be positive. "
                f"Using default value 512.",
                UserWarning,
            )
            return 512

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_REDIS_CACHE_SIZE_MB value '{cache_size_str}'. "
            f"Must be a positive integer. Using default value 512.",
            UserWarning,
        )
        return 512


def _get_max_sequential_prefetch_items() -> int:
    """
    Get maximum sequential prefetch items from environment with validation.

    Returns:
        int: Maximum sequential prefetch items (default: 5)
    """
    try:
        items_str = os.getenv("KWE_MAX_SEQUENTIAL_PREFETCH_ITEMS", "5")
        if not items_str or items_str.strip() == "":
            return 5
        items = int(float(items_str))
        return max(1, min(items, 20))  # Clamp between 1 and 20
    except (ValueError, TypeError):
        return 5


def _get_sequential_pattern_min_length() -> int:
    """
    Get sequential pattern minimum length from environment with validation.

    Returns:
        int: Sequential pattern minimum length (default: 3)
    """
    try:
        length_str = os.getenv("KWE_SEQUENTIAL_PATTERN_MIN_LENGTH", "3")
        if not length_str or length_str.strip() == "":
            return 3
        length = int(float(length_str))
        return max(2, min(length, 10))  # Clamp between 2 and 10
    except (ValueError, TypeError):
        return 3


def _get_max_prefetch_queue_size() -> int:
    """
    Get maximum prefetch queue size from environment with validation.

    Returns:
        int: Maximum prefetch queue size (default: 50)
    """
    try:
        size_str = os.getenv("KWE_MAX_PREFETCH_QUEUE_SIZE", "50")
        if not size_str or size_str.strip() == "":
            return 50
        size = int(float(size_str))
        return max(10, min(size, 1000))  # Clamp between 10 and 1000
    except (ValueError, TypeError):
        return 50


def _get_max_concurrent_prefetches() -> int:
    """
    Get maximum concurrent prefetches from environment with validation.

    Returns:
        int: Maximum concurrent prefetches (default: 3)
    """
    try:
        concurrent_str = os.getenv("KWE_MAX_CONCURRENT_PREFETCHES", "3")
        if not concurrent_str or concurrent_str.strip() == "":
            return 3
        concurrent = int(float(concurrent_str))
        return max(1, min(concurrent, 20))  # Clamp between 1 and 20
    except (ValueError, TypeError):
        return 3


def _get_prefetch_timeout_seconds() -> int:
    """
    Get prefetch timeout in seconds from environment with validation.

    Returns:
        int: Prefetch timeout in seconds (default: 30)
    """
    try:
        timeout_str = os.getenv("KWE_PREFETCH_TIMEOUT_SECONDS", "30")
        if not timeout_str or timeout_str.strip() == "":
            return 30
        timeout = int(float(timeout_str))
        return max(5, min(timeout, 300))  # Clamp between 5 and 300 seconds
    except (ValueError, TypeError):
        return 30


def _get_min_confidence_threshold() -> float:
    """
    Get minimum confidence threshold from environment with validation.

    Returns:
        float: Minimum confidence threshold (default: 0.6)
    """
    try:
        threshold_str = os.getenv("KWE_MIN_CONFIDENCE_THRESHOLD", "0.6")
        if not threshold_str or threshold_str.strip() == "":
            return 0.6
        threshold = float(threshold_str)
        return max(0.1, min(threshold, 1.0))  # Clamp between 0.1 and 1.0
    except (ValueError, TypeError):
        return 0.6


def _get_max_prefetch_bandwidth_mb() -> int:
    """
    Get maximum prefetch bandwidth in MB from environment with validation.

    Returns:
        int: Maximum prefetch bandwidth in MB (default: 100)
    """
    try:
        bandwidth_str = os.getenv("KWE_MAX_PREFETCH_BANDWIDTH_MB", "100")
        if not bandwidth_str or bandwidth_str.strip() == "":
            return 100
        bandwidth = int(float(bandwidth_str))
        return max(10, min(bandwidth, 10000))  # Clamp between 10 and 10000 MB
    except (ValueError, TypeError):
        return 100


def _get_max_prefetch_memory_mb() -> int:
    """
    Get maximum prefetch memory in MB from environment with validation.

    Returns:
        int: Maximum prefetch memory in MB (default: 200)
    """
    try:
        memory_str = os.getenv("KWE_MAX_PREFETCH_MEMORY_MB", "200")
        if not memory_str or memory_str.strip() == "":
            return 200
        memory = int(float(memory_str))
        return max(50, min(memory, 8192))  # Clamp between 50 and 8192 MB
    except (ValueError, TypeError):
        return 200


def _get_frequency_decay_rate() -> float:
    """
    Get frequency decay rate from environment with validation.

    Returns:
        float: Frequency decay rate (default: 0.9)
    """
    try:
        decay_str = os.getenv("KWE_FREQUENCY_DECAY_RATE", "0.9")
        if not decay_str or decay_str.strip() == "":
            return 0.9
        decay = float(decay_str)
        return max(0.1, min(decay, 1.0))  # Clamp between 0.1 and 1.0
    except (ValueError, TypeError):
        return 0.9


def _get_scale_check_interval() -> int:
    """
    Get scale check interval from environment with validation.

    Returns:
        int: Scale check interval in seconds (default: 30)
    """
    try:
        interval_str = os.getenv("KWE_SCALE_CHECK_INTERVAL", "30")
        if not interval_str or interval_str.strip() == "":
            return 30
        interval = int(float(interval_str))  # Handle float strings
        if interval > 0:
            return interval
        else:
            import warnings

            warnings.warn(
                f"KWE_SCALE_CHECK_INTERVAL value {interval} must be positive. "
                f"Using default value 30.",
                UserWarning,
            )
            return 30
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_SCALE_CHECK_INTERVAL value '{interval_str}'. "
            f"Must be a positive integer. Using default value 30.",
            UserWarning,
        )
        return 30


def _get_insight_flush_interval() -> int:
    """
    Get insight flush interval from environment with validation.

    Returns:
        int: Insight flush interval in seconds (default: 60)
    """
    try:
        interval_str = os.getenv("KWE_INSIGHT_FLUSH_INTERVAL", "60")
        if not interval_str or interval_str.strip() == "":
            return 60
        interval = int(float(interval_str))  # Handle float strings
        if interval > 0:
            return interval
        else:
            import warnings

            warnings.warn(
                f"KWE_INSIGHT_FLUSH_INTERVAL value {interval} must be positive. "
                f"Using default value 60.",
                UserWarning,
            )
            return 60
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_INSIGHT_FLUSH_INTERVAL value '{interval_str}'. "
            f"Must be a positive integer. Using default value 60.",
            UserWarning,
        )
        return 60


def _get_metrics_flush_interval() -> int:
    """
    Get metrics flush interval from environment with validation.

    Returns:
        int: Metrics flush interval in seconds (default: 300)
    """
    try:
        interval_str = os.getenv("KWE_METRICS_FLUSH_INTERVAL", "300")
        if not interval_str or interval_str.strip() == "":
            return 300
        interval = int(float(interval_str))  # Handle float strings
        if interval > 0:
            return interval
        else:
            import warnings

            warnings.warn(
                f"KWE_METRICS_FLUSH_INTERVAL value {interval} must be positive. "
                f"Using default value 300.",
                UserWarning,
            )
            return 300
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_METRICS_FLUSH_INTERVAL value '{interval_str}'. "
            f"Must be a positive integer. Using default value 300.",
            UserWarning,
        )
        return 300


def _get_metrics_update_interval() -> int:
    """
    Get metrics update interval from environment with validation.

    Returns:
        int: Metrics update interval in operations (default: 100)
    """
    try:
        interval_str = os.getenv("KWE_METRICS_UPDATE_INTERVAL", "100")
        if not interval_str or interval_str.strip() == "":
            return 100
        interval = int(float(interval_str))  # Handle float strings
        if interval > 0:
            return interval
        else:
            import warnings

            warnings.warn(
                f"KWE_METRICS_UPDATE_INTERVAL value {interval} must be positive. "
                f"Using default value 100.",
                UserWarning,
            )
            return 100
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_METRICS_UPDATE_INTERVAL value '{interval_str}'. "
            f"Must be a positive integer. Using default value 100.",
            UserWarning,
        )
        return 100


def _get_max_retries() -> int:
    """
    Get maximum retry attempts from environment with validation.

    Returns:
        int: Maximum retry attempts (default: 3)
    """
    try:
        retries_str = os.getenv("KWE_MAX_RETRIES", "3")
        if not retries_str or retries_str.strip() == "":
            return 3
        retries = int(float(retries_str))  # Handle float strings
        if retries > 0:
            return retries
        else:
            import warnings

            warnings.warn(
                f"KWE_MAX_RETRIES value {retries} must be positive. "
                f"Using default value 3.",
                UserWarning,
            )
            return 3
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_MAX_RETRIES value '{retries_str}'. "
            f"Must be a positive integer. Using default value 3.",
            UserWarning,
        )
        return 3


def _get_recovery_max_retries() -> int:
    """
    Get recovery maximum retry attempts from environment with validation.

    Returns:
        int: Recovery maximum retry attempts (default: 5)
    """
    try:
        retries_str = os.getenv("KWE_RECOVERY_MAX_RETRIES", "5")
        if not retries_str or retries_str.strip() == "":
            return 5
        retries = int(float(retries_str))  # Handle float strings
        if retries > 0:
            return retries
        else:
            import warnings

            warnings.warn(
                f"KWE_RECOVERY_MAX_RETRIES value {retries} must be positive. "
                f"Using default value 5.",
                UserWarning,
            )
            return 5
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_RECOVERY_MAX_RETRIES value '{retries_str}'. "
            f"Must be a positive integer. Using default value 5.",
            UserWarning,
        )
        return 5


def _get_circuit_failure_threshold() -> int:
    """
    Get circuit breaker failure threshold from environment with validation.

    Returns:
        int: Circuit breaker failure threshold (default: 5)
    """
    try:
        threshold_str = os.getenv("KWE_CIRCUIT_FAILURE_THRESHOLD", "5")
        if not threshold_str or threshold_str.strip() == "":
            return 5
        threshold = int(float(threshold_str))  # Handle float strings
        if threshold > 0:
            return threshold
        else:
            import warnings

            warnings.warn(
                f"KWE_CIRCUIT_FAILURE_THRESHOLD value {threshold} must be positive. "
                f"Using default value 5.",
                UserWarning,
            )
            return 5
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_CIRCUIT_FAILURE_THRESHOLD value '{threshold_str}'. "
            f"Must be a positive integer. Using default value 5.",
            UserWarning,
        )
        return 5


def _get_bridge_max_attempts() -> int:
    """
    Get memory bridge maximum attempts from environment with validation.

    Returns:
        int: Memory bridge maximum attempts (default: 3)
    """
    try:
        attempts_str = os.getenv("KWE_BRIDGE_MAX_ATTEMPTS", "3")
        if not attempts_str or attempts_str.strip() == "":
            return 3
        attempts = int(float(attempts_str))  # Handle float strings
        if attempts > 0:
            return attempts
        else:
            import warnings

            warnings.warn(
                f"KWE_BRIDGE_MAX_ATTEMPTS value {attempts} must be positive. "
                f"Using default value 3.",
                UserWarning,
            )
            return 3
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_BRIDGE_MAX_ATTEMPTS value '{attempts_str}'. "
            f"Must be a positive integer. Using default value 3.",
            UserWarning,
        )
        return 3


def _get_memory_feedback_timeout() -> int:
    """
    Get memory feedback timeout from environment with validation.

    Validates range (1-300 seconds) with fallback to default 60 seconds.

    Returns:
        int: Memory feedback timeout in seconds (1-300)
    """
    try:
        timeout_str = os.getenv("KWE_MEMORY_FEEDBACK_TIMEOUT", "60")

        # Handle empty string case
        if not timeout_str or timeout_str.strip() == "":
            return 60

        timeout = int(timeout_str)

        # Validate range: 1-300 seconds (5 minutes max)
        if 1 <= timeout <= 300:
            return timeout
        else:
            # Log warning for out-of-range values
            import warnings

            warnings.warn(
                f"KWE_MEMORY_FEEDBACK_TIMEOUT value {timeout} is outside valid range (1-300 seconds). "
                f"Using default value 60 seconds.",
                UserWarning,
            )
            return 60

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_MEMORY_FEEDBACK_TIMEOUT value '{timeout_str}'. "
            f"Must be an integer between 1 and 300 seconds. Using default value 60 seconds.",
            UserWarning,
        )
        return 60


def _get_batch_size() -> int:
    """
    Get batch size from environment with validation.

    Validates positive integer with fallback to default 10.

    Returns:
        int: Batch size (minimum 1)
    """
    try:
        batch_size_str = os.getenv("KWE_BATCH_SIZE", "10")

        # Handle empty string case
        if not batch_size_str or batch_size_str.strip() == "":
            return 10

        batch_size = int(float(batch_size_str))  # Handle float strings
        if batch_size > 0:
            return batch_size
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"KWE_BATCH_SIZE value {batch_size} must be positive. Using default value 10.",
                UserWarning,
            )
            return 10

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_BATCH_SIZE value '{batch_size_str}'. "
            f"Must be a positive integer. Using default value 10.",
            UserWarning,
        )
        return 10


def _get_batch_timeout_ms() -> int:
    """
    Get batch timeout in milliseconds from environment with validation.

    Validates positive integer with fallback to default 100ms.

    Returns:
        int: Batch timeout in milliseconds (minimum 1)
    """
    try:
        timeout_str = os.getenv("KWE_BATCH_TIMEOUT_MS", "100")

        # Handle empty string case
        if not timeout_str or timeout_str.strip() == "":
            return 100

        timeout = int(float(timeout_str))  # Handle float strings
        if timeout > 0:
            return timeout
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"KWE_BATCH_TIMEOUT_MS value {timeout} must be positive. Using default value 100.",
                UserWarning,
            )
            return 100

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_BATCH_TIMEOUT_MS value '{timeout_str}'. "
            f"Must be a positive integer. Using default value 100.",
            UserWarning,
        )
        return 100


def _get_chunk_size() -> int:
    """
    Get chunk size from environment with validation.

    Validates positive integer with fallback to default 4096.

    Returns:
        int: Chunk size (minimum 1)
    """
    try:
        chunk_size_str = os.getenv("KWE_CHUNK_SIZE", "4096")

        # Handle empty string case
        if not chunk_size_str or chunk_size_str.strip() == "":
            return 4096

        chunk_size = int(float(chunk_size_str))  # Handle float strings
        if chunk_size > 0:
            return chunk_size
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"KWE_CHUNK_SIZE value {chunk_size} must be positive. Using default value 4096.",
                UserWarning,
            )
            return 4096

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_CHUNK_SIZE value '{chunk_size_str}'. "
            f"Must be a positive integer. Using default value 4096.",
            UserWarning,
        )
        return 4096


def _get_streaming_chunk_size() -> int:
    """
    Get streaming chunk size from environment with validation.

    Validates positive integer with fallback to default 50.

    Returns:
        int: Streaming chunk size (minimum 1)
    """
    try:
        chunk_size_str = os.getenv("KWE_STREAMING_CHUNK_SIZE", "50")

        # Handle empty string case
        if not chunk_size_str or chunk_size_str.strip() == "":
            return 50

        chunk_size = int(float(chunk_size_str))  # Handle float strings
        if chunk_size > 0:
            return chunk_size
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"KWE_STREAMING_CHUNK_SIZE value {chunk_size} must be positive. Using default value 50.",
                UserWarning,
            )
            return 50

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_STREAMING_CHUNK_SIZE value '{chunk_size_str}'. "
            f"Must be a positive integer. Using default value 50.",
            UserWarning,
        )
        return 50


def _get_timeout_min_timeout() -> float:
    """
    Get timeout minimum timeout from environment with validation.

    Validates positive float with fallback to default 120.0 seconds.

    Returns:
        float: Minimum timeout in seconds (minimum 0.1)
    """
    try:
        timeout_str = os.getenv("KWE_TIMEOUT_MIN_TIMEOUT", "120.0")

        # Handle empty string case
        if not timeout_str or timeout_str.strip() == "":
            return 120.0

        timeout = float(timeout_str)
        if timeout > 0:
            return timeout
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_MIN_TIMEOUT value '{timeout_str}'. "
                f"Must be a positive number. Using default value 120.0.",
                UserWarning,
            )
            return 120.0

    except (ValueError, TypeError):
        # Fallback to default timeout on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_MIN_TIMEOUT value '{timeout_str}'. "
            f"Must be a positive number. Using default value 120.0.",
            UserWarning,
        )
        return 120.0


def _get_timeout_complexity_multiplier() -> float:
    """
    Get timeout complexity multiplier from environment with validation.

    Validates positive float with fallback to default 1.5.

    Returns:
        float: Complexity multiplier (minimum 0.1)
    """
    try:
        multiplier_str = os.getenv("KWE_TIMEOUT_COMPLEXITY_MULTIPLIER", "1.5")

        # Handle empty string case
        if not multiplier_str or multiplier_str.strip() == "":
            return 1.5

        multiplier = float(multiplier_str)
        if multiplier > 0:
            return multiplier
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_COMPLEXITY_MULTIPLIER value '{multiplier_str}'. "
                f"Must be a positive number. Using default value 1.5.",
                UserWarning,
            )
            return 1.5

    except (ValueError, TypeError):
        # Fallback to default multiplier on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_COMPLEXITY_MULTIPLIER value '{multiplier_str}'. "
            f"Must be a positive number. Using default value 1.5.",
            UserWarning,
        )
        return 1.5


def _get_timeout_retry_multiplier() -> float:
    """
    Get timeout retry multiplier from environment with validation.

    Validates positive float with fallback to default 1.3.

    Returns:
        float: Retry multiplier (minimum 0.1)
    """
    try:
        multiplier_str = os.getenv("KWE_TIMEOUT_RETRY_MULTIPLIER", "1.3")

        # Handle empty string case
        if not multiplier_str or multiplier_str.strip() == "":
            return 1.3

        multiplier = float(multiplier_str)
        if multiplier > 0:
            return multiplier
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_RETRY_MULTIPLIER value '{multiplier_str}'. "
                f"Must be a positive number. Using default value 1.3.",
                UserWarning,
            )
            return 1.3

    except (ValueError, TypeError):
        # Fallback to default multiplier on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_RETRY_MULTIPLIER value '{multiplier_str}'. "
            f"Must be a positive number. Using default value 1.3.",
            UserWarning,
        )
        return 1.3


def _get_timeout_performance_threshold() -> float:
    """
    Get timeout performance threshold from environment with validation.

    Validates float between 0.0 and 1.0 with fallback to default 0.8.

    Returns:
        float: Performance threshold (0.0 to 1.0)
    """
    try:
        threshold_str = os.getenv("KWE_TIMEOUT_PERFORMANCE_THRESHOLD", "0.8")

        # Handle empty string case
        if not threshold_str or threshold_str.strip() == "":
            return 0.8

        threshold = float(threshold_str)
        if 0.0 <= threshold <= 1.0:
            return threshold
        else:
            # Log warning for out-of-range values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_PERFORMANCE_THRESHOLD value '{threshold_str}'. "
                f"Must be between 0.0 and 1.0. Using default value 0.8.",
                UserWarning,
            )
            return 0.8

    except (ValueError, TypeError):
        # Fallback to default threshold on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_PERFORMANCE_THRESHOLD value '{threshold_str}'. "
            f"Must be a number between 0.0 and 1.0. Using default value 0.8.",
            UserWarning,
        )
        return 0.8


def _get_timeout_max_event_history() -> int:
    """
    Get timeout max event history from environment with validation.

    Validates positive integer with fallback to default 1000.

    Returns:
        int: Maximum event history size (minimum 1)
    """
    try:
        history_str = os.getenv("KWE_TIMEOUT_MAX_EVENT_HISTORY", "1000")

        # Handle empty string case
        if not history_str or history_str.strip() == "":
            return 1000

        history = int(float(history_str))  # Handle float strings
        if history > 0:
            return history
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_MAX_EVENT_HISTORY value '{history_str}'. "
                f"Must be a positive integer. Using default value 1000.",
                UserWarning,
            )
            return 1000

    except (ValueError, TypeError):
        # Fallback to default history size on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_MAX_EVENT_HISTORY value '{history_str}'. "
            f"Must be a positive integer. Using default value 1000.",
            UserWarning,
        )
        return 1000


def _get_timeout_adaptive_window_size() -> int:
    """
    Get timeout adaptive window size from environment with validation.

    Validates positive integer with fallback to default 50.

    Returns:
        int: Adaptive window size (minimum 1)
    """
    try:
        window_str = os.getenv("KWE_TIMEOUT_ADAPTIVE_WINDOW_SIZE", "50")

        # Handle empty string case
        if not window_str or window_str.strip() == "":
            return 50

        window = int(float(window_str))  # Handle float strings
        if window > 0:
            return window
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_ADAPTIVE_WINDOW_SIZE value '{window_str}'. "
                f"Must be a positive integer. Using default value 50.",
                UserWarning,
            )
            return 50

    except (ValueError, TypeError):
        # Fallback to default window size on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_ADAPTIVE_WINDOW_SIZE value '{window_str}'. "
            f"Must be a positive integer. Using default value 50.",
            UserWarning,
        )
        return 50


def _get_timeout_complexity_classification_base() -> float:
    """
    Get timeout complexity classification base from environment with validation.

    Validates positive float with fallback to default 30.0 seconds.

    Returns:
        float: Complexity classification base timeout (minimum 1.0 seconds)
    """
    try:
        timeout_str = os.getenv("KWE_TIMEOUT_COMPLEXITY_CLASSIFICATION_BASE", "30.0")

        # Handle empty string case
        if not timeout_str or timeout_str.strip() == "":
            return 30.0

        timeout = float(timeout_str)
        if timeout > 0:
            return timeout
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_COMPLEXITY_CLASSIFICATION_BASE value '{timeout_str}'. "
                f"Must be a positive number. Using default value 30.0.",
                UserWarning,
            )
            return 30.0

    except (ValueError, TypeError):
        # Fallback to default timeout on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_COMPLEXITY_CLASSIFICATION_BASE value '{timeout_str}'. "
            f"Must be a positive number. Using default value 30.0.",
            UserWarning,
        )
        return 30.0


def _get_timeout_knowledge_assessment_base() -> float:
    """
    Get timeout knowledge assessment base from environment with validation.

    Validates positive float with fallback to default 45.0 seconds.

    Returns:
        float: Knowledge assessment base timeout (minimum 1.0 seconds)
    """
    try:
        timeout_str = os.getenv("KWE_TIMEOUT_KNOWLEDGE_ASSESSMENT_BASE", "45.0")

        # Handle empty string case
        if not timeout_str or timeout_str.strip() == "":
            return 45.0

        timeout = float(timeout_str)
        if timeout > 0:
            return timeout
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_KNOWLEDGE_ASSESSMENT_BASE value '{timeout_str}'. "
                f"Must be a positive number. Using default value 45.0.",
                UserWarning,
            )
            return 45.0

    except (ValueError, TypeError):
        # Fallback to default timeout on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_KNOWLEDGE_ASSESSMENT_BASE value '{timeout_str}'. "
            f"Must be a positive number. Using default value 45.0.",
            UserWarning,
        )
        return 45.0


def _get_timeout_complex_reasoning_base() -> float:
    """
    Get timeout complex reasoning base from environment with validation.

    Validates positive float with fallback to default 120.0 seconds.

    Returns:
        float: Complex reasoning base timeout (minimum 1.0 seconds)
    """
    try:
        timeout_str = os.getenv("KWE_TIMEOUT_COMPLEX_REASONING_BASE", "120.0")

        # Handle empty string case
        if not timeout_str or timeout_str.strip() == "":
            return 120.0

        timeout = float(timeout_str)
        if timeout > 0:
            return timeout
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_COMPLEX_REASONING_BASE value '{timeout_str}'. "
                f"Must be a positive number. Using default value 120.0.",
                UserWarning,
            )
            return 120.0

    except (ValueError, TypeError):
        # Fallback to default timeout on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_COMPLEX_REASONING_BASE value '{timeout_str}'. "
            f"Must be a positive number. Using default value 120.0.",
            UserWarning,
        )
        return 120.0


def _get_timeout_strategy_development_base() -> float:
    """
    Get timeout strategy development base from environment with validation.

    Validates positive float with fallback to default 90.0 seconds.

    Returns:
        float: Strategy development base timeout (minimum 1.0 seconds)
    """
    try:
        timeout_str = os.getenv("KWE_TIMEOUT_STRATEGY_DEVELOPMENT_BASE", "90.0")

        # Handle empty string case
        if not timeout_str or timeout_str.strip() == "":
            return 90.0

        timeout = float(timeout_str)
        if timeout > 0:
            return timeout
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_STRATEGY_DEVELOPMENT_BASE value '{timeout_str}'. "
                f"Must be a positive number. Using default value 90.0.",
                UserWarning,
            )
            return 90.0

    except (ValueError, TypeError):
        # Fallback to default timeout on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_STRATEGY_DEVELOPMENT_BASE value '{timeout_str}'. "
            f"Must be a positive number. Using default value 90.0.",
            UserWarning,
        )
        return 90.0


def _get_timeout_agent_routing_base() -> float:
    """
    Get timeout agent routing base from environment with validation.

    Validates positive float with fallback to default 120.0 seconds.

    Returns:
        float: Agent routing base timeout (minimum 1.0 seconds)
    """
    try:
        timeout_str = os.getenv("KWE_TIMEOUT_AGENT_ROUTING_BASE", "120.0")

        # Handle empty string case
        if not timeout_str or timeout_str.strip() == "":
            return 120.0

        timeout = float(timeout_str)
        if timeout > 0:
            return timeout
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_AGENT_ROUTING_BASE value '{timeout_str}'. "
                f"Must be a positive number. Using default value 120.0.",
                UserWarning,
            )
            return 120.0

    except (ValueError, TypeError):
        # Fallback to default timeout on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_AGENT_ROUTING_BASE value '{timeout_str}'. "
            f"Must be a positive number. Using default value 120.0.",
            UserWarning,
        )
        return 120.0


def _get_timeout_agent_selection_base() -> float:
    """
    Get timeout agent selection base from environment with validation.

    Validates positive float with fallback to default 60.0 seconds.

    Returns:
        float: Agent selection base timeout (minimum 1.0 seconds)
    """
    try:
        timeout_str = os.getenv("KWE_TIMEOUT_AGENT_SELECTION_BASE", "60.0")

        # Handle empty string case
        if not timeout_str or timeout_str.strip() == "":
            return 60.0

        timeout = float(timeout_str)
        if timeout > 0:
            return timeout
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_AGENT_SELECTION_BASE value '{timeout_str}'. "
                f"Must be a positive number. Using default value 60.0.",
                UserWarning,
            )
            return 60.0

    except (ValueError, TypeError):
        # Fallback to default timeout on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_AGENT_SELECTION_BASE value '{timeout_str}'. "
            f"Must be a positive number. Using default value 60.0.",
            UserWarning,
        )
        return 60.0


def _get_timeout_max_global() -> float:
    """
    Get timeout max global from environment with validation.

    Validates positive float with fallback to default 600.0 seconds.

    Returns:
        float: Maximum global timeout (minimum 1.0 seconds)
    """
    try:
        timeout_str = os.getenv("KWE_TIMEOUT_MAX_GLOBAL", "600.0")

        # Handle empty string case
        if not timeout_str or timeout_str.strip() == "":
            return 600.0

        timeout = float(timeout_str)
        if timeout > 0:
            return timeout
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_MAX_GLOBAL value '{timeout_str}'. "
                f"Must be a positive number. Using default value 600.0.",
                UserWarning,
            )
            return 600.0

    except (ValueError, TypeError):
        # Fallback to default timeout on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_MAX_GLOBAL value '{timeout_str}'. "
            f"Must be a positive number. Using default value 600.0.",
            UserWarning,
        )
        return 600.0


def _get_timeout_min_global() -> float:
    """
    Get timeout min global from environment with validation.

    Validates positive float with fallback to default 10.0 seconds.

    Returns:
        float: Minimum global timeout (minimum 1.0 seconds)
    """
    try:
        timeout_str = os.getenv("KWE_TIMEOUT_MIN_GLOBAL", "10.0")

        # Handle empty string case
        if not timeout_str or timeout_str.strip() == "":
            return 10.0

        timeout = float(timeout_str)
        if timeout > 0:
            return timeout
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_TIMEOUT_MIN_GLOBAL value '{timeout_str}'. "
                f"Must be a positive number. Using default value 10.0.",
                UserWarning,
            )
            return 10.0

    except (ValueError, TypeError):
        # Fallback to default timeout on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_TIMEOUT_MIN_GLOBAL value '{timeout_str}'. "
            f"Must be a positive number. Using default value 10.0.",
            UserWarning,
        )
        return 10.0


def _get_log_level() -> str:
    """
    Get log level from environment with validation.

    Validates log level against valid uvicorn/Python logging levels.

    Returns:
        str: Log level (critical, error, warning, info, debug, trace)
    """
    try:
        log_level_str = os.getenv("KWE_LOG_LEVEL", "info")

        # Handle empty string case
        if not log_level_str or log_level_str.strip() == "":
            return "info"

        # Normalize to lowercase for comparison
        log_level = log_level_str.strip().lower()

        # Valid uvicorn log levels
        valid_levels = ["critical", "error", "warning", "info", "debug", "trace"]

        if log_level in valid_levels:
            return log_level
        else:
            # Log warning for invalid log level values
            import warnings

            warnings.warn(
                f"Invalid KWE_LOG_LEVEL value '{log_level_str}'. "
                f"Must be one of: {', '.join(valid_levels)}. Using default value 'info'.",
                UserWarning,
            )
            return "info"

    except Exception:
        # Fallback to default log level on any error
        return "info"


def _get_websocket_fallback_host() -> str:
    """
    Get WebSocket fallback host from environment with validation.

    Returns:
        str: WebSocket fallback host address
    """
    host_str = os.getenv("KWE_WEBSOCKET_FALLBACK_HOST", "localhost")

    # Handle empty string case
    if not host_str or host_str.strip() == "":
        return "localhost"

    return host_str.strip()


def _get_websocket_fallback_port() -> int:
    """
    Get WebSocket fallback port from environment with validation.

    Validates range (1-65535) with fallback to default 8000.

    Returns:
        int: WebSocket fallback port (1-65535)
    """
    try:
        port_str = os.getenv("KWE_WEBSOCKET_FALLBACK_PORT", "8000")

        # Handle empty string case
        if not port_str or port_str.strip() == "":
            return 8000

        port = int(port_str)

        # Validate range: 1-65535
        if 1 <= port <= 65535:
            return port
        else:
            # Log warning for out-of-range values
            import warnings

            warnings.warn(
                f"KWE_WEBSOCKET_FALLBACK_PORT value {port} is outside valid range (1-65535). "
                f"Using default value 8000.",
                UserWarning,
            )
            return 8000

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_WEBSOCKET_FALLBACK_PORT value '{port_str}'. "
            f"Must be an integer between 1 and 65535. Using default value 8000.",
            UserWarning,
        )
        return 8000


def _get_websocket_fallback_protocol() -> str:
    """
    Get WebSocket fallback protocol from environment with validation.

    Validates protocol values ('ws' or 'wss') with fallback to 'ws'.

    Returns:
        str: WebSocket fallback protocol ('ws' for standard, 'wss' for SSL/TLS)
    """
    try:
        protocol_str = os.getenv("KWE_WEBSOCKET_FALLBACK_PROTOCOL", "ws")

        # Handle empty string case
        if not protocol_str or protocol_str.strip() == "":
            return "ws"

        protocol = protocol_str.strip().lower()

        # Validate protocol: only 'ws' or 'wss' allowed
        if protocol in ["ws", "wss"]:
            return protocol
        else:
            # Log warning for invalid protocol values
            import warnings

            warnings.warn(
                f"Invalid KWE_WEBSOCKET_FALLBACK_PROTOCOL value '{protocol}'. "
                f"Must be 'ws' or 'wss'. Using default value 'ws'.",
                UserWarning,
            )
            return "ws"

    except (ValueError, TypeError):
        # Log warning for invalid values
        import warnings

        warnings.warn(
            f"Invalid KWE_WEBSOCKET_FALLBACK_PROTOCOL value '{protocol_str}'. "
            f"Must be 'ws' or 'wss'. Using default value 'ws'.",
            UserWarning,
        )
        return "ws"


def _get_deepseek_analyzer_model() -> str:
    """
    Get deepseek analyzer model from environment with validation.

    Returns:
        str: Deepseek analyzer model name
    """
    model_str = os.getenv("KWE_DEEPSEEK_ANALYZER_MODEL", "deepseek-coder:latest")

    # Handle empty string case
    if not model_str or model_str.strip() == "":
        return "deepseek-coder:latest"

    return model_str.strip()


def _get_qdrant_content_structures_collection() -> str:
    """
    Get Qdrant content structures collection name from environment with validation.

    Returns:
        str: Qdrant content structures collection name
    """
    collection_str = os.getenv(
        "KWE_QDRANT_CONTENT_STRUCTURES_COLLECTION", "content_structures"
    )

    # Handle empty string case
    if not collection_str or collection_str.strip() == "":
        return "content_structures"

    return collection_str.strip()


def _get_qdrant_generation_patterns_collection() -> str:
    """
    Get Qdrant generation patterns collection name from environment with validation.

    Returns:
        str: Qdrant generation patterns collection name
    """
    collection_str = os.getenv(
        "KWE_QDRANT_GENERATION_PATTERNS_COLLECTION", "generation_patterns"
    )

    # Handle empty string case
    if not collection_str or collection_str.strip() == "":
        return "generation_patterns"

    return collection_str.strip()


def _get_qdrant_workflow_embeddings_collection() -> str:
    """
    Get Qdrant workflow embeddings collection name from environment with validation.

    Returns:
        str: Qdrant workflow embeddings collection name
    """
    collection_str = os.getenv(
        "KWE_QDRANT_WORKFLOW_EMBEDDINGS_COLLECTION", "kwe_workflow_embeddings"
    )

    # Handle empty string case
    if not collection_str or collection_str.strip() == "":
        return "kwe_workflow_embeddings"

    return collection_str.strip()


@dataclass
class RedisConfig:
    """Redis database configuration."""

    host: str = "localhost"
    port: int = 6380
    db: int = 0
    password: str = ""
    default_ttl: int = 3600
    socket_timeout: int = 30
    socket_connect_timeout: int = 30
    socket_keepalive: bool = True
    health_check_interval: int = field(
        default_factory=lambda: _get_redis_health_check_interval()
    )
    connection_pool_size: int = field(
        default_factory=lambda: _get_redis_connection_pool_size()
    )
    max_connections: int = field(default_factory=lambda: _get_redis_max_connections())
    protocol: str = field(default_factory=lambda: _get_redis_protocol())

    def get_redis_url(self) -> str:
        """
        Construct Redis URL with configurable protocol.

        Returns:
            str: Complete Redis URL (e.g., 'redis://localhost:6379' or 'rediss://localhost:6379')
        """
        return f"{self.protocol}://{self.host}:{self.port}"


@dataclass
class PostgresConfig:
    """PostgreSQL database configuration."""

    host: str = field(
        default_factory=lambda: os.getenv("KWE_POSTGRES_HOST", "192.168.1.119")
    )
    port: int = field(
        default_factory=lambda: int(os.getenv("KWE_POSTGRES_PORT", "5432"))
    )
    database: str = field(
        default_factory=lambda: os.getenv(
            "KWE_POSTGRES_DATABASE", "kwe_temporal_memory"
        )
    )
    user: str = field(default_factory=lambda: os.getenv("KWE_POSTGRES_USER", "post"))
    password: str = field(
        default_factory=lambda: os.getenv("KWE_POSTGRES_PASSWORD", "")
    )
    connection_pool_size: int = field(
        default_factory=lambda: _get_postgresql_connection_pool_size()
    )


@dataclass
class Neo4jConfig:
    """Neo4j database configuration."""

    host: str = field(default_factory=lambda: os.getenv("KWE_NEO4J_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("KWE_NEO4J_PORT", "7687")))
    user: str = field(default_factory=lambda: os.getenv("KWE_NEO4J_USER", "neo4j"))
    password: str = field(default_factory=lambda: os.getenv("KWE_NEO4J_PASSWORD", ""))
    connection_pool_size: int = field(
        default_factory=lambda: _get_neo4j_connection_pool_size()
    )


@dataclass
class QdrantConfig:
    """Qdrant vector database configuration."""

    host: str = field(default_factory=lambda: _get_qdrant_host())
    port: int = field(default_factory=lambda: _get_qdrant_port())
    api_key: str = field(default_factory=lambda: _get_qdrant_api_key())
    semantic_collection: str = "kwe_semantic_memory"
    content_structures_collection: str = field(
        default_factory=lambda: _get_qdrant_content_structures_collection()
    )
    generation_patterns_collection: str = field(
        default_factory=lambda: _get_qdrant_generation_patterns_collection()
    )
    workflow_embeddings_collection: str = field(
        default_factory=lambda: _get_qdrant_workflow_embeddings_collection()
    )

    def get_qdrant_url(self) -> str:
        """
        Construct Qdrant URL.

        Returns:
            str: Complete Qdrant URL (e.g., 'http://localhost:6333')
        """
        return f"http://{self.host}:{self.port}"


@dataclass
class MemoryConfig:
    """Memory system configuration."""

    state_manager_pool_size: int = field(
        default_factory=lambda: _get_memory_state_manager_pool_size()
    )
    memory_feedback_endpoint: str = field(
        default_factory=lambda: _get_memory_feedback_endpoint()
    )
    memory_feedback_timeout: int = field(
        default_factory=lambda: _get_memory_feedback_timeout()
    )


@dataclass
class PoolSizesConfig:
    """Connection pool sizes configuration.
    
    MED-045: Configurable connection pool sizes for system components
    """

    memory_bridge_pool_size: int = field(default_factory=lambda: _get_memory_bridge_pool_size())
    postgresql_connection_pool_size: int = field(default_factory=lambda: _get_postgresql_connection_pool_size())
    state_manager_max_pool_size: int = field(default_factory=lambda: _get_state_manager_max_pool_size())
    redis_connection_pool_size: int = field(default_factory=lambda: _get_redis_connection_pool_size())
    memory_aware_pool_size: int = field(default_factory=lambda: _get_memory_aware_pool_size())


@dataclass
class DatabaseConfig:
    """Database configurations container."""

    redis: RedisConfig = field(default_factory=RedisConfig)
    postgres: PostgresConfig = field(default_factory=PostgresConfig)
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)


@dataclass
class GPUConfig:
    """GPU configuration for model acceleration."""

    director_config: Dict[str, Any] = field(
        default_factory=lambda: {
            "hip_visible_devices": "0",
            "n_gpu_layers": 35,
            "use_gpu": True,
        }
    )


@dataclass
class ServiceConfig:
    """Service configuration for MCP server."""

    host: str = field(default_factory=lambda: _get_service_host())
    port: int = field(default_factory=lambda: _get_service_port())
    workers: int = field(default_factory=lambda: _get_service_workers())
    timeout: int = field(default_factory=lambda: _get_service_timeout())
    log_level: str = field(default_factory=lambda: _get_log_level())
    websocket_fallback_host: str = field(
        default_factory=lambda: _get_websocket_fallback_host()
    )
    websocket_fallback_port: int = field(
        default_factory=lambda: _get_websocket_fallback_port()
    )
    websocket_fallback_protocol: str = field(
        default_factory=lambda: _get_websocket_fallback_protocol()
    )


@dataclass
class LLMConfig:
    """
    LLM configuration for Ollama integration.
    
    Now uses centralized model configuration to eliminate hardcoded references.
    All model selection is handled through the centralized configuration system.
    """

    ollama_url: str = field(default_factory=lambda: _get_ollama_base_url())  # MED-044: Configurable Ollama URL
    
    # Default parameters - actual model is determined by centralized config
    default_temperature: float = 0.7
    default_max_tokens: int = 2000
    deepseek_analyzer_model: str = field(
        default_factory=lambda: _get_deepseek_analyzer_model()
    )

    def __post_init__(self):
        """Initialize LLM configuration with centralized model management."""
        # Note: actual model selection is handled by centralized ModelConfigurationManager
        # This class now provides only Ollama connection parameters
        
        # Validate Ollama connection parameters
        if not self.ollama_url:
            raise ValueError("LLM ollama_url cannot be empty")
        
        # Ensure ollama_url has proper format
        if not self.ollama_url.startswith(("http://", "https://")):
            self.ollama_url = f"http://{self.ollama_url}"
        
        # Ensure temperature is reasonable
        if self.default_temperature < 0 or self.default_temperature > 2:
            self.default_temperature = 0.7  # Reset to safe default
            
        # Ensure max_tokens is reasonable
        if self.default_max_tokens <= 0:
            self.default_max_tokens = 2000  # Default token limit
        elif self.default_max_tokens > 32000:
            self.default_max_tokens = 32000  # Maximum reasonable limit
            
        # Initialize model selection flags if not set
        if not hasattr(self, '_model_selection_initialized'):
            self._model_selection_initialized = True
    
    async def get_model_for_task(self, task_type: str = "default") -> str:
        """Get model for specific task using centralized configuration."""
        try:
            from core.model_config import get_model_for_task
            return await get_model_for_task(task_type)
        except ImportError:
            # Fallback for backward compatibility during migration
            return "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M"
    
    async def get_model_parameters(self, task_type: str = "default") -> Dict[str, Any]:
        """Get model parameters using centralized configuration."""
        try:
            from core.model_config import get_model_parameters
            return await get_model_parameters(task_type)
        except ImportError:
            # Fallback for backward compatibility during migration
            return {
                "temperature": self.default_temperature,
                "max_tokens": self.default_max_tokens,
                "timeout": 120
            }
    
    @property
    def default_model(self) -> str:
        """
        Backward compatibility property for default model.
        
        Note: This is synchronous and should be replaced with async get_model_for_task().
        Returns the default centralized model for immediate access.
        """
        return "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M"
    
    def get_agent_model(self, agent_type: str = "general") -> str:
        """
        Backward compatibility method for agent model retrieval.
        
        Note: This is synchronous. For async operations, use get_model_for_task().
        """
        # Map agent types to task types for centralized config
        agent_to_task_mapping = {
            "coder": "coding",
            "tester": "analysis", 
            "analyst": "analysis",
            "planner": "reasoning",
            "documenter": "document_generation",
            "validator": "analysis",
            "memory_manager": "default",
            "director": "reasoning",
            "research": "research",
            "debugger": "analysis",
            "general": "default"
        }
        
        # Return centralized model for backward compatibility
        # Real implementation should use async get_model_for_task()
        return "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M"


def _get_api_gzip_minimum_size() -> int:
    """Get configurable GZip minimum size value from config"""
    try:
        size_str = os.getenv("KWE_API_GZIP_MINIMUM_SIZE", "1000")

        # Handle empty string case
        if not size_str or size_str.strip() == "":
            return 1000

        size = int(float(size_str))  # Handle float strings
        if size > 0:
            return size
        else:
            # Log warning for non-positive values
            import warnings

            warnings.warn(
                f"Invalid KWE_API_GZIP_MINIMUM_SIZE value '{size_str}'. "
                f"Must be a positive integer. Using default value 1000.",
                UserWarning,
            )
            return 1000

    except (ValueError, TypeError):
        # Fallback to default size on conversion error
        import warnings

        warnings.warn(
            f"Invalid KWE_API_GZIP_MINIMUM_SIZE value '{size_str}'. "
            f"Must be a positive integer. Using default value 1000.",
            UserWarning,
        )
        return 1000


def _get_api_cors_allowed_origins() -> List[str]:
    """Get configurable CORS allowed origins from config"""
    try:
        origins_str = os.getenv(
            "KWE_API_CORS_ALLOWED_ORIGINS",
            "http://localhost:3000,http://localhost:8000",
        )

        # Handle empty string case
        if not origins_str or origins_str.strip() == "":
            return ["http://localhost:3000", "http://localhost:8000"]

        # Split by comma and strip whitespace
        origins = [
            origin.strip() for origin in origins_str.split(",") if origin.strip()
        ]

        # Security warning for wildcard usage
        if "*" in origins:
            import warnings

            warnings.warn(
                "Using wildcard '*' in CORS allowed origins is a security risk. "
                "Consider specifying exact origins for production environments.",
                UserWarning,
            )

        return (
            origins if origins else ["http://localhost:3000", "http://localhost:8000"]
        )

    except Exception:
        # Fallback to secure default origins on any error
        return ["http://localhost:3000", "http://localhost:8000"]


def _get_api_cors_allow_credentials() -> bool:
    """Get configurable CORS allow credentials from config"""
    try:
        credentials_str = os.getenv("KWE_API_CORS_ALLOW_CREDENTIALS", "false")

        # Handle empty string case
        if not credentials_str or credentials_str.strip() == "":
            return False

        # Convert to boolean (secure default: False)
        return credentials_str.lower().strip() in ("true", "1", "yes", "on")

    except Exception:
        # Fallback to secure default on any error
        return False


def _get_api_cors_allow_methods() -> List[str]:
    """Get configurable CORS allow methods from config"""
    try:
        methods_str = os.getenv(
            "KWE_API_CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS"
        )

        # Handle empty string case
        if not methods_str or methods_str.strip() == "":
            return ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

        # Split by comma and strip whitespace
        methods = [
            method.strip().upper()
            for method in methods_str.split(",")
            if method.strip()
        ]

        return methods if methods else ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

    except Exception:
        # Fallback to secure default methods on any error
        return ["GET", "POST", "PUT", "DELETE", "OPTIONS"]


def _get_api_cors_allow_headers() -> List[str]:
    """Get configurable CORS allow headers from config"""
    try:
        headers_str = os.getenv(
            "KWE_API_CORS_ALLOW_HEADERS", "Content-Type,Authorization"
        )

        # Handle empty string case
        if not headers_str or headers_str.strip() == "":
            return ["Content-Type", "Authorization"]

        # Split by comma and strip whitespace
        headers = [
            header.strip() for header in headers_str.split(",") if header.strip()
        ]

        return headers if headers else ["Content-Type", "Authorization"]

    except Exception:
        # Fallback to secure default headers on any error
        return ["Content-Type", "Authorization"]


@dataclass(frozen=True)
class APIConfig:
    """API middleware configuration for KWE FastAPI endpoints."""

    # GZip middleware configuration
    gzip_minimum_size: int = field(default_factory=lambda: _get_api_gzip_minimum_size())

    # CORS middleware configuration
    cors_allowed_origins: List[str] = field(
        default_factory=lambda: _get_api_cors_allowed_origins()
    )
    cors_allow_credentials: bool = field(
        default_factory=lambda: _get_api_cors_allow_credentials()
    )
    cors_allow_methods: List[str] = field(
        default_factory=lambda: _get_api_cors_allow_methods()
    )
    cors_allow_headers: List[str] = field(
        default_factory=lambda: _get_api_cors_allow_headers()
    )


@dataclass(frozen=True)
class TimeoutConfig:
    """Timeout policy configuration for KWE core components."""

    # Basic timeout values
    complex_task: int = 120  # seconds
    medium_task: int = 60  # seconds
    simple_task: int = 30  # seconds

    # Timeout policy values from timeout_manager.py
    min_timeout: float = field(default_factory=lambda: _get_timeout_min_timeout())
    complexity_multiplier: float = field(
        default_factory=lambda: _get_timeout_complexity_multiplier()
    )
    retry_multiplier: float = field(
        default_factory=lambda: _get_timeout_retry_multiplier()
    )
    performance_threshold: float = field(
        default_factory=lambda: _get_timeout_performance_threshold()
    )
    max_event_history: int = field(
        default_factory=lambda: _get_timeout_max_event_history()
    )
    adaptive_window_size: int = field(
        default_factory=lambda: _get_timeout_adaptive_window_size()
    )

    # MED-042: Configurable timeout values for timeout manager operations
    complexity_classification_base: float = field(
        default_factory=lambda: _get_timeout_complexity_classification_base()
    )
    knowledge_assessment_base: float = field(
        default_factory=lambda: _get_timeout_knowledge_assessment_base()
    )
    complex_reasoning_base: float = field(
        default_factory=lambda: _get_timeout_complex_reasoning_base()
    )
    strategy_development_base: float = field(
        default_factory=lambda: _get_timeout_strategy_development_base()
    )
    agent_routing_base: float = field(
        default_factory=lambda: _get_timeout_agent_routing_base()
    )
    agent_selection_base: float = field(
        default_factory=lambda: _get_timeout_agent_selection_base()
    )
    max_global: float = field(default_factory=lambda: _get_timeout_max_global())
    min_global: float = field(default_factory=lambda: _get_timeout_min_global())


@dataclass
class WorkspaceConfig:
    """Workspace and path configuration with dynamic path detection."""

    def __post_init__(self):
        """Initialize paths dynamically after object creation."""
        # Use dynamic path detection instead of hardcoded paths
        self._project_root = get_project_root()
        self._kwe_server_root = get_kwe_server_root()

    @property
    def project_root(self) -> str:
        """Get the project root directory dynamically."""
        return str(self._project_root)

    @property
    def kwe_server_root(self) -> str:
        """Get the KWE server root directory dynamically."""
        return str(self._kwe_server_root)

    workspace_root: str = field(
        default_factory=lambda: os.getenv("KWE_WORKSPACE_ROOT", "/tmp/ai_generated")
        or "/tmp/ai_generated"
    )
    test_runs_dir: str = "test_runs"
    docs_path: str = field(default_factory=lambda: _get_docs_path())


@dataclass(frozen=True)
class CacheConfig:
    """Cache size configuration for KWE core components."""

    template_cache_size: int = field(default_factory=lambda: _get_template_cache_size())
    performance_cache_size: int = field(
        default_factory=lambda: _get_performance_cache_size()
    )
    adaptation_history_size: int = field(
        default_factory=lambda: _get_adaptation_history_size()
    )
    prediction_cache_size: int = field(
        default_factory=lambda: _get_prediction_cache_size()
    )
    redis_cache_size_mb: int = field(default_factory=lambda: _get_redis_cache_size_mb())

    # Intelligent cache prefetch configuration
    max_sequential_prefetch_items: int = field(
        default_factory=lambda: _get_max_sequential_prefetch_items()
    )
    sequential_pattern_min_length: int = field(
        default_factory=lambda: _get_sequential_pattern_min_length()
    )
    max_prefetch_queue_size: int = field(
        default_factory=lambda: _get_max_prefetch_queue_size()
    )
    max_concurrent_prefetches: int = field(
        default_factory=lambda: _get_max_concurrent_prefetches()
    )
    timeout_seconds: int = field(
        default_factory=lambda: _get_prefetch_timeout_seconds()
    )
    min_confidence_threshold: float = field(
        default_factory=lambda: _get_min_confidence_threshold()
    )
    max_prefetch_bandwidth_mb: int = field(
        default_factory=lambda: _get_max_prefetch_bandwidth_mb()
    )
    max_prefetch_memory_mb: int = field(
        default_factory=lambda: _get_max_prefetch_memory_mb()
    )
    frequency_decay_rate: float = field(
        default_factory=lambda: _get_frequency_decay_rate()
    )


@dataclass(frozen=True)
class MonitoringConfig:
    """Monitoring interval configuration for KWE core components."""

    scale_check_interval: int = field(
        default_factory=lambda: _get_scale_check_interval()
    )
    insight_flush_interval: int = field(
        default_factory=lambda: _get_insight_flush_interval()
    )
    metrics_flush_interval: int = field(
        default_factory=lambda: _get_metrics_flush_interval()
    )
    metrics_update_interval: int = field(
        default_factory=lambda: _get_metrics_update_interval()
    )


@dataclass(frozen=True)
class RetryConfig:
    """Retry limits and circuit breaker threshold configuration for KWE core components."""

    max_retries: int = field(default_factory=lambda: _get_max_retries())
    recovery_max_retries: int = field(
        default_factory=lambda: _get_recovery_max_retries()
    )
    circuit_failure_threshold: int = field(
        default_factory=lambda: _get_circuit_failure_threshold()
    )
    bridge_max_attempts: int = field(default_factory=lambda: _get_bridge_max_attempts())


@dataclass(frozen=True)
class BatchConfig:
    """Batch processing configuration for KWE core components."""

    batch_size: int = field(default_factory=lambda: _get_batch_size())
    batch_timeout_ms: int = field(default_factory=lambda: _get_batch_timeout_ms())
    chunk_size: int = field(default_factory=lambda: _get_chunk_size())
    streaming_chunk_size: int = field(
        default_factory=lambda: _get_streaming_chunk_size()
    )


def _get_cache_default_ttl() -> int:
    """
    Get default cache TTL from environment with validation.

    Returns:
        int: Default cache TTL in seconds (default: 3600)
    """
    try:
        ttl_str = os.getenv("KWE_CACHE_DEFAULT_TTL", "3600")
        if not ttl_str or ttl_str.strip() == "":
            return 3600
        ttl = int(float(ttl_str))  # Handle float strings and truncate
        if ttl > 0:
            return ttl
        else:
            import warnings

            warnings.warn(
                f"KWE_CACHE_DEFAULT_TTL value {ttl} must be positive. "
                f"Using default value 3600.",
                UserWarning,
            )
            return 3600
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_CACHE_DEFAULT_TTL value '{ttl_str}'. "
            f"Must be a positive integer. Using default value 3600.",
            UserWarning,
        )
        return 3600


def _get_cache_short_ttl() -> int:
    """
    Get short cache TTL from environment with validation.

    Returns:
        int: Short cache TTL in seconds (default: 300)
    """
    try:
        ttl_str = os.getenv("KWE_CACHE_SHORT_TTL", "300")
        if not ttl_str or ttl_str.strip() == "":
            return 300
        ttl = int(float(ttl_str))  # Handle float strings and truncate
        if ttl > 0:
            return ttl
        else:
            import warnings

            warnings.warn(
                f"KWE_CACHE_SHORT_TTL value {ttl} must be positive. "
                f"Using default value 300.",
                UserWarning,
            )
            return 300
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_CACHE_SHORT_TTL value '{ttl_str}'. "
            f"Must be a positive integer. Using default value 300.",
            UserWarning,
        )
        return 300


def _get_cache_long_ttl() -> int:
    """
    Get long cache TTL from environment with validation.

    Returns:
        int: Long cache TTL in seconds (default: 86400)
    """
    try:
        ttl_str = os.getenv("KWE_CACHE_LONG_TTL", "86400")
        if not ttl_str or ttl_str.strip() == "":
            return 86400
        ttl = int(float(ttl_str))  # Handle float strings and truncate
        if ttl > 0:
            return ttl
        else:
            import warnings

            warnings.warn(
                f"KWE_CACHE_LONG_TTL value {ttl} must be positive. "
                f"Using default value 86400.",
                UserWarning,
            )
            return 86400
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_CACHE_LONG_TTL value '{ttl_str}'. "
            f"Must be a positive integer. Using default value 86400.",
            UserWarning,
        )
        return 86400


def _get_cache_memory_ttl() -> int:
    """
    Get memory cache TTL from environment with validation.

    Returns:
        int: Memory cache TTL in seconds (default: 1800)
    """
    try:
        ttl_str = os.getenv("KWE_CACHE_MEMORY_TTL", "1800")
        if not ttl_str or ttl_str.strip() == "":
            return 1800
        ttl = int(float(ttl_str))  # Handle float strings and truncate
        if ttl > 0:
            return ttl
        else:
            import warnings

            warnings.warn(
                f"KWE_CACHE_MEMORY_TTL value {ttl} must be positive. "
                f"Using default value 1800.",
                UserWarning,
            )
            return 1800
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_CACHE_MEMORY_TTL value '{ttl_str}'. "
            f"Must be a positive integer. Using default value 1800.",
            UserWarning,
        )
        return 1800


def _get_cache_content_ttl() -> int:
    """
    Get content cache TTL from environment with validation.

    Returns:
        int: Content cache TTL in seconds (default: 7200)
    """
    try:
        ttl_str = os.getenv("KWE_CACHE_CONTENT_TTL", "7200")
        if not ttl_str or ttl_str.strip() == "":
            return 7200
        ttl = int(float(ttl_str))  # Handle float strings and truncate
        if ttl > 0:
            return ttl
        else:
            import warnings

            warnings.warn(
                f"KWE_CACHE_CONTENT_TTL value {ttl} must be positive. "
                f"Using default value 7200.",
                UserWarning,
            )
            return 7200
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_CACHE_CONTENT_TTL value '{ttl_str}'. "
            f"Must be a positive integer. Using default value 7200.",
            UserWarning,
        )
        return 7200


# Cache TTL configuration helper functions for MED-043: Hardcoded Cache TTL Values
def _get_cache_ttl_memory_deviation() -> int:
    """Get memory deviation cache TTL from environment with validation."""
    try:
        ttl_str = os.getenv("KWE_CACHE_TTL_MEMORY_DEVIATION", "600")
        if not ttl_str or ttl_str.strip() == "":
            return 600
        ttl = int(float(ttl_str))  # Handle float strings and truncate
        if ttl > 0:
            return ttl
        else:
            import warnings
            warnings.warn(f"Invalid KWE_CACHE_TTL_MEMORY_DEVIATION value '{ttl_str}'. Must be a positive integer. Using default value 600.", UserWarning)
            return 600
    except (ValueError, TypeError):
        import warnings
        warnings.warn(f"Invalid KWE_CACHE_TTL_MEMORY_DEVIATION value '{ttl_str}'. Must be a positive integer. Using default value 600.", UserWarning)
        return 600


def _get_cache_ttl_redis_state_min() -> int:
    """Get Redis state minimum cache TTL from environment with validation."""
    try:
        ttl_str = os.getenv("KWE_CACHE_TTL_REDIS_STATE_MIN", "30")
        if not ttl_str or ttl_str.strip() == "":
            return 30
        ttl = int(float(ttl_str))  # Handle float strings and truncate
        if ttl > 0:
            return ttl
        else:
            import warnings
            warnings.warn(f"Invalid KWE_CACHE_TTL_REDIS_STATE_MIN value '{ttl_str}'. Must be a positive integer. Using default value 30.", UserWarning)
            return 30
    except (ValueError, TypeError):
        import warnings
        warnings.warn(f"Invalid KWE_CACHE_TTL_REDIS_STATE_MIN value '{ttl_str}'. Must be a positive integer. Using default value 30.", UserWarning)
        return 30


def _get_cache_ttl_redis_state_max() -> int:
    """Get Redis state maximum cache TTL from environment with validation."""
    try:
        ttl_str = os.getenv("KWE_CACHE_TTL_REDIS_STATE_MAX", "3600")
        if not ttl_str or ttl_str.strip() == "":
            return 3600
        ttl = int(float(ttl_str))  # Handle float strings and truncate
        if ttl > 0:
            return ttl
        else:
            import warnings
            warnings.warn(f"Invalid KWE_CACHE_TTL_REDIS_STATE_MAX value '{ttl_str}'. Must be a positive integer. Using default value 3600.", UserWarning)
            return 3600
    except (ValueError, TypeError):
        import warnings
        warnings.warn(f"Invalid KWE_CACHE_TTL_REDIS_STATE_MAX value '{ttl_str}'. Must be a positive integer. Using default value 3600.", UserWarning)
        return 3600


# Test configuration helper functions for MED-036
def _get_test_cache_max_size() -> int:
    """
    Get test cache max size from environment with validation.

    Returns:
        int: Test cache max size (default: 100)
    """
    try:
        size_str = os.getenv("KWE_TEST_CACHE_MAX_SIZE", "100")
        if not size_str or size_str.strip() == "":
            return 100
        size = int(float(size_str))  # Handle float strings and truncate
        if size > 0:
            # Cap at reasonable limit for test environments
            return min(size, 10000)
        else:
            import warnings

            warnings.warn(
                f"KWE_TEST_CACHE_MAX_SIZE value {size} must be positive. "
                f"Using default value 100.",
                UserWarning,
            )
            return 100
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_TEST_CACHE_MAX_SIZE value '{size_str}'. "
            f"Must be a positive integer. Using default value 100.",
            UserWarning,
        )
        return 100


def _get_test_cache_default_ttl() -> int:
    """
    Get test cache default TTL from environment with validation.

    Returns:
        int: Test cache default TTL in seconds (default: 300)
    """
    try:
        ttl_str = os.getenv("KWE_TEST_CACHE_DEFAULT_TTL", "300")
        if not ttl_str or ttl_str.strip() == "":
            return 300
        ttl = int(float(ttl_str))  # Handle float strings and truncate
        if ttl > 0:
            return ttl
        else:
            import warnings

            warnings.warn(
                f"KWE_TEST_CACHE_DEFAULT_TTL value {ttl} must be positive. "
                f"Using default value 300.",
                UserWarning,
            )
            return 300
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_TEST_CACHE_DEFAULT_TTL value '{ttl_str}'. "
            f"Must be a positive integer. Using default value 300.",
            UserWarning,
        )
        return 300


def _get_test_cache_ttl() -> int:
    """
    Get test cache TTL from environment with validation.

    Returns:
        int: Test cache TTL in seconds (default: 60)
    """
    try:
        ttl_str = os.getenv("KWE_TEST_CACHE_TTL", "60")
        if not ttl_str or ttl_str.strip() == "":
            return 60
        ttl = int(float(ttl_str))  # Handle float strings and truncate
        if ttl > 0:
            return ttl
        else:
            import warnings

            warnings.warn(
                f"KWE_TEST_CACHE_TTL value {ttl} must be positive. "
                f"Using default value 60.",
                UserWarning,
            )
            return 60
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_TEST_CACHE_TTL value '{ttl_str}'. "
            f"Must be a positive integer. Using default value 60.",
            UserWarning,
        )
        return 60


def _get_test_query_text() -> str:
    """
    Get test query text from environment with validation.

    Returns:
        str: Test query text (default: "find similar patterns for coding tasks")
    """
    query_text = os.getenv(
        "KWE_TEST_QUERY_TEXT", "find similar patterns for coding tasks"
    )
    if not query_text or query_text.strip() == "":
        return "find similar patterns for coding tasks"
    return query_text.strip()


def _get_test_query_priority() -> str:
    """
    Get test query priority from environment with validation.

    Returns:
        str: Test query priority (default: "medium")
    """
    priority = os.getenv("KWE_TEST_QUERY_PRIORITY", "medium")
    valid_priorities = ["low", "medium", "high", "critical"]
    if priority in valid_priorities:
        return priority
    else:
        import warnings

        warnings.warn(
            f"Invalid KWE_TEST_QUERY_PRIORITY value '{priority}'. "
            f"Must be one of {valid_priorities}. Using default value 'medium'.",
            UserWarning,
        )
        return "medium"


@dataclass(frozen=True)
class TestConfig:
    """Test parameter configuration for KWE memory bridge optimization."""

    # Cache configuration for test optimization
    cache_max_size: int = field(default_factory=lambda: _get_test_cache_max_size())
    cache_default_ttl: int = field(
        default_factory=lambda: _get_test_cache_default_ttl()
    )
    cache_ttl: int = field(default_factory=lambda: _get_test_cache_ttl())

    # Query configuration for test optimization
    query_text: str = field(default_factory=lambda: _get_test_query_text())
    query_priority: str = field(default_factory=lambda: _get_test_query_priority())


# Agent model configuration helper functions for MED-037
def _get_agent_model() -> str:
    """
    Get agent model from environment with centralized configuration fallback.

    Returns:
        str: Agent model name (default from centralized config)
    """
    # Use centralized model configuration
    default_model = "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M"
    
    # Check for legacy environment variable (backward compatibility)
    model = os.getenv("KWE_AGENT_MODEL")
    if model and model.strip():
        return model.strip()
    
    # Check for primary model override
    primary_model = os.getenv("KWE_PRIMARY_MODEL")
    if primary_model and primary_model.strip():
        return primary_model.strip()
    
    return default_model


def _get_model_temperature() -> float:
    """
    Get model temperature from environment with validation.

    Returns:
        float: Model temperature (default: 0.3, range: 0.0-1.0)
    """
    try:
        temp_str = os.getenv("KWE_MODEL_TEMPERATURE", "0.3")
        if not temp_str or temp_str.strip() == "":
            return 0.3
        temp = float(temp_str)
        # Clamp temperature to valid range [0.0, 1.0]
        if temp < 0.0:
            import warnings

            warnings.warn(
                f"KWE_MODEL_TEMPERATURE value {temp} is negative. " f"Clamping to 0.0.",
                UserWarning,
            )
            return 0.0
        elif temp > 1.0:
            import warnings

            warnings.warn(
                f"KWE_MODEL_TEMPERATURE value {temp} exceeds maximum 1.0. "
                f"Clamping to 1.0.",
                UserWarning,
            )
            return 1.0
        return temp
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_MODEL_TEMPERATURE value '{temp_str}'. "
            f"Must be a float between 0.0 and 1.0. Using default value 0.3.",
            UserWarning,
        )
        return 0.3


def _get_model_max_tokens() -> int:
    """
    Get model max tokens from environment with validation.

    Returns:
        int: Model max tokens (default: 300)
    """
    try:
        tokens_str = os.getenv("KWE_MODEL_MAX_TOKENS", "300")
        if not tokens_str or tokens_str.strip() == "":
            return 300
        tokens = int(float(tokens_str))  # Handle float strings and truncate
        if tokens > 0:
            return tokens
        else:
            import warnings

            warnings.warn(
                f"KWE_MODEL_MAX_TOKENS value {tokens} must be positive. "
                f"Using default value 300.",
                UserWarning,
            )
            return 300
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_MODEL_MAX_TOKENS value '{tokens_str}'. "
            f"Must be a positive integer. Using default value 300.",
            UserWarning,
        )
        return 300


def _get_server_host() -> str:
    """
    Get server host from environment with validation.

    Returns:
        str: Server host (default: "0.0.0.0")
    """
    host = os.getenv("KWE_SERVER_HOST", "0.0.0.0")
    if not host or host.strip() == "":
        return "0.0.0.0"
    return host.strip()


def _get_server_port() -> int:
    """
    Get server port from environment with validation.

    Returns:
        int: Server port (default: 8766, range: 1-65535)
    """
    try:
        port_str = os.getenv("KWE_SERVER_PORT", "8766")
        if not port_str or port_str.strip() == "":
            return 8766
        port = int(float(port_str))  # Handle float strings and truncate
        if 1 <= port <= 65535:
            return port
        else:
            import warnings

            warnings.warn(
                f"KWE_SERVER_PORT value {port} must be between 1 and 65535. "
                f"Using default value 8766.",
                UserWarning,
            )
            return 8766
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_SERVER_PORT value '{port_str}'. "
            f"Must be an integer between 1 and 65535. Using default value 8766.",
            UserWarning,
        )
        return 8766


def _get_ollama_port() -> int:
    """
    Get Ollama port from environment with validation.

    Returns:
        int: Ollama port (default: 11434, range: 1-65535)
    """
    try:
        port_str = os.getenv("KWE_OLLAMA_PORT", "11434")
        if not port_str or port_str.strip() == "":
            return 11434
        port = int(float(port_str))  # Handle float strings and truncate
        if 1 <= port <= 65535:
            return port
        else:
            import warnings

            warnings.warn(
                f"KWE_OLLAMA_PORT value {port} must be between 1 and 65535. "
                f"Using default value 11434.",
                UserWarning,
            )
            return 11434
    except (ValueError, TypeError):
        import warnings

        warnings.warn(
            f"Invalid KWE_OLLAMA_PORT value '{port_str}'. "
            f"Must be an integer between 1 and 65535. Using default value 11434.",
            UserWarning,
        )
        return 11434


# Performance Monitoring Configuration Helper Functions for MED-038
def _get_perf_response_time_warning() -> int:
    """
    Get performance response time warning threshold from environment with validation.

    Returns:
        int: Response time warning threshold in milliseconds (default: 400)
    """
    try:
        threshold_str = os.getenv("KWE_PERF_RESPONSE_TIME_WARNING", "400")
        if not threshold_str or threshold_str.strip() == "":
            return 400
        threshold = int(float(threshold_str))
        return max(1, threshold)  # Must be positive
    except (ValueError, TypeError):
        return 400


def _get_perf_response_time_critical() -> int:
    """
    Get performance response time critical threshold from environment with validation.

    Returns:
        int: Response time critical threshold in milliseconds (default: 500)
    """
    try:
        threshold_str = os.getenv("KWE_PERF_RESPONSE_TIME_CRITICAL", "500")
        if not threshold_str or threshold_str.strip() == "":
            return 500
        threshold = int(float(threshold_str))
        return max(1, threshold)  # Must be positive
    except (ValueError, TypeError):
        return 500


def _get_perf_success_rate_warning() -> float:
    """
    Get performance success rate warning threshold from environment with validation.

    Returns:
        float: Success rate warning threshold (default: 0.95)
    """
    try:
        threshold_str = os.getenv("KWE_PERF_SUCCESS_RATE_WARNING", "0.95")
        if not threshold_str or threshold_str.strip() == "":
            return 0.95
        threshold = float(threshold_str)
        return max(0.0, min(threshold, 1.0))  # Clamp between 0.0 and 1.0
    except (ValueError, TypeError):
        return 0.95


def _get_perf_success_rate_critical() -> float:
    """
    Get performance success rate critical threshold from environment with validation.

    Returns:
        float: Success rate critical threshold (default: 0.90)
    """
    try:
        threshold_str = os.getenv("KWE_PERF_SUCCESS_RATE_CRITICAL", "0.90")
        if not threshold_str or threshold_str.strip() == "":
            return 0.90
        threshold = float(threshold_str)
        return max(0.0, min(threshold, 1.0))  # Clamp between 0.0 and 1.0
    except (ValueError, TypeError):
        return 0.90


def _get_perf_error_rate_warning() -> float:
    """
    Get performance error rate warning threshold from environment with validation.

    Returns:
        float: Error rate warning threshold (default: 0.05)
    """
    try:
        threshold_str = os.getenv("KWE_PERF_ERROR_RATE_WARNING", "0.05")
        if not threshold_str or threshold_str.strip() == "":
            return 0.05
        threshold = float(threshold_str)
        return max(0.0, min(threshold, 1.0))  # Clamp between 0.0 and 1.0
    except (ValueError, TypeError):
        return 0.05


def _get_perf_error_rate_critical() -> float:
    """
    Get performance error rate critical threshold from environment with validation.

    Returns:
        float: Error rate critical threshold (default: 0.10)
    """
    try:
        threshold_str = os.getenv("KWE_PERF_ERROR_RATE_CRITICAL", "0.10")
        if not threshold_str or threshold_str.strip() == "":
            return 0.10
        threshold = float(threshold_str)
        return max(0.0, min(threshold, 1.0))  # Clamp between 0.0 and 1.0
    except (ValueError, TypeError):
        return 0.10


def _get_perf_alert_cooldown_minutes() -> int:
    """
    Get performance alert cooldown period from environment with validation.

    Returns:
        int: Alert cooldown period in minutes (default: 5)
    """
    try:
        cooldown_str = os.getenv("KWE_PERF_ALERT_COOLDOWN_MINUTES", "5")
        if not cooldown_str or cooldown_str.strip() == "":
            return 5
        cooldown = int(float(cooldown_str))
        return max(1, cooldown)  # Must be positive
    except (ValueError, TypeError):
        return 5


def _get_perf_stats_update_interval() -> int:
    """
    Get performance statistics update interval from environment with validation.

    Returns:
        int: Statistics update interval in seconds (default: 30)
    """
    try:
        interval_str = os.getenv("KWE_PERF_STATS_UPDATE_INTERVAL", "30")
        if not interval_str or interval_str.strip() == "":
            return 30
        interval = int(float(interval_str))
        return max(1, interval)  # Must be positive
    except (ValueError, TypeError):
        return 30


# Database Connection Configuration Helper Functions for MED-034
def _get_db_connection_timeout() -> int:
    """
    Get database connection timeout from environment with validation.

    Returns:
        int: Connection timeout in seconds (default: 30)
    """
    try:
        timeout_str = os.getenv("KWE_DB_CONNECTION_TIMEOUT", "30")
        if not timeout_str or timeout_str.strip() == "":
            return 30
        timeout = int(float(timeout_str))
        return max(5, min(timeout, 300))  # Clamp between 5 seconds and 5 minutes
    except (ValueError, TypeError):
        return 30


def _get_db_max_retries() -> int:
    """
    Get database connection maximum retries from environment with validation.

    Returns:
        int: Maximum retry attempts (default: 3)
    """
    try:
        retries_str = os.getenv("KWE_DB_MAX_RETRIES", "3")
        if not retries_str or retries_str.strip() == "":
            return 3
        retries = int(float(retries_str))
        return max(1, min(retries, 10))  # Clamp between 1 and 10 retries
    except (ValueError, TypeError):
        return 3


def _get_db_health_check_interval() -> int:
    """
    Get database health check interval from environment with validation.

    Returns:
        int: Health check interval in seconds (default: 30)
    """
    try:
        interval_str = os.getenv("KWE_DB_HEALTH_CHECK_INTERVAL", "30")
        if not interval_str or interval_str.strip() == "":
            return 30
        interval = int(float(interval_str))
        return max(10, min(interval, 300))  # Clamp between 10 seconds and 5 minutes
    except (ValueError, TypeError):
        return 30


def _get_ollama_base_url() -> str:
    """
    Get Ollama client base URL from environment with validation and fallback.

    Environment Variable: KWE_OLLAMA_BASE_URL
    Default: http://localhost:11434

    Returns:
        str: Ollama base URL (default: http://localhost:11434)
    
    MED-044: Enhanced URL validation and normalization for configurable service URLs
    """
    try:
        url = os.getenv("KWE_OLLAMA_BASE_URL", "http://localhost:11434")
        if not url or url.strip() == "":
            return "http://localhost:11434"

        # Basic URL validation and normalization
        url = url.strip()
        
        # Enhanced validation for invalid protocols and malformed URLs
        if not (url.startswith("http://") or url.startswith("https://")):
            # Use print instead of logger to avoid import issues
            print(f"Warning: Invalid Ollama URL format: {url}. Using default.")
            return "http://localhost:11434"
        
        # Check for incomplete URLs (e.g., "http://")
        if url in ("http://", "https://"):
            print(f"Warning: Invalid Ollama URL format: {url}. Using default.")
            return "http://localhost:11434"
        
        # Check for invalid characters (spaces, etc.)
        if " " in url:
            print(f"Warning: Invalid Ollama URL format: {url}. Using default.")
            return "http://localhost:11434"
        
        # URL normalization: remove trailing slash for base URLs
        if url.endswith("/"):
            url = url.rstrip("/")

        return url
    except Exception as e:
        # Use print instead of logger to avoid import issues
        print(f"Warning: Error reading KWE_OLLAMA_BASE_URL: {e}. Using default.")
        return "http://localhost:11434"


def _get_mcp_sequential_thinking_base_url() -> str:
    """
    Get Sequential Thinking MCP server command from environment with validation and fallback.

    Environment Variable: KWE_MCP_SEQUENTIAL_THINKING_BASE_URL
    Default: npx @modelcontextprotocol/server-sequential-thinking

    Returns:
        str: Sequential Thinking MCP server command (default: npx @modelcontextprotocol/server-sequential-thinking)
    """
    try:
        url = os.getenv("KWE_MCP_SEQUENTIAL_THINKING_BASE_URL", "npx @modelcontextprotocol/server-sequential-thinking")
        if not url or url.strip() == "":
            return "npx @modelcontextprotocol/server-sequential-thinking"

        # Basic command validation - allow both HTTP URLs and stdio commands
        url = url.strip()
        if url.startswith("http://") or url.startswith("https://") or url.startswith("npx ") or url.startswith("node "):
            return url
        else:
            # Use print instead of logger to avoid import issues
            print(
                f"Warning: Invalid Sequential Thinking MCP URL/command format: {url}. Using default."
            )
            return "npx @modelcontextprotocol/server-sequential-thinking"

        return url
    except Exception as e:
        # Use print instead of logger to avoid import issues
        print(
            f"Warning: Error reading KWE_MCP_SEQUENTIAL_THINKING_BASE_URL: {e}. Using default."
        )
        return "npx @modelcontextprotocol/server-sequential-thinking"


def _get_mcp_memory_base_url() -> str:
    """
    Get Memory MCP server command from environment with validation and fallback.

    Environment Variable: KWE_MCP_MEMORY_BASE_URL
    Default: npx @itseasy21/mcp-knowledge-graph

    Returns:
        str: Memory MCP server command (default: npx @itseasy21/mcp-knowledge-graph)
    """
    try:
        url = os.getenv("KWE_MCP_MEMORY_BASE_URL", "npx @itseasy21/mcp-knowledge-graph")
        if not url or url.strip() == "":
            return "npx @itseasy21/mcp-knowledge-graph"

        # Basic command validation - allow both HTTP URLs and stdio commands
        url = url.strip()
        if url.startswith("http://") or url.startswith("https://") or url.startswith("npx ") or url.startswith("node "):
            return url
        else:
            # Use print instead of logger to avoid import issues
            print(f"Warning: Invalid Memory MCP URL/command format: {url}. Using default.")
            return "npx @itseasy21/mcp-knowledge-graph"

        return url
    except Exception as e:
        # Use print instead of logger to avoid import issues
        print(f"Warning: Error reading KWE_MCP_MEMORY_BASE_URL: {e}. Using default.")
        return "npx @itseasy21/mcp-knowledge-graph"


def _get_mcp_context7_base_url() -> str:
    """
    Get Context7 MCP server command from environment with validation and fallback.

    Environment Variable: KWE_MCP_CONTEXT7_BASE_URL
    Default: npx @modelcontextprotocol/server-context7

    Returns:
        str: Context7 MCP server command (default: npx @modelcontextprotocol/server-context7)
    """
    try:
        url = os.getenv("KWE_MCP_CONTEXT7_BASE_URL", "npx @modelcontextprotocol/server-context7")
        if not url or url.strip() == "":
            return "npx @modelcontextprotocol/server-context7"

        # Basic command validation - allow both HTTP URLs and stdio commands
        url = url.strip()
        if url.startswith("http://") or url.startswith("https://") or url.startswith("npx ") or url.startswith("node "):
            return url
        else:
            # Use print instead of logger to avoid import issues
            print(f"Warning: Invalid Context7 MCP URL/command format: {url}. Using default.")
            return "npx @modelcontextprotocol/server-context7"

        return url
    except Exception as e:
        # Use print instead of logger to avoid import issues
        print(f"Warning: Error reading KWE_MCP_CONTEXT7_BASE_URL: {e}. Using default.")
        return "npx @modelcontextprotocol/server-context7"


def _get_mcp_servers_enabled() -> bool:
    """
    Get MCP servers enabled flag from environment with validation and fallback.

    Environment Variable: KWE_ENABLE_MCP_SERVERS
    Default: False (disabled by default to prevent startup failures)

    Returns:
        bool: Whether MCP servers should be enabled (default: False)
    """
    try:
        enabled_str = os.getenv("KWE_ENABLE_MCP_SERVERS", "false").lower().strip()
        
        # Accept various true values
        if enabled_str in ("true", "1", "yes", "on", "enabled"):
            return True
        # Accept various false values  
        elif enabled_str in ("false", "0", "no", "off", "disabled", ""):
            return False
        else:
            print(f"Warning: Invalid KWE_ENABLE_MCP_SERVERS value: {enabled_str}. Using default (false).")
            return False
            
    except Exception as e:
        print(f"Warning: Error reading KWE_ENABLE_MCP_SERVERS: {e}. Using default (false).")
        return False


def _get_redis_host() -> str:
    """
    Get Redis host from environment with validation and fallback.

    Environment Variable: KWE_REDIS_HOST
    Default: localhost

    Returns:
        str: Redis host (default: localhost)
    """
    try:
        host = os.getenv("KWE_REDIS_HOST", "localhost")
        if not host or host.strip() == "":
            return "localhost"

        # Basic host validation
        host = host.strip()
        if len(host) == 0:
            # Use print instead of logger to avoid import issues
            print(f"Warning: Empty Redis host. Using default.")
            return "localhost"

        return host
    except Exception as e:
        # Use print instead of logger to avoid import issues
        print(f"Warning: Error reading KWE_REDIS_HOST: {e}. Using default.")
        return "localhost"


def _get_redis_port() -> int:
    """
    Get Redis port from environment with validation and fallback.

    Environment Variable: KWE_REDIS_PORT
    Default: 6379

    Returns:
        int: Redis port (default: 6379)
    """
    try:
        port_str = os.getenv("KWE_REDIS_PORT", "6379")
        if not port_str or port_str.strip() == "":
            return 6379

        port = int(port_str)

        # Validate port range (1-65535)
        if 1 <= port <= 65535:
            return port
        else:
            # Use print instead of logger to avoid import issues
            print(f"Warning: Invalid Redis port {port}. Using default 6379.")
            return 6379

    except (ValueError, TypeError):
        # Use print instead of logger to avoid import issues
        print(
            f"Warning: Invalid KWE_REDIS_PORT value '{port_str}'. Using default 6379."
        )
        return 6379


def _get_redis_db() -> int:
    """
    Get Redis database number from environment with validation and fallback.

    Environment Variable: KWE_REDIS_DB
    Default: 0

    Returns:
        int: Redis database number (default: 0)
    """
    try:
        db_str = os.getenv("KWE_REDIS_DB", "0")
        if not db_str or db_str.strip() == "":
            return 0

        db = int(db_str)

        # Validate database number range (0-15 for standard Redis)
        if 0 <= db <= 15:
            return db
        else:
            # Use print instead of logger to avoid import issues
            print(f"Warning: Invalid Redis database {db}. Using default 0.")
            return 0

    except (ValueError, TypeError):
        # Use print instead of logger to avoid import issues
        print(f"Warning: Invalid KWE_REDIS_DB value '{db_str}'. Using default 0.")
        return 0


def _get_db_pool_size() -> int:
    """
    Get database connection pool size from environment with validation.

    Returns:
        int: Connection pool size (default: 20)
    """
    try:
        pool_str = os.getenv("KWE_DB_POOL_SIZE", "20")
        if not pool_str or pool_str.strip() == "":
            return 20
        pool_size = int(float(pool_str))
        return max(1, min(pool_size, 100))  # Clamp between 1 and 100 connections
    except (ValueError, TypeError):
        return 20


def _get_db_query_limit_default() -> int:
    """
    Get default database query limit from environment with validation.

    Returns:
        int: Default query limit (default: 100)
    """
    try:
        limit_str = os.getenv("KWE_DB_QUERY_LIMIT_DEFAULT", "100")
        if not limit_str or limit_str.strip() == "":
            return 100
        limit = int(float(limit_str))
        return max(1, limit)  # Must be positive
    except (ValueError, TypeError):
        return 100


def _get_db_query_limit_search() -> int:
    """
    Get search database query limit from environment with validation.

    Returns:
        int: Search query limit (default: 50)
    """
    try:
        limit_str = os.getenv("KWE_DB_QUERY_LIMIT_SEARCH", "50")
        if not limit_str or limit_str.strip() == "":
            return 50
        limit = int(float(limit_str))
        return max(1, limit)  # Must be positive
    except (ValueError, TypeError):
        return 50


def _get_db_cache_ttl_short() -> int:
    """
    Get short-term database cache TTL from environment with validation.

    Returns:
        int: Short cache TTL in seconds (default: 1800 / 30 minutes)
    """
    try:
        ttl_str = os.getenv("KWE_DB_CACHE_TTL_SHORT", "1800")
        if not ttl_str or ttl_str.strip() == "":
            return 1800
        ttl = int(float(ttl_str))
        return max(60, ttl)  # Must be at least 1 minute
    except (ValueError, TypeError):
        return 1800


def _get_db_cache_ttl_long() -> int:
    """
    Get long-term database cache TTL from environment with validation.

    Returns:
        int: Long cache TTL in seconds (default: 3600 / 1 hour)
    """
    try:
        ttl_str = os.getenv("KWE_DB_CACHE_TTL_LONG", "3600")
        if not ttl_str or ttl_str.strip() == "":
            return 3600
        ttl = int(float(ttl_str))
        return max(300, ttl)  # Must be at least 5 minutes
    except (ValueError, TypeError):
        return 3600


def _get_db_record_buffer_size() -> int:
    """
    Get database record buffer size from environment with validation.

    Returns:
        int: Record buffer size (default: 1000)
    """
    try:
        buffer_str = os.getenv("KWE_DB_RECORD_BUFFER_SIZE", "1000")
        if not buffer_str or buffer_str.strip() == "":
            return 1000
        buffer_size = int(float(buffer_str))
        return max(100, buffer_size)  # Must be at least 100 records
    except (ValueError, TypeError):
        return 1000


def _get_db_state_retention_days() -> int:
    """
    Get database state retention period from environment with validation.

    Returns:
        int: State retention in days (default: 30)
    """
    try:
        days_str = os.getenv("KWE_DB_STATE_RETENTION_DAYS", "30")
        if not days_str or days_str.strip() == "":
            return 30
        days = int(float(days_str))
        return max(1, days)  # Must be at least 1 day
    except (ValueError, TypeError):
        return 30


@dataclass(frozen=True)
class AgentModelConfig:
    """Agent model configuration for KWE AI agents."""

    # Model configuration
    model: str = field(default_factory=lambda: _get_agent_model())
    temperature: float = field(default_factory=lambda: _get_model_temperature())
    max_tokens: int = field(default_factory=lambda: _get_model_max_tokens())

    # Service configuration
    server_host: str = field(default_factory=lambda: _get_server_host())
    server_port: int = field(default_factory=lambda: _get_server_port())
    ollama_port: int = field(default_factory=lambda: _get_ollama_port())


@dataclass(frozen=True)
class PerformanceMonitoringConfig:
    """Performance monitoring threshold configuration for KWE monitoring systems."""

    # Response time thresholds (milliseconds)
    response_time_warning: int = field(
        default_factory=lambda: _get_perf_response_time_warning()
    )
    response_time_critical: int = field(
        default_factory=lambda: _get_perf_response_time_critical()
    )

    # Success rate thresholds (0.0-1.0)
    success_rate_warning: float = field(
        default_factory=lambda: _get_perf_success_rate_warning()
    )
    success_rate_critical: float = field(
        default_factory=lambda: _get_perf_success_rate_critical()
    )

    # Error rate thresholds (0.0-1.0)
    error_rate_warning: float = field(
        default_factory=lambda: _get_perf_error_rate_warning()
    )
    error_rate_critical: float = field(
        default_factory=lambda: _get_perf_error_rate_critical()
    )

    # Monitoring intervals
    alert_cooldown_minutes: int = field(
        default_factory=lambda: _get_perf_alert_cooldown_minutes()
    )
    stats_update_interval: int = field(
        default_factory=lambda: _get_perf_stats_update_interval()
    )


@dataclass(frozen=True)
class OllamaConfig:
    """Ollama client configuration for KWE AI agents."""

    # Ollama client configuration
    base_url: str = field(default_factory=lambda: _get_ollama_base_url())


@dataclass(frozen=True)
class MCPConfig:
    """MCP (Model Context Protocol) server configuration for KWE."""

    # MCP server enabled flag - disabled by default to prevent startup failures
    enabled: bool = field(default_factory=lambda: _get_mcp_servers_enabled())
    
    # MCP server base URLs
    sequential_thinking_base_url: str = field(
        default_factory=lambda: _get_mcp_sequential_thinking_base_url()
    )
    memory_base_url: str = field(default_factory=lambda: _get_mcp_memory_base_url())
    context7_base_url: str = field(default_factory=lambda: _get_mcp_context7_base_url())


@dataclass(frozen=True)
class RedisConfig:
    """Redis connection configuration for KWE caching and state management."""

    # Redis connection parameters
    host: str = field(default_factory=lambda: _get_redis_host())
    port: int = field(default_factory=lambda: _get_redis_port())
    db: int = field(default_factory=lambda: _get_redis_db())


@dataclass(frozen=True)
class DatabaseConnectionConfig:
    """Database connection configuration for KWE 4-tier memory system."""

    # Connection parameters
    connection_timeout: int = field(
        default_factory=lambda: _get_db_connection_timeout()
    )
    max_retries: int = field(default_factory=lambda: _get_db_max_retries())
    health_check_interval: int = field(
        default_factory=lambda: _get_db_health_check_interval()
    )
    pool_size: int = field(default_factory=lambda: _get_db_pool_size())

    # Query limits
    query_limit_default: int = field(
        default_factory=lambda: _get_db_query_limit_default()
    )
    query_limit_search: int = field(
        default_factory=lambda: _get_db_query_limit_search()
    )

    # Cache configuration
    cache_ttl_short: int = field(default_factory=lambda: _get_db_cache_ttl_short())
    cache_ttl_long: int = field(default_factory=lambda: _get_db_cache_ttl_long())

    # Buffer and retention
    record_buffer_size: int = field(
        default_factory=lambda: _get_db_record_buffer_size()
    )
    state_retention_days: int = field(
        default_factory=lambda: _get_db_state_retention_days()
    )


@dataclass(frozen=True)
class CacheTTLConfig:
    """Cache TTL (Time To Live) configuration for KWE caching systems."""

    # Default cache TTL for general use
    default_cache_ttl: int = field(default_factory=lambda: _get_cache_default_ttl())

    # Short cache TTL for frequently changing data
    short_cache_ttl: int = field(default_factory=lambda: _get_cache_short_ttl())

    # Long cache TTL for stable data
    long_cache_ttl: int = field(default_factory=lambda: _get_cache_long_ttl())

    # Memory cache TTL for in-memory caching
    memory_cache_ttl: int = field(default_factory=lambda: _get_cache_memory_ttl())

    # Content cache TTL for content-specific caching
    content_cache_ttl: int = field(default_factory=lambda: _get_cache_content_ttl())
    
    # MED-043: Configurable cache TTL values for specific components
    memory_deviation_ttl: int = field(default_factory=lambda: _get_cache_ttl_memory_deviation())
    redis_state_min_ttl: int = field(default_factory=lambda: _get_cache_ttl_redis_state_min())
    redis_state_max_ttl: int = field(default_factory=lambda: _get_cache_ttl_redis_state_max())


@dataclass
class SystemConfig:
    """Main configuration container for the KWE system."""

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    gpu: GPUConfig = field(default_factory=GPUConfig)
    service: ServiceConfig = field(default_factory=ServiceConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    timeout: TimeoutConfig = field(default_factory=TimeoutConfig)
    workspace: WorkspaceConfig = field(default_factory=WorkspaceConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    batch: BatchConfig = field(default_factory=BatchConfig)
    api: APIConfig = field(default_factory=APIConfig)
    cache_ttl: CacheTTLConfig = field(default_factory=CacheTTLConfig)
    test: TestConfig = field(default_factory=TestConfig)
    agent_model: AgentModelConfig = field(default_factory=AgentModelConfig)
    performance_monitoring: PerformanceMonitoringConfig = field(
        default_factory=PerformanceMonitoringConfig
    )
    database_connection: DatabaseConnectionConfig = field(
        default_factory=DatabaseConnectionConfig
    )
    pool_sizes: PoolSizesConfig = field(default_factory=PoolSizesConfig)  # MED-045: Connection pool sizes


# Global configuration instance
config = SystemConfig()

# Backward compatibility - expose flat variables for existing code
OLLAMA_URL = config.llm.ollama_url
DEFAULT_MODEL = config.llm.default_model
DEFAULT_TEMPERATURE = config.llm.default_temperature
DEFAULT_MAX_TOKENS = config.llm.default_max_tokens

# Legacy agent models mapping for backward compatibility
# Note: New code should use centralized model configuration
AGENT_MODELS = {
    "coder": "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M",
    "tester": "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M",
    "analyst": "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M",
    "planner": "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M",
    "documenter": "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M",
    "validator": "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M",
    "memory_manager": "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M",
    "director": "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M",
    "research": "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M",
    "debugger": "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M",
    "general": "hf.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF:Q4_K_M",
}
TIMEOUT_COMPLEX_TASK = config.timeout.complex_task
TIMEOUT_MEDIUM_TASK = config.timeout.medium_task
TIMEOUT_SIMPLE_TASK = config.timeout.simple_task
DEFAULT_PROJECT_ROOT = config.workspace.project_root
DEFAULT_WORKSPACE_ROOT = config.workspace.workspace_root
TEST_RUNS_DIR = config.workspace.test_runs_dir

# Additional flat variables for logging and other components
LOG_LEVEL = "INFO"
PROJECT_ROOT = config.workspace.project_root

# Database connection variables for backward compatibility
QDRANT_HOST = config.database.qdrant.host
QDRANT_PORT = config.database.qdrant.port
NEO4J_HOST = config.database.neo4j.host
NEO4J_PORT = config.database.neo4j.port
POSTGRES_HOST = config.database.postgres.host
POSTGRES_PORT = config.database.postgres.port
REDIS_HOST = config.database.redis.host
REDIS_PORT = config.database.redis.port

# KWE server directory
KWE_SERVER_DIR = os.path.join(PROJECT_ROOT, "kwe_server")


def validate_configuration() -> List[str]:
    """
    Validate the KWE configuration and return a list of warnings.

    This function performs comprehensive validation of all configuration
    values including:
    - Port range validation (1-65535)
    - Host connectivity checks (non-blocking)
    - Path existence validation
    - Environment variable consistency
    - Configuration completeness

    Returns:
        List[str]: List of warning messages. Empty list if no issues found.

    Raises:
        No exceptions are raised - all issues are reported as warnings.
    """
    warnings_list = []

    try:
        # Validate port ranges
        port_configs = [
            ("Qdrant", QDRANT_PORT),
            ("Neo4j", NEO4J_PORT),
            ("PostgreSQL", POSTGRES_PORT),
            ("Redis", REDIS_PORT),
            ("Service", config.service.port),
        ]

        for service_name, port in port_configs:
            if not isinstance(port, int):
                warnings_list.append(
                    f"{service_name} port must be an integer, got {type(port)}"
                )
            elif port < 1 or port > 65535:
                warnings_list.append(
                    f"{service_name} port {port} is outside valid range (1-65535)"
                )

        # Validate host values
        host_configs = [
            ("Qdrant", QDRANT_HOST),
            ("Neo4j", NEO4J_HOST),
            ("PostgreSQL", POSTGRES_HOST),
            ("Redis", REDIS_HOST),
            ("Service", config.service.host),
        ]

        for service_name, host in host_configs:
            if not host or not isinstance(host, str):
                warnings_list.append(
                    f"{service_name} host must be a non-empty string, got {host}"
                )
            elif len(host.strip()) == 0:
                warnings_list.append(f"{service_name} host is empty")

        # Validate paths
        path_configs = [
            ("Project Root", PROJECT_ROOT),
            ("KWE Server Directory", KWE_SERVER_DIR),
            ("Workspace Root", config.workspace.workspace_root),
        ]

        for path_name, path in path_configs:
            if not path or not isinstance(path, str):
                warnings_list.append(
                    f"{path_name} must be a non-empty string, got {path}"
                )
            elif not os.path.exists(path):
                warnings_list.append(f"{path_name} does not exist: {path}")

        # Validate LLM configuration
        if not config.llm.ollama_url or not isinstance(config.llm.ollama_url, str):
            warnings_list.append("Ollama URL must be a non-empty string")

        temp = config.llm.default_temperature
        if temp < 0.0 or temp > 2.0:
            warnings_list.append(
                f"Default temperature {temp} is outside valid range (0.0-2.0)"
            )

        if config.llm.default_max_tokens < 1:
            warnings_list.append(
                f"Default max tokens {config.llm.default_max_tokens} must be positive"
            )

        # Validate agent models (now using legacy AGENT_MODELS for backward compatibility)
        if not AGENT_MODELS:
            warnings_list.append("Agent models configuration is empty")
        else:
            for agent, model in AGENT_MODELS.items():
                if not model or not isinstance(model, str):
                    warnings_list.append(
                        f"Agent '{agent}' model must be a non-empty string, got {model}"
                    )

        # Validate timeout configurations
        timeout_configs = [
            ("Complex Task", config.timeout.complex_task),
            ("Medium Task", config.timeout.medium_task),
            ("Simple Task", config.timeout.simple_task),
        ]

        for timeout_name, timeout in timeout_configs:
            if not isinstance(timeout, int) or timeout < 1:
                warnings_list.append(
                    f"{timeout_name} timeout must be a positive integer, got {timeout}"
                )

        # Validate GPU configuration
        if not isinstance(config.gpu.director_config, dict):
            warnings_list.append("GPU director_config must be a dictionary")
        else:
            gpu_config = config.gpu.director_config
            if "hip_visible_devices" not in gpu_config:
                warnings_list.append("GPU configuration missing 'hip_visible_devices'")
            if "n_gpu_layers" not in gpu_config:
                warnings_list.append("GPU configuration missing 'n_gpu_layers'")
            if "use_gpu" not in gpu_config:
                warnings_list.append("GPU configuration missing 'use_gpu'")

        # Validate database configurations
        db_configs = [
            ("Redis", config.database.redis),
            ("PostgreSQL", config.database.postgres),
            ("Neo4j", config.database.neo4j),
            ("Qdrant", config.database.qdrant),
        ]

        for db_name, db_config in db_configs:
            if not hasattr(db_config, "host") or not hasattr(db_config, "port"):
                warnings_list.append(
                    f"{db_name} configuration missing required host/port attributes"
                )

        # Validate service configuration
        if config.service.workers < 1:
            warnings_list.append(
                f"Service workers must be positive, got {config.service.workers}"
            )

        if config.service.timeout < 1:
            warnings_list.append(
                f"Service timeout must be positive, got {config.service.timeout}"
            )

        # Check for environment variable overrides
        env_vars_to_check = [
            "QDRANT_HOST",
            "QDRANT_PORT",
            "NEO4J_HOST",
            "NEO4J_PORT",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "REDIS_HOST",
            "REDIS_PORT",
            "OLLAMA_URL",
            "LOG_LEVEL",
        ]

        for env_var in env_vars_to_check:
            if env_var in os.environ:
                warnings_list.append(
                    f"Environment variable {env_var} is set and may override configuration"
                )

    except Exception as e:
        # Catch any unexpected errors and report as warnings
        warnings_list.append(f"Configuration validation error: {str(e)}")

    return warnings_list


def validate_required_env_vars():
    """
    Validate that required environment variables are set.

    Raises:
        ValueError: If required environment variables are missing
    """
    required_vars = ["KWE_POSTGRES_PASSWORD", "KWE_NEO4J_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}. "
            f"Please set these variables or copy .env.example to .env and configure."
        )


# Create global configuration instance
config = SystemConfig()

# Validate required environment variables on import (only warn, don't crash)
try:
    validate_required_env_vars()
except ValueError as e:
    import warnings

    warnings.warn(f"Configuration warning: {e}", UserWarning)
