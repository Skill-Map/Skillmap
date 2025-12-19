# app/routers/teachers/teacher.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import uuid
from sqlalchemy import distinct
import models
import schemas
import crud
from dependencies import get_db
from auth import get_current_user, require_role

router = APIRouter(
    prefix="/api/teachers",
    tags=["admin-teachers"]
)

# ---------------------------
# Создание преподавателя (только для админов)
# ---------------------------
@router.post(
    "",
    response_model=schemas.TeacherResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_teacher(
    teacher: schemas.TeacherCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Создать нового преподавателя (админ)"""
    # Проверяем, есть ли уже пользователь с таким email
    db_user = await crud.get_user_by_email(db, teacher.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    # Создаем пользователя как преподавателя
    return await crud.create_user(db, teacher, user_type="teacher")


# ---------------------------
# Список всех преподавателей (только для админов)
# ---------------------------
@router.get("", response_model=List[schemas.TeacherResponse])
async def get_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Получить список всех преподавателей (админ)"""
    teachers = await crud.get_users_by_type(db, "teacher", skip, limit)
    
    # Фильтрация по поиску
    if search:
        search_lower = search.lower()
        teachers = [
            t for t in teachers 
            if (t.name and search_lower in t.name.lower()) or
               (t.surname and search_lower in t.surname.lower()) or
               (t.email and search_lower in t.email.lower()) or
               (t.department and search_lower in t.department.lower())
        ]
    
    # Фильтрация по активности
    if active_only:
        teachers = [t for t in teachers if t.active]
    
    return teachers


# ---------------------------
# Получить одного преподавателя по ID (админ)
# ---------------------------
@router.get("/{teacher_id}", response_model=schemas.TeacherResponse)
async def get_teacher(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Получить информацию о преподавателе по ID (админ)"""
    teacher = await crud.get_user(db, teacher_id)
    if not teacher or teacher.type != "teacher":
        raise HTTPException(status_code=404, detail="Преподаватель не найден")

    return teacher


# ---------------------------
# Обновление профиля преподавателя (сам преподаватель или админ)
# ---------------------------
@router.put("/{teacher_id}", response_model=schemas.TeacherResponse)
async def update_teacher(
    teacher_id: str,
    payload: schemas.UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Обновить профиль преподавателя"""
    # Проверяем права доступа
    if current_user.type != "admin" and current_user.id != teacher_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    
    # Проверяем, что преподаватель существует
    teacher = await crud.get_user(db, teacher_id)
    if not teacher or teacher.type != "teacher":
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    
    # Обновляем данные
    updated = await crud.update_user(db, teacher_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Преподаватель не найден")

    return updated


# ---------------------------
# Удаление преподавателя (админ)
# ---------------------------
@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Удалить преподавателя (админ)"""
    teacher = await crud.get_user(db, teacher_id)
    if not teacher or teacher.type != "teacher":
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    
    # Нельзя удалить самого себя
    if current_user.id == teacher_id:
        raise HTTPException(status_code=400, detail="Нельзя удалить свой аккаунт")

    await crud.delete_user(db, teacher_id)


# ---------------------------
# Статистика по преподавателю (админ)
# ---------------------------
@router.get("/{teacher_id}/stats")
async def get_teacher_stats_admin(
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Получить статистику по преподавателю (админ)"""
    teacher = await crud.get_user(db, teacher_id)
    if not teacher or teacher.type != "teacher":
        raise HTTPException(status_code=404, detail="Преподаватель не найден")
    
    # Получаем количество назначенных заданий
    from sqlalchemy import func
    assignments_count_result = await db.execute(
        select(func.count(models.LessonAssignment.id))
        .where(models.LessonAssignment.assigned_by == teacher_id)
    )
    assignments_count = assignments_count_result.scalar() or 0
    
    # Получаем количество студентов, которым назначены задания
    students_count_result = await db.execute(
        select(func.count(distinct(models.LessonAssignment.user_id)))
        .where(models.LessonAssignment.assigned_by == teacher_id)
    )
    students_count = students_count_result.scalar() or 0
    
    # Получаем количество курсов, где есть назначения
    courses_count_result = await db.execute(
        select(func.count(distinct(models.CourseModule.course_id)))
        .select_from(models.LessonAssignment)
        .join(models.CourseLesson, models.LessonAssignment.lesson_id == models.CourseLesson.id)
        .join(models.CourseModule, models.CourseLesson.module_id == models.CourseModule.id)
        .where(models.LessonAssignment.assigned_by == teacher_id)
    )
    courses_count = courses_count_result.scalar() or 0
    
    return {
        "teacher_id": teacher_id,
        "name": f"{teacher.surname} {teacher.name}",
        "email": teacher.email,
        "stats": {
            "courses": courses_count,
            "students": students_count,
            "assignments": assignments_count,
            "avg_rating": teacher.rating or 0,
        },
        "info": {
            "department": teacher.department or "",
            "title": teacher.title or "",
            "hire_date": teacher.hire_date or "",
            "active": teacher.active,
        }
    }