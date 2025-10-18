#!/usr/bin/env python3
"""
Test if security framework works for ALL types of queries
- SELECT queries
- JOIN queries  
- Aggregation queries
- Subqueries
- Complex filtering
"""

from engines.unified_connector import UnifiedConnector
from config import get_settings

class QueryTypeTester:
    def __init__(self):
        self.connector = UnifiedConnector()
        self.settings = get_settings()
        self.current_user_role = 'engineering_manager'  # Test with restricted role
        
        # Security policies
        self.security_policies = {
            'employees': {
                'rls': "department = 'Engineering'",
                'columns': ['name', 'department', 'access_level']  # No salary_sum
            },
            'sales': {
                'rls': "region IN ('North', 'South')", 
                'columns': ['product', 'amount_sum', 'region', 'quarter']  # No customer
            }
        }
    
    def apply_security(self, query, table_name):
        """Apply security to any query"""
        if table_name not in self.security_policies:
            return query
        
        # This is the LIMITATION - our current approach only works for simple SELECT *
        # For complex queries, we need a more sophisticated approach
        if "SELECT *" in query.upper() and "FROM " + table_name in query.upper():
            columns = ", ".join(self.security_policies[table_name]['columns'])
            rls = self.security_policies[table_name]['rls']
            
            # Replace SELECT * with secured columns
            secured_query = query.replace("SELECT *", f"SELECT {columns}")
            
            # Add WHERE clause if not exists
            if "WHERE" not in secured_query.upper():
                secured_query += f" WHERE {rls}"
            else:
                # This gets complex - we'd need SQL parsing
                secured_query += f" AND {rls}"
                
            return secured_query
        
        return query  # Can't secure complex queries with current approach
    
    def test_different_query_types(self):
        """Test security with various query types"""
        print("🧪 TESTING SECURITY FRAMEWORK WITH DIFFERENT QUERY TYPES")
        print("=" * 70)
        print("�� Testing as: engineering_manager")
        print("📊 Should only see Engineering department, no salary data")
        print("=" * 70)
        
        self.connector.initialize_connector('druid', self.settings.druid_config)
        
        test_queries = [
            {
                'name': 'Simple SELECT *',
                'query': "SELECT * FROM employees",
                'table': 'employees',
                'should_work': True
            },
            {
                'name': 'Specific columns SELECT',
                'query': "SELECT name, department FROM employees", 
                'table': 'employees',
                'should_work': False  # Our framework won't modify this
            },
            {
                'name': 'Aggregation query',
                'query': "SELECT department, COUNT(*) as emp_count FROM employees GROUP BY department",
                'table': 'employees', 
                'should_work': False
            },
            {
                'name': 'Complex WHERE clause',
                'query': "SELECT * FROM employees WHERE access_level = 'confidential'",
                'table': 'employees',
                'should_work': True  # Should add department filter
            },
            {
                'name': 'JOIN query (if we had related tables)',
                'query': "SELECT e.name, s.product FROM employees e, sales s WHERE e.department = 'Sales'",
                'table': 'employees', 
                'should_work': False  # Too complex for current approach
            },
            {
                'name': 'Subquery',
                'query': "SELECT * FROM employees WHERE department IN (SELECT DISTINCT department FROM employees WHERE access_level = 'confidential')",
                'table': 'employees',
                'should_work': False
            }
        ]
        
        print("\n📋 QUERY SECURITY TEST RESULTS:")
        print("-" * 70)
        
        for test in test_queries:
            print(f"\n🔍 {test['name']}")
            print(f"   Original: {test['query']}")
            
            secured_query = self.apply_security(test['query'], test['table'])
            print(f"   Secured:  {secured_query}")
            
            try:
                result = self.connector.execute_query(secured_query, engine_type='druid')
                
                if "SELECT *" in test['query'] and test['should_work']:
                    # Check if security was applied
                    expected_columns = set(self.security_policies[test['table']]['columns'])
                    actual_columns = set(result.columns) if len(result) > 0 else set()
                    
                    has_salary = 'salary_sum' in actual_columns
                    has_unauthorized_data = len(actual_columns - expected_columns) > 0
                    
                    if not has_salary and not has_unauthorized_data:
                        print(f"   ✅ SECURITY WORKING - {len(result)} rows, proper columns")
                    else:
                        print(f"   ⚠️  SECURITY LEAK - Unauthorized columns: {actual_columns - expected_columns}")
                else:
                    print(f"   📊 Executed - {len(result)} rows")
                    
            except Exception as e:
                print(f"   ❌ Failed: {e}")
        
        print("\n" + "=" * 70)
        print("📊 ANALYSIS: Current Framework Limitations")
        print("-" * 70)
        print("✅ WORKS FOR: Simple SELECT * FROM table queries")
        print("❌ LIMITED FOR:")
        print("   - Queries with specific column selections")
        print("   - Aggregation queries (GROUP BY, COUNT, SUM)") 
        print("   - JOIN queries across multiple tables")
        print("   - Subqueries and complex filtering")
        print("   - Queries with existing WHERE clauses")
        
        print("\n💡 SOLUTION NEEDED: SQL Parsing & Rewriting")
        print("   To handle all query types, we need:")
        print("   1. SQL parser to understand query structure")
        print("   2. Column-level rewriting for any SELECT clause")
        print("   3. Smart WHERE clause integration")
        print("   4. JOIN-aware security policies")
        
        self.connector.close_all()

if __name__ == "__main__":
    tester = QueryTypeTester()
    tester.test_different_query_types()
