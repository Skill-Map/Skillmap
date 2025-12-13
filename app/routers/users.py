from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

import crud
import schemas
from database import get_db
from auth import get_current_active_user, require_role
import models

router = APIRouter(prefix="/user", tags=["users"])

@router.get("/", response_model=schemas.UserInDB)
async def read_current_user(
    current_user: models.User = Depends(get_current_active_user)
):
    return current_user

@router.get("/{user_id}", response_model=schemas.UserInDB)
async def read_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    db_user = await crud.get_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверка прав доступа
    if current_user.type != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return db_user

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Только админ или сам пользователь может удалить
    if current_user.type != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db_user = await crud.delete_user(db, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}

# Создаем отдельный роутер для API v1
router_v1 = APIRouter(prefix="/api/v1/users", tags=["users-v1"])

@router_v1.get("/me")
async def read_current_user(
    current_user: models.User = Depends(get_current_active_user)
):
    """Возвращает данные текущего авторизованного пользователя"""
    # Просто возвращаем объект пользователя
    # SQLAlchemy модель автоматически сериализуется в JSON
    return {
        "id": current_user.id,
        "email": current_user.email,
        "surname": current_user.surname,
        "name": current_user.name,
        "patronymic": current_user.patronymic,
        "phone": current_user.phone,
        "active": current_user.active,
        "type": current_user.type,
        "reg_date": current_user.reg_date.isoformat() if current_user.reg_date else None,
        "up_date": current_user.up_date,
        # Поля для студента
        "status": current_user.status,
        "track_id": current_user.track_id,
        "group_code": current_user.group_code,
        "progress_percent": current_user.progress_percent,
        "credits_earned": current_user.credits_earned,
        "hours_per_week": current_user.hours_per_week,
        "enrollment_date": current_user.enrollment_date,
        "expected_graduation": current_user.expected_graduation,
        # Поля для преподавателя
        "title": current_user.title,
        "department": current_user.department,
        "hire_date": current_user.hire_date,
        "teacher_hours_per_week": current_user.teacher_hours_per_week,
        "rating": current_user.rating,
    }