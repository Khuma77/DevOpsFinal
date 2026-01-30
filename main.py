# main.py — финальная версия с metrics и logging
from fastapi import Form, Request, Response
import socket
from datetime import datetime
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.base import BaseHTTPMiddleware
import uvicorn
import time

from sheets import (
    get_user_by_username,
    pwd_context,
    create_user,
    get_all_products,
    get_products_by_seller,
    create_product,
    get_orders_by_customer,
    get_orders_by_seller,
    get_orders_for_logist,
    create_order,
    update_order_status,
    assign_logist_to_order,
    get_all_users,
    get_user_info,
)

from metrics import (
    track_requests, 
    record_user_login, 
    get_metrics,
    REQUEST_COUNT,
    REQUEST_DURATION
)

from logging_config import (
    setup_logging,
    log_user_login,
    log_api_request,
    log_error,
    logger
)

# Setup logging
setup_logging()

# Middleware for request tracking
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Get user_id from request if available
        user_id = None
        if request.method == "POST":
            # Try to get user_id from form data or query params
            try:
                if "user_id" in str(request.url):
                    user_id = request.query_params.get("user_id")
            except:
                pass
        
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=str(response.status_code)
        ).inc()
        
        REQUEST_DURATION.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)
        
        # Log request
        log_api_request(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code,
            duration=duration,
            user_id=user_id
        )
        
        return response

app = FastAPI(title="Marketplace — Google Sheets Backend с Metrics")

# Add middleware
app.add_middleware(MetricsMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
async def startup_message():
    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = "127.0.0.1"

    logger.info(
        "application_startup",
        event_type="application_startup",
        hostname=hostname,
        local_ip=local_ip,
        timestamp=datetime.now().isoformat()
    )

    print("\n" + "═" * 70)
    print("  MARKETPLACE BACKEND УСПЕШНО ЗАПУЩЕН")
    print(f"  Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  Адреса:")
    print(f"     • http://127.0.0.1:8000")
    print(f"     • http://{local_ip}:8000")
    print("  Ссылки:")
    print("     • Главная:       http://127.0.0.1:8000")
    print("     • Тест:          http://127.0.0.1:8000/test")
    print("     • Swagger:       http://127.0.0.1:8000/docs")
    print("     • Metrics:       http://127.0.0.1:8000/metrics")
    print("═" * 70 + "\n")


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint"""
    return get_metrics()


@app.get("/", response_class=HTMLResponse)
async def home():
    return RedirectResponse("/static/index.html")


@app.get("/test", response_class=HTMLResponse)
async def test_page():
    return RedirectResponse("/static/test.html")


@app.get("/api/test")
@track_requests("test")
async def test_connection():
    try:
        users = get_all_users()
        products = get_all_products()
        orders = get_all_orders()
        
        count = len(users)
        sample = users[0] if users else {"message": "пока нет пользователей"}
        
        # Business metrics summary
        business_metrics = {
            "total_users": len(users),
            "total_products": len(products),
            "total_orders": len(orders),
            "users_by_role": {},
            "orders_by_status": {}
        }
        
        # Count users by role
        for user in users:
            role = user.get("role", "unknown")
            business_metrics["users_by_role"][role] = business_metrics["users_by_role"].get(role, 0) + 1
        
        # Count orders by status
        for order in orders:
            status = order.get("status", "unknown")
            business_metrics["orders_by_status"][status] = business_metrics["orders_by_status"].get(status, 0) + 1
        
        return {
            "status": "success",
            "message": "Google Sheets подключён",
            "users_count": count,
            "sample": sample,
            "business_metrics": business_metrics,
            "time": datetime.now().isoformat()
        }
    except Exception as e:
        log_error("health_check_error", str(e))
        return {"status": "error", "message": str(e)}


@app.post("/api/login")
@track_requests("login")
async def login(username: str = Form(...), password: str = Form(...)):
    try:
        user = get_user_by_username(username)
        if not user:
            log_user_login(username, "unknown", success=False, error="User not found")
            raise HTTPException(401, "Пользователь не найден")

        if not pwd_context.verify(password, user.get("password_hash", "")):
            log_user_login(username, user.get("role", "unknown"), success=False, error="Invalid password")
            raise HTTPException(401, "Неверный пароль")

        role = user.get("role")
        redirect_map = {
            "customer": "/static/customer.html",
            "seller": "/static/seller.html",
            "logist": "/static/logist.html"
        }

        if role not in redirect_map:
            log_user_login(username, role, success=False, error="Unknown role")
            raise HTTPException(400, "Неизвестная роль")

        # Record successful login
        record_user_login(role)
        log_user_login(username, role, success=True)

        return JSONResponse({
            "status": "success",
            "role": role,
            "redirect": redirect_map[role],
            "user_id": user["ID"]
        })
    except HTTPException:
        raise
    except Exception as e:
        log_error("login_error", str(e), {"username": username})
        raise HTTPException(500, "Внутренняя ошибка сервера")


@app.post("/api/register")
@track_requests("register")
async def register(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    full_name: str = Form(default=""),
    phone: str = Form(default="")
):
    try:
        user = create_user(username, password, role, full_name, phone)
        return {"status": "success", "user": user}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        log_error("registration_error", str(e), {"username": username, "role": role})
        raise HTTPException(500, "Внутренняя ошибка сервера")


@app.get("/api/users")
@track_requests("users")
async def get_all_users_api():
    return get_all_users()


@app.get("/api/products")
@track_requests("products")
async def api_get_products():
    return get_all_products()


@app.get("/api/products/my")
@track_requests("products_my")
async def api_get_my_products(seller_id: str):
    return get_products_by_seller(seller_id)


@app.post("/api/products")
@track_requests("products_create")
async def api_create_product(
    seller_id: str = Form(...),
    name: str = Form(...),
    price: float = Form(...),
    description: str = Form(default=""),
    stock: int = Form(default=10),
    image_url: str = Form(default="")
):
    try:
        product = create_product(seller_id, name, price, description, stock, image_url)
        return {"status": "success", "product": product}
    except Exception as e:
        log_error("product_creation_api_error", str(e), {"seller_id": seller_id})
        raise HTTPException(500, str(e))


@app.get("/api/orders/customer")
@track_requests("orders_customer")
async def api_orders_customer(customer_id: str):
    return get_orders_by_customer(customer_id)


@app.get("/api/orders/seller")
@track_requests("orders_seller")
async def api_orders_seller(seller_id: str):
    return get_orders_by_seller(seller_id)


@app.get("/api/orders/logist")
@track_requests("orders_logist")
async def api_orders_logist(logist_id: str):
    return get_orders_for_logist(logist_id)


@app.post("/api/orders")
@track_requests("orders_create")
async def api_create_order(
    customer_id: str = Form(...),
    seller_id: str = Form(...),
    product_id: str = Form(...),
    quantity: int = Form(...),
    total_price: float = Form(...)
):
    try:
        order = create_order(customer_id, seller_id, product_id, quantity, total_price)
        return {"status": "success", "order": order}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        log_error("order_creation_api_error", str(e), {"customer_id": customer_id})
        raise HTTPException(500, str(e))


@app.post("/api/orders/{order_id}/status")
@track_requests("orders_status_update")
async def api_update_status(order_id: str, status: str = Form(...)):
    try:
        if update_order_status(order_id, status):
            return {"status": "success"}
        raise HTTPException(404, "Заказ не найден")
    except HTTPException:
        raise
    except Exception as e:
        log_error("order_status_update_api_error", str(e), {"order_id": order_id, "status": status})
        raise HTTPException(500, "Внутренняя ошибка сервера")


@app.post("/api/orders/{order_id}/assign-logist")
@track_requests("orders_assign_logist")
async def api_assign_logist(order_id: str, logist_id: str = Form(...)):
    try:
        if assign_logist_to_order(order_id, logist_id):
            return {"status": "success"}
        raise HTTPException(404, "Заказ не найден")
    except HTTPException:
        raise
    except Exception as e:
        log_error("logist_assignment_error", str(e), {"order_id": order_id, "logist_id": logist_id})
        raise HTTPException(500, "Внутренняя ошибка сервера")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)