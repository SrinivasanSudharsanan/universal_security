#!/usr/bin/env python3
"""
Database-driven SQL Rewriter 
Integrates with your existing sql_rewriter.py
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import sqlglot
import sqlglot.expressions as exp

# Use your existing SQL rewriter as base
from .sql_rewriter import SQLRewriter
from app.security.policies.policy_manager import SQLDialect
from app.security.policies.database_repository import DatabaseSecurityPolicy

logger = logging.getLogger(__name__)

class DatabaseSQLRewriter(SQLRewriter):
    """
    Enhanced SQL rewriter that uses database-driven policies
    Extends your existing SQLRewriter class
    """
    
    def rewrite_sql_with_policies(
        self,
        sql: str,
        policies: DatabaseSecurityPolicy,
        dialect: SQLDialect = SQLDialect.MYSQL
    ) -> Tuple[str, List[str]]:
        """
        Rewrite SQL using database-driven security policies
        Returns: (secured_sql, warnings)
        """
        warnings = []
        
        try:
            # Parse SQL using your existing method
            parsed = self.parse_sql(sql, dialect)
            
            # Apply database-driven security policies
            secured = self._apply_database_policies(parsed, policies, warnings)
            
            # Generate secured SQL
            secure_sql = secured.sql(dialect=dialect.value)
            
            logger.info(f"SQL rewritten with database policies: {sql} -> {secure_sql}")
            return secure_sql, warnings
            
        except Exception as e:
            logger.error(f"Database SQL rewriting failed: {e}")
            warnings.append(f"Security rewriting failed: {str(e)}")
            return sql, warnings
    
    def _apply_database_policies(
        self,
        expression: exp.Expression,
        policies: DatabaseSecurityPolicy,
        warnings: List[str]
    ) -> exp.Expression:
        """Apply database-driven security policies to SQL AST"""
        
        if isinstance(expression, exp.Select):
            return self._secure_select_with_policies(expression, policies, warnings)
        elif isinstance(expression, exp.Union):
            return self._secure_union_with_policies(expression, policies, warnings)
        elif isinstance(expression, exp.Subquery):
            # Secure subqueries recursively
            expression.this = self._apply_database_policies(expression.this, policies, warnings)
        
        return expression
    
    def _secure_select_with_policies(
        self,
        select: exp.Select,
        policies: DatabaseSecurityPolicy,
        warnings: List[str]
    ) -> exp.Select:
        """Apply database policies to SELECT statement"""
        
        # Get all tables in the query
        tables = self._extract_tables(select)
        
        for table_name, table_expr in tables.items():
            # Apply RLS from database
            if table_name in policies.rls_filters:
                select = self._apply_rls_from_database(select, table_name, policies.rls_filters[table_name], warnings)
            
            # Apply CLS from database
            if (table_name in policies.allowed_columns or 
                table_name in policies.blocked_columns):
                select = self._apply_cls_from_database(select, table_name, policies, warnings)
        
        return select
    
    def _apply_rls_from_database(
        self,
        select: exp.Select,
        table_name: str,
        rls_condition: str,
        warnings: List[str]
    ) -> exp.Select:
        """Apply RLS condition from database"""
        try:
            # Parse the RLS condition
            filter_expr = sqlglot.parse_one(rls_condition)
            
            # Get existing WHERE clause
            where_expr = select.args.get("where")
            
            if where_expr:
                # Combine with AND
                combined = exp.and_(where_expr.this, filter_expr)
                select.args["where"] = exp.Where(this=combined)
            else:
                # Add new WHERE clause
                select.args["where"] = exp.Where(this=filter_expr)
            
            warnings.append(f"Applied database RLS to {table_name}: {rls_condition}")
            
        except Exception as e:
            warnings.append(f"Failed to apply database RLS for {table_name}: {str(e)}")
        
        return select
    
    def _apply_cls_from_database(
        self,
        select: exp.Select,
        table_name: str,
        policies: DatabaseSecurityPolicy,
        warnings: List[str]
    ) -> exp.Select:
        """Apply CLS policies from database"""
        
        allowed_columns = policies.allowed_columns.get(table_name, [])
        blocked_columns = policies.blocked_columns.get(table_name, [])
        
        # Handle SELECT *
        expressions = select.args.get("expressions", [])
        if len(expressions) == 1 and isinstance(expressions[0], exp.Star):
            if allowed_columns:
                # Replace * with allowed columns
                select.args["expressions"] = [
                    exp.column(col, table=table_name) for col in allowed_columns
                ]
                warnings.append(f"Replaced * with database-allowed columns for {table_name}")
            return select
        
        # Filter existing expressions based on database policies
        safe_expressions = []
        for expr in expressions:
            if isinstance(expr, exp.Column):
                col_name = expr.name
                
                # Check blocked columns from database
                if col_name in blocked_columns:
                    warnings.append(f"Removed database-blocked column: {table_name}.{col_name}")
                    continue
                
                # Check allowed columns from database
                if allowed_columns and col_name not in allowed_columns:
                    warnings.append(f"Removed database-unauthorized column: {table_name}.{col_name}")
                    continue
            
            safe_expressions.append(expr)
        
        select.args["expressions"] = safe_expressions
        return select
    
    def _extract_tables(self, select: exp.Select) -> Dict[str, exp.Expression]:
        """Extract table references - reuse your existing method if available"""
        tables = {}
        
        # Main FROM table
        from_expr = select.args.get("from")
        if from_expr and isinstance(from_expr, exp.From):
            main_table = from_expr.this
            if isinstance(main_table, exp.Table):
                tables[main_table.name] = main_table
        
        # JOIN tables
        joins = select.args.get("joins", [])
        for join in joins:
            if hasattr(join, 'this') and isinstance(join.this, exp.Table):
                tables[join.this.name] = join.this
        
        return tables
    
    def _secure_union_with_policies(
        self,
        union: exp.Union,
        policies: DatabaseSecurityPolicy,
        warnings: List[str]
    ) -> exp.Union:
        """Apply database policies to UNION query"""
        
        if union.this:
            union.this = self._apply_database_policies(union.this, policies, warnings)
        
        if union.expression:
            union.expression = self._apply_database_policies(union.expression, policies, warnings)
        
        return union
