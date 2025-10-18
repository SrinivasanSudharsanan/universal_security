#!/usr/bin/env python3
"""
Check the actual schema of our Druid tables to get correct column names
"""

from engines.unified_connector import UnifiedConnector
from config import get_settings

def check_actual_schema():
    print("🔍 CHECKING ACTUAL TABLE SCHEMAS")
    print("=" * 50)
    
    connector = UnifiedConnector()
    settings = get_settings()
    
    connector.initialize_connector('druid', settings.druid_config)
    
    tables = ['employees', 'sales']
    
    for table in tables:
        print(f"\n📋 Table: {table}")
        print("-" * 30)
        
        try:
            # Get sample data to see actual columns
            result = connector.execute_query(f"SELECT * FROM {table} LIMIT 1", engine_type='druid')
            print(f"✅ Actual columns: {list(result.columns)}")
            
            # Show data types and sample values
            if len(result) > 0:
                sample = result.iloc[0]
                print("📊 Sample data:")
                for col, value in sample.items():
                    print(f"   {col}: {value} (type: {type(value).__name__})")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    connector.close_all()

if __name__ == "__main__":
    check_actual_schema()
