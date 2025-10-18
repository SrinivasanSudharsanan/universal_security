#!/usr/bin/env python3
"""
Ingest data using inline spec - no external files needed
"""

import requests
import json
import time

def ingest_inline_data():
    print("📤 INGESTING DATA VIA INLINE SPEC")
    print("=" * 50)
    
    coordinator_url = "http://localhost:8081"
    
    # Inline data ingestion for employees
    employees_spec = {
        "type": "index_parallel",
        "spec": {
            "ioConfig": {
                "type": "index_parallel",
                "inputSource": {
                    "type": "inline",
                    "data": """{"id": 1, "name": "Alice Engineer", "department": "Engineering", "salary": 80000, "access_level": "confidential", "timestamp": "2024-01-01T00:00:00Z"}
{"id": 2, "name": "Bob Sales", "department": "Sales", "salary": 60000, "access_level": "restricted", "timestamp": "2024-01-01T00:00:00Z"}
{"id": 3, "name": "Carol HR", "department": "HR", "salary": 70000, "access_level": "confidential", "timestamp": "2024-01-01T00:00:00Z"}
{"id": 4, "name": "David Manager", "department": "Engineering", "salary": 90000, "access_level": "confidential", "timestamp": "2024-01-01T00:00:00Z"}
{"id": 5, "name": "Eva Intern", "department": "Sales", "salary": 45000, "access_level": "public", "timestamp": "2024-01-01T00:00:00Z"}"""
                },
                "inputFormat": {
                    "type": "json"
                }
            },
            "tuningConfig": {
                "type": "index_parallel",
                "partitionsSpec": {
                    "type": "dynamic"
                }
            },
            "dataSchema": {
                "dataSource": "employees",
                "timestampSpec": {
                    "column": "timestamp",
                    "format": "iso"
                },
                "dimensionsSpec": {
                    "dimensions": ["name", "department", "access_level"]
                },
                "metricsSpec": [
                    {
                        "name": "count",
                        "type": "count"
                    },
                    {
                        "name": "salary_sum", 
                        "type": "longSum",
                        "fieldName": "salary"
                    }
                ],
                "granularitySpec": {
                    "type": "uniform",
                    "segmentGranularity": "DAY",
                    "queryGranularity": "NONE",
                    "rollup": False
                }
            }
        }
    }
    
    # Inline data ingestion for sales
    sales_spec = {
        "type": "index_parallel",
        "spec": {
            "ioConfig": {
                "type": "index_parallel",
                "inputSource": {
                    "type": "inline",
                    "data": """{"sale_id": 101, "product": "Product-A", "amount": 5000, "customer": "Company-X", "region": "North", "quarter": "Q1", "timestamp": "2024-01-15T00:00:00Z"}
{"sale_id": 102, "product": "Product-B", "amount": 3000, "customer": "Company-Y", "region": "South", "quarter": "Q1", "timestamp": "2024-01-16T00:00:00Z"}
{"sale_id": 103, "product": "Product-C", "amount": 7500, "customer": "Company-Z", "region": "East", "quarter": "Q1", "timestamp": "2024-01-17T00:00:00Z"}
{"sale_id": 104, "product": "Product-A", "amount": 4500, "customer": "Company-X", "region": "North", "quarter": "Q2", "timestamp": "2024-04-15T00:00:00Z"}
{"sale_id": 105, "product": "Product-B", "amount": 6000, "customer": "Company-W", "region": "West", "quarter": "Q2", "timestamp": "2024-04-16T00:00:00Z"}"""
                },
                "inputFormat": {
                    "type": "json"
                }
            },
            "tuningConfig": {
                "type": "index_parallel",
                "partitionsSpec": {
                    "type": "dynamic"
                }
            },
            "dataSchema": {
                "dataSource": "sales",
                "timestampSpec": {
                    "column": "timestamp",
                    "format": "iso"
                },
                "dimensionsSpec": {
                    "dimensions": ["product", "customer", "region", "quarter"]
                },
                "metricsSpec": [
                    {
                        "name": "count",
                        "type": "count"
                    },
                    {
                        "name": "amount_sum", 
                        "type": "longSum",
                        "fieldName": "amount"
                    }
                ],
                "granularitySpec": {
                    "type": "uniform",
                    "segmentGranularity": "DAY",
                    "queryGranularity": "NONE",
                    "rollup": False
                }
            }
        }
    }
    
    try:
        print("1. Submitting employees ingestion...")
        response = requests.post(
            f"{coordinator_url}/druid/indexer/v1/task",
            json=employees_spec,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            task_id = response.json()['task']
            print(f"✅ Employees task: {task_id}")
        else:
            print(f"❌ Employees failed: {response.status_code} - {response.text}")
        
        time.sleep(2)
        
        print("2. Submitting sales ingestion...")
        response = requests.post(
            f"{coordinator_url}/druid/indexer/v1/task",
            json=sales_spec,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            task_id = response.json()['task']
            print(f"✅ Sales task: {task_id}")
        else:
            print(f"❌ Sales failed: {response.status_code} - {response.text}")
            
        print("\n⏳ Waiting 45 seconds for ingestion to complete...")
        time.sleep(45)
        
        # Check datasources
        print("\n3. Checking available datasources...")
        ds_response = requests.get("http://localhost:8888/druid/v2/datasources")
        if ds_response.status_code == 200:
            datasources = ds_response.json()
            print("📊 Available datasources:")
            for ds in datasources:
                print(f"   ✅ {ds}")
                # Try to query the data
                try:
                    query_response = requests.post(
                        "http://localhost:8888/druid/v2/sql",
                        json={"query": f"SELECT COUNT(*) as count FROM {ds}"},
                        headers={'Content-Type': 'application/json'}
                    )
                    if query_response.status_code == 200:
                        result = query_response.json()
                        if result:
                            print(f"      📈 Row count: {result[0]['count']}")
                except:
                    pass
        else:
            print("❌ Could not fetch datasources")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    ingest_inline_data()
