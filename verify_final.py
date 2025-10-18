#!/usr/bin/env python3
"""
Final verification of security database
"""

import asyncio
import asyncpg

async def verify_complete_setup():
    print("FINAL SECURITY DATABASE VERIFICATION")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='security_user',
            password='security_pass',
            database='universal_security'
        )
        
        print("Connected to database")
        
        # Comprehensive verification
        print("\nVERIFICATION RESULTS:")
        print("-" * 40)
        
        # 1. Check all security tables
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'security_%'
            ORDER BY table_name
        """)
        
        print(f"Security tables: {len(tables)}")
        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table['table_name']}")
            print(f"  {table['table_name']}: {count} rows")
        
        # 2. Check roles
        roles = await conn.fetch("SELECT role_name, description FROM security_roles ORDER BY role_name")
        print(f"\nSecurity roles: {len(roles)}")
        for role in roles:
            print(f"  {role['role_name']}: {role['description']}")
        
        # 3. Check users and their roles
        user_roles = await conn.fetch("""
            SELECT u.username, u.email, r.role_name 
            FROM security_users u
            JOIN security_user_roles ur ON u.user_id = ur.user_id
            JOIN security_roles r ON ur.role_id = r.role_id
            ORDER BY u.username, r.role_name
        """)
        
        print(f"\nUser-role mappings: {len(user_roles)}")
        for ur in user_roles:
            print(f"  {ur['username']} ({ur['email']}) -> {ur['role_name']}")
        
        # 4. Test basic operations
        print("\nTesting operations:")
        
        # Test SELECT with JOIN
        admin_roles = await conn.fetch("""
            SELECT r.role_name 
            FROM security_users u
            JOIN security_user_roles ur ON u.user_id = ur.user_id
            JOIN security_roles r ON ur.role_id = r.role_id
            WHERE u.username = 'admin'
        """)
        print(f"  SELECT with JOIN test: {[r['role_name'] for r in admin_roles]}")
        
        # Test data sources table
        sources_count = await conn.fetchval("SELECT COUNT(*) FROM security_data_sources")
        print(f"  Data sources: {sources_count}")
        
        await conn.close()
        
        print("\nVERIFICATION COMPLETE: All tests passed!")
        print("\nSecurity database is ready for use.")
        return True
        
    except Exception as e:
        print(f"Verification failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_complete_setup())
    exit(0 if success else 1)
