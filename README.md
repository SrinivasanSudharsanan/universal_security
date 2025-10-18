# Polylytics Universal Data Security Platform

Enterprise-grade security layer for universal data access across multiple data engines.

## Features

- **Universal SQL Security**: Consistent security policies across all data engines
- **Row-Level Security (RLS)**: Dynamic data filtering based on user context
- **Column-Level Security (CLS)**: Fine-grained column access control
- **Multi-Engine Support**: Druid, Iceberg, Snowflake, Databricks, and more
- **Audit & Compliance**: Comprehensive logging and compliance reporting
- **Real-time Policy Enforcement**: Dynamic policy application without data movement

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Local Development

1. **Clone and setup**:
```bash
git clone <repository>
cd polylytics
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt