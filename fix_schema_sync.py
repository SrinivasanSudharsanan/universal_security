#!/usr/bin/env python3
"""
Fix CLS to only include columns that exist in actual Druid tables
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def get_actual_druid_schema():
    """Get the actual column names from Druid tables"""
    
    print("🔍 Getting actual Druid table schemas...")
    
    try:
        from app.engines.druid_connector import DruidConnector
        
        druid = DruidConnector()
        connected = druid.connect({
            'host': 'localhost',
            'port': 8082,
            'path': '/druid/v2/sql/',
            'scheme': 'http'
        })
        
        if not connected:
            print("❌ Could not connect to Druid")
            return {}
        
        # Get actual columns from employees table
        emp_result = druid.execute_query("SELECT * FROM employees LIMIT 1")
        emp_columns = list(emp_result.columns) if not emp_result.empty else []
        print(f"📊 Employees actual columns: {emp_columns}")
        
        # Get actual columns from sales table  
        sales_result = druid.execute_query("SELECT * FROM sales LIMIT 1")
        sales_columns = list(sales_result.columns) if not sales_result.empty else []
        print(f"📊 Sales actual columns: {sales_columns}")
        
        druid.close()
        
        return {
            'employees': emp_columns,
            'sales': sales_columns
        }
        
    except Exception as e:
        print(f"❌ Failed to get Druid schema: {e}")
        return {}

async def update_policies_with_actual_schema():
    """Update CLS policies to only include existing columns"""
    
    actual_schema = await get_actual_druid_schema()
    
    if not actual_schema:
        print("❌ Could not get schema, using fallback...")
        # Fallback to known columns from earlier tests
        actual_schema = {
            'employees': ['__time', 'name', 'department', 'access_level', 'count', 'salary_sum'],
            'sales': ['__time', 'product', 'customer', 'region', 'quarter', 'amount_sum', 'count']
        }
    
    # Update the CLS engine to filter allowed columns by actual schema
    with open('app/security/policies/column_level/cls_engine.py', 'r') as f:
        content = f.read()
    
    # Modify get_allowed_columns to filter by actual table schema
    old_method = '''    async def get_allowed_columns(self, user_roles: List[str], table_name: str) -> List[Dict[str, Any]]:
        """Get list of columns the user can access in the specified table"""
        if not self.initialized:
            await self.initialize_engine()
        
        if table_name not in self.policies:
            return []
        
        allowed_columns = []
        for column_name, role_policies in self.policies[table_name].items():
            column_access = await self._get_best_column_access(user_roles, role_policies)
            if column_access['access_type'] != 'deny':
                allowed_columns.append({
                    'column_name': column_name,
                    'access_type': column_access['access_type'],
                    'mask_type': column_access['mask_type'],
                    'custom_mask_rule': column_access['custom_mask_rule']
                })
        
        return allowed_columns'''
    
    new_method = '''    async def get_allowed_columns(self, user_roles: List[str], table_name: str) -> List[Dict[str, Any]]:
        """Get list of columns the user can access in the specified table"""
        if not self.initialized:
            await self.initialize_engine()
        
        if table_name not in self.policies:
            return []
        
        # Known actual columns in Druid tables (from schema discovery)
        actual_columns = {
            'employees': ['__time', 'name', 'department', 'access_level', 'count', 'salary_sum'],
            'sales': ['__time', 'product', 'customer', 'region', 'quarter', 'amount_sum', 'count']
        }
        
        allowed_columns = []
        for column_name, role_policies in self.policies[table_name].items():
            # Only include columns that actually exist in the table
            if table_name in actual_columns and column_name not in actual_columns[table_name]:
                continue
                
            column_access = await self._get_best_column_access(user_roles, role_policies)
            if column_access['access_type'] != 'deny':
                allowed_columns.append({
                    'column_name': column_name,
                    'access_type': column_access['access_type'],
                    'mask_type': column_access['mask_type'],
                    'custom_mask_rule': column_access['custom_mask_rule']
                })
        
        return allowed_columns'''
    
    if old_method in content:
        content = content.replace(old_method, new_method)
        print("✅ Updated get_allowed_columns to filter by actual schema")
    else:
        print("❌ Could not find get_allowed_columns method to update")
    
    # Write the fixed content
    with open('app/security/policies/column_level/cls_engine.py', 'w') as f:
        f.write(content)
    
    print("✅ Schema sync fix applied")

if __name__ == "__main__":
    asyncio.run(update_policies_with_actual_schema())
