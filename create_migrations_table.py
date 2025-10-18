#!/usr/bin/env python3
"""
Create the security_schema_migrations table for tracking schema changes
"""

import asyncio
import asyncpg

async def create_migrations_table():
    """Create the migrations tracking table"""
    print("📋 Creating Security Schema Migrations Table")
    print("=" * 50)
    
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='security_user',
            password='security_pass',
            database='universal_security'
        )
        
        # Create migrations table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS security_schema_migrations (
                migration_id SERIAL PRIMARY KEY,
                version VARCHAR(50) UNIQUE NOT NULL,
                description TEXT NOT NULL,
                checksum VARCHAR(64) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                applied_by VARCHAR(255) DEFAULT 'system'
            )
        """)
        
        print("✅ Created security_schema_migrations table")
        
        # Insert initial migration record for current schema
        # First, let's calculate a checksum of current schema
        schema_info = await conn.fetch("""
            SELECT 
                table_name,
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name LIKE 'security_%'
            ORDER BY table_name, ordinal_position
        """)
        
        import hashlib
        schema_str = ""
        for row in schema_info:
            schema_str += f"{row['table_name']}.{row['column_name']}:{row['data_type']}:{row['is_nullable']}:{row['column_default']};"
        
        initial_checksum = hashlib.sha256(schema_str.encode()).hexdigest()
        
        # Insert initial migration
        await conn.execute("""
            INSERT INTO security_schema_migrations 
            (version, description, checksum, applied_by)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (version) DO NOTHING
        """, "1.0.0", "Initial security schema setup", initial_checksum, "system")
        
        print("✅ Added initial migration record")
        
        # Verify the table was created
        table_exists = await conn.fetchval("""
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'security_schema_migrations'
        """)
        
        if table_exists:
            print("✅ Migrations table verified")
        
        # Show current migrations
        migrations = await conn.fetch("""
            SELECT version, description, applied_at 
            FROM security_schema_migrations 
            ORDER BY applied_at
        """)
        
        print(f"\n📊 Migration History: {len(migrations)} records")
        for mig in migrations:
            print(f"   📝 {mig['version']}: {mig['description']}")
        
        await conn.close()
        
        print(f"\n🎉 Migrations system ready!")
        return True
        
    except Exception as error:
        print(f"❌ Failed to create migrations table: {error}")
        return False

if __name__ == "__main__":
    success = asyncio.run(create_migrations_table())
    exit(0 if success else 1)
