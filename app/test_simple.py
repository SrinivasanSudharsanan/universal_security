#!/usr/bin/env python3
"""
Simple test that doesn't depend on the config structure
"""

print("🔧 Testing basic setup...")

# Test core dependencies
try:
    import pandas as pd
    print("✅ pandas: OK")
except ImportError as e:
    print(f"❌ pandas: {e}")

try:
    import sqlalchemy
    print("✅ sqlalchemy: OK")
except ImportError as e:
    print(f"❌ sqlalchemy: {e}")

try:
    from databricks import sql
    print("✅ databricks-sql-connector: OK")
except ImportError as e:
    print(f"❌ databricks-sql-connector: {e}")

try:
    import snowflake.connector
    print("✅ snowflake-connector-python: OK")
except ImportError as e:
    print(f"❌ snowflake-connector-python: {e}")

try:
    from pydruid.db import connect
    print("✅ pydruid: OK")
except ImportError as e:
    print(f"❌ pydruid: {e}")

try:
    from pyiceberg.catalog import load_catalog
    print("✅ pyiceberg: OK")
except ImportError as e:
    print(f"❌ pyiceberg: {e}")

print("\n🧪 Testing connector imports...")

# Test if we can import the base connector
try:
    from engines.base_connector import BaseConnector
    print("✅ BaseConnector: OK")
except ImportError as e:
    print(f"❌ BaseConnector: {e}")

# Test individual connectors
connectors = ['databricks_connector', 'snowflake_connector', 'druid_connector', 'iceberg_connector']
for connector in connectors:
    try:
        module = __import__(f'engines.{connector}', fromlist=[''])
        print(f"✅ {connector}: OK")
    except ImportError as e:
        print(f"❌ {connector}: {e}")

print("\n🎉 Dependency check completed!")