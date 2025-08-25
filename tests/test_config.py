#!/usr/bin/env python3
"""
Simple test script for LTMC centralized configuration
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ltms.config.centralized_config import ConfigManager

def test_configuration():
    """Test the centralized configuration system"""
    print("Testing LTMC Centralized Configuration System")
    print("=" * 50)
    
    # Initialize configuration manager
    config_manager = CentralizedConfigManager()
    
    # List available instances
    instances = config_manager.list_instances()
    print(f"Available instances: {instances}")
    
    # Test each instance
    for instance_name in instances:
        print(f"\n--- Testing Instance: {instance_name} ---")
        
        # Get instance configuration
        config = config_manager.get_instance(instance_name)
        if not config:
            print(f"  ❌ Failed to load configuration")
            continue
        
        # Display configuration
        print(f"  Description: {config.description}")
        print(f"  Data Directory: {config.data_dir}")
        print(f"  Uses SQLite: {config.use_sqlite}")
        print(f"  Uses FAISS: {config.use_faiss}")
        
        if config.use_sqlite and config.database:
            print(f"  Database: {config.database.path}")
        else:
            print(f"  Database: Not used")
        
        if config.use_faiss and config.faiss:
            print(f"  FAISS Index: {config.faiss.path}")
        else:
            print(f"  FAISS Index: Not used")
        
        print(f"  Redis: {config.redis.host}:{config.redis.port}")
        print(f"  Neo4j: {config.neo4j.uri}")
        
        # Validate instance
        is_valid, errors = config_manager.validate_instance(instance_name)
        if is_valid:
            print(f"  ✅ Configuration valid")
        else:
            print(f"  ⚠️  Configuration issues:")
            for error in errors:
                print(f"    - {error}")
        
        # Get environment variables
        env_vars = config_manager.get_environment_vars(instance_name)
        print(f"  Environment variables: {len(env_vars)} set")
    
    print("\n" + "=" * 50)
    print("Configuration test completed!")

if __name__ == "__main__":
    test_configuration()
