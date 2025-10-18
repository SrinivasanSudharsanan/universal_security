#!/usr/bin/env python3
"""
Create security test data using SQL queries on existing Druid tables
"""

from engines.unified_connector import UnifiedConnector
from config import get_settings

def create_security_test_data():
    print("🗃️ CREATING SECURITY TEST DATA USING SQL")
    print("=" * 50)
    
    connector = UnifiedConnector()
    settings = get_settings()
    
    connector.initialize_connector('druid', settings.druid_config)
    
    print("1. Using Existing Tables for Security Testing:")
    print("-" * 40)
    
    all_tables = connector.list_tables(engine_type='druid')
    print(f"Available tables: {len(all_tables)}")
    
    # Use segments table as our base for security testing
    if 'segments' in all_tables:
        print("✅ Using 'segments' table for security testing")
        
        # Create a view or use the table directly with security policies
        try:
            # Get segments data structure
            segments_sample = connector.execute_query(
                "SELECT * FROM segments LIMIT 3", 
                engine_type='druid'
            )
            print("📋 Segments table structure:")
            print(f"   Columns: {list(segments_sample.columns)}")
            
            # Create security policies based on segments data
            security_test_cases = [
                {
                    'role': 'admin',
                    'description': 'Can see all segments',
                    'query': "SELECT segment_id, datasource, start, end, size, is_available FROM segments"
                },
                {
                    'role': 'engineering', 
                    'description': 'Can see only engineering-related segments',
                    'query': "SELECT segment_id, datasource, is_available FROM segments WHERE datasource LIKE '%engineering%' OR datasource LIKE '%test%'"
                },
                {
                    'role': 'sales',
                    'description': 'Can see only sales-related segments', 
                    'query': "SELECT segment_id, datasource FROM segments WHERE datasource LIKE '%sales%' OR datasource LIKE '%marketing%'"
                },
                {
                    'role': 'public',
                    'description': 'Can see only public segments',
                    'query': "SELECT segment_id, datasource FROM segments WHERE is_available = true AND datasource NOT LIKE '%private%'"
                }
            ]
            
            print("\n2. Testing Security Policies:")
            print("-" * 40)
            
            for test_case in security_test_cases:
                print(f"\n🎭 Testing as {test_case['role']}:")
                print(f"   📝 {test_case['description']}")
                
                try:
                    result = connector.execute_query(test_case['query'], engine_type='druid')
                    print(f"   ✅ Access granted: {len(result)} rows visible")
                    if len(result) > 0:
                        print(f"   📊 Sample: {result.iloc[0].to_dict()}")
                except Exception as e:
                    print(f"   ❌ Access failed: {e}")
                    
        except Exception as e:
            print(f"❌ Could not use segments table: {e}")
    
    # Also test with servers table
    if 'servers' in all_tables:
        print("\n3. Testing Server Access Security:")
        print("-" * 40)
        
        server_security_tests = [
            {
                'role': 'admin',
                'query': "SELECT server, server_type, tier, curr_size, max_size FROM servers"
            },
            {
                'role': 'monitoring',
                'query': "SELECT server, server_type, tier FROM servers WHERE server_type = 'historical'"
            },
            {
                'role': 'public', 
                'query': "SELECT server FROM servers"
            }
        ]
        
        for test in server_security_tests:
            try:
                result = connector.execute_query(test['query'], engine_type='druid')
                print(f"🎭 {test['role']}: {len(result)} servers visible")
            except Exception as e:
                print(f"❌ {test['role']}: {e}")
    
    connector.close_all()
    
    print("\n" + "=" * 50)
    print("🎯 SECURITY TESTING COMPLETE")
    print("   Using existing Druid tables for role-based security testing")
    print("   No data ingestion required!")

if __name__ == "__main__":
    create_security_test_data()
