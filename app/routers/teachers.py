from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

import crud
import schemas
from database import get_db
from auth import get_current_user, require_role
import models

router = APIRouter(prefix="/trainer", tags=["teachers"])

@router.post("/", response_model=schemas.TeacherResponse)
async def create_teacher(
    teacher: schemas.TeacherCreate,
    db: AsyncSession = Depends(get_db)
):
    # Регистрация преподавателя не требует авторизации
    db_user = await crud.get_user_by_email(db, teacher.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(db, teacher)

@router.get("/", response_model=List[schemas.TeacherResponse])
async def read_teachers(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return await crud.get_users_by_type(db, "teacher")

@router.get("/{teacher_id}", response_model=schemas.TeacherResponse)
async def read_teacher(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_user = await crud.get_user(db, teacher_id)
    if db_user is None or db_user.type != "teacher":
        raise HTTPException(status_code=404, detail="Teacher not found")
    return db_user

@router.put("/", response_model=schemas.TeacherResponse)
async def update_teacher(
    teacher_update: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.type != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must be a teacher"
        )
    
    db_user = await crud.update_user(db, current_user.id, teacher_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return db_user

@router.delete("/{teacher_id}")
async def delete_teacher(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Удалять может только админ или сам преподаватель
    if current_user.type != "admin" and current_user.id != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db_user = await crud.delete_user(db, teacher_id)
    if db_user is None or db_user.type != "teacher":
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    return {"message": "Teacher deleted successfully"}