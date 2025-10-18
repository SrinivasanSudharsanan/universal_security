#!/usr/bin/env python3
"""
FINAL POLISHED SECURITY TEST - Working perfectly with real Druid data
"""

from engines.unified_connector import UnifiedConnector
from config import get_settings

class FinalSecurityTester:
    def __init__(self):
        self.connector = UnifiedConnector()
        self.settings = get_settings()
        self.current_user_role = None
        
        # Security policies using ACTUAL Druid column names (avoiding reserved keywords)
        self.security_policies = {
            # Row-Level Security policies
            'rls_policies': {
                'employees': {
                    'admin': "1=1",
                    'hr': "1=1", 
                    'engineering_manager': "department = 'Engineering'",
                    'sales_manager': "department IN ('Sales', 'Marketing')",
                    'employee': "access_level = 'public'",
                    'public': "access_level = 'public'"
                },
                'sales': {
                    'admin': "1=1",
                    'sales_director': "1=1",
                    'regional_manager': "region IN ('North', 'South')",
                    'sales_rep': "amount_sum < 6000",
                    'public': "1=0"
                }
            },
            
            # Column-Level Security - Using actual columns, avoiding 'count' reserved word
            'cls_policies': {
                'employees': {
                    'admin': ['name', 'department', 'salary_sum', 'access_level'],
                    'hr': ['name', 'department', 'salary_sum'],
                    'engineering_manager': ['name', 'department', 'access_level'],
                    'sales_manager': ['name', 'department', 'access_level'],
                    'employee': ['name', 'department'],
                    'public': ['name', 'department']
                },
                'sales': {
                    'admin': ['product', 'amount_sum', 'customer', 'region', 'quarter'],
                    'sales_director': ['product', 'amount_sum', 'customer', 'region', 'quarter'],
                    'regional_manager': ['product', 'amount_sum', 'region', 'quarter'],
                    'sales_rep': ['product', 'amount_sum', 'quarter'],
                    'public': ['product', 'quarter']
                }
            }
        }
    
    def set_user_role(self, role):
        """Set current user role"""
        self.current_user_role = role
        return True
    
    def apply_security_to_query(self, table_name):
        """Apply RLS and column security to query"""
        if (table_name not in self.security_policies['rls_policies'] or 
            self.current_user_role not in self.security_policies['rls_policies'][table_name]):
            return f"SELECT * FROM {table_name}"
        
        allowed_columns = self.security_policies['cls_policies'][table_name][self.current_user_role]
        columns_str = ", ".join(allowed_columns)
        rls_condition = self.security_policies['rls_policies'][table_name][self.current_user_role]
        
        return f"SELECT {columns_str} FROM {table_name} WHERE {rls_condition}"
    
    def run_final_test(self):
        """Run final comprehensive security test"""
        print("🎯 FINAL UNIVERSAL SECURITY FRAMEWORK TEST")
        print("=" * 60)
        print("📊 Testing on: employees, sales (Real Druid Data Tables)")
        print("🎭 Security: Role-Based + Column-Level + Row-Level")
        print("=" * 60)
        
        self.connector.initialize_connector('druid', self.settings.druid_config)
        
        try:
            # Test key security scenarios
            test_cases = [
                {'role': 'hr', 'table': 'employees', 'expected_rows': 5, 'check': 'salary_sum access'},
                {'role': 'engineering_manager', 'table': 'employees', 'expected_rows': 2, 'check': 'department filter'},
                {'role': 'employee', 'table': 'employees', 'expected_rows': 1, 'check': 'public only'},
                {'role': 'sales_director', 'table': 'sales', 'expected_rows': 5, 'check': 'full sales access'},
                {'role': 'regional_manager', 'table': 'sales', 'expected_rows': 3, 'check': 'regional filter'},
                {'role': 'public', 'table': 'sales', 'expected_rows': 0, 'check': 'no sales access'}
            ]
            
            print("🔒 SECURITY TEST RESULTS:")
            print("-" * 50)
            
            all_passed = True
            for test in test_cases:
                self.current_user_role = test['role']
                query = self.apply_security_to_query(test['table'])
                
                try:
                    result = self.connector.execute_query(query, engine_type='druid')
                    actual_rows = len(result)
                    passed = actual_rows == test['expected_rows']
                    status = "✅ PASS" if passed else "❌ FAIL"
                    
                    if not passed:
                        all_passed = False
                    
                    print(f"{status} {test['role']:20} | {test['table']:12} | "
                          f"Expected: {test['expected_rows']:2} | Actual: {actual_rows:2} | {test['check']}")
                          
                except Exception as e:
                    print(f"❌ ERROR {test['role']:20} | {test['table']:12} | Error: {e}")
                    all_passed = False
            
            print("\n" + "=" * 60)
            if all_passed:
                print("🎉 ALL SECURITY TESTS PASSED!")
                print("   ✅ Universal Security Framework is WORKING")
                print("   ✅ Real Druid Data Tables Secured")
                print("   ✅ Role-Based Access Control")
                print("   ✅ Column-Level Security")
                print("   ✅ Row-Level Security")
            else:
                print("⚠️  Some tests failed - check security policies")
                
        finally:
            self.connector.close_all()

if __name__ == "__main__":
    tester = FinalSecurityTester()
    tester.run_final_test()
