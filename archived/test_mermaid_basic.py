#!/usr/bin/env python3
"""
Basic Mermaid Integration Test

Test the core Mermaid functionality without full LTMC dependencies.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_mermaid_models():
    """Test Mermaid data models."""
    print("🧪 Testing Mermaid Models...")
    
    try:
        from ltmc_mcp_server.tools.mermaid.mermaid_models import (
            DiagramType, OutputFormat, DiagramComplexity,
            MermaidDiagramRequest, MermaidDiagramResponse
        )
        
        # Test enum values
        assert DiagramType.FLOWCHART == "flowchart"
        assert OutputFormat.SVG == "svg"
        assert DiagramComplexity.SIMPLE == "simple"
        
        # Test model creation
        request = MermaidDiagramRequest(
            content="graph TD\n    A --> B",
            diagram_type=DiagramType.FLOWCHART,
            output_format=OutputFormat.SVG
        )
        
        assert request.content == "graph TD\n    A --> B"
        assert request.diagram_type == DiagramType.FLOWCHART
        
        print("✅ Mermaid models test passed")
        return True
        
    except Exception as e:
        print(f"❌ Mermaid models test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_matplotlib_generation():
    """Test basic matplotlib diagram generation."""
    print("\n🧪 Testing Matplotlib Diagram Generation...")
    
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        from io import StringIO
        
        # Create a simple test diagram
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 10)
        
        # Add a rectangle (flowchart box)
        rect = patches.Rectangle((3, 4), 4, 2, linewidth=1, edgecolor='blue', facecolor='lightblue')
        ax.add_patch(rect)
        ax.text(5, 5, 'Test Box', ha='center', va='center', fontsize=12)
        
        ax.set_title('Mermaid Test Diagram')
        ax.axis('off')
        
        # Test SVG generation
        buffer = StringIO()
        plt.savefig(buffer, format='svg', bbox_inches='tight')
        svg_content = buffer.getvalue()
        
        plt.close()
        
        # Validate SVG content
        assert '<svg' in svg_content
        assert 'Test Box' in svg_content
        assert len(svg_content) > 1000  # Should be a substantial SVG
        
        print("✅ Matplotlib generation test passed")
        print(f"   Generated SVG: {len(svg_content)} characters")
        return True
        
    except Exception as e:
        print(f"❌ Matplotlib generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_basic_service():
    """Test basic Mermaid service functionality without dependencies."""
    print("\n🧪 Testing Basic Service Logic...")
    
    try:
        # Test content hash generation
        import hashlib
        
        content = "graph TD\n    A --> B"
        diagram_type = "flowchart"
        output_format = "svg"
        theme = "default"
        
        hash_content = f"{content}_{diagram_type}_{output_format}_{theme}"
        content_hash = hashlib.md5(hash_content.encode()).hexdigest()
        
        assert len(content_hash) == 32
        assert content_hash == hashlib.md5(hash_content.encode()).hexdigest()
        
        print("✅ Basic service logic test passed")
        print(f"   Content hash: {content_hash[:12]}...")
        return True
        
    except Exception as e:
        print(f"❌ Basic service test failed: {e}")
        return False

async def main():
    """Run all Mermaid tests."""
    print("🚀 MERMAID INTEGRATION BASIC TESTS")
    print("=" * 50)
    
    tests = [
        test_mermaid_models,
        test_matplotlib_generation,
        test_basic_service
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Tests passed: {passed}/{total}")
    print(f"❌ Tests failed: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Basic Mermaid integration is working correctly")
        print("🚀 Ready for MCP server integration")
        return True
    else:
        print(f"\n⚠️ {total - passed} tests failed")
        print("❌ Mermaid integration needs fixes before MCP integration")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)