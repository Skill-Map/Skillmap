from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

import crud
import schemas
from database import get_db
from auth import get_current_active_user, require_role
import models

router = APIRouter(prefix="/moderator", tags=["moderators"])

@router.post("/", response_model=schemas.ModeratorResponse)
async def create_moderator(
    moderator: schemas.ModeratorCreate,
    db: AsyncSession = Depends(get_db)
):
    # Регистрация модератора не требует авторизации
    db_user = await crud.get_user_by_email(db, moderator.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(db, moderator)

@router.get("/", response_model=List[schemas.ModeratorResponse])
async def read_moderators(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.type not in ["admin", "moderator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return await crud.get_users_by_type(db, "moderator")

@router.get("/{moderator_id}", response_model=schemas.ModeratorResponse)
async def read_moderator(
    moderator_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.type not in ["admin", "moderator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    db_user = await crud.get_user(db, moderator_id)
    if db_user is None or db_user.type != "moderator":
        raise HTTPException(status_code=404, detail="Moderator not found")
    return db_user

@router.put("/", response_model=schemas.ModeratorResponse)
async def update_moderator(
    moderator_update: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.type != "moderator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Must be a moderator"
        )
    
    db_user = await crud.update_user(db, current_user.id, moderator_update)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Moderator not found")
    return db_user

@router.delete("/{moderator_id}")
async def delete_moderator(
    moderator_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    if current_user.type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can delete moderators"
        )
    
    db_user = await crud.delete_user(db, moderator_id)
    if db_user is None or db_user.type != "moderator":
        raise HTTPException(status_code=404, detail="Moderator not found")
    
    return {"message": "Moderator deleted successfully"}