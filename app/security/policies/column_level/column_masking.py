#!/usr/bin/env python3
"""
Universal Column Masking Engine
Provides consistent data masking across all database types
"""

import logging
import re
import hashlib
from typing import Any, Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class MaskingEngine:
    """
    Universal data masking engine
    Consistent masking across PostgreSQL, MySQL, Druid, etc.
    """
    
    def __init__(self):
        self.masking_rules = self._initialize_masking_rules()
        self.database_specific = self._initialize_database_specific()
    
    def _initialize_masking_rules(self) -> Dict:
        """Initialize universal masking rules"""
        return {
            "full": self._apply_full_mask,
            "partial": self._apply_partial_mask,
            "email": self._apply_email_mask,
            "phone": self._apply_phone_mask,
            "ssn": self._apply_ssn_mask,
            "credit_card": self._apply_credit_card_mask,
            "hash": self._apply_hash_mask,
            "custom": self._apply_custom_mask
        }
    
    def _initialize_database_specific(self) -> Dict:
        """Initialize database-specific masking implementations"""
        return {
            "postgres": {
                "full": "NULL",  # PostgreSQL specific
                "hash": "MD5({column})"
            },
            "mysql": {
                "full": "NULL",
                "hash": "MD5({column})"
            },
            "druid": {
                "full": "''",
                "hash": "MD5({column})"
            },
            "snowflake": {
                "full": "NULL",
                "hash": "MD5({column})"
            }
        }
    
    def mask_data(self, data: Any, mask_type: str, custom_rule: str = None) -> Any:
        """
        Apply data masking to a value
        Universal implementation - works the same everywhere
        """
        if data is None:
            return None
        
        try:
            mask_function = self.masking_rules.get(mask_type, self._apply_full_mask)
            return mask_function(data, custom_rule)
        except Exception as e:
            logger.warning(f"Masking failed for type {mask_type}, using full mask: {e}")
            return self._apply_full_mask(data)
    
    def generate_sql_mask(
        self, 
        column_name: str, 
        mask_type: str, 
        engine_type: str = "postgres",
        custom_rule: str = None
    ) -> str:
        """
        Generate SQL expression for masking at database level
        Database-specific implementations for performance
        """
        if engine_type in self.database_specific and mask_type in self.database_specific[engine_type]:
            template = self.database_specific[engine_type][mask_type]
            return template.format(column=column_name)
        
        # Fallback to universal SQL
        return self._generate_universal_sql_mask(column_name, mask_type, custom_rule)
    
    def _generate_universal_sql_mask(self, column_name: str, mask_type: str, custom_rule: str) -> str:
        """Generate universal SQL masking expression"""
        if mask_type == "full":
            return "NULL"
        elif mask_type == "partial":
            return f"CONCAT(SUBSTRING({column_name}, 1, 2), '***', SUBSTRING({column_name}, -2))"
        elif mask_type == "email":
            return f"CONCAT(SUBSTRING({column_name}, 1, 1), '***', SUBSTRING({column_name}, POSITION('@' IN {column_name}) - 1, 1), SUBSTRING({column_name}, POSITION('@' IN {column_name})))"
        elif mask_type == "hash":
            return f"MD5({column_name})"
        else:
            return "NULL"  # Default fallback
    
    def _apply_full_mask(self, data: Any, custom_rule: str = None) -> str:
        """Apply full data masking"""
        return "***"
    
    def _apply_partial_mask(self, data: Any, custom_rule: str = None) -> str:
        """Apply partial data masking"""
        data_str = str(data)
        if len(data_str) <= 4:
            return "****"
        
        # Custom rule format: "first_chars:2,last_chars:2,mask_char:*"
        if custom_rule:
            return self._apply_custom_partial_mask(data_str, custom_rule)
        
        # Default: first 2, last 2 characters visible
        return data_str[:2] + "***" + data_str[-2:]
    
    def _apply_custom_partial_mask(self, data: str, custom_rule: str) -> str:
        """Apply custom partial masking based on rule"""
        try:
            # Parse custom rule: "first_chars:2,last_chars:2,mask_char:*"
            params = {}
            for part in custom_rule.split(','):
                key, value = part.split(':', 1)
                params[key.strip()] = value.strip()
            
            first_chars = int(params.get('first_chars', 2))
            last_chars = int(params.get('last_chars', 2))
            mask_char = params.get('mask_char', '*')
            mask_length = int(params.get('mask_length', 3))
            
            if len(data) <= first_chars + last_chars:
                return mask_char * len(data)
            
            return (data[:first_chars] + 
                   mask_char * mask_length + 
                   data[-last_chars:])
                   
        except Exception as e:
            logger.warning(f"Custom mask rule failed, using default: {e}")
            return self._apply_partial_mask(data)
    
    def _apply_email_mask(self, data: Any, custom_rule: str = None) -> str:
        """Apply email address masking"""
        email = str(data)
        if '@' not in email:
            return self._apply_partial_mask(email)
        
        username, domain = email.split('@', 1)
        masked_username = username[0] + "***" + (username[-1] if len(username) > 1 else "")
        return f"{masked_username}@{domain}"
    
    def _apply_phone_mask(self, data: Any, custom_rule: str = None) -> str:
        """Apply phone number masking"""
        phone = re.sub(r'\D', '', str(data))  # Keep only digits
        
        if len(phone) == 10:  # US format
            return f"***-***-{phone[-4:]}"
        elif len(phone) == 11 and phone[0] == '1':  # US with country code
            return f"+1-***-***-{phone[-4:]}"
        else:
            # International format - show last 4 digits
            return f"***-{phone[-4:]}" if len(phone) >= 4 else "***"
    
    def _apply_ssn_mask(self, data: Any, custom_rule: str = None) -> str:
        """Apply SSN masking"""
        ssn = re.sub(r'\D', '', str(data))
        if len(ssn) == 9:
            return f"***-**-{ssn[-4:]}"
        return "***-**-****"
    
    def _apply_credit_card_mask(self, data: Any, custom_rule: str = None) -> str:
        """Apply credit card masking"""
        card = re.sub(r'\D', '', str(data))
        if len(card) >= 4:
            return f"****-****-****-{card[-4:]}"
        return "****-****-****-****"
    
    def _apply_hash_mask(self, data: Any, custom_rule: str = None) -> str:
        """Apply hash-based masking"""
        data_str = str(data)
        hash_obj = hashlib.md5(data_str.encode())
        return f"hash_{hash_obj.hexdigest()[:8]}"
    
    def _apply_custom_mask(self, data: Any, custom_rule: str = None) -> Any:
        """Apply custom masking rule"""
        if not custom_rule:
            return self._apply_full_mask(data)
        
        try:
            # Simple custom rule evaluation
            # Example: "regex:(\d{3})-(\d{2})-(\d{4}):***-**-$3"
            if custom_rule.startswith('regex:'):
                parts = custom_rule.split(':', 2)
                if len(parts) == 3:
                    pattern, replacement = parts[1], parts[2]
                    return re.sub(pattern, replacement, str(data))
            
            # Python expression (use with caution)
            elif custom_rule.startswith('python:'):
                # In production, use a sandboxed environment
                expression = custom_rule[7:]
                return eval(expression, {'data': data, 'len': len, 'str': str})
            
            return self._apply_full_mask(data)
            
        except Exception as e:
            logger.error(f"Custom mask failed: {e}")
            return self._apply_full_mask(data)
    
    def get_supported_mask_types(self) -> Dict[str, str]:
        """Get supported masking types and descriptions"""
        return {
            "full": "Complete data hiding",
            "partial": "Partial data visibility",
            "email": "Email address protection",
            "phone": "Phone number protection", 
            "ssn": "Social Security Number protection",
            "credit_card": "Credit card number protection",
            "hash": "Hash-based anonymization",
            "custom": "Custom masking rules"
        }
    
    def validate_mask_type(self, mask_type: str) -> bool:
        """Validate if mask type is supported"""
        return mask_type in self.masking_rules

# Global instance for easy access
universal_masking_engine = MaskingEngine()
