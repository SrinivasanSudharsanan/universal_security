#!/usr/bin/env python3
"""
Create test data structure for CLS testing
We'll use simulated Druid data for testing
"""

import asyncio
import json

async def create_druid_cls_test_data():
    """Create test data structure for CLS testing"""
    print("📊 Creating Test Data Structure for CLS")
    print("=" * 50)
    
    # Test data for employee_sensitive table
    employee_data = [
        {
            "employee_id": 1,
            "name": "John Doe",
            "email": "john.doe@company.com",
            "phone": "555-0101",
            "salary": 75000,
            "department": "Engineering",
            "ssn": "123-45-6789",
            "performance_rating": "A"
        },
        {
            "employee_id": 2, 
            "name": "Jane Smith",
            "email": "jane.smith@company.com", 
            "phone": "555-0102",
            "salary": 82000,
            "department": "Sales",
            "ssn": "987-65-4321",
            "performance_rating": "B"
        },
        {
            "employee_id": 3,
            "name": "Bob Johnson",
            "email": "bob.johnson@company.com",
            "phone": "555-0103", 
            "salary": 68000,
            "department": "Marketing",
            "ssn": "456-78-9012",
            "performance_rating": "A"
        }
    ]
    
    # Test data for customer_pii table
    customer_data = [
        {
            "customer_id": 101,
            "full_name": "Alice Brown",
            "email": "alice.brown@email.com",
            "phone": "555-0201",
            "address": "123 Main St, City, State 12345",
            "credit_card": "4111-1111-1111-1111",
            "date_of_birth": "1985-05-15",
            "loyalty_tier": "Gold"
        },
        {
            "customer_id": 102,
            "full_name": "Charlie Wilson", 
            "email": "charlie.wilson@email.com",
            "phone": "555-0202",
            "address": "456 Oak Ave, City, State 12345",
            "credit_card": "5500-0000-0000-0004", 
            "date_of_birth": "1990-12-20",
            "loyalty_tier": "Silver"
        }
    ]
    
    print("✅ Created test data structures for CLS testing")
    print("   - employee_sensitive: 3 records with PII")
    print("   - customer_pii: 2 records with sensitive data")
    
    return {
        "employee_sensitive": employee_data,
        "customer_pii": customer_data
    }

if __name__ == "__main__":
    test_data = asyncio.run(create_druid_cls_test_data())
    print(f"\n📋 Test Data Summary:")
    for table, records in test_data.items():
        print(f"   {table}: {len(records)} records")
