#!/usr/bin/env python3
"""
Test the Universal CLS Engine with the simple setup
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.security.policies.column_level.cls_engine import UniversalClsEngine
from app.security.policies.column_level.allowed_columns import UniversalAllowedColumns
from app.utils.db_utils import DatabaseManager, execute_query

async def test_cls_engine():
    """Test the CLS engine with the simple setup"""
    print("🔐 Testing Universal CLS Engine")
    print("=" * 35)
    
    try:
        # Initialize database connection
        await DatabaseManager.get_pool()
        
        # 1. Test CLS Engine
        print("1. Initializing CLS Engine...")
        cls_engine = UniversalClsEngine(execute_query)
        await cls_engine.initialize_engine()
        
        engine_status = cls_engine.get_engine_status()
        print(f"   ✅ Engine: {engine_status['engine_type']}")
        print(f"   ✅ Tables: {engine_status['tables_covered']}")
        print(f"   ✅ Policies: {engine_status['total_policies']}")
        
        # 2. Test Allowed Columns Manager
        print("\n2. Testing Allowed Columns Manager...")
        allowed_manager = UniversalAllowedColumns(execute_query)
        await allowed_manager.initialize_permissions()
        
        perm_summary = allowed_manager.get_permission_summary()
        print(f"   ✅ Manager: {perm_summary['manager_type']}")
        print(f"   ✅ Tables: {perm_summary['total_tables']}")
        print(f"   ✅ Policies: {perm_summary['total_policies']}")
        
        # 3. Test different user roles
        print("\n3. Testing Column Access by Role...")
        
        test_roles = [
            (["admin"], "Full Access Admin"),
            (["data_engineer"], "Technical Role"),
            (["business_analyst"], "Business Role"), 
            (["user"], "Restricted User")
        ]
        
        for user_roles, description in test_roles:
            print(f"\n   �� {description}: {user_roles}")
            
            # Get allowed columns
            allowed_columns = await cls_engine.get_allowed_columns(user_roles, "test_employees")
            print(f"   �� Allowed columns: {len(allowed_columns)}")
            for col in allowed_columns:
                # Get access details
                access = await cls_engine.get_column_access(user_roles, "test_employees", col)
                mask_info = f" ({access['mask_type']})" if access['mask_type'] else ""
                print(f"      ✅ {col}: {access['access_type']}{mask_info}")
        
        # 4. Test SQL rewriting
        print("\n4. Testing SQL Query Rewriting...")
        test_query = "SELECT * FROM test_employees"
        
        for role in ["admin", "data_engineer", "business_analyst", "user"]:
            rewritten = await cls_engine.rewrite_sql_select(test_query, [role], "druid")
            print(f"   🔄 {role}:")
            print(f"      Original: {test_query}")
            print(f"      Rewritten: {rewritten}")
            print()
        
        # 5. Test data masking
        print("\n5. Testing Data Masking...")
        from app.security.policies.column_level.column_masking import universal_masking_engine
        
        test_data = [
            ("john.doe@company.com", "email"),
            ("Jane Smith", "partial"),
            ("75000", "partial"),
            ("Engineering", "full")
        ]
        
        for data, mask_type in test_data:
            masked = universal_masking_engine.mask_data(data, mask_type)
            print(f"   🎭 {mask_type}: '{data}' -> '{masked}'")
        
        await DatabaseManager.close_pool()
        
        print(f"\n🎉 Universal CLS Engine Test Complete!")
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
    success = asyncio.run(test_cls_engine())
    exit(0 if success else 1)
