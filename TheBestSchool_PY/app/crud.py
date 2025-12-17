from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
import models
import schemas
from auth import get_password_hash
from typing import List, Optional
import uuid
from auth import verify_password
from models import User

# CRUD для User
async def get_user(db: AsyncSession, user_id: str):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(
        select(models.User).where(models.User.email == email)
    )
    return result.scalar_one_or_none()

async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(
        select(models.User).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def create_user(db: AsyncSession, email: str, password: str, **extra):
    """
    Универсальный create_user.
    Принимает email, password и любые дополнительные поля через **extra
    """
    hashed_password = get_password_hash(password)
    payload = {"id": str(uuid.uuid4()), "email": email, "password": hashed_password}
    payload.update(extra)
    user = models.User(**payload)
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise
    await db.refresh(user)
    return user

async def update_user(db: AsyncSession, user_id: str, user_update: schemas.UserUpdate):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    db_user = result.scalar_one_or_none()
    
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    
    if "password" in update_data:
        update_data["password"] = get_password_hash(update_data["password"])
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def delete_user(db: AsyncSession, user_id: str):
    result = await db.execute(
        select(models.User).where(models.User.id == user_id)
    )
    db_user = result.scalar_one_or_none()
    
    if db_user:
        await db.delete(db_user)
        await db.commit()
    
    return db_user

# CRUD для специфичных типов
async def get_users_by_type(db: AsyncSession, user_type: str):
    result = await db.execute(
        select(models.User).where(models.User.type == user_type)
    )
    return result.scalars().all()

# CRUD для Training
async def create_training(db: AsyncSession, training: schemas.TrainingCreate, teacher_id: str, apprentice_id: str):
    db_training = models.Training(
        number_gym=training.number_gym,
        teacher_id=teacher_id,
        apprentice_id=apprentice_id,
        date=training.date,
        time_start=training.time_start
    )
    db.add(db_training)
    await db.commit()
    await db.refresh(db_training)
    return db_training

async def get_training(db: AsyncSession, training_id: int):
    result = await db.execute(
        select(models.Training)
        .options(joinedload(models.Training.teacher), joinedload(models.Training.apprentice))
        .where(models.Training.id == training_id)
    )
    return result.scalar_one_or_none()

async def get_trainings_by_teacher(db: AsyncSession, teacher_id: str):
    result = await db.execute(
        select(models.Training)
        .options(joinedload(models.Training.apprentice))
        .where(models.Training.teacher_id == teacher_id)
    )
    return result.scalars().all()

async def get_trainings_by_apprentice(db: AsyncSession, apprentice_id: str):
    result = await db.execute(
        select(models.Training)
        .options(joinedload(models.Training.teacher))
        .where(models.Training.apprentice_id == apprentice_id)
    )
    return result.scalars().all()

async def delete_training(db: AsyncSession, training_id: int):
    result = await db.execute(
        select(models.Training).where(models.Training.id == training_id)
    )
    db_training = result.scalar_one_or_none()
    
    if db_training:
        await db.delete(db_training)
        await db.commit()
    
    return db_training

# CRUD для TeacherSchedule
async def create_or_update_schedule(db: AsyncSession, teacher_id: str, schedule: schemas.TeacherScheduleCreate):
    result = await db.execute(
        select(models.TeacherSchedule).where(models.TeacherSchedule.id == teacher_id)
    )
    db_schedule = result.scalar_one_or_none()
    
    if db_schedule:
        # Обновляем существующее расписание
        for field, value in schedule.dict(exclude_unset=True).items():
            setattr(db_schedule, field, value)
    else:
        # Создаем новое расписание
        db_schedule = models.TeacherSchedule(
            id=teacher_id,
            **schedule.dict()
        )
        db.add(db_schedule)
    
    await db.commit()
    await db.refresh(db_schedule)
    return db_schedule

async def get_schedule(db: AsyncSession, teacher_id: str):
    result = await db.execute(
        select(models.TeacherSchedule)
        .options(joinedload(models.TeacherSchedule.teacher))
        .where(models.TeacherSchedule.id == teacher_id)
    )
    return result.scalar_one_or_none()

async def delete_schedule_day(db: AsyncSession, teacher_id: str, day: str):
    result = await db.execute(
        select(models.TeacherSchedule).where(models.TeacherSchedule.id == teacher_id)
    )
    db_schedule = result.scalar_one_or_none()
    
    if db_schedule:
        # Обнуляем поля для указанного дня
        day_field_start = f"{day.lower()}_start"
        day_field_end = f"{day.lower()}_end"
        
        if hasattr(db_schedule, day_field_start):
            setattr(db_schedule, day_field_start, None)
            setattr(db_schedule, day_field_end, None)
            
            await db.commit()
            await db.refresh(db_schedule)
    
    return db_schedule

# Добавьте в crud.py

async def get_all_trainings(db: AsyncSession):
    """Получить все тренировки"""
    result = await db.execute(
        select(models.Training)
        .options(joinedload(models.Training.teacher), joinedload(models.Training.apprentice))
    )
    return result.scalars().all()

async def get_users_by_type(db: AsyncSession, user_type: str):
    """Получить пользователей по типу (all для всех)"""
    if user_type == "all":
        result = await db.execute(
            select(models.User)
        )
    else:
        result = await db.execute(
            select(models.User).where(models.User.type == user_type)
        )
    return result.scalars().all()

async def authenticate_user(db: AsyncSession, username: str, password: str):
    result = await db.execute(
        select(User).where(User.email == username)
    )
    user = result.scalars().first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user