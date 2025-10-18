#!/usr/bin/env python3
"""
Simple test to check Druid connection and available tables
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.engines.druid_async_connector import AsyncDruidConnector

async def test_druid_connection():
    """Test basic Druid connection"""
    
    print("🔌 Testing Druid Connection...")
    
    connector = AsyncDruidConnector()
    
    try:
        # Try with default connection parameters
        await connector.initialize()
        
        # Test connection
        is_connected = await connector.test_connection()
        print(f"✅ Connection test: {is_connected}")
        
        # List available tables
        tables = await connector.list_tables()
        print(f"📋 Available tables: {tables}")
        
        # Test a simple query on each table
        for table in tables[:3]:  # Test first 3 tables
            try:
                print(f"\n🧪 Testing table: {table}")
                
                # Simple count query
                count_query = f"SELECT COUNT(*) as row_count FROM {table}"
                result = await connector.execute_query(count_query)
                print(f"   📊 Row count: {result}")
                
                # Sample data query
                sample_query = f"SELECT * FROM {table} LIMIT 2"
                sample_result = await connector.execute_query(sample_query)
                print(f"   🔍 Sample data: {len(sample_result)} rows")
                
                if sample_result:
                    print(f"   📝 Columns: {list(sample_result[0].keys())}")
                    
            except Exception as e:
                print(f"   ❌ Table {table} query failed: {e}")
                
    except Exception as e:
        print(f"❌ Druid connection failed: {e}")
        
        # Try alternative connection parameters
        print("\n🔄 Trying alternative connection parameters...")
        alternative_configs = [
            {'host': 'localhost', 'port': 8888, 'path': '/druid/v2/sql/', 'scheme': 'http'},
            {'host': '127.0.0.1', 'port': 8082, 'path': '/druid/v2/sql/', 'scheme': 'http'},
            {'host': 'localhost', 'port': 8082, 'path': '/sql/', 'scheme': 'http'},
        ]
        
        for config in alternative_configs:
            try:
                print(f"   Trying {config}...")
                connector = AsyncDruidConnector()
                await connector.initialize(config)
                
                tables = await connector.list_tables()
                print(f"   ✅ Success! Tables: {tables}")
                break
                
            except Exception as config_error:
                print(f"   ❌ Failed: {config_error}")
    
    finally:
        await connector.close()

if __name__ == "__main__":
    asyncio.run(test_druid_connection())
