#!/usr/bin/env python3
"""
Quick smoke test for connectors
"""

import sys
import os

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.unified_connector import UnifiedConnector
from config import get_settings

def quick_test():
    """Quick test to verify basic functionality"""
    print("🔧 Running quick connector test...")
    
    connector = UnifiedConnector()
    settings = get_settings()
    
    # Test each connector
    engines = [
        ('databricks', settings.databricks_config),
        ('snowflake', settings.snowflake_config),
        ('druid', settings.druid_config),
        ('iceberg', settings.iceberg_config)
    ]
    
    for engine_type, config in engines:
        print(f"\nTesting {engine_type}...")
        try:
            # Initialize connector
            success = connector.initialize_connector(engine_type, config)
            print(f"  Initialization: {'✅ SUCCESS' if success else '❌ FAILED'}")
            
            if success:
                # Test connection
                is_connected = connector.test_connection(engine_type)
                print(f"  Connection test: {'✅ PASS' if is_connected else '❌ FAIL'}")
                
                # Try to list tables
                try:
                    tables = connector.list_tables(engine_type=engine_type)
                    print(f"  List tables: ✅ WORKS ({len(tables)} tables)")
                except NotImplementedError:
                    print(f"  List tables: ⚠ NOT IMPLEMENTED")
                except Exception as e:
                    print(f"  List tables: ❌ ERROR - {e}")
            
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
    
    # Clean up
    connector.close_all()
    print("\n🧹 All connections closed")
    print("\n✅ Quick test completed!")

if __name__ == "__main__":
    quick_test()