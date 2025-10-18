#!/usr/bin/env python3
"""
Fix CLS Engine with proper naming based on actual file structure
"""

import os

def fix_cls_properly():
    """Fix CLS engine with correct naming based on actual files"""
    print("🔧 Fixing CLS Engine Properly")
    print("=" * 35)
    
    cls_dir = "app/security/policies/column_level"
    
    # Fix cls_engine.py
    cls_engine_path = os.path.join(cls_dir, "cls_engine.py")
    if os.path.exists(cls_engine_path):
        print("1. Fixing cls_engine.py...")
        with open(cls_engine_path, 'r') as file:
            content = file.read()
        
        # Fix the constructor parameter name
        if "def __init__(self, db_utils):" in content:
            content = content.replace(
                "def __init__(self, db_utils):",
                "def __init__(self, database_query_function):"
            )
            print("   ✅ Fixed constructor parameter")
        
        # Fix the instance variable assignment
        if "self.db_utils = db_utils" in content:
            content = content.replace(
                "self.db_utils = db_utils",
                "self.database_query_function = database_query_function"
            )
            print("   ✅ Fixed instance variable")
        
        # Fix the database query calls
        if "await self.db_utils.execute_query" in content:
            content = content.replace(
                "await self.db_utils.execute_query",
                "await self.database_query_function"
            )
            print("   ✅ Fixed database query calls")
        
        with open(cls_engine_path, 'w') as file:
            file.write(content)
        print("   ✅ cls_engine.py fixed successfully")
    
    # Fix allowed_columns.py
    allowed_columns_path = os.path.join(cls_dir, "allowed_columns.py")
    if os.path.exists(allowed_columns_path):
        print("2. Fixing allowed_columns.py...")
        with open(allowed_columns_path, 'r') as file:
            content = file.read()
        
        # Fix the constructor parameter name
        if "def __init__(self, db_utils):" in content:
            content = content.replace(
                "def __init__(self, db_utils):",
                "def __init__(self, database_query_function):"
            )
            print("   ✅ Fixed constructor parameter")
        
        # Fix the instance variable assignment
        if "self.db_utils = db_utils" in content:
            content = content.replace(
                "self.db_utils = db_utils",
                "self.database_query_function = database_query_function"
            )
            print("   ✅ Fixed instance variable")
        
        # Fix the database query calls
        if "await self.db_utils.execute_query" in content:
            content = content.replace(
                "await self.db_utils.execute_query",
                "await self.database_query_function"
            )
            print("   ✅ Fixed database query calls")
        
        with open(allowed_columns_path, 'w') as file:
            file.write(content)
        print("   ✅ allowed_columns.py fixed successfully")
    
    print(f"\n🎉 CLS Engine Fixed Properly!")
    print("   ✅ Based on actual file structure")
    print("   ✅ Proper naming conventions applied")

if __name__ == "__main__":
    fix_cls_properly()
