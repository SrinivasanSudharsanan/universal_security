import snowflake.connector
import pandas as pd
from typing import Any, Dict, List, Optional
import logging
from .base_connector import BaseConnector

logger = logging.getLogger(__name__)

class SnowflakeConnector(BaseConnector):
    def __init__(self):
        self.connection = None
        self.is_connected = False
    
    def connect(self, connection_params: Dict[str, Any]) -> bool:
        try:
            self.connection = snowflake.connector.connect(
                account=connection_params['account'],
                user=connection_params['user'],
                password=connection_params['password'],
                warehouse=connection_params['warehouse'],
                database=connection_params['database'],
                schema=connection_params['schema']
            )
            self.is_connected = True
            logger.info("Successfully connected to Snowflake")
            return True
        except Exception as e:
            logger.error(f"Snowflake connection failed: {str(e)}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        if not self.is_connected:
            raise Exception("Not connected to Snowflake")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            cursor.close()
            return pd.DataFrame(result, columns=columns)
        except Exception as e:
            logger.error(f"Snowflake query failed: {str(e)}")
            raise
    
    def execute_command(self, command: str, params: Optional[Dict] = None) -> bool:
        if not self.is_connected:
            raise Exception("Not connected to Snowflake")
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(command, params)
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"Snowflake command failed: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        if not self.is_connected:
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
        except Exception:
            return False
    
    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.is_connected = False
    
    def get_schema(self, table_name: str) -> Dict[str, Any]:
        query = f"DESCRIBE TABLE {table_name}"
        result = self.execute_query(query)
        return result.set_index('name')['type'].to_dict()
    
    def list_tables(self) -> List[str]:
        result = self.execute_query("SHOW TABLES")
        return result['name'].tolist()