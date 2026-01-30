# metrics.py - Prometheus metrics va business metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import CollectorRegistry, multiprocess, REGISTRY
import time
from functools import wraps
from typing import Callable
import structlog

# Prometheus metrics
REQUEST_COUNT = Counter(
    'marketplace_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'marketplace_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

# Business metrics
USER_REGISTRATIONS = Counter(
    'marketplace_user_registrations_total',
    'Total number of user registrations',
    ['role']
)

USER_LOGINS = Counter(
    'marketplace_user_logins_total',
    'Total number of successful logins',
    ['role']
)

ORDERS_CREATED = Counter(
    'marketplace_orders_created_total',
    'Total number of orders created'
)

ORDERS_STATUS_CHANGES = Counter(
    'marketplace_orders_status_changes_total',
    'Total number of order status changes',
    ['from_status', 'to_status']
)

PRODUCTS_CREATED = Counter(
    'marketplace_products_created_total',
    'Total number of products created'
)

ACTIVE_USERS = Gauge(
    'marketplace_active_users',
    'Number of active users',
    ['role']
)

ACTIVE_PRODUCTS = Gauge(
    'marketplace_active_products',
    'Number of active products with stock > 0'
)

PENDING_ORDERS = Gauge(
    'marketplace_pending_orders',
    'Number of pending orders',
    ['status']
)

GOOGLE_SHEETS_OPERATIONS = Counter(
    'marketplace_google_sheets_operations_total',
    'Total Google Sheets operations',
    ['operation', 'sheet', 'status']
)

GOOGLE_SHEETS_DURATION = Histogram(
    'marketplace_google_sheets_operation_duration_seconds',
    'Google Sheets operation duration',
    ['operation', 'sheet']
)

# Decorator for tracking request metrics
def track_requests(endpoint: str):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            method = "POST" if hasattr(func, '__name__') and 'post' in func.__name__.lower() else "GET"
            
            try:
                result = await func(*args, **kwargs)
                status_code = "200"
                REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
                return result
            except Exception as e:
                status_code = "500"
                REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
                raise
            finally:
                duration = time.time() - start_time
                REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)
        
        return wrapper
    return decorator

# Decorator for tracking Google Sheets operations
def track_sheets_operation(operation: str, sheet: str):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                GOOGLE_SHEETS_OPERATIONS.labels(operation=operation, sheet=sheet, status="success").inc()
                return result
            except Exception as e:
                GOOGLE_SHEETS_OPERATIONS.labels(operation=operation, sheet=sheet, status="error").inc()
                raise
            finally:
                duration = time.time() - start_time
                GOOGLE_SHEETS_DURATION.labels(operation=operation, sheet=sheet).observe(duration)
        
        return wrapper
    return decorator

# Business metrics functions
def record_user_registration(role: str):
    """Record user registration"""
    USER_REGISTRATIONS.labels(role=role).inc()

def record_user_login(role: str):
    """Record successful user login"""
    USER_LOGINS.labels(role=role).inc()

def record_order_created():
    """Record order creation"""
    ORDERS_CREATED.inc()

def record_order_status_change(from_status: str, to_status: str):
    """Record order status change"""
    ORDERS_STATUS_CHANGES.labels(from_status=from_status, to_status=to_status).inc()

def record_product_created():
    """Record product creation"""
    PRODUCTS_CREATED.inc()

def update_active_users_gauge(users_data):
    """Update active users gauge"""
    role_counts = {}
    for user in users_data:
        role = user.get('role', 'unknown')
        role_counts[role] = role_counts.get(role, 0) + 1
    
    for role, count in role_counts.items():
        ACTIVE_USERS.labels(role=role).set(count)

def update_active_products_gauge(products_data):
    """Update active products gauge"""
    active_count = len([p for p in products_data if int(p.get('stock', 0)) > 0])
    ACTIVE_PRODUCTS.set(active_count)

def update_pending_orders_gauge(orders_data):
    """Update pending orders gauge"""
    status_counts = {}
    for order in orders_data:
        status = order.get('status', 'unknown')
        status_counts[status] = status_counts.get(status, 0) + 1
    
    for status, count in status_counts.items():
        PENDING_ORDERS.labels(status=status).set(count)

# Function to get metrics
def get_metrics():
    """Return Prometheus metrics"""
    return generate_latest(REGISTRY)