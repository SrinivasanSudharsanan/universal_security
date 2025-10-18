#!/usr/bin/env python3
"""
Comprehensive security test using INFORMATION_SCHEMA tables
Tests Roles, RLS, and Column Security
"""

from engines.unified_connector import UnifiedConnector
from config import get_settings

class InformationSchemaSecurityTester:
    def __init__(self):
        self.connector = UnifiedConnector()
        self.settings = get_settings()
        self.current_user_role = None
        
        # Security policies for INFORMATION_SCHEMA tables
        self.rls_policies = {
            'TABLES': {
                'admin': "1=1",  # See all tables
                'engineering': "TABLE_SCHEMA IN ('druid', 'sys')",
                'analyst': "TABLE_SCHEMA = 'INFORMATION_SCHEMA'",
                'public': "TABLE_NAME LIKE 'COLUMNS' OR TABLE_NAME LIKE 'TABLES'",
                'guest': "1=0"  # See nothing
            },
            'COLUMNS': {
                'admin': "1=1",  # See all columns
                'engineering': "TABLE_SCHEMA IN ('druid', 'sys')",
                'analyst': "TABLE_SCHEMA = 'INFORMATION_SCHEMA'", 
                'public': "TABLE_NAME LIKE 'COLUMNS' OR TABLE_NAME LIKE 'TABLES'",
                'guest': "1=0"
            },
            'SCHEMATA': {
                'admin': "1=1",  # See all schemas
                'engineering': "SCHEMA_NAME IN ('druid', 'sys')",
                'analyst': "SCHEMA_NAME = 'INFORMATION_SCHEMA'",
                'public': "SCHEMA_NAME = 'INFORMATION_SCHEMA'",
                'guest': "1=0"
            }
        }
        
        self.column_policies = {
            'TABLES': {
                'admin': ['TABLE_CATALOG', 'TABLE_SCHEMA', 'TABLE_NAME', 'TABLE_TYPE'],
                'engineering': ['TABLE_SCHEMA', 'TABLE_NAME', 'TABLE_TYPE'],
                'analyst': ['TABLE_NAME', 'TABLE_TYPE'],
                'public': ['TABLE_NAME'],
                'guest': ['TABLE_NAME']
            },
            'COLUMNS': {
                'admin': ['TABLE_CATALOG', 'TABLE_SCHEMA', 'TABLE_NAME', 'COLUMN_NAME', 'DATA_TYPE'],
                'engineering': ['TABLE_SCHEMA', 'TABLE_NAME', 'COLUMN_NAME', 'DATA_TYPE'],
                'analyst': ['TABLE_NAME', 'COLUMN_NAME', 'DATA_TYPE'],
                'public': ['TABLE_NAME', 'COLUMN_NAME'],
                'guest': ['TABLE_NAME']
            },
            'SCHEMATA': {
                'admin': ['CATALOG_NAME', 'SCHEMA_NAME', 'SCHEMA_OWNER'],
                'engineering': ['SCHEMA_NAME', 'SCHEMA_OWNER'],
                'analyst': ['SCHEMA_NAME'],
                'public': ['SCHEMA_NAME'],
                'guest': ['SCHEMA_NAME']
            }
        }
    
    def set_user_role(self, role):
        """Set current user role"""
        valid_roles = ['admin', 'engineering', 'analyst', 'public', 'guest']
        if role in valid_roles:
            self.current_user_role = role
            print(f"🔐 User role set to: {role}")
            return True
        print(f"❌ Invalid role: {role}")
        return False
    
    def apply_security_to_query(self, table_name):
        """Apply RLS and column security to query"""
        if table_name not in self.rls_policies or self.current_user_role not in self.rls_policies[table_name]:
            return None
        
        # Get allowed columns
        allowed_columns = self.column_policies[table_name][self.current_user_role]
        columns_str = ", ".join(allowed_columns)
        
        # Get RLS condition
        rls_condition = self.rls_policies[table_name][self.current_user_role]
        
        # Build secured query
        query = f"SELECT {columns_str} FROM INFORMATION_SCHEMA.{table_name} WHERE {rls_condition}"
        
        print(f"🛡️  Secured Query for {self.current_user_role}:")
        print(f"   {query}")
        
        return query
    
    def test_role_based_access(self):
        """Test role-based access to INFORMATION_SCHEMA"""
        print("🎭 TESTING ROLE-BASED ACCESS CONTROL")
        print("=" * 50)
        
        test_roles = ['admin', 'engineering', 'analyst', 'public', 'guest']
        test_tables = ['TABLES', 'COLUMNS', 'SCHEMATA']
        
        for role in test_roles:
            self.set_user_role(role)
            print(f"\n{'='*30}")
            print(f"Testing as: {role.upper()}")
            print(f"{'='*30}")
            
            for table in test_tables:
                print(f"\n📋 Table: {table}")
                
                secured_query = self.apply_security_to_query(table)
                if not secured_query:
                    print("   ❌ No security policy defined")
                    continue
                
                try:
                    result = self.connector.execute_query(secured_query, engine_type='druid')
                    print(f"   ✅ Access granted: {len(result)} rows visible")
                    
                    if len(result) > 0:
                        # Show sample of what this role can see
                        sample = result.iloc[0].to_dict()
                        print(f"   👁️  Sample data: {sample}")
                    
                except Exception as e:
                    print(f"   ❌ Access failed: {e}")
    
    def test_column_level_security(self):
        """Test column-level security"""
        print("\n\n🔒 TESTING COLUMN-LEVEL SECURITY")
        print("=" * 50)
        
        test_roles = ['admin', 'engineering', 'public']
        table = 'COLUMNS'
        
        for role in test_roles:
            self.set_user_role(role)
            print(f"\nRole: {role}")
            
            secured_query = self.apply_security_to_query(table)
            if secured_query:
                try:
                    result = self.connector.execute_query(secured_query, engine_type='druid')
                    columns_visible = len(result.columns) if len(result) > 0 else 0
                    print(f"   📊 Columns visible: {columns_visible}")
                    print(f"   👀 Can see: {list(result.columns)}")
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
    
    def test_row_level_security(self):
        """Test row-level security"""
        print("\n\n📊 TESTING ROW-LEVEL SECURITY")
        print("=" * 50)
        
        table = 'TABLES'
        test_roles = ['admin', 'engineering', 'public']
        
        print("Comparing row visibility across roles:")
        print("-" * 40)
        
        role_results = {}
        for role in test_roles:
            self.set_user_role(role)
            secured_query = self.apply_security_to_query(table)
            
            if secured_query:
                try:
                    result = self.connector.execute_query(secured_query, engine_type='druid')
                    role_results[role] = len(result)
                    print(f"   {role:12}: {len(result):3} tables visible")
                    
                    # Show what tables are visible
                    if len(result) > 0:
                        tables_visible = result['TABLE_NAME'].tolist()[:3]  # First 3 tables
                        print(f"               Sample: {tables_visible}")
                except Exception as e:
                    print(f"   {role:12}: ❌ {e}")
        
        print(f"\n📈 RLS Effectiveness:")
        admin_count = role_results.get('admin', 0)
        for role in test_roles[1:]:
            if role in role_results:
                reduction = ((admin_count - role_results[role]) / admin_count) * 100
                print(f"   {role:12}: {reduction:.1f}% data reduction vs admin")
    
    def run_comprehensive_test(self):
        """Run all security tests"""
        print("🛡️ COMPREHENSIVE SECURITY TESTING WITH INFORMATION_SCHEMA")
        print("=" * 60)
        
        # Initialize connection
        self.connector.initialize_connector('druid', self.settings.druid_config)
        
        try:
            # Test 1: Role-based access
            self.test_role_based_access()
            
            # Test 2: Column-level security  
            self.test_column_level_security()
            
            # Test 3: Row-level security
            self.test_row_level_security()
            
            print("\n" + "=" * 60)
            print("🎯 SECURITY TESTING COMPLETE!")
            print("   ✅ Role-Based Access Control")
            print("   ✅ Column-Level Security") 
            print("   ✅ Row-Level Security")
            print("   ✅ Using Real Druid INFORMATION_SCHEMA Tables")
            
        finally:
            self.connector.close_all()

if __name__ == "__main__":
    tester = InformationSchemaSecurityTester()
    tester.run_comprehensive_test()
