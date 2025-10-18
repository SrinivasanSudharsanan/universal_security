#!/usr/bin/env python3
"""
Test CLS Integration with Druid - Working version
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_cls_integration():
    """Test CLS integration with Druid"""
    
    print("🧪 Testing CLS Integration with Druid")
    print("=" * 50)
    
    try:
        # Try to import the CLS connector
        try:
            from app.engines.druid_cls_connector import DruidClsConnector
            print("✅ Successfully imported DruidClsConnector")
        except ImportError as e:
            print(f"❌ Import failed: {e}")
            print("Available files in app/engines/:")
            import os
            if os.path.exists('app/engines'):
                for f in os.listdir('app/engines'):
                    print(f"  - {f}")
            return
        
        # Initialize connector
        connector = DruidClsConnector()
        print("🔄 Initializing CLS connector...")
        
        try:
            await connector.initialize()
            print("✅ CLS connector initialized successfully")
        except Exception as e:
            print(f"❌ Connector initialization failed: {e}")
            return
        
        # Check status
        try:
            status = connector.get_connector_status()
            print("\n📊 Connector Status:")
            print(f"   CLS Engine: {status['cls_engine_initialized']}")
            print(f"   Druid Connected: {status['druid_connected']}")
            print(f"   Policies Loaded: {status['cls_status'].get('total_policies', 0)}")
            print(f"   Tables Covered: {status['cls_status'].get('tables_covered', 0)}")
        except Exception as e:
            print(f"❌ Status check failed: {e}")
        
        # Test basic functionality
        print("\n🔍 Testing Basic CLS Functionality")
        print("-" * 30)
        
        # Test 1: Table access information
        test_tables = ['employees', 'sales']
        test_roles = [['admin'], ['analyst'], ['employee']]
        
        for table in test_tables:
            print(f"\n📋 Table: {table}")
            for roles in test_roles:
                try:
                    table_info = await connector.get_secure_table_info(roles, table)
                    accessible = table_info.get('accessible', False)
                    if accessible:
                        allowed_cols = len(table_info.get('allowed_columns', []))
                        print(f"   👥 {roles}: ✅ Accessible ({allowed_cols} columns)")
                    else:
                        print(f"   👥 {roles}: ❌ No access")
                except Exception as e:
                    print(f"   👥 {roles}: ⚠️ Error: {str(e)[:50]}")
        
        # Test 2: Simple queries
        print("\n🔍 Testing Queries with CLS")
        print("-" * 30)
        
        queries = [
            ("SELECT name, department FROM employees LIMIT 2", "Employee Data"),
            ("SELECT product, region FROM sales LIMIT 2", "Sales Data")
        ]
        
        for query, description in queries:
            print(f"\n{description}:")
            print(f"Query: {query}")
            
            for roles in [['admin'], ['analyst']]:
                try:
                    results = await connector.execute_secure_query(
                        query=query,
                        user_roles=roles,
                        user_id=f"test_{roles[0]}"
                    )
                    print(f"   👥 {roles}: {len(results)} results")
                    if results:
                        print(f"      Columns: {list(results[0].keys())}")
                except Exception as e:
                    print(f"   👥 {roles}: ❌ {str(e)[:60]}")
        
        # Test 3: Show security differences
        print("\n🛡️ Testing Security Enforcement")
        print("-" * 30)
        
        sensitive_query = "SELECT name, salary_sum, customer, amount_sum FROM (SELECT * FROM employees LIMIT 1) e, (SELECT * FROM sales LIMIT 1) s"
        
        print(f"Query: {sensitive_query}")
        
        for roles, role_name in [(['admin'], 'Admin'), (['analyst'], 'Analyst')]:
            try:
                results = await connector.execute_secure_query(
                    query=sensitive_query,
                    user_roles=roles,
                    user_id=f"security_test_{role_name.lower()}"
                )
                print(f"   👤 {role_name}: {len(results)} results")
                if results:
                    print(f"      Visible data: {list(results[0].keys())}")
            except Exception as e:
                print(f"   👤 {role_name}: ❌ {str(e)[:60]}")
        
        # Cleanup
        await connector.close()
        print("\n🎉 CLS Integration Test Completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cls_integration())
