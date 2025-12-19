from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.params import Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json

from database import get_db
from auth import require_role
import models

router = APIRouter(prefix="/api/admin", tags=["admin"])

# ============ ПОМОЩНИКИ ============
async def _get_user_or_404(db: AsyncSession, user_id: str) -> models.User:
    """Получить пользователя по ID или вернуть 404"""
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

async def _get_course_or_404(db: AsyncSession, course_id: uuid.UUID) -> models.Course:
    """Получить курс по ID или вернуть 404"""
    result = await db.execute(
        select(models.Course)
        .where(models.Course.id == course_id)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    return course

def _serialize_user(user: models.User) -> Dict[str, Any]:
    """Сериализация пользователя со всеми полями"""
    # Базовые поля
    data = {
        "id": user.id,
        "email": user.email,
        "surname": user.surname or "",
        "name": user.name or "",
        "patronymic": user.patronymic or "",
        "phone": user.phone or "",
        "type": user.type,
        "active": bool(user.active),
        "reg_date": user.reg_date.isoformat() if user.reg_date else None,
        "up_date": user.up_date,
    }
    
    # Поля по типам
    if user.type == "admin":
        data.update({
            "super_permissions": user.super_permissions or False,
            "can_manage_roles": user.can_manage_roles or False,
            "can_manage_billing": user.can_manage_billing or False,
            "can_impersonate": user.can_impersonate or False,
            "last_audit_action": user.last_audit_action.isoformat() if user.last_audit_action else None,
        })
    
    elif user.type == "apprentice":
        data.update({
            "status": user.status or "active",
            "track_id": user.track_id or "",
            "group_code": user.group_code or "",
            "hours_per_week": user.hours_per_week or 0,
            "progress_percent": float(user.progress_percent or 0),
            "credits_earned": user.credits_earned or 0,
            "enrollment_date": user.enrollment_date or "",
            "expected_graduation": user.expected_graduation or "",
        })
    
    elif user.type == "teacher":
        data.update({
            "hire_date": user.hire_date or "",
            "department": user.department or "",
            "title": user.title or "",
            "bio": user.bio or "",
            "specialties": user.specialties or [],
            "office_hours": user.office_hours or "",
            "teacher_hours_per_week": user.teacher_hours_per_week or 0,
            "rating": float(user.rating or 0),
        })
    
    elif user.type == "moderator":
        data.update({
            "assigned_scope": user.assigned_scope or "",
            "permissions_scope": user.permissions_scope or "",
            "on_call": bool(user.on_call or False),
            "warnings_issued": user.warnings_issued or 0,
            "users_banned": user.users_banned or 0,
            "last_action_at": user.last_action_at.isoformat() if user.last_action_at else None,
        })
    
    return data

def _serialize_course(course: models.Course, student_count: int = 0) -> Dict[str, Any]:
    """Сериализация курса"""
    return {
        "id": str(course.id),
        "name": course.name or "",
        "description": course.description or "",
        "category": course.category or "",
        "category_name": course.category_name or "",
        "category_color": course.category_color or "#1A535C",
        "icon": course.icon or "",
        "duration": course.duration or "",
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "is_public": bool(course.is_public),
        "student_count": student_count,
    }

# ============ ЭНДПОИНТЫ ПОЛЬЗОВАТЕЛЕЙ ============
@router.get("/users", response_model=List[Dict[str, Any]])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    type_filter: Optional[str] = Query(None, alias="type"),
    active_only: Optional[bool] = Query(None, alias="active"),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """
    Получить список пользователей с фильтрацией
    - type: фильтр по роли (admin, teacher, apprentice, moderator)
    - active: фильтр по активности
    - search: поиск по email, имени, фамилии, телефону
    """
    query = select(models.User).order_by(models.User.reg_date.desc())
    
    # Фильтры
    filters = []
    if type_filter:
        filters.append(models.User.type == type_filter)
    if active_only is not None:
        filters.append(models.User.active == active_only)
    if search:
        search_term = f"%{search}%"
        filters.append(or_(
            models.User.email.ilike(search_term),
            models.User.name.ilike(search_term),
            models.User.surname.ilike(search_term),
            models.User.patronymic.ilike(search_term),
            models.User.phone.ilike(search_term),
        ))
    
    if filters:
        query = query.where(and_(*filters))
    
    # Пагинация
    query = query.offset(skip).limit(limit)
    
    # Выполнение запроса
    result = await db.execute(query)
    users = result.scalars().all()
    
    return [_serialize_user(user) for user in users]

@router.get("/users/{user_id}", response_model=Dict[str, Any])
async def get_user_details(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Получить детальную информацию о пользователе"""
    user = await _get_user_or_404(db, user_id)
    return _serialize_user(user)

@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Изменить роль пользователя"""
    new_role = payload.get("new_role")
    
    if not new_role or new_role not in ("admin", "teacher", "apprentice", "moderator"):
        raise HTTPException(
            status_code=400,
            detail="Некорректная роль. Допустимые значения: admin, teacher, apprentice, moderator"
        )
    
    user = await _get_user_or_404(db, user_id)
    
    # Нельзя изменить роль самому себе (опционально)
    # current_user = get_current_user()
    # if str(user.id) == str(current_user.id):
    #     raise HTTPException(status_code=400, detail="Нельзя изменить свою роль")
    
    if user.type == new_role:
        return {"message": "Роль не изменена", "user_id": user.id, "role": user.type}
    
    # Автоматическое заполнение полей при смене роли
    user.type = new_role
    now_date = datetime.now().strftime("%d.%m.%Y")
    
    if new_role == "teacher" and not user.hire_date:
        user.hire_date = now_date
        user.department = user.department or "Общий отдел"
        user.title = user.title or "Преподаватель"
    
    elif new_role == "apprentice" and not user.enrollment_date:
        user.enrollment_date = now_date
        user.status = user.status or "active"
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return {
        "message": "Роль успешно обновлена",
        "user_id": user.id,
        "new_role": user.type,
        "full_name": f"{user.surname} {user.name}"
    }

@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Активировать/деактивировать пользователя"""
    active = payload.get("active")
    
    if active is None:
        raise HTTPException(status_code=400, detail="Поле 'active' обязательно")
    
    user = await _get_user_or_404(db, user_id)
    
    # Нельзя деактивировать самого себя (опционально)
    # current_user = get_current_user()
    # if str(user.id) == str(current_user.id) and not active:
    #     raise HTTPException(status_code=400, detail="Нельзя деактивировать свой аккаунт")
    
    if bool(user.active) == bool(active):
        return {
            "message": "Статус не изменен",
            "user_id": user.id,
            "active": user.active
        }
    
    user.active = bool(active)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    action = "активирован" if user.active else "деактивирован"
    return {
        "message": f"Пользователь {action}",
        "user_id": user.id,
        "active": user.active,
        "full_name": f"{user.surname} {user.name}"
    }

@router.post("/users/{user_id}/enroll")
async def enroll_user_to_course(
    user_id: str,
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Зачислить пользователя на курс"""
    user = await _get_user_or_404(db, user_id)
    course_name = (payload.get("course_name") or "").strip()
    
    if not course_name:
        raise HTTPException(status_code=400, detail="Название курса обязательно")
    
    # Поиск существующего курса
    course_result = await db.execute(
        select(models.Course).where(models.Course.name == course_name)
    )
    course = course_result.scalar_one_or_none()
    
    # Создание нового курса, если не найден
    if not course:
        category = payload.get("category") or "it"
        category_name_map = {
            "frontend": "Frontend-разработка",
            "backend": "Backend-разработка",
            "qa": "Тестирование (QA)",
            "devops": "DevOps",
            "ml": "Машинное обучение",
            "analytics": "Аналитика",
            "it": "IT"
        }
        
        course = models.Course(
            name=course_name,
            description=payload.get("description") or f"Курс '{course_name}'",
            category=category,
            category_name=category_name_map.get(category, "IT"),
            category_color=payload.get("category_color") or "#1A535C"
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)
    
    # Проверка, уже ли зачислен
    existing_enrollment = await db.execute(
        select(models.UserCourseProgress).where(
            models.UserCourseProgress.user_id == user.id,
            models.UserCourseProgress.course_id == course.id
        )
    )
    
    if existing_enrollment.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Пользователь уже зачислен на курс '{course_name}'"
        )
    
    # Создание записи о прогрессе
    progress = models.UserCourseProgress(
        id=str(uuid.uuid4()),
        user_id=user.id,
        course_id=course.id,
        current_module_id=None,
        completed_lessons=[],
        progress_percent=0.0
    )
    
    db.add(progress)
    await db.commit()
    await db.refresh(progress)
    
    return {
        "message": "Пользователь успешно зачислен на курс",
        "user_id": user.id,
        "course_id": str(course.id),
        "course_name": course.name,
        "progress_id": progress.id,
        "enrollment_date": datetime.now().isoformat()
    }

# ============ ЭНДПОИНТЫ КУРСОВ ============
@router.get("/courses", response_model=List[Dict[str, Any]])
async def get_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Получить список курсов"""
    query = select(models.Course).order_by(models.Course.created_at.desc())
    
    if category:
        query = query.where(models.Course.category == category)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    courses = result.scalars().all()
    
    # Получение количества студентов для каждого курса
    serialized_courses = []
    for course in courses:
        # Подсчет студентов на курсе
        count_result = await db.execute(
            select(func.count(models.UserCourseProgress.id))
            .where(models.UserCourseProgress.course_id == course.id)
        )
        student_count = count_result.scalar() or 0
        
        serialized_courses.append(_serialize_course(course, student_count))
    
    return serialized_courses

@router.get("/courses/{course_id}", response_model=Dict[str, Any])
async def get_course_details(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Получить детальную информацию о курсе"""
    course = await _get_course_or_404(db, course_id)
    
    # Подсчет студентов
    count_result = await db.execute(
        select(func.count(models.UserCourseProgress.id))
        .where(models.UserCourseProgress.course_id == course.id)
    )
    student_count = count_result.scalar() or 0
    
    # Загрузка связанных данных (модули, уроки)
    course_with_modules = await db.execute(
        select(models.Course)
        .options(selectinload(models.Course.modules).selectinload(models.CourseModule.lessons))
        .where(models.Course.id == course.id)
    )
    course = course_with_modules.scalar_one()
    
    course_data = _serialize_course(course, student_count)
    
    # Добавление информации о модулях и уроках
    modules_data = []
    for module in course.modules:
        module_data = {
            "id": str(module.id),
            "title": module.title or "",
            "description": module.description or "",
            "order": module.order or 0,
            "lesson_count": len(module.lessons) if module.lessons else 0,
            "lessons": [
                {
                    "id": str(lesson.id),
                    "title": lesson.title or "",
                    "order": lesson.order or 0,
                    "has_pptx": bool(lesson.pptx_url),
                    "has_homework": bool(lesson.homework_url)
                }
                for lesson in module.lessons
            ] if module.lessons else []
        }
        modules_data.append(module_data)
    
    course_data["modules"] = modules_data
    course_data["module_count"] = len(modules_data)
    
    return course_data

@router.post("/courses", status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Создать новый курс"""
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Название курса обязательно")
    
    # Проверка на дубликат
    existing = await db.execute(
        select(models.Course).where(models.Course.name == name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Курс с названием '{name}' уже существует"
        )
    
    # Категория и её название
    category = payload.get("category") or "it"
    category_map = {
        "frontend": ("Frontend-разработка", "#4F46E5"),
        "backend": ("Backend-разработка", "#059669"),
        "qa": ("Тестирование (QA)", "#DC2626"),
        "devops": ("DevOps", "#7C3AED"),
        "ml": ("Машинное обучение", "#DB2777"),
        "analytics": ("Аналитика", "#0891B2"),
        "it": ("IT", "#1A535C")
    }
    
    category_name, category_color = category_map.get(category, ("IT", "#1A535C"))
    
    # Создание курса
    course = models.Course(
        name=name,
        description=payload.get("description") or f"Курс '{name}'",
        category=category,
        category_name=payload.get("category_name") or category_name,
        category_color=payload.get("category_color") or category_color,
        icon=payload.get("icon") or "",
        duration=payload.get("duration") or "",
        is_public=bool(payload.get("is_public", True))
    )
    
    db.add(course)
    await db.commit()
    await db.refresh(course)
    
    return {
        "message": "Курс успешно создан",
        "course": _serialize_course(course, 0)
    }

@router.put("/courses/{course_id}")
async def update_course(
    course_id: uuid.UUID,
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Обновить курс"""
    course = await _get_course_or_404(db, course_id)
    
    # Проверка уникальности имени (если изменилось)
    new_name = payload.get("name")
    if new_name and new_name != course.name:
        existing = await db.execute(
            select(models.Course).where(
                models.Course.name == new_name,
                models.Course.id != course.id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Курс с названием '{new_name}' уже существует"
            )
        course.name = new_name
    
    # Обновление остальных полей
    if "description" in payload:
        course.description = payload["description"]
    if "category" in payload:
        course.category = payload["category"]
    if "category_name" in payload:
        course.category_name = payload["category_name"]
    if "category_color" in payload:
        course.category_color = payload["category_color"]
    if "icon" in payload:
        course.icon = payload["icon"]
    if "duration" in payload:
        course.duration = payload["duration"]
    if "is_public" in payload:
        course.is_public = bool(payload["is_public"])
    
    course.updated_at = datetime.now()
    
    db.add(course)
    await db.commit()
    await db.refresh(course)
    
    # Подсчет студентов для ответа
    count_result = await db.execute(
        select(func.count(models.UserCourseProgress.id))
        .where(models.UserCourseProgress.course_id == course.id)
    )
    student_count = count_result.scalar() or 0
    
    return {
        "message": "Курс успешно обновлен",
        "course": _serialize_course(course, student_count)
    }

@router.delete("/courses/{course_id}")
async def delete_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Удалить курс"""
    course = await _get_course_or_404(db, course_id)
    
    # Проверка, есть ли студенты на курсе
    count_result = await db.execute(
        select(func.count(models.UserCourseProgress.id))
        .where(models.UserCourseProgress.course_id == course.id)
    )
    student_count = count_result.scalar() or 0
    
    if student_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя удалить курс с {student_count} студентами"
        )
    
    await db.delete(course)
    await db.commit()
    
    return {
        "message": "Курс успешно удален",
        "course_id": str(course_id),
        "course_name": course.name
    }

# ============ СТАТИСТИКА ============
@router.get("/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Получить статистику для админ-панели"""
    
    # Общее количество пользователей по типам
    user_type_counts = {}
    for user_type in ["admin", "teacher", "apprentice", "moderator"]:
        count_result = await db.execute(
            select(func.count(models.User.id))
            .where(models.User.type == user_type)
        )
        user_type_counts[user_type] = count_result.scalar() or 0
    
    # Активные пользователи
    active_users_result = await db.execute(
        select(func.count(models.User.id))
        .where(models.User.active == True)
    )
    active_users = active_users_result.scalar() or 0
    
    # Всего курсов
    total_courses_result = await db.execute(
        select(func.count(models.Course.id))
    )
    total_courses = total_courses_result.scalar() or 0
    
    # Публичные курсы
    public_courses_result = await db.execute(
        select(func.count(models.Course.id))
        .where(models.Course.is_public == True)
    )
    public_courses = public_courses_result.scalar() or 0
    
    # Всего зачислений
    total_enrollments_result = await db.execute(
        select(func.count(models.UserCourseProgress.id))
    )
    total_enrollments = total_enrollments_result.scalar() or 0
    
    # Курсы по категориям
    category_counts = {}
    categories_result = await db.execute(
        select(models.Course.category, func.count(models.Course.id))
        .group_by(models.Course.category)
    )
    for category, count in categories_result.all():
        category_counts[category] = count
    
    return {
        "users": {
            "total": sum(user_type_counts.values()),
            "by_type": user_type_counts,
            "active": active_users,
            "inactive": sum(user_type_counts.values()) - active_users
        },
        "courses": {
            "total": total_courses,
            "public": public_courses,
            "private": total_courses - public_courses,
            "by_category": category_counts
        },
        "enrollments": {
            "total": total_enrollments,
            "average_per_course": round(total_enrollments / total_courses, 2) if total_courses > 0 else 0
        }
    }
    
@router.get("/users/{user_id}/courses-as-student")
async def get_user_courses_as_student(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Получить курсы, на которые зачислен пользователь как студент"""
    user = await _get_user_or_404(db, user_id)
    
    # Получаем все записи о прогрессе пользователя по курсам
    result = await db.execute(
        select(models.UserCourseProgress, models.Course)
        .join(models.Course, models.UserCourseProgress.course_id == models.Course.id)
        .where(models.UserCourseProgress.user_id == user.id)
        .order_by(models.UserCourseProgress.started_at.desc())
    )
    
    enrollments = result.all()
    
    courses = []
    for progress, course in enrollments:
        courses.append({
            "course_id": str(course.id),
            "course_name": course.name,
            "description": course.description,
            "category": course.category_name,
            "progress_percent": float(progress.progress_percent or 0),
            "started_at": progress.started_at.isoformat() if progress.started_at else None,
            "last_accessed": progress.last_accessed.isoformat() if progress.last_accessed else None,
            "completed_lessons_count": len(progress.completed_lessons or []),
        })
    
    return {
        "user_id": user.id,
        "user_name": f"{user.surname} {user.name}",
        "user_type": user.type,
        "total_courses": len(courses),
        "courses": courses
    }

@router.get("/users/{user_id}/courses-as-teacher")
async def get_user_courses_as_teacher(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Получить курсы, которые ведет пользователь как преподаватель"""
    user = await _get_user_or_404(db, user_id)
    
    # Получаем курсы, где пользователь является преподавателем
    # (предполагаем, что в модели Course есть поле teacher_id)
    result = await db.execute(
        select(models.Course)
        .where(models.Course.teacher_id == user.id)
        .order_by(models.Course.created_at.desc())
    )
    
    courses = result.scalars().all()
    
    formatted_courses = []
    for course in courses:
        # Подсчитываем количество студентов на курсе
        student_count_result = await db.execute(
            select(func.count(models.UserCourseProgress.id))
            .where(models.UserCourseProgress.course_id == course.id)
        )
        student_count = student_count_result.scalar() or 0
        
        # Подсчитываем количество модулей
        module_count_result = await db.execute(
            select(func.count(models.CourseModule.id))
            .where(models.CourseModule.course_id == course.id)
        )
        module_count = module_count_result.scalar() or 0
        
        formatted_courses.append({
            "course_id": str(course.id),
            "course_name": course.name,
            "description": course.description,
            "category": course.category_name,
            "created_at": course.created_at.isoformat() if course.created_at else None,
            "student_count": student_count,
            "module_count": module_count,
            "is_public": bool(course.is_public),
        })
    
    return {
        "user_id": user.id,
        "user_name": f"{user.surname} {user.name}",
        "user_type": user.type,
        "total_courses": len(formatted_courses),
        "courses": formatted_courses
    }
    
# ============ НАЗНАЧЕНИЕ ПРЕПОДАВАТЕЛЕЙ НА КУРСЫ ============

@router.get("/courses/{course_id}/teachers")
async def get_course_teachers(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Получить преподавателей назначенных на курс"""
    result = await db.execute(
        select(models.TeacherCourseAssignment, models.User)
        .join(models.User, models.TeacherCourseAssignment.teacher_id == models.User.id)
        .where(
            models.TeacherCourseAssignment.course_id == course_id,
            models.TeacherCourseAssignment.status == "active"
        )
        .order_by(models.User.surname, models.User.name)
    )
    
    assignments = result.all()
    
    teachers = []
    for assignment, teacher in assignments:
        teachers.append({
            "assignment_id": str(assignment.id),
            "teacher_id": str(teacher.id),
            "teacher_name": f"{teacher.surname} {teacher.name}",
            "teacher_email": teacher.email,
            "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
            "assigned_by": str(assignment.assigned_by)
        })
    
    return teachers

@router.post("/courses/{course_id}/assign-teacher")
async def assign_teacher_to_course(
    course_id: uuid.UUID,
    payload: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("admin"))
):
    """Назначить преподавателя на курс"""
    teacher_id = payload.get("teacher_id")
    
    if not teacher_id:
        raise HTTPException(status_code=400, detail="Необходимо указать teacher_id")
    
    # Проверяем существование курса
    course = await _get_course_or_404(db, course_id)
    
    # Проверяем существование преподавателя
    teacher_result = await db.execute(
        select(models.User).where(
            models.User.id == teacher_id,
            models.User.type == "teacher"
        )
    )
    teacher = teacher_result.scalar_one_or_none()
    
    if not teacher:
        raise HTTPException(status_code=404, detail="Преподаватель не найден или не является учителем")
    
    # Проверяем, не назначен ли уже преподаватель на этот курс
    existing_result = await db.execute(
        select(models.TeacherCourseAssignment).where(
            models.TeacherCourseAssignment.course_id == course.id,
            models.TeacherCourseAssignment.teacher_id == teacher.id,
            models.TeacherCourseAssignment.status == "active"
        )
    )
    
    if existing_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Преподаватель уже назначен на этот курс")
    
    # Создаем назначение
    assignment = models.TeacherCourseAssignment(
        teacher_id=teacher.id,
        course_id=course.id,
        assigned_by=current_user.id,
        status="active"
    )
    
    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    
    return {
        "message": "Преподаватель успешно назначен на курс",
        "assignment_id": str(assignment.id),
        "course_name": course.name,
        "teacher_name": f"{teacher.surname} {teacher.name}"
    }

@router.delete("/courses/{course_id}/teachers/{teacher_id}")
async def remove_teacher_from_course(
    course_id: uuid.UUID,
    teacher_id: str,
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Удалить преподавателя с курса"""
    result = await db.execute(
        select(models.TeacherCourseAssignment).where(
            models.TeacherCourseAssignment.course_id == course_id,
            models.TeacherCourseAssignment.teacher_id == teacher_id,
            models.TeacherCourseAssignment.status == "active"
        )
    )
    
    assignment = result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Назначение не найдено")
    
    # Мягкое удаление - меняем статус
    assignment.status = "inactive"
    await db.commit()
    
    return {
        "message": "Преподаватель удален с курса",
        "course_id": str(course_id),
        "teacher_id": teacher_id
    }

@router.get("/teachers/available")
async def get_available_teachers(
    course_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Получить доступных преподавателей (не назначенных на курс)"""
    # Получаем всех преподавателей
    teachers_query = select(models.User).where(
        models.User.type == "teacher",
        models.User.active == True
    ).order_by(models.User.surname, models.User.name)
    
    result = await db.execute(teachers_query)
    all_teachers = result.scalars().all()
    
    available_teachers = []
    
    for teacher in all_teachers:
        teacher_data = {
            "id": str(teacher.id),
            "name": f"{teacher.surname} {teacher.name}",
            "email": teacher.email,
            "department": teacher.department or "",
            "title": teacher.title or "",
            "assigned_courses": []
        }
        
        # Если указан course_id, проверяем назначен ли уже преподаватель на этот курс
        if course_id:
            assignment_result = await db.execute(
                select(models.TeacherCourseAssignment).where(
                    models.TeacherCourseAssignment.course_id == course_id,
                    models.TeacherCourseAssignment.teacher_id == teacher.id,
                    models.TeacherCourseAssignment.status == "active"
                )
            )
            
            is_assigned = assignment_result.scalar_one_or_none() is not None
            teacher_data["is_assigned"] = is_assigned
        
        # Получаем курсы на которые назначен преподаватель
        assignments_result = await db.execute(
            select(models.TeacherCourseAssignment, models.Course)
            .join(models.Course, models.TeacherCourseAssignment.course_id == models.Course.id)
            .where(
                models.TeacherCourseAssignment.teacher_id == teacher.id,
                models.TeacherCourseAssignment.status == "active"
            )
        )
        
        for assignment, course in assignments_result.all():
            teacher_data["assigned_courses"].append({
                "course_id": str(course.id),
                "course_name": course.name,
                "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None
            })
        
        available_teachers.append(teacher_data)
    
    return available_teachers

@router.get("/users/teachers")
async def get_all_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _ = Depends(require_role("admin"))
):
    """Получить всех преподавателей"""
    query = select(models.User).where(
        models.User.type == "teacher"
    ).order_by(models.User.surname, models.User.name)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(or_(
            models.User.name.ilike(search_term),
            models.User.surname.ilike(search_term),
            models.User.email.ilike(search_term),
        ))
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    teachers = result.scalars().all()
    
    teachers_list = []
    for teacher in teachers:
        # Подсчитываем количество назначенных курсов
        courses_count_result = await db.execute(
            select(func.count(models.TeacherCourseAssignment.id))
            .where(
                models.TeacherCourseAssignment.teacher_id == teacher.id,
                models.TeacherCourseAssignment.status == "active"
            )
        )
        courses_count = courses_count_result.scalar() or 0
        
        teachers_list.append({
            "id": str(teacher.id),
            "name": f"{teacher.surname} {teacher.name}",
            "email": teacher.email,
            "phone": teacher.phone or "",
            "department": teacher.department or "",
            "title": teacher.title or "",
            "active": bool(teacher.active),
            "hire_date": teacher.hire_date or "",
            "courses_count": courses_count
        })
    
    return teachers_list