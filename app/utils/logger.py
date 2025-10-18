import logging
import sys
from typing import Optional
import structlog

def setup_logging(level: str = "INFO", json_format: bool = False):
    """Setup structured logging"""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s" if json_format else "%(levelname)s - %(name)s - %(message)s",
        level=getattr(logging, level.upper()),
        stream=sys.stdout
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if json_format else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """Get structured logger"""
    return structlog.get_logger(name)