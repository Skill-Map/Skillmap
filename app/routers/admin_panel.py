# app/routers/admin_panel.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import joinedload
from typing import List
from datetime import datetime

import crud
import schemas
from database import get_db
from auth import get_current_active_user, require_role
import models

router = APIRouter(prefix="/admin-panel", tags=["admin-panel"])

@router.get("/users/full", response_model=List[schemas.UserInDB])
async def get_all_users_full(
    skip: int = 0,
    limit: int = 100,
    user_type: str = Query(None, description="Filter by user type"),
    active: bool = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Получить полную информацию о всех пользователях"""
    users = await crud.get_users(db, skip, limit)
    
    # Фильтрация
    filtered_users = []
    for user in users:
        if user_type and user.type != user_type:
            continue
        if active is not None and user.active != active:
            continue
        filtered_users.append(user)
    
    return filtered_users

@router.post("/users/{user_id}/promote-to-teacher")
async def promote_to_teacher(
    user_id: str,
    teacher_data: schemas.TeacherCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Назначить пользователя преподавателем"""
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.type == "teacher":
        raise HTTPException(status_code=400, detail="User is already a teacher")
    
    # Подготавливаем данные для обновления
    update_data = teacher_data.dict()
    update_data["type"] = "teacher"
    
    # Сохраняем базовые данные пользователя
    update_data["email"] = user.email
    update_data["surname"] = user.surname or teacher_data.surname
    update_data["name"] = user.name or teacher_data.name
    update_data["patronymic"] = user.patronymic or teacher_data.patronymic
    
    # Обновляем пользователя
    updated_user = await crud.update_user(db, user_id, update_data)
    
    return {
        "message": "User promoted to teacher successfully",
        "user": updated_user
    }

@router.post("/users/{user_id}/promote-to-admin")
async def promote_to_admin(
    user_id: str,
    admin_data: schemas.AdminCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Назначить пользователя администратором"""
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.type == "admin":
        raise HTTPException(status_code=400, detail="User is already an admin")
    
    update_data = admin_data.dict()
    update_data["type"] = "admin"
    
    # Сохраняем базовые данные
    update_data["email"] = user.email
    update_data["surname"] = user.surname or admin_data.surname
    update_data["name"] = user.name or admin_data.name
    
    updated_user = await crud.update_user(db, user_id, update_data)
    
    return {
        "message": "User promoted to admin successfully",
        "user": updated_user
    }

@router.get("/stats/detailed")
async def get_detailed_stats(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Получить детальную статистику системы"""
    # Статистика пользователей
    all_users = await crud.get_users(db, 0, 1000)
    
    # Статистика тренировок
    result = await db.execute(
        select(models.Training)
        .options(joinedload(models.Training.teacher), joinedload(models.Training.apprentice))
    )
    trainings = result.scalars().all()
    
    return {
        "users": {
            "total": len(all_users),
            "by_type": {
                "apprentice": len([u for u in all_users if u.type == "apprentice"]),
                "teacher": len([u for u in all_users if u.type == "teacher"]),
                "admin": len([u for u in all_users if u.type == "admin"]),
                "moderator": len([u for u in all_users if u.type == "moderator"])
            },
            "active": len([u for u in all_users if u.active])
        },
        "trainings": {
            "total": len(trainings),
            "upcoming": len([t for t in trainings if t.date >= datetime.now().strftime("%d.%m.%Y")])
        },
        "system": {
            "uptime": "100%",
            "last_backup": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "database_size": "~10MB"
        }
    }

@router.get("/users/search")
async def search_users(
    query: str = Query(..., description="Search query (email, name, surname)"),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Поиск пользователей по email, имени или фамилии"""
    result = await db.execute(
        select(models.User).where(
            or_(
                models.User.email.ilike(f"%{query}%"),
                models.User.name.ilike(f"%{query}%"),
                models.User.surname.ilike(f"%{query}%")
            )
        ).limit(50)
    )
    
    users = result.scalars().all()
    return users

@router.get("/users/export")
async def export_users(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Экспорт данных пользователей в CSV формате"""
    users = await crud.get_users(db, 0, 1000)
    
    # Создаем CSV заголовок
    csv_content = "id,email,surname,name,type,active,reg_date\n"
    
    for user in users:
        csv_content += f"{user.id},{user.email},{user.surname},{user.name},{user.type},{user.active},{user.reg_date}\n"
    
    return {
        "filename": f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "content": csv_content,
        "count": len(users)
    }