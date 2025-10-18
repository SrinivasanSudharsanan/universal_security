#!/usr/bin/env python3
"""
Check the REAL column names in your Druid tables
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.engines.druid_connector import DruidConnector

def check_real_schema():
    print("🔍 Checking REAL Druid table columns...")
    
    druid = DruidConnector()
    connected = druid.connect({
        'host': 'localhost',
        'port': 8082,
        'path': '/druid/v2/sql/',
        'scheme': 'http'
    })
    
    if not connected:
        print("❌ Could not connect to Druid")
        return
    
    # Check employees table with different approach
    print("\n📊 Employees table schema:")
    try:
        # Try multiple approaches to get schema
        emp_result = druid.execute_query("SELECT * FROM employees LIMIT 1")
        if not emp_result.empty:
            print(f"   All columns: {list(emp_result.columns)}")
            
            # Check individual columns
            for col in ['name', 'department', 'salary_sum', 'access_level', 'count']:
                try:
                    test_result = druid.execute_query(f"SELECT {col} FROM employees LIMIT 1")
                    print(f"   ✅ '{col}' exists")
                except:
                    print(f"   ❌ '{col}' does NOT exist")
        else:
            print("   No data found")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Check sales table
    print("\n📊 Sales table schema:")
    try:
        sales_result = druid.execute_query("SELECT * FROM sales LIMIT 1")
        if not sales_result.empty:
            print(f"   All columns: {list(sales_result.columns)}")
            
            # Check individual columns
            for col in ['product', 'customer', 'region', 'amount_sum', 'count', 'quarter']:
                try:
                    test_result = druid.execute_query(f"SELECT {col} FROM sales LIMIT 1")
                    print(f"   ✅ '{col}' exists")
                except:
                    print(f"   ❌ '{col}' does NOT exist")
        else:
            print("   No data found")
    except Exception as e:
        print(f"   Error: {e}")
    
    druid.close()

if __name__ == "__main__":
    check_real_schema()
