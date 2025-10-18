#!/usr/bin/env python3
"""
Async wrapper for Druid connector to work with CLS system
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import pandas as pd
from app.engines.druid_connector import DruidConnector

logger = logging.getLogger(__name__)

class AsyncDruidConnector:
    """
    Async wrapper for synchronous Druid connector
    Enables compatibility with async CLS system
    """
    
    def __init__(self):
        self.druid_connector = DruidConnector()
        self._is_connected = False
        
    async def initialize(self, connection_params: Dict[str, Any] = None):
        """Initialize Druid connection asynchronously"""
        
        # Default connection parameters
        if connection_params is None:
            connection_params = {
                'host': 'localhost',
                'port': 8082,
                'path': '/druid/v2/sql/',
                'scheme': 'http'
            }
        
        print(f"🔌 Connecting to Druid: {connection_params['host']}:{connection_params['port']}")
        
        # Run synchronous connect in thread pool
        loop = asyncio.get_event_loop()
        self._is_connected = await loop.run_in_executor(
            None, 
            self.druid_connector.connect, 
            connection_params
        )
        
        if self._is_connected:
            print("✅ Async Druid connector initialized")
            logger.info("✅ Async Druid connector initialized")
        else:
            logger.error("❌ Failed to initialize Async Druid connector")
            raise Exception("Druid connection failed")
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Execute query asynchronously and return results as dictionaries"""
        
        if not self._is_connected:
            raise Exception("Druid connector not initialized")
        
        print(f"📊 Executing Druid query: {query[:100]}...")
        
        loop = asyncio.get_event_loop()
        
        try:
            # Execute query in thread pool
            df = await loop.run_in_executor(
                None,
                self.druid_connector.execute_query,
                query,
                params
            )
            
            # FIX: Handle case where execute_query returns None
            if df is None:
                print("⚠️  Query returned None - returning empty results")
                return []
                
            # Convert DataFrame to list of dictionaries
            if not df.empty:
                results = df.to_dict('records')
                print(f"✅ Query successful, returned {len(results)} rows")
                return results
            else:
                print("⚠️  Query returned empty DataFrame")
                return []
                
        except Exception as e:
            print(f"❌ Druid query failed: {e}")
            # Return empty list instead of raising to allow CLS to continue
            return []
    
    async def test_connection(self) -> bool:
        """Test connection asynchronously"""
        if not self._is_connected:
            return False
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.druid_connector.test_connection)
    
    async def get_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.druid_connector.get_schema, table_name)
    
    async def list_tables(self) -> List[str]:
        """List tables asynchronously"""
        try:
            loop = asyncio.get_event_loop()
            tables = await loop.run_in_executor(None, self.druid_connector.list_tables)
            print(f"📋 Found tables: {tables}")
            return tables
        except Exception as e:
            print(f"⚠️  Could not list tables: {e}")
            return ['employees', 'sales']  # Fallback to known tables
    
    async def close(self):
        """Close connection asynchronously"""
        if self._is_connected:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.druid_connector.close)
            self._is_connected = False
            logger.info("Async Druid connector closed")
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._is_connected
