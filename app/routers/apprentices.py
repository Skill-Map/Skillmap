from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

import crud
import schemas
from database import get_db
from auth import get_current_user, require_role
import models

router = APIRouter(prefix="/apprentice", tags=["apprentices"])

@router.post("/", response_model=schemas.ApprenticeResponse)
async def create_apprentice(
    apprentice: schemas.ApprenticeCreate,
    db: AsyncSession = Depends(get_db)
):
    # Регистрация ученика не требует авторизации
    db_user = await crud.get_user_by_email(db, apprentice.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Проверяем существование преподавателя-советника
    if apprentice.advisor_user_id:
        advisor = await crud.get_user(db, apprentice.advisor_user_id)
        if not advisor or advisor.type != "teacher":
            raise HTTPException(
                status_code=400,
                detail="Advisor must be a teacher"
            )
    
    return await crud.create_user(db, apprentice)

@router.get("/", response_model=List[schemas.ApprenticeResponse])
async def read_apprentices(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return await crud.get_users_by_type(db, "apprentice")

@router.get("/{apprentice_id}", response_model=schemas.ApprenticeResponse)
async def read_apprentice(
    apprentice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_user = await crud.get_user(db, apprentice_id)
    if db_user is None or db_user.type != "apprentice":
        raise HTTPException(status_code=404, detail="Apprentice not found")
    
    # Проверка прав доступа
    if current_user.type not in ["admin", "teacher"] and current_user.id != apprentice_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return db_user

@router.put("/", response_model=schemas.ApprenticeResponse)
async def update_apprentice(
    apprentice_update: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.type != "apprentice":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must be an apprentice"
        )
    
    db_user = await crud.update_user(db, current_user.id, apprentice_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Apprentice not found")
    return db_user

@router.delete("/{apprentice_id}")
async def delete_apprentice(
    apprentice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Удалять может только админ или сам ученик
    if current_user.type != "admin" and current_user.id != apprentice_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db_user = await crud.delete_user(db, apprentice_id)
    if db_user is None or db_user.type != "apprentice":
        raise HTTPException(status_code=404, detail="Apprentice not found")
    
    return {"message": "Apprentice deleted successfully"}