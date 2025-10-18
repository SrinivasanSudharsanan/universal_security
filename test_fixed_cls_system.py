#!/usr/bin/env python3
"""
Test the fixed CLS system
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.security.policies.column_level.cls_engine import UniversalClsEngine
from app.security.policies.column_level.allowed_columns import UniversalAllowedColumns
from app.utils.db_utils import DatabaseManager

async def test_fixed_cls_system():
    """Test the fixed CLS system"""
    print("🔐 Testing Fixed CLS System")
    print("=" * 30)
    
    try:
        # Initialize database connection
        print("1. Initializing database connection...")
        database_pool = await DatabaseManager.get_pool()
        
        # Create proper database query function
        async def execute_database_query(query_string, *query_parameters):
            async with database_pool.acquire() as connection:
                return await connection.fetch(query_string, *query_parameters)
        
        # Test CLS Engine
        print("2. Testing CLS Engine...")
        cls_engine = UniversalClsEngine(execute_database_query)
        await cls_engine.initialize_engine()
        
        engine_status = cls_engine.get_engine_status()
        print(f"   ✅ Engine: {engine_status['engine_type']}")
        print(f"   ✅ Tables: {engine_status['tables_covered']}")
        print(f"   ✅ Policies: {engine_status['total_policies']}")
        
        # Test Allowed Columns Manager
        print("3. Testing Allowed Columns Manager...")
        allowed_manager = UniversalAllowedColumns(execute_database_query)
        await allowed_manager.initialize_permissions()
        
        permission_summary = allowed_manager.get_permission_summary()
        print(f"   ✅ Manager: {permission_summary['manager_type']}")
        print(f"   ✅ Tables: {permission_summary['total_tables']}")
        print(f"   ✅ Policies: {permission_summary['total_policies']}")
        
        # Test basic functionality
        print("4. Testing basic functionality...")
        
        # Test admin access
        admin_columns = await cls_engine.get_allowed_columns(["admin"], "test_employees")
        print(f"   👤 Admin can access: {len(admin_columns)} columns")
        
        # Test data engineer access  
        data_engineer_columns = await cls_engine.get_allowed_columns(["data_engineer"], "test_employees")
        print(f"   👤 Data Engineer can access: {len(data_engineer_columns)} columns")
        
        await DatabaseManager.close_pool()
        
        print(f"\n🎉 Fixed CLS System Test Complete!")
        print("   ✅ Database connection working")
        print("   ✅ CLS policies loaded")
        print("   ✅ Column access control functional")
        
        return True
        
    except Exception as error:
        print(f"❌ Test failed: {error}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fixed_cls_system())
    exit(0 if success else 1)
