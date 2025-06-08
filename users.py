# backend/app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from app.services.mongodb import fetch_users, find_user_by_email, add_user, delete_user
from app.models.user import UserIn, UserOut
from app.dependencies import admin_required

router = APIRouter(prefix="/api/users", tags=["users"])

@router.get("/", response_model=list[UserOut], dependencies=[Depends(admin_required)])
async def list_users():
    """
    Только админ видит всех пользователей.
    """
    docs = await fetch_users()
    users = []
    for d in docs:
        d["id"] = str(d["_id"])
        users.append(UserOut(**d))
    return users

@router.get("/me", response_model=UserOut)
async def get_my_profile(user_email: str):
    """
    Любой пользователь может получить свой профиль, указав email.
    (В prod здесь должна быть авторизация, но для простоты — через query-параметр.)
    """
    doc = await find_user_by_email(user_email)
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    data = {**doc, "id": str(doc["_id"])}
    return UserOut(**data)

@router.post("/", response_model=UserOut, status_code=201)
async def create_user(user: UserIn):
    """
    Открытая регистрация — всем new пользователям назначаем роль="user".
    """
    if await find_user_by_email(user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    data = user.dict()
    data["role"] = "user"
    created = await add_user(data)
    return UserOut(**created)

@router.delete("/{user_id}", status_code=204, dependencies=[Depends(admin_required)])
async def remove_user(user_id: str):
    """
    Админ может удалить любого пользователя по его id.
    """
    deleted = await delete_user(user_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return JSONResponse(status_code=204, content=None)
