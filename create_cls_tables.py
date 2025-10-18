#!/usr/bin/env python3
"""
Create the missing CLS tables
"""

import asyncio
import asyncpg

async def create_cls_tables():
    """Create the missing CLS tables"""
    print("🏗️ Creating Missing CLS Tables")
    print("=" * 35)
    
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='security_user',
            password='security_pass',
            database='universal_security'
        )
        
        # 1. Create security_tables table (might be missing)
        print("1. Creating security_tables table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS security_tables (
                table_id SERIAL PRIMARY KEY,
                source_id INTEGER REFERENCES security_data_sources(source_id),
                table_name VARCHAR(255) NOT NULL,
                schema_name VARCHAR(255),
                description TEXT,
                is_sensitive BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_id, table_name)
            )
        """)
        print("   ✅ Created security_tables")
        
        # 2. Create security_columns table
        print("2. Creating security_columns table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS security_columns (
                column_id SERIAL PRIMARY KEY,
                table_id INTEGER REFERENCES security_tables(table_id),
                column_name VARCHAR(255) NOT NULL,
                data_type VARCHAR(100),
                is_sensitive BOOLEAN DEFAULT FALSE,
                sensitivity_level VARCHAR(50) DEFAULT 'low',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(table_id, column_name)
            )
        """)
        print("   ✅ Created security_columns")
        
        # 3. Create security_cls_policies table
        print("3. Creating security_cls_policies table...")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS security_cls_policies (
                policy_id SERIAL PRIMARY KEY,
                policy_name VARCHAR(255) NOT NULL,
                role_id INTEGER REFERENCES security_roles(role_id),
                column_id INTEGER REFERENCES security_columns(column_id),
                access_type VARCHAR(50) NOT NULL,
                mask_type VARCHAR(50),
                custom_mask_rule TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(role_id, column_id)
            )
        """)
        print("   ✅ Created security_cls_policies")
        
        # Verify tables were created
        print("\n4. Verifying table creation...")
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('security_tables', 'security_columns', 'security_cls_policies')
            ORDER BY table_name
        """)
        
        created_tables = [t['table_name'] for t in tables]
        print(f"   ✅ CLS Tables: {', '.join(created_tables)}")
        
        await conn.close()
        
        print(f"\n🎉 CLS Tables Created Successfully!")
        print("   ✅ Ready for CLS policy setup")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create CLS tables: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(create_cls_tables())
    exit(0 if success else 1)
