"""
LTMC Legacy Removal - Main Orchestration Entry Point
Unified entry point for coordinated legacy code removal workflow.

Uses extracted modular components for clean architecture:
- LegacyCodeAnalyzer: Analysis agent
- SafetyValidator: Validation agent  
- CoordinatedLegacyRemovalWorkflow: Master orchestrator

Replaces the monolithic legacy_removal_coordinated_agents.py file.
"""

from .legacy_removal_workflow import CoordinatedLegacyRemovalWorkflow


def main():
    """
    Main entry point for coordinated legacy code removal.
    
    Creates and executes the complete coordinated workflow using
    all extracted modular components and comprehensive LTMC tool integration.
    
    Returns:
        Dict[str, Any]: Complete workflow results
    """
    print("🚀 LTMC Legacy Removal - Coordinated Agent Workflow")
    print("Using Modular Architecture with Extracted Components")
    print("=" * 70)
    
    # Create and execute coordinated workflow
    workflow = CoordinatedLegacyRemovalWorkflow()
    
    # Execute complete legacy removal process
    results = workflow.execute_coordinated_legacy_removal()
    
    if results.get('success'):
        print("\n🎉 LEGACY REMOVAL WORKFLOW COMPLETED SUCCESSFULLY!")
        print(f"📊 Workflow ID: {results.get('workflow_id')}")
        print(f"🔍 Legacy Analysis: {len(results.get('analysis_results', {}).get('legacy_decorators', []))} decorators found")
        print(f"✅ Safety Validation: {results.get('validation_results', {}).get('validation_report', {}).get('safety_score', 0):.1f}% safety score")
        print(f"📋 Removal Plan: {results.get('removal_plan', {}).get('tasks_created', 0)} tasks created")
    else:
        print(f"\n❌ WORKFLOW FAILED: {results.get('error', 'Unknown error')}")
        print("Check logs for detailed error information")
    
    return results


if __name__ == "__main__":
    main()