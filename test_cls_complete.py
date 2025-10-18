#!/usr/bin/env python3
"""
Complete test of the fixed CLS engine
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_cls_complete():
    """Complete test of the fixed CLS engine"""
    
    print("🧪 Complete CLS Engine Test")
    print("=" * 40)
    
    try:
        from app.security.policies.column_level.cls_engine import UniversalClsEngine
        from app.utils.db_utils import DatabaseManager
        
        database_pool = await DatabaseManager.get_pool()
        
        async def execute_database_query(query_string, *query_parameters):
            async with database_pool.acquire() as connection:
                return await connection.fetch(query_string, *query_parameters)
        
        cls_engine = UniversalClsEngine(execute_database_query)
        
        print("🔄 Initializing CLS engine...")
        await cls_engine.initialize_engine()
        
        status = cls_engine.get_engine_status()
        print(f"📊 CLS Engine Status: {status}")
        
        # Test different roles
        print(f"\n🔍 Testing Role-Based Access")
        print("-" * 30)
        
        test_cases = [
            (['admin'], "Administrator"),
            (['analyst'], "Data Analyst"),
            (['hr'], "HR Manager"),
            (['employee'], "Employee"),
            (['guest'], "Guest")
        ]
        
        for roles, role_name in test_cases:
            print(f"\n👤 {role_name} (Roles: {roles})")
            
            # Test employees table
            emp_cols = await cls_engine.get_allowed_columns(roles, 'employees')
            print(f"   📋 employees: {len(emp_cols)} columns")
            if emp_cols:
                sample_cols = [col['column_name'] for col in emp_cols[:3]]
                print(f"      Sample: {sample_cols}")
            
            # Test sales table
            sales_cols = await cls_engine.get_allowed_columns(roles, 'sales')
            print(f"   📋 sales: {len(sales_cols)} columns")
            if sales_cols:
                sample_cols = [col['column_name'] for col in sales_cols[:3]]
                print(f"      Sample: {sample_cols}")
        
        # Test specific column access
        print(f"\n🔍 Testing Specific Column Access")
        print("-" * 30)
        
        test_columns = [
            ('employees', 'salary_sum'),
            ('employees', 'name'),
            ('sales', 'customer'),
            ('sales', 'amount_sum')
        ]
        
        for table, column in test_columns:
            print(f"\n📊 {table}.{column}:")
            for roles, role_name in test_cases[:2]:  # Just admin and analyst
                access = await cls_engine.get_column_access(roles, table, column)
                status = "✅" if access['access_type'] == 'allow' else "🎭" if access['access_type'] == 'mask' else "❌"
                print(f"   {role_name:<15}: {status} {access['access_type']}" + 
                      (f" ({access['mask_type']})" if access['mask_type'] else ""))
        
        # Test query rewriting
        print(f"\n🔍 Testing Query Rewriting")
        print("-" * 30)
        
        test_queries = [
            "SELECT * FROM employees LIMIT 1",
            "SELECT name, salary_sum FROM employees WHERE department = 'Engineering'",
            "SELECT * FROM sales LIMIT 1"
        ]
        
        for query in test_queries:
            print(f"\n📝 Original: {query}")
            for roles, role_name in test_cases[:2]:
                rewritten = await cls_engine.rewrite_sql_select(query, roles, "druid")
                if rewritten != query:
                    print(f"   {role_name}: 🔄 Rewritten")
                    print(f"      {rewritten}")
                else:
                    print(f"   {role_name}: ✅ No change needed")
        
        await DatabaseManager.close_pool()
        print(f"\n🎉 Complete CLS Test Finished!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_cls_complete())
