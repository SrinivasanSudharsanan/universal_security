#!/usr/bin/env python3
"""
Final database setup with proper error handling
"""

import asyncio
import asyncpg
import sys

async def setup_database():
    print("🚀 Final Security Database Setup")
    print("=" * 50)
    
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'security_user',
        'password': 'security_pass',
        'database': 'universal_security'
    }
    
    try:
        # Test connection
        conn = await asyncpg.connect(**db_config)
        print("✅ Connected to PostgreSQL")
        
        # Create tables one by one with better error handling
        tables_sql = [
            # Security Roles
            """
            CREATE TABLE IF NOT EXISTS security_roles (
                role_id SERIAL PRIMARY KEY,
                role_name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                is_system_role BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Security Users
            """
            CREATE TABLE IF NOT EXISTS security_users (
                user_id VARCHAR(255) PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                email VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # User-Role Mapping
            """
            CREATE TABLE IF NOT EXISTS security_user_roles (
                user_id VARCHAR(255) REFERENCES security_users(user_id) ON DELETE CASCADE,
                role_id INTEGER REFERENCES security_roles(role_id) ON DELETE CASCADE,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, role_id)
            )
            """
        ]
        
        # Execute table creation
        for i, sql in enumerate(tables_sql, 1):
            try:
                await conn.execute(sql)
                print(f"✅ Table {i}/3 created successfully")
            except Exception as e:
                print(f"⚠️  Table {i}: {e}")
        
        # Insert basic data
        print("\n📥 Inserting default data...")
        
        # Insert roles
        await conn.execute("""
            INSERT INTO security_roles (role_name, description, is_system_role) VALUES
            ('admin', 'Full system access', TRUE),
            ('user', 'Standard user access', FALSE)
            ON CONFLICT (role_name) DO NOTHING
        """)
        
        # Insert users
        await conn.execute("""
            INSERT INTO security_users (user_id, username, email, is_active) VALUES
            ('admin', 'admin', 'admin@company.com', TRUE),
            ('user1', 'user1', 'user1@company.com', TRUE)
            ON CONFLICT (user_id) DO NOTHING
        """)
        
        # Insert user roles
        await conn.execute("""
            INSERT INTO security_user_roles (user_id, role_id) VALUES
            ('admin', (SELECT role_id FROM security_roles WHERE role_name = 'admin')),
            ('user1', (SELECT role_id FROM security_roles WHERE role_name = 'user'))
            ON CONFLICT (user_id, role_id) DO NOTHING
        """)
        
        print("✅ Default data inserted")
        
        # Verify setup
        print("\n🔍 Verifying setup...")
        roles_count = await conn.fetchval("SELECT COUNT(*) FROM security_roles")
        users_count = await conn.fetchval("SELECT COUNT(*) FROM security_users")
        mappings_count = await conn.fetchval("SELECT COUNT(*) FROM security_user_roles")
        
        print(f"✅ Security roles: {roles_count}")
        print(f"✅ Security users: {users_count}") 
        print(f"✅ User-role mappings: {mappings_count}")
        
        await conn.close()
        print("\n🎉 Security database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_database())
    sys.exit(0 if success else 1)
