#!/usr/bin/env python3
"""
Minimal test to check basic imports
"""

print("🔧 Testing basic imports...")

try:
    import pandas as pd
    print("✅ pandas imported")
except ImportError as e:
    print(f"❌ pandas: {e}")

try:
    from config import Settings
    print("✅ Settings imported")
    settings = Settings()
    print("✅ Settings instance created")
except ImportError as e:
    print(f"❌ Settings: {e}")

try:
    from engines.unified_connector import UnifiedConnector
    print("✅ UnifiedConnector imported")
    
    # Test creating an instance
    connector = UnifiedConnector()
    print("✅ UnifiedConnector instance created")
    
except ImportError as e:
    print(f"❌ UnifiedConnector: {e}")
except Exception as e:
    print(f"❌ UnifiedConnector instantiation: {e}")

print("\n🎉 Basic import test completed!")