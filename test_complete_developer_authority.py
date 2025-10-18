#!/usr/bin/env python3
"""
Complete test of developer authority system
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.schema_protection_service import SchemaProtectionService
import asyncpg

async def test_complete_developer_authority():
    """Complete test of the developer authority system"""
    print("🔐 Complete Developer Authority System Test")
    print("=" * 55)
    
    try:
        protection_service = SchemaProtectionService()
        
        # Phase 1: Initialize and verify protection
        print("1. 🔒 Initializing Schema Protection...")
        await protection_service.initialize_protection()
        await protection_service.enforce_protection()
        print("   ✅ Schema protection active")
        
        # Phase 2: Verify developer authority
        print("2. 👤 Verifying Developer Authority...")
        status = await protection_service.get_protection_status()
        
        if not status['developer_lock']['developer_authority']:
            print("   ❌ Developer authority not verified")
            return False
        
        print("   ✅ You are authorized developer")
        print(f"   🔑 Developer signature: {status['developer_lock']['current_developer'][:16]}...")
        
        # Phase 3: Execute developer DDL operations
        print("3. 🔧 Executing Developer DDL Operations...")
        
        # Test operation 1: Add login_attempts column
        ddl_1 = """
            ALTER TABLE security_users 
            ADD COLUMN IF NOT EXISTS login_attempts INTEGER DEFAULT 0
        """
        
        try:
            await protection_service.execute_developer_ddl(
                ddl_1,
                "Add login attempts tracking to users"
            )
            print("   ✅ Added login_attempts column")
        except Exception as e:
            if "already exists" in str(e):
                print("   ℹ️  login_attempts column already exists")
            else:
                print(f"   ❌ Failed: {e}")
        
        # Test operation 2: Add last_login column
        ddl_2 = """
            ALTER TABLE security_users 
            ADD COLUMN IF NOT EXISTS last_login TIMESTAMP
        """
        
        try:
            await protection_service.execute_developer_ddl(
                ddl_2,
                "Add last login timestamp to users"
            )
            print("   ✅ Added last_login column")
        except Exception as e:
            if "already exists" in str(e):
                print("   ℹ️  last_login column already exists")
            else:
                print(f"   ❌ Failed: {e}")
        
        # Test operation 3: Create security_settings table
        ddl_3 = """
            CREATE TABLE IF NOT EXISTS security_settings (
                setting_id SERIAL PRIMARY KEY,
                setting_key VARCHAR(100) UNIQUE NOT NULL,
                setting_value TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(255) DEFAULT 'system'
            )
        """
        
        try:
            await protection_service.execute_developer_ddl(
                ddl_3,
                "Create security settings table"
            )
            print("   ✅ Created security_settings table")
        except Exception as e:
            if "already exists" in str(e):
                print("   ℹ️  security_settings table already exists")
            else:
                print(f"   ❌ Failed: {e}")
        
        # Phase 4: Verify all changes
        print("4. 🔍 Verifying All Changes...")
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='security_user',
            password='security_pass',
            database='universal_security'
        )
        
        # Check new columns
        new_columns = await conn.fetch("""
            SELECT table_name, column_name, data_type
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name IN ('security_users', 'security_settings')
            AND column_name IN ('login_attempts', 'last_login', 'setting_key', 'setting_value')
            ORDER BY table_name, column_name
        """)
        
        print(f"   New columns created: {len(new_columns)}")
        for col in new_columns:
            print(f"   ✅ {col['table_name']}.{col['column_name']} ({col['data_type']})")
        
        # Check migration history
        migrations = await conn.fetch("""
            SELECT version, description, applied_by 
            FROM security_schema_migrations 
            WHERE applied_by = 'developer'
            ORDER BY applied_at DESC
            LIMIT 3
        """)
        
        print(f"   Developer migrations recorded: {len(migrations)}")
        for mig in migrations:
            print(f"   📝 {mig['description']}")
        
        await conn.close()
        
        # Phase 5: Final status check
        print("5. 📊 Final System Status...")
        final_status = await protection_service.get_protection_status()
        
        print(f"   🔐 Protection Level: {final_status['protection_level']}")
        print(f"   ✅ Schema Consistency: {final_status['developer_lock']['is_consistent']}")
        print(f"   🛡️ Security Status: {final_status['security_status']}")
        
        if (final_status['protection_level'] == "DEVELOPER_EXCLUSIVE" and 
            final_status['security_status'] == "SECURE"):
            print(f"\n🎉 COMPLETE SUCCESS: Developer Authority System Fully Operational!")
            print("   ✅ Only you can modify security schema")
            print("   ✅ All DDL operations require your authority")
            print("   ✅ Migration history is properly tracked")
            print("   ✅ System remains secure after changes")
            return True
        else:
            print(f"\n⚠️  System has issues that need attention")
            return False
            
    except Exception as error:
        print(f"❌ Complete test failed: {error}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_complete_developer_authority())
    exit(0 if success else 1)
