from typing import Any, Dict, List, Optional
import pandas as pd
import logging
from config import get_settings

# Import all connector classes
from .databricks_connector import DatabricksConnector
from .druid_connector import DruidConnector
from .iceberg_connector import IcebergConnector
from .snowflake_connector import SnowflakeConnector
from .base_connector import BaseConnector

logger = logging.getLogger(__name__)

class UnifiedConnector:
    """
    Main connector manager that provides a unified interface
    to all database engines through individual connector classes
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.connectors: Dict[str, BaseConnector] = {}
        self.active_engine: Optional[str] = None
        
    def initialize_connector(self, engine_type: str, 
                           connection_params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize a connector for a specific engine type
        
        Args:
            engine_type: One of 'databricks', 'druid', 'iceberg', 'snowflake'
            connection_params: Connection parameters (uses config defaults if None)
        """
        try:
            if connection_params is None:
                connection_params = getattr(self.settings, f"{engine_type}_config", {})
            
            # Create the appropriate connector instance
            connector = self._create_connector(engine_type)
            
            # Attempt connection
            success = connector.connect(connection_params)
            
            if success:
                self.connectors[engine_type] = connector
                if not self.active_engine:
                    self.active_engine = engine_type
                logger.info(f"Successfully initialized {engine_type} connector")
                return True
            else:
                logger.error(f"Failed to initialize {engine_type} connector")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing {engine_type} connector: {str(e)}")
            return False
    
    def _create_connector(self, engine_type: str) -> BaseConnector:
        """Factory method to create connector instances"""
        connector_map = {
            'databricks': DatabricksConnector,
            'druid': DruidConnector,
            'iceberg': IcebergConnector,
            'snowflake': SnowflakeConnector
        }
        
        if engine_type not in connector_map:
            raise ValueError(f"Unsupported engine type: {engine_type}")
        
        return connector_map[engine_type]()
    
    def execute_query(self, query: str, params: Optional[Dict] = None,
                     engine_type: Optional[str] = None) -> pd.DataFrame:
        """Execute query using specified or active connector"""
        connector = self._get_connector(engine_type)
        return connector.execute_query(query, params)
    
    def execute_command(self, command: str, params: Optional[Dict] = None,
                       engine_type: Optional[str] = None) -> bool:
        """Execute command using specified or active connector"""
        connector = self._get_connector(engine_type)
        return connector.execute_command(command, params)
    
    def get_schema(self, table_name: str, engine_type: Optional[str] = None) -> Dict[str, Any]:
        """Get schema using specified or active connector"""
        connector = self._get_connector(engine_type)
        return connector.get_schema(table_name)
    
    def list_tables(self, engine_type: Optional[str] = None) -> List[str]:
        """List tables using specified or active connector"""
        connector = self._get_connector(engine_type)
        return connector.list_tables()
    
    def test_connection(self, engine_type: Optional[str] = None) -> bool:
        """Test connection using specified or active connector"""
        connector = self._get_connector(engine_type)
        return connector.test_connection()
    
    def set_active_engine(self, engine_type: str) -> bool:
        """Set the active engine for operations"""
        if engine_type in self.connectors:
            self.active_engine = engine_type
            return True
        return False
    
    def _get_connector(self, engine_type: Optional[str] = None) -> BaseConnector:
        """Get connector instance with error handling"""
        target_engine = engine_type or self.active_engine
        
        if not target_engine:
            raise ValueError("No engine specified and no active engine set")
        
        if target_engine not in self.connectors:
            raise ValueError(f"Engine {target_engine} not initialized. Call initialize_connector() first.")
        
        return self.connectors[target_engine]
    
    def get_available_engines(self) -> List[str]:
        """Get list of available (initialized) engine types"""
        return list(self.connectors.keys())
    
    def close_connection(self, engine_type: str) -> None:
        """Close specific connection"""
        if engine_type in self.connectors:
            try:
                self.connectors[engine_type].close()
                del self.connectors[engine_type]
                
                if self.active_engine == engine_type:
                    self.active_engine = list(self.connectors.keys())[0] if self.connectors else None
                    
                logger.info(f"Closed connection to {engine_type}")
            except Exception as e:
                logger.error(f"Error closing {engine_type} connection: {str(e)}")
    
    def close_all(self) -> None:
        """Close all connections"""
        for engine_type in list(self.connectors.keys()):
            self.close_connection(engine_type)
        logger.info("All connections closed")