#!/usr/bin/env python3
"""
Simple CLS setup using existing security data
"""

import asyncio
import asyncpg

async def setup_simple_cls():
    """Setup simple CLS policies using existing data"""
    print("🔐 Simple CLS Setup")
    print("=" * 25)
    
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='security_user',
            password='security_pass',
            database='universal_security'
        )
        
        # 1. Get existing Druid data source or create one
        print("1. Setting up data source...")
        druid_source = await conn.fetchrow("""
            SELECT source_id FROM security_data_sources 
            WHERE engine_type = 'druid' LIMIT 1
        """)
        
        if not druid_source:
            druid_source = await conn.fetchrow("""
                INSERT INTO security_data_sources 
                (source_name, engine_type, connection_config)
                VALUES ($1, $2, $3)
                RETURNING source_id
            """, 'druid_cls_test', 'druid', '{"host": "localhost", "port": 8082}')
            print("   ✅ Created Druid data source")
        else:
            print("   ✅ Using existing Druid data source")
        
        druid_source_id = druid_source['source_id']
        
        # 2. Create a simple test table
        print("\n2. Creating test table...")
        test_table = await conn.fetchrow("""
            INSERT INTO security_tables 
            (source_id, table_name, description, is_sensitive)
            VALUES ($1, $2, $3, $4)
            RETURNING table_id
        """, druid_source_id, 'test_employees', 'Test employee data for CLS', True)
        
        table_id = test_table['table_id']
        print(f"   ✅ Created test_employees table (ID: {table_id})")
        
        # 3. Add some test columns
        print("\n3. Adding test columns...")
        test_columns = [
            ('emp_id', 'integer', False, 'low'),
            ('full_name', 'varchar', True, 'medium'),
            ('email', 'varchar', True, 'high'),
            ('salary', 'integer', True, 'high'),
            ('department', 'varchar', False, 'low')
        ]
        
        column_ids = {}
        for col_name, data_type, is_sensitive, sensitivity in test_columns:
            column = await conn.fetchrow("""
                INSERT INTO security_columns 
                (table_id, column_name, data_type, is_sensitive, sensitivity_level)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING column_id
            """, table_id, col_name, data_type, is_sensitive, sensitivity)
            
            column_ids[col_name] = column['column_id']
            sensitive_flag = "🔒" if is_sensitive else "🔓"
            print(f"   {sensitive_flag} {col_name} ({sensitivity})")
        
        # 4. Get existing roles
        print("\n4. Getting security roles...")
        roles = await conn.fetch("""
            SELECT role_id, role_name FROM security_roles 
            WHERE role_name IN ('admin', 'data_engineer', 'business_analyst', 'user')
        """)
        
        role_ids = {role['role_name']: role['role_id'] for role in roles}
        for role_name, role_id in role_ids.items():
            print(f"   👤 {role_name} (ID: {role_id})")
        
        # 5. Create simple CLS policies
        print("\n5. Creating CLS policies...")
        
        # Define policies for each role
        policies = [
            # Admin - full access to everything
            ('admin', 'emp_id', 'allow', None),
            ('admin', 'full_name', 'allow', None),
            ('admin', 'email', 'allow', None),
            ('admin', 'salary', 'allow', None),
            ('admin', 'department', 'allow', None),
            
            # Data Engineer - masked sensitive data
            ('data_engineer', 'emp_id', 'allow', None),
            ('data_engineer', 'full_name', 'allow', None),
            ('data_engineer', 'email', 'mask', 'email'),
            ('data_engineer', 'salary', 'mask', 'partial'),
            ('data_engineer', 'department', 'allow', None),
            
            # Business Analyst - limited access
            ('business_analyst', 'emp_id', 'allow', None),
            ('business_analyst', 'full_name', 'mask', 'partial'),
            ('business_analyst', 'email', 'deny', None),
            ('business_analyst', 'salary', 'deny', None),
            ('business_analyst', 'department', 'allow', None),
            
            # User - very limited
            ('user', 'emp_id', 'allow', None),
            ('user', 'full_name', 'mask', 'partial'),
            ('user', 'email', 'deny', None),
            ('user', 'salary', 'deny', None),
            ('user', 'department', 'deny', None),
        ]
        
        for role_name, column_name, access_type, mask_type in policies:
            await conn.execute("""
                INSERT INTO security_cls_policies 
                (role_id, column_id, access_type, mask_type, policy_name, is_active)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, role_ids[role_name], column_ids[column_name], access_type, mask_type,
               f"{role_name}_{column_name}", True)
            
            mask_info = f" ({mask_type})" if mask_type else ""
            print(f"   ✅ {role_name} -> {column_name}: {access_type}{mask_info}")
        
        # 6. Verify setup
        print("\n6. Verifying CLS setup...")
        policy_count = await conn.fetchval("SELECT COUNT(*) FROM security_cls_policies WHERE is_active = true")
        column_count = await conn.fetchval("SELECT COUNT(*) FROM security_columns WHERE table_id = $1", table_id)
        
        print(f"   📊 Policies created: {policy_count}")
        print(f"   📊 Columns configured: {column_count}")
        
        await conn.close()
        
        print(f"\n🎉 Simple CLS Setup Complete!")
        print("   ✅ Test table and columns created")
        print("   ✅ CLS policies configured")
        print("   ✅ Ready for Universal CLS engine testing")
        
        return True
        
    except Exception as e:
        print(f"❌ CLS setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_simple_cls())
    exit(0 if success else 1)
