from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
import models
import schemas
from auth import get_password_hash
from typing import List, Optional
import uuid

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

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    
    # Создаем базового пользователя
    db_user = models.User(
        id=str(uuid.uuid4()),
        email=user.email,
        surname=user.surname,
        name=user.name,
        patronymic=user.patronymic,
        password=hashed_password,
        type=user.type,
        active=user.active
    )
    
    # Заполняем специфичные поля в зависимости от типа
    if isinstance(user, schemas.AdminCreate):
        db_user.super_permissions = user.super_permissions
        db_user.can_manage_roles = user.can_manage_roles
        db_user.can_manage_billing = user.can_manage_billing
        db_user.can_impersonate = user.can_impersonate
    elif isinstance(user, schemas.ApprenticeCreate):
        db_user.status = user.status
        db_user.track_id = user.track_id
        db_user.group_code = user.group_code
        db_user.advisor_user_id = user.advisor_user_id
        db_user.hours_per_week = user.hours_per_week
        db_user.progress_percent = user.progress_percent
        db_user.credits_earned = user.credits_earned
        db_user.enrollment_date = user.enrollment_date
        db_user.expected_graduation = user.expected_graduation
    elif isinstance(user, schemas.TeacherCreate):
        db_user.hire_date = user.hire_date
        db_user.department = user.department
        db_user.title = user.title
        db_user.bio = user.bio
        db_user.specialties = user.specialties
        db_user.office_hours = user.office_hours
        db_user.teacher_hours_per_week = user.teacher_hours_per_week
        db_user.rating = user.rating
    elif isinstance(user, schemas.ModeratorCreate):
        db_user.assigned_scope = user.assigned_scope
        db_user.permissions_scope = user.permissions_scope
        db_user.on_call = user.on_call
        db_user.warnings_issued = user.warnings_issued
        db_user.users_banned = user.users_banned
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

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