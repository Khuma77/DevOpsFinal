# logging_config.py - Structured logging configuration for Loki
import structlog
import logging
import sys
from datetime import datetime
import json
import os
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Setup structured logging for Loki"""
    
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
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
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging with file handler
    file_handler = RotatingFileHandler(
        "logs/marketplace.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    logging.basicConfig(
        format="%(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            file_handler
        ],
        level=logging.INFO,
    )

# Create logger instance
logger = structlog.get_logger("marketplace")

# Business event logging functions
def log_user_registration(username: str, role: str, success: bool = True):
    """Log user registration event"""
    logger.info(
        "user_registration",
        event_type="user_registration",
        username=username,
        role=role,
        success=success,
        timestamp=datetime.now().isoformat()
    )

def log_user_login(username: str, role: str, success: bool = True, error: str = None):
    """Log user login event"""
    logger.info(
        "user_login",
        event_type="user_login",
        username=username,
        role=role,
        success=success,
        error=error,
        timestamp=datetime.now().isoformat()
    )

def log_order_created(order_id: str, customer_id: str, seller_id: str, total_price: float):
    """Log order creation event"""
    logger.info(
        "order_created",
        event_type="order_created",
        order_id=order_id,
        customer_id=customer_id,
        seller_id=seller_id,
        total_price=total_price,
        timestamp=datetime.now().isoformat()
    )

def log_order_status_change(order_id: str, from_status: str, to_status: str, user_id: str = None):
    """Log order status change event"""
    logger.info(
        "order_status_change",
        event_type="order_status_change",
        order_id=order_id,
        from_status=from_status,
        to_status=to_status,
        changed_by=user_id,
        timestamp=datetime.now().isoformat()
    )

def log_product_created(product_id: str, seller_id: str, name: str, price: float):
    """Log product creation event"""
    logger.info(
        "product_created",
        event_type="product_created",
        product_id=product_id,
        seller_id=seller_id,
        product_name=name,
        price=price,
        timestamp=datetime.now().isoformat()
    )

def log_google_sheets_operation(operation: str, sheet: str, success: bool = True, error: str = None, duration: float = None):
    """Log Google Sheets operation"""
    logger.info(
        "google_sheets_operation",
        event_type="google_sheets_operation",
        operation=operation,
        sheet=sheet,
        success=success,
        error=error,
        duration_seconds=duration,
        timestamp=datetime.now().isoformat()
    )

def log_api_request(method: str, endpoint: str, status_code: int, duration: float, user_id: str = None):
    """Log API request"""
    logger.info(
        "api_request",
        event_type="api_request",
        method=method,
        endpoint=endpoint,
        status_code=status_code,
        duration_seconds=duration,
        user_id=user_id,
        timestamp=datetime.now().isoformat()
    )

def log_error(error_type: str, error_message: str, context: dict = None):
    """Log application error"""
    logger.error(
        "application_error",
        event_type="application_error",
        error_type=error_type,
        error_message=error_message,
        context=context or {},
        timestamp=datetime.now().isoformat()
    )