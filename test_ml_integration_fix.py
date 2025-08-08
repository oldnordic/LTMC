#!/usr/bin/env python3
"""Test the ML integration fix by attempting to initialize the AdvancedLearningIntegration."""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_ml_integration():
    """Test if ML integration initializes successfully."""
    print("Testing ML Integration Fix...")
    print("=" * 50)
    
    try:
        from ltms.ml.learning_integration import AdvancedLearningIntegration
        
        # Initialize the integration
        integration = AdvancedLearningIntegration(db_path="ltmc.db")
        
        print("Starting initialization...")
        success = await integration.initialize()
        
        if success:
            print("✅ SUCCESS: ML Integration initialized successfully!")
            
            # Get status
            status = await integration.get_integration_status()
            print(f"Integration Status: {status['overall_status']}")
            print(f"Active Components: {status['active_components']}/{status['total_components']}")
            
            # Cleanup
            await integration.cleanup()
            
        else:
            print("❌ FAILED: ML Integration initialization failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ EXCEPTION during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test function."""
    success = await test_ml_integration()
    
    if success:
        print("\n🎉 ML INTEGRATION FIX SUCCESSFUL!")
        print("Ready to restart the live server!")
    else:
        print("\n💥 ML INTEGRATION STILL HAS ISSUES")
        print("Need to investigate further...")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))