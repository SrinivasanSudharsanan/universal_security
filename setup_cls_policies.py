#!/usr/bin/env python3
"""
Setup complete CLS policies for PostgreSQL + Druid testing
"""

import asyncio
import asyncpg

async def setup_cls_policies():
    """Create comprehensive CLS policies for testing"""
    print("🔐 Setting Up Complete CLS Policies")
    print("=" * 50)
    
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='security_user', 
            password='security_pass',
            database='universal_security'
        )
        
        # 1. Get or create Druid data source
        print("1. Setting up Druid data source...")
        druid_source = await conn.fetchrow("""
            INSERT INTO security_data_sources (source_name, engine_type, connection_config)
            VALUES ('druid_cls_test', 'druid', '{"host": "localhost", "port": 8082}')
            ON CONFLICT (source_name) 
            DO UPDATE SET engine_type = EXCLUDED.engine_type
            RETURNING source_id
        """)
        
        druid_source_id = druid_source['source_id']
        print(f"   ✅ Druid source ID: {druid_source_id}")
        
        # 2. Register tables
        print("\n2. Registering Druid tables...")
        tables = [
            ('employee_sensitive', 'Employee data with PII and salary', True),
            ('customer_pii', 'Customer personal identifiable information', True)
        ]
        
        table_ids = {}
        for table_name, description, is_sensitive in tables:
            table_result = await conn.fetchrow("""
                INSERT INTO security_tables (source_id, table_name, description, is_sensitive)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (source_id, table_name) 
                DO UPDATE SET description = EXCLUDED.description
                RETURNING table_id
            """, druid_source_id, table_name, description, is_sensitive)
            
            table_ids[table_name] = table_result['table_id']
            print(f"   ✅ Table: {table_name} (ID: {table_result['table_id']})")
        
        # 3. Register columns with sensitivity levels
        print("\n3. Registering columns with sensitivity...")
        columns_config = {
            'employee_sensitive': [
                ('employee_id', 'integer', 'low'),
                ('name', 'varchar', 'medium'),
                ('email', 'varchar', 'high'),
                ('phone', 'varchar', 'high'),
                ('salary', 'integer', 'high'),
                ('department', 'varchar', 'low'),
                ('ssn', 'varchar', 'critical'),
                ('performance_rating', 'varchar', 'medium')
            ],
            'customer_pii': [
                ('customer_id', 'integer', 'low'),
                ('full_name', 'varchar', 'high'),
                ('email', 'varchar', 'high'),
                ('phone', 'varchar', 'high'),
                ('address', 'varchar', 'high'),
                ('credit_card', 'varchar', 'critical'),
                ('date_of_birth', 'date', 'high'),
                ('loyalty_tier', 'varchar', 'low')
            ]
        }
        
        column_ids = {}
        for table_name, columns in columns_config.items():
            table_id = table_ids[table_name]
            for col_name, data_type, sensitivity in columns:
                col_result = await conn.fetchrow("""
                    INSERT INTO security_columns (table_id, column_name, data_type, is_sensitive, sensitivity_level)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (table_id, column_name) 
                    DO UPDATE SET data_type = EXCLUDED.data_type, sensitivity_level = EXCLUDED.sensitivity_level
                    RETURNING column_id
                """, table_id, col_name, data_type, sensitivity in ['high', 'critical'], sensitivity)
                
                column_ids[f"{table_name}.{col_name}"] = col_result['column_id']
                print(f"   ✅ {table_name}.{col_name} ({sensitivity})")
        
        # 4. Get role IDs
        print("\n4. Getting security roles...")
        roles = await conn.fetch("""
            SELECT role_id, role_name FROM security_roles ORDER BY role_name
        """)
        
        role_ids = {role['role_name']: role['role_id'] for role in roles}
        for role_name, role_id in role_ids.items():
            print(f"   ✅ Role: {role_name} (ID: {role_id})")
        
        # 5. Create CLS policies
        print("\n5. Creating CLS policies...")
        
        # Define policies: (table.column, role, access_type, mask_type)
        cls_policies = [
            # Admin - Full access to everything
            ('employee_sensitive.*', 'admin', 'allow', None),
            ('customer_pii.*', 'admin', 'allow', None),
            
            # Data Engineer - Access to most data, but mask sensitive PII
            ('employee_sensitive.employee_id', 'data_engineer', 'allow', None),
            ('employee_sensitive.name', 'data_engineer', 'allow', None),
            ('employee_sensitive.email', 'data_engineer', 'mask', 'email'),
            ('employee_sensitive.phone', 'data_engineer', 'mask', 'phone'),
            ('employee_sensitive.salary', 'data_engineer', 'mask', 'partial'),
            ('employee_sensitive.department', 'data_engineer', 'allow', None),
            ('employee_sensitive.ssn', 'data_engineer', 'mask', 'ssn'),
            ('employee_sensitive.performance_rating', 'data_engineer', 'allow', None),
            
            ('customer_pii.customer_id', 'data_engineer', 'allow', None),
            ('customer_pii.full_name', 'data_engineer', 'mask', 'partial'),
            ('customer_pii.email', 'data_engineer', 'mask', 'email'),
            ('customer_pii.phone', 'data_engineer', 'mask', 'phone'),
            ('customer_pii.address', 'data_engineer', 'mask', 'partial'),
            ('customer_pii.credit_card', 'data_engineer', 'mask', 'credit_card'),
            ('customer_pii.date_of_birth', 'data_engineer', 'deny', None),
            ('customer_pii.loyalty_tier', 'data_engineer', 'allow', None),
            
            # Business Analyst - Limited access, heavy masking
            ('employee_sensitive.employee_id', 'business_analyst', 'allow', None),
            ('employee_sensitive.name', 'business_analyst', 'mask', 'partial'),
            ('employee_sensitive.email', 'business_analyst', 'deny', None),
            ('employee_sensitive.phone', 'business_analyst', 'deny', None),
            ('employee_sensitive.salary', 'business_analyst', 'mask', 'hash'),
            ('employee_sensitive.department', 'business_analyst', 'allow', None),
            ('employee_sensitive.ssn', 'business_analyst', 'deny', None),
            ('employee_sensitive.performance_rating', 'business_analyst', 'allow', None),
            
            ('customer_pii.customer_id', 'business_analyst', 'allow', None),
            ('customer_pii.full_name', 'business_analyst', 'mask', 'partial'),
            ('customer_pii.email', 'business_analyst', 'deny', None),
            ('customer_pii.phone', 'business_analyst', 'deny', None),
            ('customer_pii.address', 'business_analyst', 'deny', None),
            ('customer_pii.credit_card', 'business_analyst', 'deny', None),
            ('customer_pii.date_of_birth', 'business_analyst', 'deny', None),
            ('customer_pii.loyalty_tier', 'business_analyst', 'allow', None),
            
            # User - Very restricted access
            ('employee_sensitive.employee_id', 'user', 'allow', None),
            ('employee_sensitive.name', 'user', 'mask', 'partial'),
            ('employee_sensitive.email', 'user', 'deny', None),
            ('employee_sensitive.phone', 'user', 'deny', None),
            ('employee_sensitive.salary', 'user', 'deny', None),
            ('employee_sensitive.department', 'user', 'allow', None),
            ('employee_sensitive.ssn', 'user', 'deny', None),
            ('employee_sensitive.performance_rating', 'user', 'deny', None),
            
            ('customer_pii.customer_id', 'user', 'deny', None),
            ('customer_pii.full_name', 'user', 'deny', None),
            ('customer_pii.email', 'user', 'deny', None),
            ('customer_pii.phone', 'user', 'deny', None),
            ('customer_pii.address', 'user', 'deny', None),
            ('customer_pii.credit_card', 'user', 'deny', None),
            ('customer_pii.date_of_birth', 'user', 'deny', None),
            ('customer_pii.loyalty_tier', 'user', 'deny', None),
        ]
        
        policies_created = 0
        for policy_pattern, role_name, access_type, mask_type in cls_policies:
            role_id = role_ids[role_name]
            
            # Handle wildcard policies
            if policy_pattern.endswith('.*'):
                table_name = policy_pattern[:-2]
                table_id = table_ids[table_name]
                
                # Get all columns for this table
                columns = await conn.fetch("""
                    SELECT column_id FROM security_columns WHERE table_id = $1
                """, table_id)
                
                for column in columns:
                    await conn.execute("""
                        INSERT INTO security_cls_policies 
                        (role_id, column_id, access_type, mask_type, policy_name, is_active)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (role_id, column_id) 
                        DO UPDATE SET access_type = EXCLUDED.access_type, mask_type = EXCLUDED.mask_type
                    """, role_id, column['column_id'], access_type, mask_type, 
                       f"{role_name}_{table_name}_full", True)
                    policies_created += 1
            else:
                # Specific column policy
                table_name, column_name = policy_pattern.split('.')
                column_key = f"{table_name}.{column_name}"
                
                if column_key in column_ids:
                    await conn.execute("""
                        INSERT INTO security_cls_policies 
                        (role_id, column_id, access_type, mask_type, policy_name, is_active)
                        VALUES ($1, $2, $3, $4, $5, $6)
                        ON CONFLICT (role_id, column_id) 
                        DO UPDATE SET access_type = EXCLUDED.access_type, mask_type = EXCLUDED.mask_type
                    """, role_id, column_ids[column_key], access_type, mask_type,
                       f"{role_name}_{table_name}_{column_name}", True)
                    policies_created += 1
        
        print(f"   ✅ Created {policies_created} CLS policies")
        
        # 6. Verify setup
        print("\n6. Verifying CLS setup...")
        policy_count = await conn.fetchval("""
            SELECT COUNT(*) FROM security_cls_policies WHERE is_active = true
        """)
        
        table_count = await conn.fetchval("""
            SELECT COUNT(*) FROM security_tables WHERE source_id = $1
        """, druid_source_id)
        
        column_count = await conn.fetchval("""
            SELECT COUNT(*) FROM security_columns c
            JOIN security_tables t ON c.table_id = t.table_id
            WHERE t.source_id = $1
        """, druid_source_id)
        
        print(f"   📊 Tables: {table_count}")
        print(f"   📊 Columns: {column_count}") 
        print(f"   📊 Policies: {policy_count}")
        
        await conn.close()
        
        print(f"\n🎉 CLS Policy Setup Complete!")
        print("   ✅ PostgreSQL security policies configured")
        print("   ✅ Ready for Druid data testing")
        print("   ✅ Universal CLS engine can now be tested")
        
        return True
        
    except Exception as e:
        print(f"❌ CLS setup failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_cls_policies())
    exit(0 if success else 1)
