#!/usr/bin/env python3
"""
Check what tables are actually available in Druid for security testing
"""

from engines.unified_connector import UnifiedConnector
from config import get_settings

def check_available_tables():
    print("📋 CHECKING AVAILABLE TABLES FOR SECURITY TESTING")
    print("=" * 50)
    
    connector = UnifiedConnector()
    settings = get_settings()
    
    connector.initialize_connector('druid', settings.druid_config)
    
    # Get all available tables
    all_tables = connector.list_tables(engine_type='druid')
    
    print(f"Total tables available: {len(all_tables)}")
    print("\nAvailable tables:")
    for table in all_tables:
        print(f"  📋 {table}")
        
        # Try to get table info
        try:
            # Get column information
            result = connector.execute_query(
                f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}'",
                engine_type='druid'
            )
            print(f"     Columns: {len(result)}")
            for _, row in result.iterrows():
                print(f"       {row['COLUMN_NAME']} ({row['DATA_TYPE']})")
                
        except Exception as e:
            print(f"     ❌ Could not get schema: {e}")
    
    print("\n2. Testing Data Access on Available Tables:")
    print("-" * 40)
    
    # Test each table with a simple query
    for table in all_tables[:3]:  # Test first 3 tables
        try:
            print(f"\nTesting table: {table}")
            result = connector.execute_query(f"SELECT * FROM {table} LIMIT 2", engine_type='druid')
            print(f"✅ Accessible - {len(result)} rows, {len(result.columns)} columns")
            if len(result) > 0:
                print(f"   Sample columns: {list(result.columns)[:5]}")  # Show first 5 columns
        except Exception as e:
            print(f"❌ Cannot access: {e}")
    
    connector.close_all()
    
    print("\n" + "=" * 50)
    print("💡 RECOMMENDATION:")
    print("   Use INFORMATION_SCHEMA tables for security testing")
    print("   They contain structured data perfect for role-based testing")

if __name__ == "__main__":
    check_available_tables()
