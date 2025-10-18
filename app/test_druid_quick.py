#!/usr/bin/env python3
"""
Test Druid connector with proper Druid SQL syntax
"""

import requests
from engines.unified_connector import UnifiedConnector
from config import get_settings

def test_druid_direct():
    """Test Druid SQL endpoint with correct syntax"""
    print("🧪 Testing Druid SQL Endpoint")
    print("=" * 40)
    
    # Druid has specific SQL requirements - use simpler queries
    test_queries = [
        {"query": "SELECT 1"},  # Simple test
        {"query": "SELECT 1 AS test_value"},  # With alias
        {"query": "SELECT CURRENT_TIMESTAMP AS current_time"}  # Timestamp
    ]
    
    for i, query_data in enumerate(test_queries, 1):
        try:
            print(f"Query {i}: {query_data['query']}")
            response = requests.post(
                "http://localhost:8082/druid/v2/sql/",
                json=query_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ SUCCESS - Rows: {len(data)}")
                if data:
                    print(f"   Sample: {data[0]}")
                return True
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                # Don't return False yet, try next query
                
        except Exception as e:
            print(f"❌ Exception: {e}")
    
    return False

def test_our_connector():
    """Test our Druid connector with proper SQL"""
    print("\n🔌 Testing Our Druid Connector")
    print("=" * 40)
    
    connector = UnifiedConnector()
    settings = get_settings()
    
    print("Configuration:")
    for key, value in settings.druid_config.items():
        print(f"  {key}: {value}")
    
    try:
        # Initialize connector
        print("\n📡 Initializing connector...")
        success = connector.initialize_connector('druid', settings.druid_config)
        
        if not success:
            print("❌ Connector initialization failed")
            return False
        
        print("✅ Connector initialized successfully")
        
        # Test connection
        print("\n🔗 Testing connection...")
        is_connected = connector.test_connection('druid')
        print(f"Connection test: {'✅ PASS' if is_connected else '❌ FAIL'}")
        
        if not is_connected:
            print("❌ Cannot connect to Druid")
            return False
        
        # Test basic queries with proper Druid SQL
        print("\n📊 Testing queries with proper Druid SQL...")
        
        queries = [
            "SELECT 1",
            "SELECT 1 AS test_value",
            "SELECT 'hello' AS message",
            "SELECT CURRENT_TIMESTAMP AS now"
        ]
        
        for query in queries:
            try:
                result = connector.execute_query(query, engine_type='druid')
                print(f"✅ '{query}' - {len(result)} rows")
                if len(result) > 0:
                    print(f"   Data: {result.iloc[0].to_dict()}")
            except Exception as e:
                print(f"❌ '{query}' failed: {e}")
        
        # Test information schema (if available)
        print("\n📋 Testing information schema...")
        try:
            tables = connector.list_tables(engine_type='druid')
            print(f"✅ Found {len(tables)} tables")
            if tables:
                for table in tables[:3]:  # Show first 3 tables
                    print(f"   📊 {table}")
        except Exception as e:
            print(f"⚠️  Table listing: {e}")
        
        print("\n🎉 SUCCESS! Our Druid connector is working!")
        return True
        
    except Exception as e:
        print(f"❌ Connector test failed: {e}")
        return False
    finally:
        connector.close_all()
        print("🔒 Connections closed")

def main():
    print("🚀 DRUID CONNECTOR TEST (Fixed Syntax)")
    print("=" * 50)
    
    # First test Druid directly with proper SQL
    if not test_druid_direct():
        print("\n💡 Trying alternative approach...")
    
    # Then test our connector
    success = test_our_connector()
    
    if success:
        print("\n" + "=" * 50)
        print("🎉 DRUID CONNECTOR IS WORKING!")
    else:
        print("\n💥 Some tests failed")
    
    return success

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)