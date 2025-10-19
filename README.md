# Universal Column-Level Security (CLS) System

## Overview

The Universal Column-Level Security (CLS) System is an enterprise-grade, fine-grained data access control solution designed to secure data across multiple database engines such as Druid, PostgreSQL, and MySQL.

It provides real-time query rewriting, data masking, role-based access control, and comprehensive auditing — all without requiring application code changes.

### Key Features

Real-time Query Rewriting – Automatically modifies SQL queries to enforce security policies.

Dynamic Data Masking – Supports multiple masking strategies (partial, full, email, phone, custom).

Role-Based Access Control (RBAC) – Fine-grained permissions per user role.

Multi-Database Support – Works seamlessly with Druid, PostgreSQL, MySQL, and others.

Comprehensive Audit Logging – Tracks all security-related events and access patterns.

High Performance – Uses policy caching and asynchronous operations for efficiency.

No Code Changes Required – Security enforcement is fully transparent to applications.


###Installation Prerequisites

Python 3.8+
PostgreSQL 12+
Apache Druid (optional)
MySQL (optional)
Quick Start

###Clone the repository
git clone https://github.com/yourusername/universal_security.git
cd universal_security


Set up a virtual environment
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows


###Install dependencies
pip install -r requirements.txt
Set up the database
psql -h localhost -U postgres -c "CREATE DATABASE universal_security;"
psql -h localhost -U postgres -d universal_security -f setup_cls_tables.sql


Configure environment variables
cp .env.example .env
Edit .env with your database credentials

##Demo and Testing

###Run a comprehensive demo:

python cls_demo.py


###Test the CLS engine:

python test_cls_complete.py


###Test Druid integration:

python test_cls_integration.py

Configuration
Database Configuration

###Edit app/utils/db_utils.py with your PostgreSQL credentials:

POSTGRES_URL = "postgresql://username:password@localhost:5432/universal_security"

Druid Configuration

###Update connection parameters:

druid_config = {
    'host': 'localhost',
    'port': 8082,
    'path': '/druid/v2/sql/',
    'scheme': 'http'
}

Policy Management
Defining Security Policies

Security policies are stored in PostgreSQL and define column-level access rules.

-- Example: Admin has full access, Analyst sees masked data
INSERT INTO column_level_security_policies VALUES
('employees', 'salary_sum', 'admin', 'allow', NULL, NULL, true),
('employees', 'salary_sum', 'analyst', 'mask', 'partial', '$$$,###', true),
('employees', 'salary_sum', 'guest', 'deny', NULL, NULL, true);

Policy Structure
Field	Description
table_name	Target table
column_name	Column to secure
role_name	Role associated with policy
access_type	allow / deny / mask
mask_type	partial / full / email / phone / hash / custom
custom_mask_rule	Pattern for masking
is_active	Policy activation flag
Usage Examples
Basic CLS Integration
from app.engines.druid_cls_connector import DruidClsConnector

# Initialize secured connector
connector = DruidClsConnector()
await connector.initialize()

# Execute secure query
results = await connector.execute_secure_query(
    query="SELECT * FROM employees WHERE department = 'Engineering'",
    user_roles=["analyst"],
    user_id="user_123"
)

Direct CLS Engine Usage
from app.security.policies.column_level.cls_engine import UniversalClsEngine

cls_engine = UniversalClsEngine(database_query_function)
await cls_engine.initialize_engine()

# Retrieve allowed columns
allowed_columns = await cls_engine.get_allowed_columns(
    user_roles=["admin", "hr"], 
    table_name="employees"
)

# Rewrite SQL query with security enforcement
secured_sql = await cls_engine.rewrite_sql_select(
    original_sql="SELECT * FROM employees",
    user_roles=["analyst"],
    engine_type="druid"
)

Security Features
Data Masking Types
Mask Type	Example
Partial Masking	123-45-6789 → XXX-XX-6789
Full Masking	sensitive@email.com → **********
Email Masking	user@example.com → u***@example.com
Phone Masking	+1-555-0123 → +1-555-****
Custom Masking	Define custom patterns
Role-Based Access Example
Role	salary_sum	customer	access_level
Admin	Full access	Full access	Full access
Analyst	Masked ($$$,###)	Masked (XXXX-####)	Full access
HR	Full access	No access	Full access
Employee	No access	No access	No access
Performance

Policy Caching – Policies are loaded once and cached in memory.

Async Operations – Non-blocking database operations.

Connection Pooling – Optimized resource utilization.

Minimal Overhead – Query rewriting adds less than 1 ms overhead.

Monitoring & Audit
Security Event Logging

Each query is logged with:

User ID and roles

Original and secured SQL

Execution results

Timestamp and status

Access Reports
SELECT user_id, action_type, table_name, success, created_at
FROM security_audit_log 
WHERE created_at >= NOW() - INTERVAL '1 day';

Deployment
Production Considerations

Database Security

Use encrypted connections

Secure credential storage

Regular backups

Performance

Monitor policy cache

Tune connection pools

Index policy tables

High Availability

Database replication

Multiple CLS engine instances

Load balancing

Docker Deployment
FROM python:3.8-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "app/main.py"]

Contributing

Fork the repository

Create a feature branch

git checkout -b feature/new-security-feature


Commit changes

git commit -am "Add new security feature"


Push to your branch

git push origin feature/new-security-feature


Submit a Pull Request

License

This project is licensed under the MIT License. See the LICENSE
 file for details.

Support

Email: security-support@example.com

Issues: GitHub Issues

Documentation: Project Wiki

Acknowledgments

Built with Python AsyncIO for high performance

Universal security engine design

Enterprise-grade security principles

Real-world production testing

Universal Column-Level Security System
Enterprise-grade data protection made simple.

Get Started
 • Documentation
 • Examples
