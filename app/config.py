from pydantic_settings import BaseSettings
from typing import Dict, Any


class Settings(BaseSettings):
    """Application settings"""
    
    # Unified connector settings
    default_engine: str = "databricks"
    
    # Connection configurations for different engines
    databricks_config: Dict[str, Any] = {
        "server_hostname": "your-host.cloud.databricks.com",
        "http_path": "/sql/1.0/warehouses/your-warehouse-id",
        "access_token": "your-token"
    }
    
    druid_config: Dict[str, Any] = {
        "host": "localhost",
        "port": 8082,
        "path": "/druid/v2/sql/",
        "scheme": "http"
    }
    
    iceberg_config: Dict[str, Any] = {
        "catalog": "iceberg_catalog",
        "warehouse": "s3://your-warehouse/",
        "uri": "thrift://localhost:9084"
    }
    
    snowflake_config: Dict[str, Any] = {
        "account": "your-account",
        "user": "your-user",
        "password": "your-password",
        "warehouse": "your-warehouse",
        "database": "your-database",
        "schema": "your-schema"
    }
    
    class Config:
        env_file = ".env"


def get_settings():
    return Settings()