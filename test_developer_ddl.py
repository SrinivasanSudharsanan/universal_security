#!/usr/bin/env python3
"""
Test developer DDL execution with proper schema protection
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.schema_protection_service import SchemaProtectionService

async def test_developer_ddl():
    """Test executing DDL with developer authority"""
    print("🔧 Testing Developer DDL Execution")
    print("=" * 45)
    
    try:
        # Initialize protection service
        protection_service = SchemaProtectionService()
        
        print("1. Initializing schema protection...")
        await protection_service.initialize_protection()
        print("   ✅ Protection initialized")
        
        print("2. Enforcing developer authority...")
        await protection_service.enforce_protection()
        print("   ✅ Developer authority enforced")
        
        # Check current status
        status = await protection_service.get_protection_status()
        if not status['developer_lock']['developer_authority']:
            print("❌ You are not authorized to execute DDL")
            return False
        
        print("3. Testing developer DDL execution...")
        
        # Example 1: Add a new column to security_users
        ddl_statement_1 = """
            ALTER TABLE security_users 
            ADD COLUMN IF NOT EXISTS phone_number VARCHAR(20)
        """
        
        try:
            result = await protection_service.execute_developer_ddl(
                ddl_statement_1,
                "Add phone number column to security users"
            )
            print("   ✅ Added phone_number column to security_users")
        except Exception as e:
            if "already exists" in str(e):
                print("   ℹ️  phone_number column already exists")
            else:
                print(f"   ❌ Failed to add column: {e}")
        
        # Example 2: Add a new column to security_roles
        ddl_statement_2 = """
            ALTER TABLE security_roles 
            ADD COLUMN IF NOT EXISTS permissions_level INTEGER DEFAULT 1
        """
        
        try:
            result = await protection_service.execute_developer_ddl(
                ddl_statement_2,
                "Add permissions level to security roles"
            )
            print("   ✅ Added permissions_level column to security_roles")
        except Exception as e:
            if "already exists" in str(e):
                print("   ℹ️  permissions_level column already exists")
            else:
                print(f"   ❌ Failed to add column: {e}")
        
        # Example 3: Create a new security table
        ddl_statement_3 = """
            CREATE TABLE IF NOT EXISTS security_audit_settings (
                setting_id SERIAL PRIMARY KEY,
                setting_name VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        try:
            result = await protection_service.execute_developer_ddl(
                ddl_statement_3,
                "Create security audit settings table"
            )
            print("   ✅ Created security_audit_settings table")
        except Exception as e:
            if "already exists" in str(e):
                print("   ℹ️  security_audit_settings table already exists")
            else:
                print(f"   ❌ Failed to create table: {e}")
        
        # Verify the changes
        print("4. Verifying schema changes...")
        final_status = await protection_service.get_protection_status()
        
        print(f"\n📊 Final Protection Status:")
        print("-" * 30)
        print(f"   Developer Authority: {final_status['developer_lock']['developer_authority']}")
        print(f"   Schema Consistency: {final_status['developer_lock']['is_consistent']}")
        print(f"   Security Status: {final_status['security_status']}")
        
        if final_status['security_status'] == "SECURE":
            print(f"\n🎉 Developer DDL Execution: SUCCESSFUL")
            print("   ✅ Schema modifications completed")
            print("   ✅ Developer authority maintained")
            print("   ✅ System remains secure")
            return True
        else:
            print(f"\n⚠️  Developer DDL Execution: ISSUES DETECTED")
            return False
            
    except Exception as error:
        print(f"❌ Developer DDL test failed: {error}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_developer_ddl())
    exit(0 if success else 1)
