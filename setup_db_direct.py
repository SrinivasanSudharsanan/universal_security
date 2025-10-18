#!/usr/bin/env python3
"""
Direct database setup - no dependencies
"""

import asyncio
import asyncpg
import sys

async def setup_database_direct():
    print("🚀 Direct Security Database Setup")
    print("=" * 50)
    
    # Database connection details
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'user': 'security_user',
        'password': 'security_pass',
        'database': 'universal_security'
    }
    
    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(**db_config)
        print("✅ Connected to PostgreSQL")
        
        # Read and execute the SQL schema
        try:
            with open('sql/init_security_schema.sql', 'r') as f:
                schema_sql = f.read()
        except FileNotFoundError:
            print("❌ SQL file not found: sql/init_security_schema.sql")
            print("💡 Creating basic security schema...")
            schema_sql = """
            -- Basic Security Schema
            CREATE TABLE IF NOT EXISTS security_roles (
                role_id SERIAL PRIMARY KEY,
                role_name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS security_users (
                user_id VARCHAR(255) PRIMARY KEY,
                username VARCHAR(255) UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS security_user_roles (
                user_id VARCHAR(255) REFERENCES security_users(user_id),
                role_id INTEGER REFERENCES security_roles(role_id),
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, role_id)
            );
            
            INSERT INTO security_roles (role_name, description) VALUES 
            ('admin', 'Full system access'),
            ('user', 'Standard user access')
            ON CONFLICT (role_name) DO NOTHING;
            
            INSERT INTO security_users (user_id, username) VALUES 
            ('admin', 'admin')
            ON CONFLICT (user_id) DO NOTHING;
            
            INSERT INTO security_user_roles (user_id, role_id) VALUES 
            ('admin', (SELECT role_id FROM security_roles WHERE role_name = 'admin'))
            ON CONFLICT (user_id, role_id) DO NOTHING;
            """
        
        # Split and execute commands
        commands = [cmd.strip() for cmd in schema_sql.split(';') if cmd.strip()]
        
        success_count = 0
        for i, command in enumerate(commands, 1):
            if command and not command.startswith('--'):
                try:
                    await conn.execute(command)
                    success_count += 1
                    print(f"✅ Command {i}/{len(commands)}: OK")
                except Exception as e:
                    if "already exists" not in str(e) and "duplicate" not in str(e):
                        print(f"⚠️  Command {i}: {e}")
                    else:
                        success_count += 1
                        print(f"✅ Command {i}: Already exists")
        
        print(f"\n�� Commands executed: {success_count}/{len(commands)}")
        
        # Test the setup
        print("\n🔍 Testing setup...")
        roles_count = await conn.fetchval("SELECT COUNT(*) FROM security_roles")
        users_count = await conn.fetchval("SELECT COUNT(*) FROM security_users")
        
        print(f"✅ Security roles: {roles_count}")
        print(f"✅ Security users: {users_count}")
        
        await conn.close()
        
        print("\n🎉 Security database setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("\n💡 Troubleshooting:")
        print("1. Make sure PostgreSQL is running: sudo service postgresql status")
        print("2. Check if database/user exists")
        print("3. Verify credentials")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_database_direct())
    sys.exit(0 if success else 1)
