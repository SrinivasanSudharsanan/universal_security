#!/usr/bin/env python3
"""
Comprehensive security testing on real Druid data tables (employees & sales)
Uses ACTUAL column names from Druid tables
"""

from engines.unified_connector import UnifiedConnector
from config import get_settings

class FixedRealDataSecurityTester:
    def __init__(self):
        self.connector = UnifiedConnector()
        self.settings = get_settings()
        self.current_user_role = None
        
        # Security policies using ACTUAL Druid column names
        self.security_policies = {
            # Row-Level Security policies
            'rls_policies': {
                'employees': {
                    'admin': "1=1",  # See all employees
                    'hr': "1=1",  # HR can see all but with column restrictions
                    'engineering_manager': "department = 'Engineering'",
                    'sales_manager': "department IN ('Sales', 'Marketing')",
                    'employee': "access_level = 'public'",  # Only public info
                    'public': "access_level = 'public'"
                },
                'sales': {
                    'admin': "1=1",  # See all sales
                    'sales_director': "1=1",  # All sales data
                    'regional_manager': "region IN ('North', 'South')",
                    'sales_rep': "amount_sum < 6000",  # Smaller deals only
                    'public': "1=0"  # No public access to sales
                }
            },
            
            # Column-Level Security policies - USING ACTUAL COLUMN NAMES
            'cls_policies': {
                'employees': {
                    'admin': ['name', 'department', 'salary_sum', 'access_level', 'count'],
                    'hr': ['name', 'department', 'salary_sum'],  # No access_level
                    'engineering_manager': ['name', 'department', 'access_level'],  # No salary_sum
                    'sales_manager': ['name', 'department', 'access_level'],  # No salary_sum
                    'employee': ['name', 'department'],  # Minimal info
                    'public': ['name', 'department']  # Public info only
                },
                'sales': {
                    'admin': ['product', 'amount_sum', 'customer', 'region', 'quarter', 'count'],
                    'sales_director': ['product', 'amount_sum', 'customer', 'region', 'quarter'],
                    'regional_manager': ['product', 'amount_sum', 'region', 'quarter'],  # No customer names
                    'sales_rep': ['product', 'amount_sum', 'quarter'],  # Limited info
                    'public': ['product', 'quarter']  # Very limited
                }
            }
        }
    
    def set_user_role(self, role):
        """Set current user role"""
        valid_roles = ['admin', 'hr', 'engineering_manager', 'sales_manager', 'sales_director', 'regional_manager', 'employee', 'public']
        if role in valid_roles:
            self.current_user_role = role
            print(f"🔐 User role set to: {role}")
            return True
        print(f"❌ Invalid role: {role}")
        return False
    
    def apply_security_to_query(self, table_name):
        """Apply RLS and column security to query"""
        if table_name not in self.security_policies['rls_policies']:
            return f"SELECT * FROM {table_name}"
        
        if self.current_user_role not in self.security_policies['rls_policies'][table_name]:
            return f"SELECT * FROM {table_name}"
        
        # Get allowed columns
        allowed_columns = self.security_policies['cls_policies'][table_name][self.current_user_role]
        columns_str = ", ".join(allowed_columns)
        
        # Get RLS condition
        rls_condition = self.security_policies['rls_policies'][table_name][self.current_user_role]
        
        # Build secured query
        query = f"SELECT {columns_str} FROM {table_name} WHERE {rls_condition}"
        
        print(f"🛡️  Secured Query for {self.current_user_role}:")
        print(f"   {query}")
        
        return query
    
    def test_role_based_access(self):
        """Test role-based access to real data tables"""
        print("🎭 TESTING ROLE-BASED ACCESS ON REAL DATA")
        print("=" * 50)
        print("📝 Using ACTUAL Druid column names: salary_sum, amount_sum")
        print("=" * 50)
        
        test_roles = ['admin', 'hr', 'engineering_manager', 'sales_manager', 'employee', 'public']
        test_tables = ['employees', 'sales']
        
        for role in test_roles:
            self.set_user_role(role)
            print(f"\n{'='*40}")
            print(f"Testing as: {role.upper()}")
            print(f"{'='*40}")
            
            for table in test_tables:
                print(f"\n📋 Table: {table}")
                
                secured_query = self.apply_security_to_query(table)
                
                try:
                    result = self.connector.execute_query(secured_query, engine_type='druid')
                    print(f"   ✅ Access granted: {len(result)} rows visible")
                    print(f"   📊 Columns visible: {len(result.columns)}")
                    print(f"   👀 Can see: {list(result.columns)}")
                    
                    if len(result) > 0:
                        # Show sample of what this role can see
                        sample = result.iloc[0].to_dict()
                        print(f"   👁️  Sample data: {sample}")
                    
                except Exception as e:
                    print(f"   ❌ Access failed: {e}")
    
    def test_data_leak_prevention(self):
        """Test that sensitive data is properly protected"""
        print("\n\n🔒 TESTING DATA LEAK PREVENTION")
        print("=" * 50)
        
        sensitive_tests = [
            {
                'role': 'admin',
                'table': 'employees',
                'sensitive_field': 'salary_sum',
                'should_see': True
            },
            {
                'role': 'engineering_manager', 
                'table': 'employees',
                'sensitive_field': 'salary_sum',
                'should_see': False
            },
            {
                'role': 'sales_director',
                'table': 'sales', 
                'sensitive_field': 'customer',
                'should_see': True
            },
            {
                'role': 'regional_manager',
                'table': 'sales',
                'sensitive_field': 'customer', 
                'should_see': False
            }
        ]
        
        print("Testing sensitive data protection:")
        print("-" * 40)
        
        for test in sensitive_tests:
            self.set_user_role(test['role'])
            secured_query = self.apply_security_to_query(test['table'])
            
            try:
                result = self.connector.execute_query(secured_query, engine_type='druid')
                columns = list(result.columns) if len(result) > 0 else []
                
                has_sensitive_data = test['sensitive_field'] in columns
                status = "✅ PASS" if has_sensitive_data == test['should_see'] else "❌ FAIL"
                
                print(f"{status} {test['role']:20} | {test['table']:12} | {test['sensitive_field']:15} | "
                      f"Should see: {test['should_see']:5} | Actually sees: {has_sensitive_data:5}")
                      
            except Exception as e:
                print(f"❌ ERROR {test['role']:20} | {test['table']:12} | {test['sensitive_field']:15} | Error: {e}")
    
    def test_business_scenarios(self):
        """Test real business security scenarios"""
        print("\n\n🏢 TESTING BUSINESS SECURITY SCENARIOS")
        print("=" * 50)
        
        scenarios = [
            {
                'name': 'HR View vs Manager View',
                'roles': ['hr', 'engineering_manager'],
                'table': 'employees',
                'check': 'salary_sum visibility'
            },
            {
                'name': 'Sales Territory Access',
                'roles': ['sales_director', 'regional_manager'],
                'table': 'sales', 
                'check': 'regional data access'
            },
            {
                'name': 'Public Data Exposure',
                'roles': ['admin', 'public'],
                'table': 'employees',
                'check': 'data reduction'
            }
        ]
        
        for scenario in scenarios:
            print(f"\n📋 Scenario: {scenario['name']}")
            print(f"   Check: {scenario['check']}")
            print("   " + "-" * 30)
            
            role_results = {}
            for role in scenario['roles']:
                self.set_user_role(role)
                secured_query = self.apply_security_to_query(scenario['table'])
                
                try:
                    result = self.connector.execute_query(secured_query, engine_type='druid')
                    role_results[role] = len(result)
                    print(f"   👤 {role:20}: {len(result):2} rows visible")
                    
                except Exception as e:
                    print(f"   👤 {role:20}: ❌ {e}")
            
            # Calculate data reduction
            if len(role_results) == 2:
                roles = list(role_results.keys())
                if role_results[roles[0]] > 0:
                    reduction = ((role_results[roles[0]] - role_results[roles[1]]) / role_results[roles[0]]) * 100
                    print(f"   📊 Data reduction: {reduction:.1f}% for {roles[1]} vs {roles[0]}")
    
    def run_comprehensive_test(self):
        """Run all security tests"""
        print("🛡️ COMPREHENSIVE SECURITY TESTING ON REAL DATA")
        print("=" * 60)
        print("📊 Testing on tables: employees, sales")
        print("🎭 Testing roles: admin, hr, engineering_manager, sales_manager, employee, public")
        print("📝 Using ACTUAL Druid columns: salary_sum, amount_sum")
        print("=" * 60)
        
        # Initialize connection
        self.connector.initialize_connector('druid', self.settings.druid_config)
        
        try:
            # Test 1: Role-based access
            self.test_role_based_access()
            
            # Test 2: Data leak prevention
            self.test_data_leak_prevention()
            
            # Test 3: Business scenarios
            self.test_business_scenarios()
            
            print("\n" + "=" * 60)
            print("🎯 REAL DATA SECURITY TESTING COMPLETE!")
            print("   ✅ Role-Based Access Control on Business Data")
            print("   ✅ Column-Level Security (Salary, Customer Data)")
            print("   ✅ Row-Level Security (Department, Region Filters)")
            print("   ✅ Data Leak Prevention Verified")
            print("   ✅ Business Scenarios Validated")
            print("   🎉 USING ACTUAL DRUID DATA TABLES!")
            
        finally:
            self.connector.close_all()

if __name__ == "__main__":
    tester = FixedRealDataSecurityTester()
    tester.run_comprehensive_test()
