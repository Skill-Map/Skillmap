from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

import crud
import schemas
from database import get_db
from auth import get_current_active_user, require_role
import models

router = APIRouter(prefix="/admin", tags=["admins"])

@router.post("/", response_model=schemas.AdminResponse)
async def create_admin(
    admin: schemas.AdminCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    db_user = await crud.get_user_by_email(db, admin.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(db, admin)

@router.get("/", response_model=List[schemas.AdminResponse])
async def read_admins(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    return await crud.get_users_by_type(db, "admin")

@router.get("/{admin_id}", response_model=schemas.AdminResponse)
async def read_admin(
    admin_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    db_user = await crud.get_user(db, admin_id)
    if db_user is None or db_user.type != "admin":
        raise HTTPException(status_code=404, detail="Admin not found")
    return db_user

@router.put("/", response_model=schemas.AdminResponse)
async def update_admin(
    admin_update: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    # Обновляем текущего пользователя (админа)
    db_user = await crud.update_user(db, current_user.id, admin_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Admin not found")
    return db_user

@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    if current_user.id == admin_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete yourself"
        )
    
    db_user = await crud.delete_user(db, admin_id)
    if db_user is None or db_user.type != "admin":
        raise HTTPException(status_code=404, detail="Admin not found")
    
    return {"message": "Admin deleted successfully"}

# Добавьте в конец файла admins.py

# Эндпоинт для получения всех пользователей (любого типа)
@router.get("/users/all", response_model=List[schemas.UserInDB])
async def get_all_users(
    skip: int = 0,
    limit: int = 100,
    user_type: str = None,  # Опциональный фильтр
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Получить всех пользователей системы (только для админов)"""
    if user_type:
        return await crud.get_users_by_type(db, user_type)
    return await crud.get_users(db, skip, limit)

# Эндпоинт для изменения роли пользователя
@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: str,
    role_data: dict,  # {"new_role": "teacher"}
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Изменить роль пользователя (только для админов)"""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_role = role_data.get("new_role")
    if new_role not in ["admin", "teacher", "apprentice", "moderator"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    # Обновляем роль
    update_data = {"type": new_role}
    
    # Если назначаем преподавателем, добавляем обязательные поля
    if new_role == "teacher":
        update_data.update({
            "hire_date": "01.01.2024",
            "department": "Общий отдел",
            "title": "Преподаватель",
            "teacher_hours_per_week": 20
        })
    
    updated_user = await crud.update_user(db, user_id, update_data)
    
    return {
        "message": f"User role changed to {new_role}",
        "user": updated_user
    }

# Эндпоинт для блокировки/активации пользователя
@router.put("/users/{user_id}/status")
async def change_user_status(
    user_id: str,
    status_data: dict,  # {"active": false}
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Изменить статус активности пользователя"""
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot change your own status")
    
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    active = status_data.get("active")
    if active is None:
        raise HTTPException(status_code=400, detail="Active field required")
    
    updated_user = await crud.update_user(db, user_id, {"active": active})
    
    return {
        "message": f"User {'activated' if active else 'deactivated'}",
        "user": updated_user
    }

# Эндпоинт для статистики системы
@router.get("/stats")
async def get_system_stats(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Получить статистику системы (только для админов)"""
    from sqlalchemy import func, select
    
    # Подсчет пользователей по типам
    result = await db.execute(
        select(models.User.type, func.count(models.User.id))
        .group_by(models.User.type)
    )
    user_stats = dict(result.all())
    
    # Подсчет активных тренировок
    result = await db.execute(
        select(func.count(models.Training.id))
    )
    training_count = result.scalar()
    
    return {
        "total_users": sum(user_stats.values()),
        "users_by_type": user_stats,
        "active_trainings": training_count,
        "system_health": "healthy"
    }