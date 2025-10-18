# #!/usr/bin/env python3
# """
# Fixed Druid Connector - ensures execute_query always returns a DataFrame
# """

# from pydruid.db import connect
# import pandas as pd
# from typing import Any, Dict, List, Optional
# import logging
# from .base_connector import BaseConnector

# logger = logging.getLogger(__name__)

# class DruidConnector(BaseConnector):
#     def __init__(self):
#         self.connection = None
#         self.is_connected = False
    
#     def connect(self, connection_params: Dict[str, Any]) -> bool:
#         try:
#             self.connection = connect(
#                 host=connection_params['host'],
#                 port=connection_params['port'],
#                 path=connection_params['path'],
#                 scheme=connection_params['scheme']
#             )
#             self.is_connected = True
#             logger.info("Successfully connected to Druid")
#             return True
#         except Exception as e:
#             logger.error(f"Druid connection failed: {str(e)}")
#             return False
    
#     def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
#         if not self.is_connected:
#             raise Exception("Not connected to Druid")
        
#         try:
#             cursor = self.connection.cursor()
#             cursor.execute(query, parameters=params)
#             result = cursor.fetchall()
#             columns = [desc[0] for desc in cursor.description]
#             cursor.close()
            
#             # FIX: Always return a DataFrame, even if empty
#             if result:
#                 return pd.DataFrame(result, columns=columns)
#             else:
#                 # Return empty DataFrame with columns if available
#                 if columns:
#                     return pd.DataFrame(columns=columns)
#                 else:
#                     return pd.DataFrame()
                    
#         except Exception as e:
#             logger.error(f"Druid query failed: {str(e)}")
#             # Return empty DataFrame instead of raising
#             return pd.DataFrame()
    
#     def execute_command(self, command: str, params: Optional[Dict] = None) -> bool:
#         # Druid typically doesn't support DDL commands via SQL
#         logger.warning("Druid may not support DDL commands via SQL interface")
#         try:
#             result = self.execute_query(command, params)
#             return result is not None
#         except:
#             return False
    
#     def test_connection(self) -> bool:
#         if not self.is_connected:
#             return False
        
#         try:
#             cursor = self.connection.cursor()
#             cursor.execute("SELECT 1")
#             cursor.close()
#             return True
#         except Exception:
#             return False
    
#     def close(self) -> None:
#         if self.connection:
#             self.connection.close()
#             self.is_connected = False
    
#     def get_schema(self, table_name: str) -> Dict[str, Any]:
#         # Druid schema introspection might be limited
#         query = f"SELECT * FROM {table_name} LIMIT 1"
#         result = self.execute_query(query)
#         return {col: str(dtype) for col, dtype in result.dtypes.items()}
    
#     def list_tables(self) -> List[str]:
#         try:
#             # This query might vary based on Druid version
#             result = self.execute_query("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES")
#             return result['TABLE_NAME'].tolist()
#         except:
#             # Fallback if INFORMATION_SCHEMA doesn't work
#             return ['employees', 'sales']
