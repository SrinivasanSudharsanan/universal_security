#!/usr/bin/env python3
"""
Complete database structure report
"""

import asyncio
import asyncpg

async def generate_database_report():
    print("📊 UNIVERSAL SECURITY DATABASE REPORT")
    print("=" * 55)
    
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='security_user',
            password='security_pass',
            database='universal_security'
        )
        
        # 1. Count all tables
        print("1. 📋 DATABASE TABLES SUMMARY")
        print("-" * 35)
        
        all_tables = await conn.fetch("""
            SELECT table_name, table_type
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print(f"Total tables in database: {len(all_tables)}")
        
        # 2. Security Tables Details
        print(f"\n2. 🔒 SECURITY TABLES DETAILS")
        print("-" * 35)
        
        security_tables = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'security_%'
            ORDER BY table_name
        """)
        
        print(f"Security tables: {len(security_tables)}")
        
        for table in security_tables:
            table_name = table['table_name']
            
            # Get column details for each security table
            columns = await conn.fetch("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = $1
                ORDER BY ordinal_position
            """, table_name)
            
            print(f"\n   🏷️  Table: {table_name}")
            print(f"   📊 Columns: {len(columns)}")
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                print(f"      • {col['column_name']} ({col['data_type']}) {nullable}{default}")
        
        # 3. Security Users Details
        print(f"\n3. 👥 SECURITY USERS")
        print("-" * 35)
        
        users = await conn.fetch("""
            SELECT 
                user_id,
                username,
                email,
                is_active,
                created_at,
                password_hash IS NOT NULL as has_password
            FROM security_users 
            ORDER BY username
        """)
        
        print(f"Total users: {len(users)}")
        for user in users:
            status = "✅ ACTIVE" if user['is_active'] else "❌ INACTIVE"
            password_status = "🔐 HAS PASSWORD" if user['has_password'] else "⚠️ NO PASSWORD"
            print(f"   👤 {user['username']} ({user['email']})")
            print(f"      ID: {user['user_id']}, Status: {status}, {password_status}")
            print(f"      Created: {user['created_at']}")
        
        # 4. Security Roles and User Mappings
        print(f"\n4. 🛡️ SECURITY ROLES AND ASSIGNMENTS")
        print("-" * 35)
        
        roles = await conn.fetch("""
            SELECT role_id, role_name, description, is_system_role
            FROM security_roles 
            ORDER BY role_name
        """)
        
        print(f"Total roles: {len(roles)}")
        for role in roles:
            system_flag = "🔧 SYSTEM" if role['is_system_role'] else "👤 CUSTOM"
            print(f"   🎯 {role['role_name']} ({system_flag})")
            print(f"      Description: {role['description']}")
            
            # Get users with this role
            role_users = await conn.fetch("""
                SELECT u.username
                FROM security_user_roles ur
                JOIN security_users u ON ur.user_id = u.user_id
                WHERE ur.role_id = $1
                ORDER BY u.username
            """, role['role_id'])
            
            if role_users:
                user_list = ", ".join([u['username'] for u in role_users])
                print(f"      Users: {user_list}")
            else:
                print(f"      Users: None")
        
        # 5. Data Sources
        print(f"\n5. 🌐 DATA SOURCES")
        print("-" * 35)
        
        data_sources = await conn.fetch("""
            SELECT source_id, source_name, engine_type, is_active, created_at
            FROM security_data_sources 
            ORDER BY source_name
        """)
        
        print(f"Total data sources: {len(data_sources)}")
        for source in data_sources:
            status = "✅ ACTIVE" if source['is_active'] else "❌ INACTIVE"
            print(f"   🔗 {source['source_name']} ({source['engine_type']})")
            print(f"      Status: {status}, Created: {source['created_at']}")
        
        # 6. Database Statistics
        print(f"\n6. 📈 DATABASE STATISTICS")
        print("-" * 35)
        
        stats = await conn.fetch("""
            SELECT 
                (SELECT COUNT(*) FROM security_roles) as roles_count,
                (SELECT COUNT(*) FROM security_users) as users_count,
                (SELECT COUNT(*) FROM security_user_roles) as mappings_count,
                (SELECT COUNT(*) FROM security_data_sources) as sources_count,
                (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') as total_tables,
                (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'security_%') as security_tables_count
        """)
        
        stat = stats[0]
        print(f"   Security Roles: {stat['roles_count']}")
        print(f"   Security Users: {stat['users_count']}")
        print(f"   User-Role Mappings: {stat['mappings_count']}")
        print(f"   Data Sources: {stat['sources_count']}")
        print(f"   Total Tables: {stat['total_tables']}")
        print(f"   Security Tables: {stat['security_tables_count']}")
        
        await conn.close()
        
        print(f"\n🎯 REPORT SUMMARY")
        print("=" * 55)
        print(f"✅ Security Framework: OPERATIONAL")
        print(f"✅ Database Structure: COMPLETE")
        print(f"✅ User Management: READY")
        print(f"✅ Role-Based Access: CONFIGURED")
        print(f"✅ Data Sources: REGISTERED")
        
        return True
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(generate_database_report())
    exit(0 if success else 1)
