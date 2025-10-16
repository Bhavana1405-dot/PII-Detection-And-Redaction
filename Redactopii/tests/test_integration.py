# =============================================================================
# FILE: test_integration.py
# DESCRIPTION: Quick test to verify setup
# =============================================================================

"""
Quick integration test
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "Redactopii"))

from Redactopii.core.redaction_engine import RedactionEngine
from Redactopii.core.config import RedactionConfig
from Redactopii.integrations.octopii_adapter import OctopiiAdapter

def test_adapter():
    """Test Octopii adapter"""
    print("Testing Octopii Adapter...")
    
    sample_report = {
        "file_path": "test.txt",
        "pii_class": "financial",
        "score": 67,
        "country_of_origin": "US",
        "faces": 0,
        "identifiers": ["123-45-6789"],
        "emails": ["test@example.com"],
        "phone_numbers": ["+1-555-123-4567"],
        "addresses": ["123 Main St"]
    }
    
    adapter = OctopiiAdapter()
    entities = adapter.parse_report(sample_report)
    
    print(f"  ✓ Found {len(entities)} PII entities")
    for entity in entities:
        print(f"    - {entity.entity_type.value}: {entity.value}")
    
    return len(entities) > 0

def test_engine():
    """Test redaction engine"""
    print("\nTesting Redaction Engine...")
    
    config = RedactionConfig()
    engine = RedactionEngine(config)
    
    print(f"  ✓ Engine initialized")
    print(f"  ✓ Output directories:")
    for name, path in engine.output_dirs.items():
        print(f"    - {name}: {path}")
    
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Integration Test")
    print("=" * 60)
    
    try:
        test1 = test_adapter()
        test2 = test_engine()
        
        if test1 and test2:
            print("\n" + "=" * 60)
            print("✓ All tests passed!")
            print("=" * 60)
            print("\nReady to use! Try:")
            print("  python Redactopii/redactopii.py --help")
            sys.exit(0)
        else:
            print("\n✗ Some tests failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)