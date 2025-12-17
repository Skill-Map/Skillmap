from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID

import models
from dependencies import get_db

router = APIRouter(prefix="/api/courses", tags=["courses"])

# -------------------------------------------------
# Курсы
# -------------------------------------------------
@router.get("/", response_model=List[dict])
async def get_courses(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(models.Course).where(models.Course.is_public.is_(True))

    if category:
        query = query.where(models.Course.category == category)

    if search:
        term = f"%{search}%"
        query = query.where(
            models.Course.name.ilike(term)
            | models.Course.description.ilike(term)
            | models.Course.category_name.ilike(term)
        )

    result = await db.execute(query.order_by(models.Course.created_at))
    courses = result.scalars().all()

    return [
        {
            "id": str(c.id),
            "name": c.name,
            "description": c.description,
            "category": c.category,
            "category_name": c.category_name,
            "category_color": c.category_color,
            "icon": c.icon,
            "duration": c.duration,
            "is_public": c.is_public,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in courses
    ]

# -------------------------------------------------
# Категории
# -------------------------------------------------
@router.get("/categories", response_model=List[dict])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            models.Course.category,
            models.Course.category_name,
            models.Course.category_color,
            func.count(models.Course.id).label("course_count"),
        )
        .where(models.Course.is_public.is_(True))
        .group_by(
            models.Course.category,
            models.Course.category_name,
            models.Course.category_color,
        )
        .order_by(models.Course.category_name)
    )

    return [
        {
            "category": r.category,
            "category_name": r.category_name,
            "category_color": r.category_color,
            "course_count": r.course_count,
        }
        for r in result.all()
    ]

# -------------------------------------------------
# Один курс
# -------------------------------------------------
@router.get("/{course_id}", response_model=dict)
async def get_course(course_id: UUID, db: AsyncSession = Depends(get_db)):
    course = await db.scalar(
        select(models.Course).where(
            models.Course.id == course_id,
            models.Course.is_public.is_(True),
        )
    )

    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")

    return {
        "id": str(course.id),
        "name": course.name,
        "description": course.description,
        "category": course.category,
        "category_name": course.category_name,
        "category_color": course.category_color,
        "icon": course.icon,
        "duration": course.duration,
        "is_public": course.is_public,
        "created_at": course.created_at.isoformat() if course.created_at else None,
    }

# -------------------------------------------------
# Модули курса
# -------------------------------------------------
@router.get("/{course_id}/modules", response_model=List[dict])
async def get_course_modules(course_id: UUID, db: AsyncSession = Depends(get_db)):
    course_exists = await db.scalar(
        select(models.Course.id).where(
            models.Course.id == course_id,
            models.Course.is_public.is_(True),
        )
    )

    if not course_exists:
        raise HTTPException(status_code=404, detail="Курс не найден")

    result = await db.execute(
        select(models.CourseModule)
        .where(models.CourseModule.course_id == course_id)
        .order_by(models.CourseModule.order)
    )
    modules = result.scalars().all()

    return [
        {
            "id": str(m.id),
            "course_id": str(m.course_id),
            "order": m.order,
            "title": m.title,
            "description": m.description,
            "recommended_time": m.recommended_time,
        }
        for m in modules
    ]

# -------------------------------------------------
# Уроки модуля
# -------------------------------------------------
@router.get("/{course_id}/modules/{module_id}/lessons", response_model=List[dict])
async def get_module_lessons(
    course_id: UUID,
    module_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    course_exists = await db.scalar(
        select(models.Course.id).where(
            models.Course.id == course_id,
            models.Course.is_public.is_(True),
        )
    )
    if not course_exists:
        raise HTTPException(status_code=404, detail="Курс не найден")

    module = await db.scalar(
        select(models.CourseModule).where(
            models.CourseModule.id == module_id,
            models.CourseModule.course_id == course_id,
        )
    )
    if not module:
        raise HTTPException(status_code=404, detail="Модуль не найден")

    result = await db.execute(
        select(models.CourseLesson)
        .where(models.CourseLesson.module_id == module_id)
        .order_by(models.CourseLesson.order)
    )
    lessons = result.scalars().all()

    return [
        {
            "id": str(l.id),
            "module_id": str(l.module_id),
            "order": l.order,
            "title": l.title,
            "description": l.description,
        }
        for l in lessons
    ]

# -------------------------------------------------
# Полный курс
# -------------------------------------------------
@router.get("/{course_id}/full", response_model=dict)
async def get_full_course(course_id: UUID, db: AsyncSession = Depends(get_db)):
    course = await db.scalar(
        select(models.Course).where(
            models.Course.id == course_id,
            models.Course.is_public.is_(True),
        )
    )
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")

    modules_result = await db.execute(
        select(models.CourseModule)
        .where(models.CourseModule.course_id == course_id)
        .order_by(models.CourseModule.order)
    )
    modules = modules_result.scalars().all()
    modules_data = []

    for module in modules:
        lessons_result = await db.execute(
            select(models.CourseLesson)
            .where(models.CourseLesson.module_id == module.id)
            .order_by(models.CourseLesson.order)
        )
        lessons = lessons_result.scalars().all()

        modules_data.append(
            {
                "id": str(module.id),
                "order": module.order,
                "title": module.title,
                "description": module.description,
                "recommended_time": module.recommended_time,
                "lessons": [
                    {
                        "id": str(l.id),
                        "order": l.order,
                        "title": l.title,
                        "description": l.description,
                    }
                    for l in lessons
                ],
            }
        )

    return {
        "course": {
            "id": str(course.id),
            "name": course.name,
            "description": course.description,
            "category": course.category,
            "category_name": course.category_name,
            "category_color": course.category_color,
            "icon": course.icon,
            "duration": course.duration,
        },
        "modules": modules_data,
        "total_modules": len(modules_data),
        "total_lessons": sum(len(m["lessons"]) for m in modules_data),
    }
