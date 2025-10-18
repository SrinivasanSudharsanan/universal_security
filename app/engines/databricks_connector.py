from databricks import sql
import pandas as pd
from typing import Any, Dict, List, Optional
import logging
from .base_connector import BaseConnector

logger = logging.getLogger(__name__)

class DatabricksConnector(BaseConnector):
    def __init__(self):
        self.connection = None
        self.is_connected = False
    
    def connect(self, connection_params: Dict[str, Any]) -> bool:
        try:
            self.connection = sql.connect(
                server_hostname=connection_params['server_hostname'],
                http_path=connection_params['http_path'],
                access_token=connection_params['access_token']
            )
            self.is_connected = True
            logger.info("Successfully connected to Databricks")
            return True
        except Exception as e:
            logger.error(f"Databricks connection failed: {str(e)}")
            return False
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        if not self.is_connected:
            raise Exception("Not connected to Databricks")
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, parameters=params)
                result = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return pd.DataFrame(result, columns=columns)
        except Exception as e:
            logger.error(f"Databricks query failed: {str(e)}")
            raise
    
    def execute_command(self, command: str, params: Optional[Dict] = None) -> bool:
        if not self.is_connected:
            raise Exception("Not connected to Databricks")
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(command, parameters=params)
            return True
        except Exception as e:
            logger.error(f"Databricks command failed: {str(e)}")
            return False
    
    def test_connection(self) -> bool:
        if not self.is_connected:
            return False
        
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception:
            return False
    
    def close(self) -> None:
        if self.connection:
            self.connection.close()
            self.is_connected = False
    
    def get_schema(self, table_name: str) -> Dict[str, Any]:
        query = f"DESCRIBE {table_name}"
        result = self.execute_query(query)
        return result.set_index('col_name')['data_type'].to_dict()
    
    def list_tables(self) -> List[str]:
        result = self.execute_query("SHOW TABLES")
        return result['tableName'].tolist()