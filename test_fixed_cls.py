#!/usr/bin/env python3
"""
Test the fixed CLS engine
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_fixed_cls():
    """Test the fixed CLS engine"""
    
    print("🧪 Testing Fixed CLS Engine")
    print("=" * 40)
    
    try:
        from app.security.policies.column_level.cls_engine import UniversalClsEngine
        from app.utils.db_utils import DatabaseManager
        
        database_pool = await DatabaseManager.get_pool()
        
        async def execute_database_query(query_string, *query_parameters):
            async with database_pool.acquire() as connection:
                print(f"📊 Executing: {query_string[:100]}...")
                result = await connection.fetch(query_string, *query_parameters)
                print(f"📊 Query returned {len(result)} rows")
                return result
        
        cls_engine = UniversalClsEngine(execute_database_query)
        
        print("🔄 Initializing fixed CLS engine...")
        await cls_engine.initialize_engine()
        
        status = cls_engine.get_engine_status()
        print(f"📊 Fixed CLS Engine Status: {status}")
        
        # Test policy access
        print("\n🔍 Testing policy access with fixed engine...")
        
        # Test employees table
        admin_cols = await cls_engine.get_allowed_columns(['admin'], 'employees')
        print(f"✅ Admin columns for employees: {len(admin_cols)}")
        if admin_cols:
            print(f"   Sample: {[col['column_name'] for col in admin_cols[:3]]}")
        
        analyst_cols = await cls_engine.get_allowed_columns(['analyst'], 'employees')
        print(f"✅ Analyst columns for employees: {len(analyst_cols)}")
        
        # Test sales table  
        admin_sales = await cls_engine.get_allowed_columns(['admin'], 'sales')
        print(f"✅ Admin columns for sales: {len(admin_sales)}")
        
        # Test specific column access
        salary_access = await cls_engine.get_column_access(['admin'], 'employees', 'salary_sum')
        print(f"✅ Admin salary access: {salary_access}")
        
        salary_analyst = await cls_engine.get_column_access(['analyst'], 'employees', 'salary_sum')
        print(f"✅ Analyst salary access: {salary_analyst}")
        
        customer_access = await cls_engine.get_column_access(['analyst'], 'sales', 'customer')
        print(f"✅ Analyst customer access: {customer_access}")
        
        await DatabaseManager.close_pool()
        
        print("\n🎉 Fixed CLS Engine Test Completed!")
        
    except Exception as e:
        print(f"❌ Fixed CLS test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_fixed_cls())
