# sheets.py — финальная версия с metrics и logging

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import uuid
from typing import List, Dict, Optional, Any
from passlib.context import CryptContext
from metrics import (
    track_sheets_operation, 
    record_user_registration, 
    record_product_created,
    record_order_created,
    record_order_status_change,
    update_active_users_gauge,
    update_active_products_gauge,
    update_pending_orders_gauge
)
from logging_config import (
    log_user_registration,
    log_product_created,
    log_order_created,
    log_order_status_change,
    log_google_sheets_operation,
    log_error
)
import time

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive",
]

creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPE)
client = gspread.authorize(creds)

SHEET_NAME = "marketplace"
sheet = client.open(SHEET_NAME)

users_ws    = sheet.worksheet("Users")
products_ws = sheet.worksheet("Products")
orders_ws   = sheet.worksheet("Orders")

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ────────────────────────────────────────
# Users
# ────────────────────────────────────────

@track_sheets_operation("get_all", "users")
def get_all_users() -> List[Dict[str, Any]]:
    try:
        users = users_ws.get_all_records()
        update_active_users_gauge(users)
        return users
    except Exception as e:
        log_error("google_sheets_error", str(e), {"operation": "get_all_users"})
        raise


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    for user in get_all_users():
        if user.get("username") == username:
            return user
    return None


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    for user in get_all_users():
        if user.get("ID") == user_id:
            return user
    return None


def get_user_info(user_id: str) -> Dict:
    user = get_user_by_id(user_id)
    if user:
        return {
            "id": user["ID"],
            "username": user["username"],
            "full_name": user.get("full_name", "Не указано"),
            "phone": user.get("phone", "Не указан")
        }
    return {"id": user_id, "username": "Не найден", "full_name": "Не найден", "phone": "Не указан"}


@track_sheets_operation("create", "users")
def create_user(
    username: str,
    password: str,
    role: str,
    full_name: str = "",
    phone: str = ""
) -> Dict[str, Any]:
    try:
        if get_user_by_username(username):
            raise ValueError("Username уже занят")

        if role not in ["customer", "seller", "logist"]:
            raise ValueError("Недопустимая роль")

        if not phone.strip():
            raise ValueError("Телефон обязателен")

        new_id = str(uuid.uuid4())[:8]
        hashed = pwd_context.hash(password)

        row = [
            new_id,
            username,
            hashed,
            role,
            full_name,
            phone,
            datetime.now().isoformat()
        ]

        users_ws.insert_row(row, 2)

        # Record metrics and logs
        record_user_registration(role)
        log_user_registration(username, role, success=True)

        return {
            "ID": new_id,
            "username": username,
            "role": role,
            "full_name": full_name,
            "phone": phone,
            "created_at": row[-1]
        }
    except Exception as e:
        log_user_registration(username, role, success=False)
        log_error("user_creation_error", str(e), {"username": username, "role": role})
        raise


# ────────────────────────────────────────
# Products
# ────────────────────────────────────────

@track_sheets_operation("get_all", "products")
def get_all_products() -> List[Dict[str, Any]]:
    try:
        products = [p for p in products_ws.get_all_records() if int(p.get("stock", 0)) > 0]
        update_active_products_gauge(products_ws.get_all_records())
        return products
    except Exception as e:
        log_error("google_sheets_error", str(e), {"operation": "get_all_products"})
        raise


def get_products_by_seller(seller_id: str) -> List[Dict[str, Any]]:
    return [p for p in get_all_products() if p.get("seller_id") == seller_id]


@track_sheets_operation("create", "products")
def create_product(
    seller_id: str,
    name: str,
    price: float,
    description: str = "",
    stock: int = 10,
    image_url: str = ""
) -> Dict[str, Any]:
    try:
        new_id = str(uuid.uuid4())[:8]

        row = [
            new_id,
            seller_id,
            name,
            float(price),
            description,
            int(stock),
            image_url,
            datetime.now().isoformat()
        ]

        products_ws.insert_row(row, 2)

        # Record metrics and logs
        record_product_created()
        log_product_created(new_id, seller_id, name, price)

        return {
            "id": new_id,
            "seller_id": seller_id,
            "name": name,
            "price": price,
            "description": description,
            "stock": stock,
            "image_url": image_url,
            "created_at": row[-1]
        }
    except Exception as e:
        log_error("product_creation_error", str(e), {"seller_id": seller_id, "name": name})
        raise


def decrease_product_stock(product_id: str, quantity: int) -> bool:
    products = products_ws.get_all_records()
    for idx, product in enumerate(products, start=2):
        if product.get("id") == product_id:
            current_stock = int(product.get("stock", 0))
            if current_stock < quantity:
                return False
            new_stock = current_stock - quantity
            products_ws.update_cell(idx, 6, new_stock)
            return True
    return False


# ────────────────────────────────────────
# Orders
# ────────────────────────────────────────

@track_sheets_operation("get_all", "orders")
def get_all_orders() -> List[Dict[str, Any]]:
    try:
        orders = orders_ws.get_all_records()
        update_pending_orders_gauge(orders)
        return orders
    except Exception as e:
        log_error("google_sheets_error", str(e), {"operation": "get_all_orders"})
        raise


def get_orders_by_customer(customer_id: str) -> List[Dict[str, Any]]:
    return [o for o in get_all_orders() if o.get("customer_id") == customer_id]


def get_orders_by_seller(seller_id: str) -> List[Dict[str, Any]]:
    return [o for o in get_all_orders() if o.get("seller_id") == seller_id]


def get_orders_for_logist(logist_id: str) -> List[Dict[str, Any]]:
    return [
        o for o in get_all_orders()
        if o.get("logist_id") == logist_id or o.get("status") == "new"
    ]


@track_sheets_operation("create", "orders")
def create_order(
    customer_id: str,
    seller_id: str,
    product_id: str,
    quantity: int,
    total_price: float,
    logist_id: str = ""
) -> Dict[str, Any]:
    try:
        if not decrease_product_stock(product_id, quantity):
            raise ValueError("Недостаточно товара на складе или товар не найден")

        new_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()

        customer_info = get_user_info(customer_id)
        seller_info = get_user_info(seller_id)

        row = [
            new_id,
            customer_id,
            seller_id,
            product_id,
            quantity,
            total_price,
            "new",
            logist_id,
            customer_info["phone"],
            seller_info["phone"],
            now,
            now
        ]

        orders_ws.insert_row(row, 2)

        # Record metrics and logs
        record_order_created()
        log_order_created(new_id, customer_id, seller_id, total_price)

        return {
            "id": new_id,
            "customer_id": customer_id,
            "seller_id": seller_id,
            "product_id": product_id,
            "quantity": quantity,
            "total_price": total_price,
            "status": "new",
            "logist_id": logist_id,
            "customer_phone": customer_info["phone"],
            "seller_phone": seller_info["phone"],
            "created_at": now,
            "updated_at": now
        }
    except Exception as e:
        log_error("order_creation_error", str(e), {
            "customer_id": customer_id, 
            "seller_id": seller_id, 
            "product_id": product_id
        })
        raise


@track_sheets_operation("update", "orders")
def update_order_status(order_id: str, new_status: str) -> bool:
    try:
        orders = get_all_orders()
        for idx, order in enumerate(orders, start=2):
            if order.get("id") == order_id:
                old_status = order.get("status", "unknown")
                orders_ws.update_cell(idx, 7, new_status)
                orders_ws.update_cell(idx, 12, datetime.now().isoformat())  # updated_at теперь столбец L
                
                # Record metrics and logs
                record_order_status_change(old_status, new_status)
                log_order_status_change(order_id, old_status, new_status)
                
                return True
        return False
    except Exception as e:
        log_error("order_status_update_error", str(e), {"order_id": order_id, "new_status": new_status})
        raise


def assign_logist_to_order(order_id: str, logist_id: str) -> bool:
    orders = get_all_orders()
    for idx, order in enumerate(orders, start=2):
        if order.get("id") == order_id:
            orders_ws.update_cell(idx, 8, logist_id)
            return True
    return False