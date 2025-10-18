import sqlglot
import sqlglot.expressions as exp
from typing import List, Dict, Any, Optional, Tuple
from app.security.policies.policy_manager import SQLDialect
import logging

logger = logging.getLogger(__name__)

class SQLRewriter:
    def __init__(self):
        self.supported_dialects = [dialect.value for dialect in SQLDialect]
    
    def parse_sql(self, sql: str, dialect: SQLDialect = SQLDialect.MYSQL) -> exp.Expression:
        """Parse SQL string into AST"""
        try:
            parsed = sqlglot.parse_one(sql, read=dialect.value)
            return parsed
        except Exception as e:
            logger.error(f"SQL parsing error: {str(e)}")
            raise ValueError(f"Invalid SQL syntax: {str(e)}")
    
    def apply_row_level_security(
        self, 
        parsed_sql: exp.Expression, 
        rls_filters: List[str],
        dialect: SQLDialect
    ) -> exp.Expression:
        """Apply RLS filters to SQL query"""
        if not rls_filters:
            return parsed_sql
        
        try:
            # Convert RLS filters to SQL expressions
            filter_expressions = []
            for filter_str in rls_filters:
                try:
                    filter_expr = sqlglot.parse_one(filter_str, read=dialect.value)
                    filter_expressions.append(filter_expr)
                except Exception as e:
                    logger.warning(f"Failed to parse RLS filter '{filter_str}': {e}")
                    continue
            
            if not filter_expressions:
                return parsed_sql
            
            # Find existing WHERE clause
            where_expr = parsed_sql.args.get("where")
            
            if where_expr:
                # Combine with AND
                combined_filter = where_expr
                for filter_expr in filter_expressions:
                    combined_filter = exp.and_(combined_filter, filter_expr)
                parsed_sql.set("where", combined_filter)
            else:
                # Create new WHERE clause
                if len(filter_expressions) == 1:
                    parsed_sql.set("where", filter_expressions[0])
                else:
                    combined_filter = filter_expressions[0]
                    for filter_expr in filter_expressions[1:]:
                        combined_filter = exp.and_(combined_filter, filter_expr)
                    parsed_sql.set("where", combined_filter)
            
            return parsed_sql
            
        except Exception as e:
            logger.error(f"RLS application error: {str(e)}")
            return parsed_sql
    
    def apply_column_level_security(
        self,
        parsed_sql: exp.Expression,
        allowed_columns: List[str],
        dialect: SQLDialect
    ) -> exp.Expression:
        """Apply CLS by filtering unauthorized columns"""
        if not allowed_columns:
            return parsed_sql
        
        try:
            def column_transformer(node):
                if isinstance(node, exp.Select):
                    new_expressions = []
                    for expr in node.expressions:
                        if isinstance(expr, exp.Star):
                            # Replace * with specific columns
                            new_expressions.extend([
                                exp.column(col) for col in allowed_columns
                            ])
                        elif isinstance(expr, exp.Column):
                            # Check if column is allowed
                            col_name = expr.name
                            if col_name in allowed_columns:
                                new_expressions.append(expr)
                        elif isinstance(expr, exp.Alias):
                            # Handle aliased columns
                            col_name = expr.alias
                            if col_name in allowed_columns:
                                new_expressions.append(expr)
                        else:
                            # Keep other expressions (functions, literals, etc.)
                            new_expressions.append(expr)
                    
                    node.set("expressions", new_expressions)
                return node
            
            return parsed_sql.transform(column_transformer)
            
        except Exception as e:
            logger.error(f"CLS application error: {str(e)}")
            return parsed_sql
    
    def detect_sensitive_operations(self, parsed_sql: exp.Expression) -> List[str]:
        """Detect potentially dangerous SQL operations"""
        warnings = []
        
        # Check for DELETE without WHERE
        if isinstance(parsed_sql, exp.Delete) and not parsed_sql.args.get("where"):
            warnings.append("DELETE operation without WHERE clause")
        
        # Check for DROP operations
        if isinstance(parsed_sql, exp.Drop):
            warnings.append("DROP operation detected")
        
        # Check for system table access
        system_tables = ["pg_", "mysql.", "information_schema", "sys."]
        for table in parsed_sql.find_all(exp.Table):
            table_name = str(table)
            if any(sys_table in table_name for sys_table in system_tables):
                warnings.append(f"Access to system table: {table_name}")
        
        return warnings
    
    def rewrite_sql(
        self,
        sql: str,
        rls_filters: List[str],
        allowed_columns: List[str],
        dialect: SQLDialect = SQLDialect.MYSQL
    ) -> Tuple[str, List[str]]:
        """Main method to rewrite SQL with security policies"""
        try:
            # Parse original SQL
            parsed = self.parse_sql(sql, dialect)
            
            # Detect sensitive operations
            warnings = self.detect_sensitive_operations(parsed)
            
            # Apply RLS
            parsed = self.apply_row_level_security(parsed, rls_filters, dialect)
            
            # Apply CLS
            parsed = self.apply_column_level_security(parsed, allowed_columns, dialect)
            
            # Generate rewritten SQL
            rewritten_sql = parsed.sql(dialect=dialect.value)
            
            return rewritten_sql, warnings
            
        except Exception as e:
            logger.error(f"SQL rewriting failed: {str(e)}")
            raise