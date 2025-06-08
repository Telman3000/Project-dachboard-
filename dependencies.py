# backend/app/dependencies.py
import os
from fastapi import Header, HTTPException, status

ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")

def admin_required(x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    # Если всё ок — зависимость возвращает None и маршрут выполняется дальше
