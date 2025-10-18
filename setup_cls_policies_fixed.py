#!/usr/bin/env python3
"""
Setup CLS policies - Fixed version without ON CONFLICT issues
"""

import asyncio
import asyncpg

async def setup_cls_policies_fixed():
    """Create CLS policies with proper error handling"""
    print("🔐 Setting Up CLS Policies - Fixed Version")
    print("=" * 55)
    
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='security_user',
            password='security_pass',
            database='universal_security'
        )
        
        # 1. Check if we have a Druid data source
        print("1. Checking Druid data source...")
        druid_source = await conn.fetchrow("""
            SELECT source_id FROM security_data_sources 
            WHERE engine_type = 'druid' LIMIT 1
        """)
        
        if not druid_source:
            # Create a Druid data source
            druid_source = await conn.fetchrow("""
                INSERT INTO security_data_sources 
                (source_name, engine_type, connection_config)
                VALUES ($1, $2, $3)
                RETURNING source_id
            """, 'druid_production', 'druid', '{"host": "localhost", "port": 8082}')
            print("   ✅ Created Druid data source")
        else:
            print("   ✅ Using existing Druid data source")
        
        druid_source_id = druid_source['source_id']
        
        # 2. Create tables if they don't exist
        print("\n2. Setting up security tables...")
        tables = [
            ('employee_sensitive', 'Employee data with PII and salary', True),
            ('customer_pii', 'Customer personal identifiable information', True)
        ]
        
        table_ids = {}
        for table_name, description, is_sensitive in tables:
            # Check if table exists
            existing_table = await conn.fetchrow("""
                SELECT table_id FROM security_tables 
                WHERE source_id = $1 AND table_name = $2
            """, druid_source_id, table_name)
            
            if existing_table:
                table_ids[table_name] = existing_table['table_id']
                print(f"   ✅ Table exists: {table_name}")
            else:
                # Create table
                new_table = await conn.fetchrow("""
                    INSERT INTO security_tables 
                    (source_id, table_name, description, is_sensitive)
                    VALUES ($1, $2, $3, $4)
                    RETURNING table_id
                """, druid_source_id, table_name, description, is_sensitive)
                table_ids[table_name] = new_table['table_id']
                print(f"   ✅ Created table: {table_name}")
        
        # 3. Create columns
        print("\n3. Setting up columns...")
        columns_config = {
            'employee_sensitive': [
                ('employee_id', 'integer', False, 'low'),
                ('name', 'varchar', True, 'medium'),
                ('email', 'varchar', True, 'high'),
                ('phone', 'varchar', True, 'high'),
                ('salary', 'integer', True, 'high'),
                ('department', 'varchar', False, 'low'),
                ('ssn', 'varchar', True, 'critical'),
                ('performance_rating', 'varchar', True, 'medium')
            ],
            'customer_pii': [
                ('customer_id', 'integer', False, 'low'),
                ('full_name', 'varchar', True, 'high'),
                ('email', 'varchar', True, 'high'),
                ('phone', 'varchar', True, 'high'),
                ('address', 'varchar', True, 'high'),
                ('credit_card', 'varchar', True, 'critical'),
                ('date_of_birth', 'date', True, 'high'),
                ('loyalty_tier', 'varchar', False, 'low')
            ]
        }
        
        column_ids = {}
        for table_name, columns in columns_config.items():
            table_id = table_ids[table_name]
            for col_name, data_type, is_sensitive, sensitivity in columns:
                # Check if column exists
                existing_column = await conn.fetchrow("""
                    SELECT column_id FROM security_columns 
                    WHERE table_id = $1 AND column_name = $2
                """, table_id, col_name)
                
                if existing_column:
                    column_ids[f"{table_name}.{col_name}"] = existing_column['column_id']
                    print(f"   ✅ Column exists: {table_name}.{col_name}")
                else:
                    # Create column
                    new_column = await conn.fetchrow("""
                        INSERT INTO security_columns 
                        (table_id, column_name, data_type, is_sensitive, sensitivity_level)
                        VALUES ($1, $2, $3, $4, $5)
                        RETURNING column_id
                    """, table_id, col_name, data_type, is_sensitive, sensitivity)
                    column_ids[f"{table_name}.{col_name}"] = new_column['column_id']
                    print(f"   ✅ Created column: {table_name}.{col_name}")
        
        # 4. Get roles
        print("\n4. Getting security roles...")
        roles = await conn.fetch("""
            SELECT role_id, role_name FROM security_roles 
            WHERE role_name IN ('admin', 'data_engineer', 'business_analyst', 'user')
        """)
        
        role_ids = {role['role_name']: role['role_id'] for role in roles}
        print(f"   ✅ Found {len(role_ids)} roles")
        
        # 5. Create CLS policies
        print("\n5. Creating CLS policies...")
        
        # Simple policies for testing
        simple_policies = [
            # Admin policies - full access
            ('employee_sensitive.employee_id', 'admin', 'allow', None),
            ('employee_sensitive.name', 'admin', 'allow', None),
            ('employee_sensitive.email', 'admin', 'allow', None),
            ('employee_sensitive.salary', 'admin', 'allow', None),
            
            # Data engineer policies - masked access
            ('employee_sensitive.employee_id', 'data_engineer', 'allow', None),
            ('employee_sensitive.name', 'data_engineer', 'allow', None),
            ('employee_sensitive.email', 'data_engineer', 'mask', 'email'),
            ('employee_sensitive.salary', 'data_engineer', 'mask', 'partial'),
            
            # Business analyst policies - limited access
            ('employee_sensitive.employee_id', 'business_analyst', 'allow', None),
            ('employee_sensitive.name', 'business_analyst', 'mask', 'partial'),
            ('employee_sensitive.email', 'business_analyst', 'deny', None),
            ('employee_sensitive.salary', 'business_analyst', 'deny', None),
            
            # User policies - very limited
            ('employee_sensitive.employee_id', 'user', 'allow', None),
            ('employee_sensitive.name', 'user', 'mask', 'partial'),
            ('employee_sensitive.email', 'user', 'deny', None),
            ('employee_sensitive.salary', 'user', 'deny', None),
        ]
        
        policies_created = 0
        for table_column, role_name, access_type, mask_type in simple_policies:
            table_name, column_name = table_column.split('.')
            column_key = f"{table_name}.{column_name}"
            
            if column_key in column_ids and role_name in role_ids:
                # Check if policy exists
                existing_policy = await conn.fetchrow("""
                    SELECT policy_id FROM security_cls_policies 
                    WHERE role_id = $1 AND column_id = $2
                """, role_ids[role_name], column_ids[column_key])
                
                if existing_policy:
                    # Update existing policy
                    await conn.execute("""
                        UPDATE security_cls_policies 
                        SET access_type = $1, mask_type = $2, is_active = true
                        WHERE policy_id = $3
                    """, access_type, mask_type, existing_policy['policy_id'])
                    print(f"   ✅ Updated policy: {role_name} -> {table_column}")
                else:
                    # Create new policy
                    await conn.execute("""
                        INSERT INTO security_cls_policies 
                        (role_id, column_id, access_type, mask_type, policy_name, is_active)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, role_ids[role_name], column_ids[column_key], access_type, mask_type,
                       f"{role_name}_{table_column}", True)
                    print(f"   ✅ Created policy: {role_name} -> {table_column}")
                
                policies_created += 1
        
        # 6. Verify setup
        print("\n6. Verifying setup...")
        total_policies = await conn.fetchval("SELECT COUNT(*) FROM security_cls_policies WHERE is_active = true")
        total_tables = await conn.fetchval("SELECT COUNT(*) FROM security_tables WHERE source_id = $1", druid_source_id)
        total_columns = await conn.fetchval("""
            SELECT COUNT(*) FROM security_columns c
            JOIN security_tables t ON c.table_id = t.table_id
            WHERE t.source_id = $1
        """, druid_source_id)
        
        print(f"   📊 Tables: {total_tables}")
        print(f"   📊 Columns: {total_columns}")
        print(f"   📊 Policies: {total_policies}")
        
        await conn.close()
        
        print(f"\n🎉 CLS Setup Complete!")
        print(f"   ✅ {policies_created} policies configured")
        print("   ✅ Ready for CLS engine testing")
        
        return True
        
    except Exception as e:
        print(f"❌ CLS setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_cls_policies_fixed())
    exit(0 if success else 1)
