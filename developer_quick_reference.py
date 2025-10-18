#!/usr/bin/env python3
"""
Quick reference for developer schema operations
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.schema_protection_service import SchemaProtectionService

async def developer_quick_reference():
    """Show quick reference for developer operations"""
    print("🚀 Developer Schema Operations - Quick Reference")
    print("=" * 55)
    
    protection_service = SchemaProtectionService()
    await protection_service.initialize_protection()
    
    status = await protection_service.get_protection_status()
    
    if not status['developer_lock']['developer_authority']:
        print("❌ You are not authorized to modify schema")
        return
    
    print("✅ You are authorized developer")
    print(f"🔑 Your signature: {status['developer_lock']['current_developer'][:16]}...")
    
    print("\n📋 Available Developer Operations:")
    print("-" * 35)
    
    operations = [
        {
            "name": "Add Column to Table",
            "example": """
                await protection_service.execute_developer_ddl(
                    \"\"\"ALTER TABLE security_users 
                    ADD COLUMN new_column_name DATA_TYPE\"\"\",
                    \"Description of change\"
                )
            """
        },
        {
            "name": "Create New Table", 
            "example": """
                await protection_service.execute_developer_ddl(
                    \"\"\"CREATE TABLE security_new_table (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(255) NOT NULL
                    )\"\"\",
                    \"Create new security table\"
                )
            """
        },
        {
            "name": "Modify Column",
            "example": """
                await protection_service.execute_developer_ddl(
                    \"\"\"ALTER TABLE security_users 
                    ALTER COLUMN column_name TYPE new_data_type\"\"\",
                    \"Modify column data type\"
                )
            """
        },
        {
            "name": "Add Index",
            "example": """
                await protection_service.execute_developer_ddl(
                    \"\"\"CREATE INDEX idx_security_users_email 
                    ON security_users(email)\"\"\",
                    \"Add index for better performance\"
                )
            """
        }
    ]
    
    for op in operations:
        print(f"\n🔧 {op['name']}:")
        print(op['example'])
    
    print(f"\n💡 Usage Tips:")
    print("-" * 15)
    print("• Always use IF NOT EXISTS for safety")
    print("• Provide clear descriptions for migrations")
    print("• Test changes in development first")
    print("• Backup before major changes")
    print("• Use transactions for multiple related changes")

if __name__ == "__main__":
    asyncio.run(developer_quick_reference())
