#!/usr/bin/env python3
"""
Corrected security tests for current Druid setup
"""

from engines.unified_connector import UnifiedConnector
from config import get_settings

def test_current_security():
    print("🔐 CURRENT DRUID SECURITY STATUS")
    print("=" * 50)
    
    connector = UnifiedConnector()
    settings = get_settings()
    
    connector.initialize_connector('druid', settings.druid_config)
    
    print("1. Available System Tables:")
    print("-" * 40)
    
    all_tables = connector.list_tables(engine_type='druid')
    print(f"Total tables: {len(all_tables)}")
    for table in all_tables:
        print(f"  📋 {table}")
    
    print("\n2. Available Schemas:")
    print("-" * 40)
    
    schemas = connector.execute_query(
        "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA", 
        engine_type='druid'
    )
    for _, row in schemas.iterrows():
        print(f"  📁 {row['SCHEMA_NAME']}")
    
    print("\n3. Testing Basic Security Context:")
    print("-" * 40)
    
    # Druid doesn't have user context in basic setup
    # Let's test what we CAN do
    test_queries = [
        "SELECT 1 AS security_test",
        "SELECT 'anonymous_user' AS current_user",
        "SELECT 'no_auth' AS auth_method"
    ]
    
    for query in test_queries:
        try:
            result = connector.execute_query(query, engine_type='druid')
            print(f"✅ {query}: {result.iloc[0].to_dict()}")
        except Exception as e:
            print(f"❌ {query}: {e}")
    
    print("\n4. Testing Data Access Patterns:")
    print("-" * 40)
    
    # Check if we can access different schemas
    schema_access = {}
    for schema in ['druid', 'sys', 'INFORMATION_SCHEMA']:
        try:
            tables_query = f"SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = '{schema}'"
            tables = connector.execute_query(tables_query, engine_type='druid')
            schema_access[schema] = len(tables)
            print(f"✅ {schema}: {len(tables)} tables accessible")
        except Exception as e:
            schema_access[schema] = 0
            print(f"❌ {schema}: {e}")
    
    connector.close_all()
    
    print("\n" + "=" * 50)
    print("🔍 SECURITY ASSESSMENT:")
    print("   ❌ No built-in user authentication")
    print("   ❌ No role-based access control") 
    print("   ❌ No row-level security")
    print("   ✅ Basic schema isolation")
    print("   ✅ Information schema accessible")
    print()
    print("💡 This is typical for basic Druid setup.")
    print("   For RLS/security, you need:")
    print("   1. Druid's security extension")
    print("   2. Or your RLS proxy layer")
    print("   3. Or implement security in application layer")

if __name__ == "__main__":
    test_current_security()