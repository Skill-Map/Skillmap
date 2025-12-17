from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from jose import jwt, JWTError
from uuid import UUID

from database import get_db
from models import User
from auth import SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/api/v1/users", tags=["users"])

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Неавторизованный доступ")
    
    token = authorization[7:]
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Неверный токен")
        
        try:
            user_uuid = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=401, detail="Неверный формат ID пользователя")
        
        # Приводим UUID к строке, чтобы сравнение с varchar работало
        result = await db.execute(select(User).where(User.id == str(user_uuid)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        return user
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Неверный токен: {str(e)}")


@router.get("/me")
async def read_current_user(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "surname": current_user.surname,
        "name": current_user.name,
        "patronymic": current_user.patronymic,
        "phone": current_user.phone,
        "active": current_user.active,
        "type": current_user.type,
        "reg_date": current_user.reg_date.isoformat() if current_user.reg_date else None,
        "up_date": current_user.up_date,
        "status": current_user.status,
        "track_id": current_user.track_id,
        "group_code": current_user.group_code,
        "progress_percent": current_user.progress_percent,
        "credits_earned": current_user.credits_earned,
        "hours_per_week": current_user.hours_per_week,
        "enrollment_date": current_user.enrollment_date,
        "expected_graduation": current_user.expected_graduation,
    }


@router.get("/{user_id}")
async def read_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID пользователя")
    
    if current_user.type != "admin" and str(current_user.id) != str(user_uuid):
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    # Приводим UUID к строке
    result = await db.execute(select(User).where(User.id == str(user_uuid)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return {
        "id": str(user.id),
        "email": user.email,
        "surname": user.surname,
        "name": user.name,
        "patronymic": user.patronymic,
        "phone": user.phone,
        "type": user.type,
        "status": user.status,
        "track_id": user.track_id,
        "group_code": user.group_code,
    }
