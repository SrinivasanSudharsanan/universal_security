#!/usr/bin/env python3
"""
SQL utilities for Universal Security Framework
"""

import re
from typing import List, Set

def extract_tables_from_sql(sql: str) -> Set[str]:
    """Extract table names from SQL query"""
    # Simple regex to extract table names from FROM and JOIN clauses
    tables = set()
    
    # Remove subqueries to avoid false positives
    sql_clean = re.sub(r'\([^)]*\)', '', sql)
    
    # Find tables in FROM clauses
    from_matches = re.finditer(r'\bFROM\s+(\w+)', sql_clean, re.IGNORECASE)
    tables.update(match.group(1) for match in from_matches)
    
    # Find tables in JOIN clauses
    join_matches = re.finditer(r'\bJOIN\s+(\w+)', sql_clean, re.IGNORECASE)
    tables.update(match.group(1) for match in join_matches)
    
    return tables

def validate_sql_condition(condition: str) -> bool:
    """Basic SQL condition validation"""
    # Simple safety check - in production use proper SQL parsing
    dangerous_keywords = ['drop', 'delete', 'truncate', 'insert', 'update', ';', '--']
    return not any(keyword in condition.lower() for keyword in dangerous_keywords)

def build_where_clause(existing_where: str, new_condition: str) -> str:
    """Build a combined WHERE clause"""
    if not existing_where:
        return new_condition
    else:
        return f"({existing_where}) AND ({new_condition})"
