#!/usr/bin/env python3
"""
Complete Druid connector functionality test
"""

import sys
import os
import pandas as pd
from engines.unified_connector import UnifiedConnector
from config import get_settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DruidTester:
    def __init__(self):
        self.connector = UnifiedConnector()
        self.settings = get_settings()
        self.druid_config = self.settings.druid_config
        
    def check_config(self):
        """Check if Druid configuration is properly set"""
        print("🔍 Checking Druid Configuration:")
        print("=" * 50)
        
        required_keys = ['host', 'port', 'path', 'scheme']
        missing_keys = [key for key in required_keys if key not in self.druid_config]
        
        if missing_keys:
            print(f"❌ Missing required configuration keys: {missing_keys}")
            return False
        
        for key, value in self.druid_config.items():
            print(f"✅ {key}: {value}")
        
        print("✅ Configuration check passed")
        return True
    
    def test_connection(self):
        """Test basic connection to Druid"""
        print("\n🔌 Testing Druid Connection:")
        print("=" * 50)
        
        try:
            success = self.connector.initialize_connector('druid', self.druid_config)
            if success:
                print("✅ Druid connector initialized successfully")
                
                # Test connection
                is_connected = self.connector.test_connection('druid')
                if is_connected:
                    print("✅ Druid connection test passed")
                    return True
                else:
                    print("❌ Druid connection test failed")
                    return False
            else:
                print("❌ Failed to initialize Druid connector")
                return False
                
        except Exception as e:
            print(f"❌ Connection test error: {e}")
            return False
    
    def test_basic_queries(self):
        """Test basic SQL queries on Druid"""
        print("\n📊 Testing Basic Queries:")
        print("=" * 50)
        
        test_queries = [
            "SELECT 1 as test_value",
            "SELECT CURRENT_TIMESTAMP as current_time",
            "SELECT 'hello_druid' as test_string"
        ]
        
        for i, query in enumerate(test_queries, 1):
            try:
                print(f"Query {i}: {query}")
                result = self.connector.execute_query(query, engine_type='druid')
                print(f"✅ Query executed successfully")
                print(f"   Result: {result.to_dict('records')}")
                print(f"   Shape: {len(result)} row(s), {len(result.columns)} column(s)")
                print()
            except Exception as e:
                print(f"❌ Query failed: {e}")
                print()
    
    def test_information_schema(self):
        """Test querying Druid's information schema"""
        print("\n📋 Testing Information Schema:")
        print("=" * 50)
        
        information_schema_queries = [
            "SELECT * FROM INFORMATION_SCHEMA.TABLES LIMIT 5",
            "SELECT * FROM INFORMATION_SCHEMA.COLUMNS LIMIT 5",
            "SELECT * FROM INFORMATION_SCHEMA.SCHEMATA LIMIT 5"
        ]
        
        for query in information_schema_queries:
            try:
                print(f"Executing: {query.split('LIMIT')[0].strip()}...")
                result = self.connector.execute_query(query, engine_type='druid')
                print(f"✅ Success - found {len(result)} rows")
                if len(result) > 0:
                    print(f"   Columns: {list(result.columns)}")
                    print(f"   First row: {result.iloc[0].to_dict()}")
                print()
            except Exception as e:
                print(f"❌ Failed: {e}")
                print()
    
    def test_list_tables(self):
        """Test listing available tables"""
        print("\n📜 Testing Table Listing:")
        print("=" * 50)
        
        try:
            tables = self.connector.list_tables(engine_type='druid')
            print(f"✅ Found {len(tables)} tables")
            
            if tables:
                print("Available tables:")
                for i, table in enumerate(tables[:10], 1):  # Show first 10 tables
                    print(f"  {i}. {table}")
                
                if len(tables) > 10:
                    print(f"  ... and {len(tables) - 10} more tables")
                    
                # Test getting schema for first table
                if tables:
                    first_table = tables[0]
                    print(f"\n🔍 Testing schema for table: {first_table}")
                    try:
                        schema = self.connector.get_schema(first_table, engine_type='druid')
                        if schema:
                            print(f"✅ Schema retrieved - {len(schema)} columns")
                            for col_name, col_type in list(schema.items())[:5]:  # Show first 5 columns
                                print(f"   {col_name}: {col_type}")
                            if len(schema) > 5:
                                print(f"   ... and {len(schema) - 5} more columns")
                        else:
                            print("❌ No schema information returned")
                    except Exception as e:
                        print(f"❌ Schema retrieval failed: {e}")
            else:
                print("⚠️  No tables found in the database")
            print()
                
        except Exception as e:
            print(f"❌ Table listing failed: {e}")
            print()
    
    def test_sample_data_queries(self):
        """Test querying actual data from tables"""
        print("\n📈 Testing Sample Data Queries:")
        print("=" * 50)
        
        try:
            tables = self.connector.list_tables(engine_type='druid')
            if tables:
                # Test with first table
                sample_table = tables[0]
                print(f"Testing with table: {sample_table}")
                
                # Get row count
                try:
                    count_query = f"SELECT COUNT(*) as row_count FROM {sample_table}"
                    count_result = self.connector.execute_query(count_query, engine_type='druid')
                    print(f"✅ Row count: {count_result.iloc[0]['row_count']}")
                except Exception as e:
                    print(f"❌ Count query failed: {e}")
                
                # Get sample data
                try:
                    sample_query = f"SELECT * FROM {sample_table} LIMIT 3"
                    sample_result = self.connector.execute_query(sample_query, engine_type='druid')
                    print(f"✅ Sample data retrieved - {len(sample_result)} rows")
                    if len(sample_result) > 0:
                        print("Sample rows:")
                        for i, (idx, row) in enumerate(sample_result.iterrows()):
                            if i < 2:  # Show first 2 rows
                                print(f"  Row {i+1}: {row.to_dict()}")
                except Exception as e:
                    print(f"❌ Sample data query failed: {e}")
            else:
                print("⚠️  No tables available for data testing")
            print()
                
        except Exception as e:
            print(f"❌ Data query testing failed: {e}")
            print()
    
    def test_complex_queries(self):
        """Test more complex SQL operations"""
        print("\n🔧 Testing Complex Queries:")
        print("=" * 50)
        
        complex_queries = [
            "SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME IS NOT NULL LIMIT 10",
            "SELECT DISTINCT TABLE_SCHEMA FROM INFORMATION_SCHEMA.TABLES"
        ]
        
        for i, query in enumerate(complex_queries, 1):
            try:
                print(f"Complex Query {i}:")
                print(f"  SQL: {query}")
                result = self.connector.execute_query(query, engine_type='druid')
                print(f"  ✅ Executed successfully - {len(result)} rows returned")
                if len(result) > 0:
                    print(f"  Columns: {list(result.columns)}")
            except Exception as e:
                print(f"  ❌ Failed: {e}")
            print()
    
    def test_error_handling(self):
        """Test error handling with invalid queries"""
        print("\n🚨 Testing Error Handling:")
        print("=" * 50)
        
        invalid_queries = [
            "SELECT * FROM non_existent_table",
            "INVALID SQL SYNTAX HERE",
            "SELECT * FROM"
        ]
        
        for i, query in enumerate(invalid_queries, 1):
            try:
                print(f"Invalid Query {i}: '{query}'")
                result = self.connector.execute_query(query, engine_type='druid')
                print(f"❌ Expected error but query succeeded: {result}")
            except Exception as e:
                print(f"✅ Correctly caught error: {e}")
            print()
    
    def run_all_tests(self):
        """Run all Druid functionality tests"""
        print("🚀 Starting Comprehensive Druid Functionality Test")
        print("=" * 60)
        
        # Run tests in sequence
        tests = [
            self.check_config,
            self.test_connection,
            self.test_basic_queries,
            self.test_information_schema,
            self.test_list_tables,
            self.test_sample_data_queries,
            self.test_complex_queries,
            self.test_error_handling
        ]
        
        results = []
        for test in tests:
            try:
                success = test()
                results.append((test.__name__, success))
            except Exception as e:
                print(f"❌ Test {test.__name__} crashed: {e}")
                results.append((test.__name__, False))
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for test_name, success in results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All Druid functionality tests completed successfully!")
        else:
            print("⚠️  Some tests failed. Check the logs above for details.")
        
        # Clean up
        self.connector.close_all()
        
        return passed == total

def main():
    """Main test function"""
    print("Druid Comprehensive Functionality Test")
    print("This will test ALL Druid connector functionality")
    print()
    
    tester = DruidTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()