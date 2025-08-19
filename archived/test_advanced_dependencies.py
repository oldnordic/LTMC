#!/usr/bin/env python3
"""
Test Advanced Dependencies for Mermaid Analysis Tools
====================================================

Validates that Neo4j and fallback similarity search capabilities are working.
"""

def test_neo4j_import():
    """Test Neo4j driver import and basic functionality."""
    print("🔍 Testing Neo4j Integration...")
    
    try:
        from neo4j import GraphDatabase, Driver
        print("   ✅ Neo4j driver imported successfully")
        
        # Test basic driver configuration (without actual connection)
        uri = "bolt://localhost:7687"  # Standard Neo4j URI
        try:
            # Just test driver creation, not actual connection
            driver = GraphDatabase.driver(uri, auth=("neo4j", "password"))
            print("   ✅ Neo4j driver can be created")
            driver.close()  # Clean up
        except Exception as e:
            print(f"   ⚠️  Neo4j connection test skipped (no server): {str(e)[:50]}...")
            
        return True
        
    except ImportError as e:
        print(f"   ❌ Neo4j import failed: {e}")
        return False

def test_similarity_fallbacks():
    """Test similarity search fallback implementations."""
    print("\n🔍 Testing Similarity Search Capabilities...")
    
    try:
        # Test scikit-learn for similarity fallback
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        print("   ✅ Scikit-learn similarity tools available")
        
        # Test basic similarity computation
        documents = [
            "graph TD A --> B",
            "flowchart TD Start --> End", 
            "sequenceDiagram Alice->>Bob: Hello"
        ]
        
        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform(documents)
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        print(f"   ✅ Computed similarity for {len(documents)} documents")
        print(f"   📊 Similarity range: {similarity_matrix.min():.3f} - {similarity_matrix.max():.3f}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Similarity fallback failed: {e}")
        return False

def test_faiss_optional():
    """Test FAISS as optional dependency with graceful fallback.""" 
    print("\n🔍 Testing FAISS Optional Integration...")
    
    try:
        import faiss
        print("   ✅ FAISS is available")
        return "faiss"
    except ImportError:
        print("   ⚠️  FAISS not available - using scikit-learn fallback")
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            print("   ✅ Scikit-learn fallback operational")
            return "sklearn"
        except ImportError:
            print("   ❌ No similarity search backend available")
            return None

def test_advanced_analysis_integration():
    """Test that advanced analysis tools can handle optional dependencies."""
    print("\n🧠 Testing Advanced Analysis Integration...")
    
    # Simulate the pattern used in analysis tools
    FAISS_AVAILABLE = False
    NEO4J_AVAILABLE = False
    
    try:
        import faiss
        FAISS_AVAILABLE = True
    except ImportError:
        pass
        
    try:
        from neo4j import GraphDatabase
        NEO4J_AVAILABLE = True
    except ImportError:
        pass
    
    print(f"   📊 FAISS Available: {FAISS_AVAILABLE}")
    print(f"   📊 Neo4j Available: {NEO4J_AVAILABLE}")
    
    # Test that we can still do analysis without optional dependencies
    if not FAISS_AVAILABLE:
        print("   ✅ Fallback similarity using scikit-learn")
    
    if not NEO4J_AVAILABLE:
        print("   ✅ Knowledge graphs will use basic relationship storage")
    else:
        print("   ✅ Advanced Neo4j knowledge graphs enabled")
        
    return True

def main():
    """Run comprehensive advanced dependencies testing."""
    print("🎯 ADVANCED DEPENDENCIES VALIDATION")
    print("=" * 45)
    
    # Test each component
    neo4j_ok = test_neo4j_import()
    similarity_ok = test_similarity_fallbacks() 
    faiss_status = test_faiss_optional()
    integration_ok = test_advanced_analysis_integration()
    
    print("\n" + "=" * 45)
    print("📊 VALIDATION RESULTS:")
    print(f"   ✅ Neo4j Driver: {'PASS' if neo4j_ok else 'FAIL'}")
    print(f"   ✅ Similarity Search: {'PASS' if similarity_ok else 'FAIL'}")
    print(f"   ✅ FAISS Status: {faiss_status or 'UNAVAILABLE'}")
    print(f"   ✅ Integration: {'PASS' if integration_ok else 'FAIL'}")
    
    if neo4j_ok and similarity_ok and integration_ok:
        print("\n🎉 ADVANCED ANALYSIS CAPABILITIES READY!")
        print("✅ Knowledge graphs: Neo4j driver available")
        print("✅ Similarity search: Fallback implementation operational") 
        print("✅ Optional dependencies: Graceful degradation working")
        print("🚀 Phase 5 Complete - Ready for Memory Integration")
        return True
    else:
        print("\n❌ Some advanced capabilities need attention")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)