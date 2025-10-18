#!/usr/bin/env python3
"""
Test script to verify that all connectors are working properly
"""

import sys
import os
import logging
from typing import Dict, Any

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.unified_connector import UnifiedConnector
from config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConnectorTestSuite:
    """Test suite for verifying connector functionality"""
    
    def __init__(self):
        self.connector = UnifiedConnector()
        self.settings = get_settings()
        self.test_results = {}
    
    def test_connection_initialization(self) -> bool:
        """Test if connectors can be initialized"""
        logger.info("Testing connector initialization...")
        
        connectors_to_test = [
            ('databricks', self.settings.databricks_config),
            ('snowflake', self.settings.snowflake_config),
            ('druid', self.settings.druid_config),
            ('iceberg', self.settings.iceberg_config)
        ]
        
        all_success = True
        
        for engine_type, config in connectors_to_test:
            try:
                logger.info(f"Initializing {engine_type} connector...")
                success = self.connector.initialize_connector(engine_type, config)
                
                if success:
                    logger.info(f"✓ {engine_type} connector initialized successfully")
                    self.test_results[f"{engine_type}_init"] = "PASS"
                else:
                    logger.error(f"✗ {engine_type} connector failed to initialize")
                    self.test_results[f"{engine_type}_init"] = "FAIL"
                    all_success = False
                    
            except Exception as e:
                logger.error(f"✗ {engine_type} connector initialization error: {e}")
                self.test_results[f"{engine_type}_init"] = f"ERROR: {e}"
                all_success = False
        
        return all_success
    
    def test_connection_status(self) -> bool:
        """Test if connections are alive"""
        logger.info("\nTesting connection status...")
        
        available_engines = self.connector.get_available_engines()
        all_success = True
        
        for engine_type in available_engines:
            try:
                is_connected = self.connector.test_connection(engine_type)
                
                if is_connected:
                    logger.info(f"✓ {engine_type} connection test passed")
                    self.test_results[f"{engine_type}_connection"] = "PASS"
                else:
                    logger.error(f"✗ {engine_type} connection test failed")
                    self.test_results[f"{engine_type}_connection"] = "FAIL"
                    all_success = False
                    
            except Exception as e:
                logger.error(f"✗ {engine_type} connection test error: {e}")
                self.test_results[f"{engine_type}_connection"] = f"ERROR: {e}"
                all_success = False
        
        return all_success
    
    def test_basic_operations(self) -> bool:
        """Test basic operations like listing tables"""
        logger.info("\nTesting basic operations...")
        
        available_engines = self.connector.get_available_engines()
        all_success = True
        
        for engine_type in available_engines:
            try:
                # Test listing tables (this should work for most connectors)
                tables = self.connector.list_tables(engine_type=engine_type)
                
                if isinstance(tables, list):
                    logger.info(f"✓ {engine_type} list_tables() works - found {len(tables)} tables")
                    self.test_results[f"{engine_type}_operations"] = "PASS"
                else:
                    logger.error(f"✗ {engine_type} list_tables() returned unexpected type")
                    self.test_results[f"{engine_type}_operations"] = "FAIL"
                    all_success = False
                    
            except NotImplementedError:
                logger.warning(f"⚠ {engine_type} list_tables() not implemented (this might be expected)")
                self.test_results[f"{engine_type}_operations"] = "NOT_IMPLEMENTED"
            except Exception as e:
                logger.error(f"✗ {engine_type} operations test failed: {e}")
                self.test_results[f"{engine_type}_operations"] = f"ERROR: {e}"
                all_success = False
        
        return all_success
    
    def test_active_engine_switching(self) -> bool:
        """Test switching between active engines"""
        logger.info("\nTesting active engine switching...")
        
        available_engines = self.connector.get_available_engines()
        
        if len(available_engines) < 2:
            logger.warning("⚠ Need at least 2 connectors to test switching")
            self.test_results["engine_switching"] = "SKIPPED"
            return True
        
        try:
            # Test switching to each available engine
            for engine_type in available_engines:
                success = self.connector.set_active_engine(engine_type)
                if success:
                    logger.info(f"✓ Successfully switched to {engine_type}")
                else:
                    logger.error(f"✗ Failed to switch to {engine_type}")
                    self.test_results["engine_switching"] = "FAIL"
                    return False
            
            self.test_results["engine_switching"] = "PASS"
            return True
            
        except Exception as e:
            logger.error(f"✗ Engine switching test failed: {e}")
            self.test_results["engine_switching"] = f"ERROR: {e}"
            return False
    
    def test_connection_management(self) -> bool:
        """Test opening and closing connections"""
        logger.info("\nTesting connection management...")
        
        try:
            available_before = len(self.connector.get_available_engines())
            
            if available_before == 0:
                logger.warning("⚠ No connections available to test management")
                self.test_results["connection_management"] = "SKIPPED"
                return True
            
            # Test closing a specific connection
            engine_to_close = self.connector.get_available_engines()[0]
            self.connector.close_connection(engine_to_close)
            
            available_after_close = len(self.connector.get_available_engines())
            
            if available_after_close == available_before - 1:
                logger.info(f"✓ Successfully closed {engine_to_close} connection")
            else:
                logger.error(f"✗ Failed to close {engine_to_close} connection")
                self.test_results["connection_management"] = "FAIL"
                return False
            
            # Test closing all connections
            self.connector.close_all()
            available_after_all = len(self.connector.get_available_engines())
            
            if available_after_all == 0:
                logger.info("✓ Successfully closed all connections")
                self.test_results["connection_management"] = "PASS"
                return True
            else:
                logger.error("✗ Failed to close all connections")
                self.test_results["connection_management"] = "FAIL"
                return False
                
        except Exception as e:
            logger.error(f"✗ Connection management test failed: {e}")
            self.test_results["connection_management"] = f"ERROR: {e}"
            return False
    
    def run_all_tests(self) -> Dict[str, str]:
        """Run all tests and return results"""
        logger.info("Starting connector test suite...")
        logger.info("=" * 50)
        
        try:
            # Run tests in sequence
            self.test_connection_initialization()
            self.test_connection_status()
            self.test_basic_operations()
            self.test_active_engine_switching()
            self.test_connection_management()
            
        finally:
            # Always close all connections
            self.connector.close_all()
        
        return self.test_results
    
    def print_summary(self):
        """Print test results summary"""
        logger.info("\n" + "=" * 50)
        logger.info("TEST SUMMARY")
        logger.info("=" * 50)
        
        for test_name, result in self.test_results.items():
            status_icon = "✓" if result == "PASS" else "✗" if result == "FAIL" else "⚠"
            logger.info(f"{status_icon} {test_name}: {result}")
        
        # Calculate overall status
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() 
                          if result == "PASS" or result == "SKIPPED")
        
        logger.info("=" * 50)
        logger.info(f"Overall: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            logger.info("🎉 All tests completed successfully!")
        else:
            logger.warning("⚠ Some tests failed. Check the logs above.")


def main():
    """Main test function"""
    print("Connector Test Suite")
    print("This will test all database connectors in your setup.")
    print("Make sure your configuration is properly set in config.py")
    print()
    
    try:
        # Run the test suite
        test_suite = ConnectorTestSuite()
        results = test_suite.run_all_tests()
        test_suite.print_summary()
        
        # Exit with appropriate code
        failed_tests = sum(1 for result in results.values() 
                          if result == "FAIL" or result.startswith("ERROR:"))
        
        if failed_tests > 0:
            sys.exit(1)  # Exit with error code if any tests failed
        else:
            sys.exit(0)  # Exit successfully if all tests passed
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during testing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()