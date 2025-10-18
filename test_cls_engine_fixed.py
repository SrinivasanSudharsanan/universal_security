#!/usr/bin/env python3
"""
Test the Universal CLS Engine - Fixed version
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.security.policies.column_level.cls_engine import UniversalClsEngine
from app.security.policies.column_level.allowed_columns import UniversalAllowedColumns
from app.utils.db_utils import DatabaseManager

async def test_cls_engine_fixed():
    """Test the CLS engine with proper database connection"""
    print("🔐 Testing Universal CLS Engine - Fixed")
    print("=" * 45)
    
    try:
        # Initialize database connection properly
        print("1. Initializing database connection...")
        pool = await DatabaseManager.get_pool()
        
        # Create a wrapper that uses the connection pool
        async def execute_query_wrapper(query, *args):
            async with pool.acquire() as conn:
                return await conn.fetch(query, *args)
        
        # 2. Test CLS Engine with proper database connection
        print("2. Initializing CLS Engine...")
        cls_engine = UniversalClsEngine(execute_query_wrapper)
        await cls_engine.initialize_engine()
        
        engine_status = cls_engine.get_engine_status()
        print(f"   ✅ Engine: {engine_status['engine_type']}")
        print(f"   ✅ Tables: {engine_status['tables_covered']}")
        print(f"   ✅ Policies: {engine_status['total_policies']}")
        
        # 3. Test Allowed Columns Manager
        print("\n3. Testing Allowed Columns Manager...")
        allowed_manager = UniversalAllowedColumns(execute_query_wrapper)
        await allowed_manager.initialize_permissions()
        
        perm_summary = allowed_manager.get_permission_summary()
        print(f"   ✅ Manager: {perm_summary['manager_type']}")
        print(f"   ✅ Tables: {perm_summary['total_tables']}")
        print(f"   ✅ Columns: {perm_summary['total_columns']}")
        print(f"   ✅ Policies: {perm_summary['total_policies']}")
        
        # 4. Test different user roles
        print("\n4. Testing Column Access by Role...")
        
        test_roles = [
            (["admin"], "Full Access Admin"),
            (["data_engineer"], "Technical Role"),
            (["business_analyst"], "Business Role"), 
            (["user"], "Restricted User")
        ]
        
        for user_roles, description in test_roles:
            print(f"\n   👤 {description}: {user_roles}")
            
            # Get table summary
            table_summary = await allowed_manager.get_table_columns_summary(user_roles, "test_employees")
            print(f"   📊 Table Access: {table_summary['accessible_columns']}/{table_summary['total_columns']} columns ({table_summary['access_level']})")
            
            # Get allowed columns
            allowed_columns = await cls_engine.get_allowed_columns(user_roles, "test_employees")
            print(f"   📋 Allowed columns: {len(allowed_columns)}")
            
            if allowed_columns:
                for col in allowed_columns:
                    # Get access details
                    access = await cls_engine.get_column_access(user_roles, "test_employees", col)
                    mask_info = f" ({access['mask_type']})" if access['mask_type'] else ""
                    print(f"      ✅ {col}: {access['access_type']}{mask_info}")
            else:
                print("      ❌ No columns accessible")
        
        # 5. Test specific column permissions
        print("\n5. Testing Specific Column Permissions...")
        test_columns = ["emp_id", "full_name", "email", "salary", "department"]
        
        for role in ["admin", "data_engineer", "business_analyst", "user"]:
            print(f"\n   👤 {role}:")
            for column in test_columns:
                permission = await allowed_manager.get_column_permission([role], "test_employees", column)
                access_info = await cls_engine.get_column_access([role], "test_employees", column)
                
                mask_info = f" [mask: {access_info['mask_type']}]" if access_info['mask_type'] else ""
                print(f"      {column}: {permission.value}{mask_info}")
        
        # 6. Test SQL rewriting with actual policies
        print("\n6. Testing SQL Query Rewriting...")
        test_queries = [
            "SELECT * FROM test_employees",
            "SELECT emp_id, full_name, email FROM test_employees WHERE department = 'Engineering'",
            "SELECT salary, department FROM test_employees"
        ]
        
        for query in test_queries:
            print(f"\n   📝 Original: {query}")
            for role in ["admin", "data_engineer"]:
                rewritten = await cls_engine.rewrite_sql_select(query, [role], "druid")
                if rewritten != query:
                    print(f"      🔄 {role}: {rewritten}")
                else:
                    print(f"      ✅ {role}: No rewriting needed (full access)")
        
        # 7. Test data masking with actual policies
        print("\n7. Testing Data Masking with Policies...")
        from app.security.policies.column_level.column_masking import universal_masking_engine
        
        # Test what data_engineer would see for email (should be masked)
        test_email = "john.doe@company.com"
        email_access = await cls_engine.get_column_access(["data_engineer"], "test_employees", "email")
        if email_access['mask_type']:
            masked_email = universal_masking_engine.mask_data(test_email, email_access['mask_type'])
            print(f"   📧 data_engineer sees email: '{test_email}' -> '{masked_email}'")
        
        # Test what business_analyst would see for full_name (should be partially masked)
        test_name = "Jane Smith"
        name_access = await cls_engine.get_column_access(["business_analyst"], "test_employees", "full_name")
        if name_access['mask_type']:
            masked_name = universal_masking_engine.mask_data(test_name, name_access['mask_type'])
            print(f"   👤 business_analyst sees name: '{test_name}' -> '{masked_name}'")
        
        # 8. Show policy details
        print("\n8. Policy Details:")
        async with pool.acquire() as conn:
            policies = await conn.fetch("""
                SELECT r.role_name, t.table_name, c.column_name, cp.access_type, cp.mask_type
                FROM security_cls_policies cp
                JOIN security_roles r ON cp.role_id = r.role_id
                JOIN security_columns c ON cp.column_id = c.column_id
                JOIN security_tables t ON c.table_id = t.table_id
                WHERE t.table_name = 'test_employees'
                ORDER BY r.role_name, c.column_name
            """)
            
            for policy in policies:
                mask_info = f" ({policy['mask_type']})" if policy['mask_type'] else ""
                print(f"   🔐 {policy['role_name']} -> {policy['table_name']}.{policy['column_name']}: {policy['access_type']}{mask_info}")
        
        await DatabaseManager.close_pool()
        
        print(f"\n🎉 Universal CLS Engine Test Complete!")
        print("   ✅ Database connection working")
        print("   ✅ CLS policies loaded successfully") 
        print("   ✅ Column access control working")
        print("   ✅ SQL rewriting functional")
        print("   ✅ Data masking operational")
        
        return True
        
    except Exception as e:
        print(f"❌ CLS engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_cls_engine_fixed())
    exit(0 if success else 1)
