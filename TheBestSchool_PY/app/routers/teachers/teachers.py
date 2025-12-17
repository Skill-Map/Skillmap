from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

import models
import schemas
import crud
from dependencies import get_db
from auth import get_current_user

router = APIRouter(
    prefix="/api/teachers",
    tags=["teachers"]
)

# ---------------------------
# Создание преподавателя
# ---------------------------
@router.post(
    "",
    response_model=schemas.TeacherResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_teacher(
    teacher: schemas.TeacherCreate,
    db: AsyncSession = Depends(get_db)
):
    db_user = await crud.get_user_by_email(db, teacher.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    return await crud.create_user(db, teacher)


# ---------------------------
# Список преподавателей
# ---------------------------
@router.get("", response_model=List[schemas.TeacherResponse])
async def get_teachers(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.type != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    return await crud.get_users_by_type(db, "teacher")


# ---------------------------
# Один преподаватель
# ---------------------------
@router.get("/{teacher_id}", response_model=schemas.TeacherResponse)
async def get_teacher(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    teacher = await crud.get_user(db, teacher_id)
    if not teacher or teacher.type != "teacher":
        raise HTTPException(status_code=404, detail="Teacher not found")

    return teacher


# ---------------------------
# Обновление профиля преподавателя
# ---------------------------
@router.put("", response_model=schemas.TeacherResponse)
async def update_teacher(
    payload: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.type != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can update profile")

    updated = await crud.update_user(db, current_user.id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Teacher not found")

    return updated


# ---------------------------
# Удаление преподавателя
# ---------------------------
@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.type != "admin" and current_user.id != teacher_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    teacher = await crud.get_user(db, teacher_id)
    if not teacher or teacher.type != "teacher":
        raise HTTPException(status_code=404, detail="Teacher not found")

    await crud.delete_user(db, teacher_id)
