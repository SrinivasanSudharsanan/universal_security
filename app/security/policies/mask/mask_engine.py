# app/security/policies/mask/mask_engine.py
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

class MaskEngine:
    """Data Masking Engine"""
    
    def __init__(self):
        self.mask_rules = {}
    
    def apply_mask(self, data: Any, data_type: str, mask_rule: str) -> Any:
        """Apply data masking based on type and rule"""
        if data is None:
            return data
            
        if mask_rule == "email":
            if isinstance(data, str) and "@" in data:
                parts = data.split("@")
                if len(parts[0]) > 2:
                    return parts[0][:2] + "***@" + parts[1]
                else:
                    return "***@" + parts[1]
        
        elif mask_rule == "phone":
            if isinstance(data, str) and len(data) >= 10:
                return data[:3] + "***" + data[-4:]
        
        elif mask_rule == "ssn":
            if isinstance(data, str) and len(data) == 9:
                return "***-**-" + data[-4:]
        
        elif mask_rule == "full":
            return "***"
        
        elif mask_rule == "partial":
            if isinstance(data, str) and len(data) > 4:
                return data[:2] + "***" + data[-2:]
        
        return data