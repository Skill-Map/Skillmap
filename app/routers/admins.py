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