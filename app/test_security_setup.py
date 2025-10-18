#!/usr/bin/env python3
"""
Test Druid security setup and check available security features
"""

from engines.unified_connector import UnifiedConnector
from config import get_settings

def test_security_features():
    print("🔐 TESTING DRUID SECURITY FEATURES")
    print("=" * 50)
    
    connector = UnifiedConnector()
    settings = get_settings()
    
    # Initialize Druid connection
    connector.initialize_connector('druid', settings.druid_config)
    
    print("1. Checking Security-Related System Tables:")
    print("-" * 40)
    
    # Check if security tables exist
    security_tables = [
        'USERS', 'ROLES', 'SCHEMATA', 'TABLE_PRIVILEGES',
        'COLUMN_PRIVILEGES', 'AUTHORIZABLES'
    ]
    
    all_tables = connector.list_tables(engine_type='druid')
    print(f"Available tables: {len(all_tables)}")
    
    for table in security_tables:
        if table in all_tables:
            print(f"✅ {table} table exists")
            # Try to query it
            try:
                result = connector.execute_query(f"SELECT * FROM INFORMATION_SCHEMA.{table} LIMIT 2", engine_type='druid')
                print(f"   📊 {len(result)} rows available")
            except Exception as e:
                print(f"   ⚠️  Cannot query: {e}")
        else:
            print(f"❌ {table} table not found")
    
    print("\n2. Testing Current User Context:")
    print("-" * 40)
    
    # Check current user/role context
    user_queries = [
        "SELECT CURRENT_USER AS current_user",
        "SELECT CURRENT_ROLE AS current_role",
        "SELECT SESSION_USER AS session_user"
    ]
    
    for query in user_queries:
        try:
            result = connector.execute_query(query, engine_type='druid')
            print(f"✅ {query}: {result.iloc[0].to_dict()}")
        except Exception as e:
            print(f"❌ {query}: {e}")
    
    print("\n3. Testing Basic Privileges:")
    print("-" * 40)
    
    # Test what we can access
    try:
        # Check schema access
        schemas = connector.execute_query(
            "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA", 
            engine_type='druid'
        )
        print(f"✅ Accessible schemas: {len(schemas)}")
        for _, row in schemas.iterrows():
            print(f"   📁 {row['SCHEMA_NAME']}")
    except Exception as e:
        print(f"❌ Schema access failed: {e}")
    
    connector.close_all()
    
    print("\n" + "=" * 50)
    print("🔍 SECURITY ASSESSMENT COMPLETE")
    print("Next: We'll test RLS and column security policies")

if __name__ == "__main__":
    test_security_features()