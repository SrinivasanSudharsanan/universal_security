#!/usr/bin/env python3
"""
Verify data tables are available and test security on them
"""

from engines.unified_connector import UnifiedConnector
from config import get_settings
import requests

def verify_data_tables():
    print("🔍 VERIFYING DATA TABLES FOR SECURITY TESTING")
    print("=" * 50)
    
    # Check datasources via API
    try:
        ds_response = requests.get("http://localhost:8888/druid/v2/datasources")
        if ds_response.status_code == 200:
            datasources = ds_response.json()
            print(f"📊 Found {len(datasources)} datasources:")
            for ds in datasources:
                print(f"   ✅ {ds}")
        else:
            print("❌ No datasources found yet")
            return
    except Exception as e:
        print(f"❌ Error checking datasources: {e}")
        return
    
    # Initialize connector and test security
    connector = UnifiedConnector()
    settings = get_settings()
    
    try:
        connector.initialize_connector('druid', settings.druid_config)
        
        # Get all tables (including our new datasources)
        all_tables = connector.list_tables(engine_type='druid')
        print(f"\n📋 All available tables: {len(all_tables)}")
        
        # Filter out INFORMATION_SCHEMA tables to find our data tables
        data_tables = [t for t in all_tables if not t.startswith('INFORMATION_SCHEMA.')]
        print(f"�� Data tables: {data_tables}")
        
        # Test each data table
        for table in data_tables:
            print(f"\n🧪 Testing table: {table}")
            try:
                # Try to query the table
                result = connector.execute_query(f"SELECT * FROM {table} LIMIT 2", engine_type='druid')
                print(f"   ✅ Accessible - {len(result)} rows, {len(result.columns)} columns")
                print(f"   📝 Columns: {list(result.columns)}")
                
                if len(result) > 0:
                    print(f"   👁️  Sample data: {result.iloc[0].to_dict()}")
                    
            except Exception as e:
                print(f"   ❌ Cannot query: {e}")
                
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        connector.close_all()
    
    print("\n" + "=" * 50)
    print("🎯 NEXT: Once you have data tables, run security tests!")
    print("   python app/information_schema_security_test.py")

if __name__ == "__main__":
    verify_data_tables()
