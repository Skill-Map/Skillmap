from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

import crud
import schemas
from database import get_db
from auth import get_current_active_user
import models

router = APIRouter(prefix="/training", tags=["training"])

@router.post("/{trainer_id}/{apprentice_id}", response_model=schemas.TrainingResponse)
async def create_training(
    trainer_id: str,
    apprentice_id: str,
    number_gym: int = Query(...),
    date: str = Query(...),  # dd.MM.yyyy
    time_start: str = Query(...),  # HH:mm
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Проверяем, что пользователи существуют и имеют правильные типы
    teacher = await crud.get_user(db, trainer_id)
    if not teacher or teacher.type != "teacher":
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    apprentice = await crud.get_user(db, apprentice_id)
    if not apprentice or apprentice.type != "apprentice":
        raise HTTPException(status_code=404, detail="Apprentice not found")
    
    # Проверяем права: только админ, учитель или сам ученик
    if current_user.type not in ["admin", "teacher"] and current_user.id != apprentice_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Создаем тренировку
    training_data = schemas.TrainingCreate(
        number_gym=number_gym,
        date=date,
        time_start=time_start
    )
    
    return await crud.create_training(db, training_data, trainer_id, apprentice_id)

@router.get("/{trainer_id}/{apprentice_id}")
async def get_available_time(
    trainer_id: str,
    apprentice_id: str,
    number_gym: int = Query(None),
    date: str = Query(None),  # dd.MM.yyyy
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Здесь должна быть логика проверки доступного времени
    # Пока возвращаем заглушку
    return {
        "available_times": ["09:00", "10:00", "11:00", "14:00", "15:00"],
        "trainer_id": trainer_id,
        "apprentice_id": apprentice_id,
        "date": date
    }

@router.get("/{training_id}", response_model=schemas.TrainingResponse)
async def read_training(
    training_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    training = await crud.get_training(db, training_id)
    if training is None:
        raise HTTPException(status_code=404, detail="Training not found")
    
    # Проверяем права доступа
    if current_user.type != "admin":
        if current_user.id not in [training.teacher_id, training.apprentice_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    return training

@router.get("/trainer/{trainer_id}", response_model=List[schemas.TrainingResponse])
async def read_trainer_trainings(
    trainer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Проверяем права доступа
    if current_user.type != "admin" and current_user.id != trainer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await crud.get_trainings_by_teacher(db, trainer_id)

@router.get("/apprentice/{apprentice_id}", response_model=List[schemas.TrainingResponse])
async def read_apprentice_trainings(
    apprentice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    # Проверяем права доступа
    if current_user.type != "admin" and current_user.id != apprentice_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return await crud.get_trainings_by_apprentice(db, apprentice_id)

@router.delete("/{training_id}")
async def delete_training(
    training_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    training = await crud.get_training(db, training_id)
    if training is None:
        raise HTTPException(status_code=404, detail="Training not found")
    
    # Проверяем права: админ, учитель или ученик этой тренировки
    if current_user.type != "admin":
        if current_user.id not in [training.teacher_id, training.apprentice_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    
    result = await crud.delete_training(db, training_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Training not found")
    
    return {"message": "Training deleted successfully"}