"""
Enhanced structured logging with correlation IDs and context.
"""
import logging
import json
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from pythonjsonlogger import jsonlogger
import sys

from config.settings import settings


class CorrelationIDFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record):
        # Correlation ID is set in middleware
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = getattr(record, 'correlation_id', None)
        return True


class TenantContextFilter(logging.Filter):
    """Add tenant context to log records."""
    
    def filter(self, record):
        if not hasattr(record, 'tenant_id'):
            record.tenant_id = getattr(record, 'tenant_id', None)
        if not hasattr(record, 'user_id'):
            record.user_id = getattr(record, 'user_id', None)
        return True


class EnhancedJsonFormatter(jsonlogger.JsonFormatter):
    """
    Enhanced JSON formatter with additional context fields.
    """
    
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id') and record.correlation_id:
            log_record['correlation_id'] = record.correlation_id
        
        # Add tenant context if available
        if hasattr(record, 'tenant_id') and record.tenant_id:
            log_record['tenant_id'] = record.tenant_id
        if hasattr(record, 'user_id') and record.user_id:
            log_record['user_id'] = record.user_id
        
        # Add exception info if present
        if record.exc_info:
            log_record['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs', 'message',
                          'pathname', 'process', 'processName', 'relativeCreated', 'thread',
                          'threadName', 'exc_info', 'exc_text', 'stack_info', 'correlation_id',
                          'tenant_id', 'user_id']:
                try:
                    # Try to serialize the value
                    json.dumps(value)
                    log_record[key] = value
                except (TypeError, ValueError):
                    log_record[key] = str(value)


def setup_structured_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    enable_file_logging: bool = False,
    log_file_path: Optional[str] = None
) -> None:
    """
    Set up enhanced structured logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('json' or 'text')
        enable_file_logging: Enable file logging
        log_file_path: Path to log file
    """
    level = log_level or settings.log_level
    format_type = log_format or settings.log_format
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))
    
    # Add filters
    console_handler.addFilter(CorrelationIDFilter())
    console_handler.addFilter(TenantContextFilter())
    
    # Set formatter
    if format_type == "json":
        formatter = EnhancedJsonFormatter(
            fmt="%(timestamp)s %(level)s %(logger)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] [%(tenant_id)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (optional)
    if enable_file_logging:
        log_path = log_file_path or "logs/powerhouse.log"
        import os
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.addFilter(CorrelationIDFilter())
        file_handler.addFilter(TenantContextFilter())
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with enhanced context support.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


class ContextLogger:
    """
    Logger wrapper that maintains context (correlation_id, tenant_id, user_id).
    """
    
    def __init__(self, logger: logging.Logger, correlation_id: Optional[str] = None,
                 tenant_id: Optional[str] = None, user_id: Optional[str] = None):
        self.logger = logger
        self.correlation_id = correlation_id
        self.tenant_id = tenant_id
        self.user_id = user_id
    
    def _add_context(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """Add context to log record."""
        if self.correlation_id:
            extra['correlation_id'] = self.correlation_id
        if self.tenant_id:
            extra['tenant_id'] = self.tenant_id
        if self.user_id:
            extra['user_id'] = self.user_id
        return extra
    
    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=self._add_context(kwargs))
    
    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=self._add_context(kwargs))
    
    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=self._add_context(kwargs))
    
    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=self._add_context(kwargs), exc_info=kwargs.get('exc_info'))
    
    def critical(self, message: str, **kwargs):
        self.logger.critical(message, extra=self._add_context(kwargs), exc_info=kwargs.get('exc_info'))

