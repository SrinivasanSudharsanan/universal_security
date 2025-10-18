from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd


class BaseConnector(ABC):
    """Abstract base class that all connectors must implement"""
    
    @abstractmethod
    def connect(self, connection_params: Dict[str, Any]) -> bool:
        """Establish connection to the database"""
        pass
    
    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        pass
    
    @abstractmethod
    def execute_command(self, command: str, params: Optional[Dict] = None) -> bool:
        """Execute a DDL/DML command"""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if connection is alive"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close the connection"""
        pass
    
    @abstractmethod
    def get_schema(self, table_name: str) -> Dict[str, Any]:
        """Get table schema information"""
        pass
    
    @abstractmethod
    def list_tables(self) -> List[str]:
        """List available tables"""
        pass