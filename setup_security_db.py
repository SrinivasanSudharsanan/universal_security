#!/usr/bin/env python3
"""
Setup security database using your existing utilities
"""

import asyncio
import os
from app.utils.db_utils import DatabaseManager, init_database

async def setup_security_database():
    """Setup the security database schema"""
    print("🚀 Setting up Security Database...")
    print("=" * 50)
    
    try:
        # Initialize database using your existing db_utils
        success = await init_database()
        
        if success:
            print("✅ Security database schema created successfully!")
            
            # Test the setup
            await test_database_setup()
        else:
            print("❌ Failed to create security database schema")
            
    except Exception as e:
        print(f"❌ Setup failed: {e}")

async def test_database_setup():
    """Test the database setup"""
    print("\n🔍 Testing database setup...")
    
    try:
        pool = await DatabaseManager.get_pool()
        
        # Test basic queries
        roles_count = await pool.fetchval("SELECT COUNT(*) FROM security_roles")
        users_count = await pool.fetchval("SELECT COUNT(*) FROM security_users")
        
        print(f"✅ Security roles: {roles_count}")
        print(f"✅ Security users: {users_count}")
        print(f"✅ Database connection: Working")
        
        print("\n🎉 Security database setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")

if __name__ == "__main__":
    asyncio.run(setup_security_database())
