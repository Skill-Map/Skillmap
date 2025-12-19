from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, distinct
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import shutil
from uuid import uuid4, UUID
import asyncio
from fastapi.responses import FileResponse
import mimetypes
import aiofiles
import aiofiles.os as aios
from sqlalchemy.orm import selectinload
from database import get_db
from auth import require_role
import models
import schemas

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

router = APIRouter(prefix="/api/teacher", tags=["teacher"])

# ============ ПОМОЩНИКИ ============
def _serialize_course_for_teacher(course: models.Course, student_count: int = 0) -> Dict[str, Any]:
    """Сериализация курса для преподавателя"""
    return {
        "id": str(course.id),
        "name": course.name or "",
        "description": course.description or "",
        "category": course.category or "",
        "category_name": course.category_name or "",
        "category_color": course.category_color or "#1A535C",
        "created_at": course.created_at.isoformat() if course.created_at else None,
        "student_count": student_count,
        "is_public": bool(course.is_public),
    }

def _serialize_student_for_teacher(student: models.User, course_count: int = 0, avg_progress: float = 0) -> Dict[str, Any]:
    """Сериализация студента для преподавателя"""
    return {
        "id": student.id,
        "email": student.email,
        "name": student.name or "",
        "surname": student.surname or "",
        "patronymic": student.patronymic or "",
        "phone": student.phone or "",
        "course_count": course_count,
        "avg_progress": avg_progress,
        "status": student.status or "active",
        "group_code": student.group_code or "",
        "progress_percent": float(student.progress_percent or 0),
    }

def _serialize_assignment(assignment: models.LessonAssignment, 
                         lesson: models.CourseLesson = None,
                         student: models.User = None) -> Dict[str, Any]:
    """Сериализация назначения"""
    data = {
        "id": str(assignment.id),
        "user_id": assignment.user_id,
        "lesson_id": str(assignment.lesson_id),
        "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
        "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
        "status": assignment.status or "assigned",
        "note": assignment.note or "",
    }
    
    if lesson:
        data.update({
            "lesson_title": lesson.title or "",
            "lesson_description": lesson.description or "",
            "pptx_url": lesson.pptx_url or "",
            "homework_url": lesson.homework_url or "",
        })
    
    if student:
        data.update({
            "student_name": f"{student.surname or ''} {student.name or ''}".strip(),
            "student_email": student.email,
        })
    
    return data

# app/routers/teachers/teacher_panel.py
# app/routers/teachers/teacher_panel.py
import aiofiles
import aiofiles.os as aios

async def save_file(f: UploadFile) -> Optional[str]:
    """Асинхронное сохранение файла"""
    if not f:
        return None
    
    try:
        # Создаем папку, если ее нет
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        ext = os.path.splitext(f.filename)[1]
        name = f"{uuid4()}{ext}"
        path = os.path.join(UPLOAD_DIR, name)
        
        # Асинхронная запись файла
        async with aiofiles.open(path, "wb") as out:
            content = await f.read()
            await out.write(content)
        
        # Сбрасываем указатель файла на начало
        await f.seek(0)
        
        return f"/uploads/{name}"
    except Exception as e:
        print(f"Ошибка сохранения файла {f.filename}: {e}")
        return None

# ============ ОСНОВНЫЕ ЭНДПОИНТЫ ============
@router.get("/dashboard")
async def get_teacher_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Дашборд преподавателя - основан на назначенных заданиях"""
    
    # 1. Курсы, где преподаватель назначил задания
    courses_query = select(
        distinct(models.CourseModule.course_id)
    ).select_from(
        models.LessonAssignment
    ).join(
        models.CourseLesson, models.LessonAssignment.lesson_id == models.CourseLesson.id
    ).join(
        models.CourseModule, models.CourseLesson.module_id == models.CourseModule.id
    ).where(
        models.LessonAssignment.assigned_by == current_user.id
    )
    
    course_ids_result = await db.execute(courses_query)
    course_ids = [row[0] for row in course_ids_result.all()]
    
    # Получаем информацию о курсах
    teacher_courses = []
    for course_id in course_ids:
        course_result = await db.execute(
            select(models.Course).where(models.Course.id == course_id)
        )
        course = course_result.scalar_one_or_none()
        if course:
            teacher_courses.append(_serialize_course_for_teacher(course))
    
    # 2. Студенты, которым преподаватель назначил задания
    students_query = select(
        distinct(models.LessonAssignment.user_id)
    ).where(
        models.LessonAssignment.assigned_by == current_user.id
    )
    
    student_ids_result = await db.execute(students_query)
    student_ids = [row[0] for row in student_ids_result.all()]
    
    # 3. Статистика
    total_assignments_result = await db.execute(
        select(func.count(models.LessonAssignment.id))
        .where(models.LessonAssignment.assigned_by == current_user.id)
    )
    total_assignments = total_assignments_result.scalar() or 0
    
    # Средний прогресс студентов (по всем курсам)
    avg_progress_result = await db.execute(
        select(func.avg(models.User.progress_percent))
        .where(models.User.id.in_(student_ids) if student_ids else False)
    )
    avg_progress = float(avg_progress_result.scalar() or 0)
    
    return {
        "teacher": {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name or "",
            "surname": current_user.surname or "",
            "department": current_user.department or "",
            "title": current_user.title or "",
            "hire_date": current_user.hire_date or "",
        },
        "stats": {
            "courses_count": len(teacher_courses),
            "students_count": len(student_ids),
            "assignments_count": total_assignments,
            "avg_progress": round(avg_progress, 1),
        },
        "courses": teacher_courses,
        "recent_activities": await _get_recent_activities(current_user.id, db)
    }

@router.get("/stats")
async def get_teacher_stats(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Статистика преподавателя"""
    
    # Студенты
    student_ids_result = await db.execute(
        select(distinct(models.LessonAssignment.user_id))
        .where(models.LessonAssignment.assigned_by == current_user.id)
    )
    student_ids = [row[0] for row in student_ids_result.all()]
    students_count = len(student_ids)
    
    # Курсы
    course_ids_result = await db.execute(
        select(distinct(models.CourseModule.course_id))
        .select_from(models.LessonAssignment)
        .join(models.CourseLesson, models.LessonAssignment.lesson_id == models.CourseLesson.id)
        .join(models.CourseModule, models.CourseLesson.module_id == models.CourseModule.id)
        .where(models.LessonAssignment.assigned_by == current_user.id)
    )
    course_ids = [row[0] for row in course_ids_result.all()]
    courses_count = len(course_ids)
    
    # Назначения
    assignments_count_result = await db.execute(
        select(func.count(models.LessonAssignment.id))
        .where(models.LessonAssignment.assigned_by == current_user.id)
    )
    assignments_count = assignments_count_result.scalar() or 0
    
    # Средний прогресс
    avg_progress_result = await db.execute(
        select(func.avg(models.User.progress_percent))
        .where(models.User.id.in_(student_ids) if student_ids else False)
    )
    avg_progress = float(avg_progress_result.scalar() or 0)
    
    return {
        "courses": courses_count,
        "students": students_count,
        "assignments": assignments_count,
        "avg_progress": round(avg_progress, 1)
    }

@router.get("/courses")
async def get_teacher_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Курсы, где преподаватель назначил задания"""
    
    query = select(
        distinct(models.Course)
    ).select_from(
        models.LessonAssignment
    ).join(
        models.CourseLesson, models.LessonAssignment.lesson_id == models.CourseLesson.id
    ).join(
        models.CourseModule, models.CourseLesson.module_id == models.CourseModule.id
    ).join(
        models.Course, models.CourseModule.course_id == models.Course.id
    ).where(
        models.LessonAssignment.assigned_by == current_user.id
    ).order_by(models.Course.created_at.desc())
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    courses = result.scalars().all()
    
    serialized_courses = []
    for course in courses:
        # Подсчет студентов на этом курсе (которым этот преподаватель назначал задания)
        student_count_result = await db.execute(
            select(func.count(distinct(models.LessonAssignment.user_id)))
            .select_from(models.LessonAssignment)
            .join(models.CourseLesson, models.LessonAssignment.lesson_id == models.CourseLesson.id)
            .join(models.CourseModule, models.CourseLesson.module_id == models.CourseModule.id)
            .where(
                models.LessonAssignment.assigned_by == current_user.id,
                models.CourseModule.course_id == course.id
            )
        )
        student_count = student_count_result.scalar() or 0
        
        serialized_courses.append(_serialize_course_for_teacher(course, student_count))
    
    return serialized_courses

@router.get("/students")
async def get_teacher_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Студенты, которым преподаватель назначил задания"""
    
    # Получаем ID студентов
    subquery = select(
        distinct(models.LessonAssignment.user_id)
    ).where(
        models.LessonAssignment.assigned_by == current_user.id
    ).subquery()
    
    query = select(models.User).where(models.User.id.in_(select(subquery)))
    
    # Поиск
    if search:
        search_term = f"%{search}%"
        query = query.where(or_(
            models.User.name.ilike(search_term),
            models.User.surname.ilike(search_term),
            models.User.email.ilike(search_term),
            models.User.phone.ilike(search_term),
        ))
    
    query = query.order_by(models.User.surname, models.User.name)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    students = result.scalars().all()
    
    serialized_students = []
    for student in students:
        # Подсчет заданий для этого студента
        assignments_count_result = await db.execute(
            select(func.count(models.LessonAssignment.id))
            .where(
                models.LessonAssignment.assigned_by == current_user.id,
                models.LessonAssignment.user_id == student.id
            )
        )
        assignments_count = assignments_count_result.scalar() or 0
        
        # Подсчет курсов для этого студента
        courses_count_result = await db.execute(
            select(func.count(distinct(models.CourseModule.course_id)))
            .select_from(models.LessonAssignment)
            .join(models.CourseLesson, models.LessonAssignment.lesson_id == models.CourseLesson.id)
            .join(models.CourseModule, models.CourseLesson.module_id == models.CourseModule.id)
            .where(
                models.LessonAssignment.assigned_by == current_user.id,
                models.LessonAssignment.user_id == student.id
            )
        )
        course_count = courses_count_result.scalar() or 0
        
        serialized_students.append(
            _serialize_student_for_teacher(student, course_count, student.progress_percent or 0)
        )
    
    return serialized_students

@router.get("/assignments")
async def get_teacher_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: str = Query(None),
    student_id: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Назначения преподавателя"""
    
    query = select(
        models.LessonAssignment,
        models.CourseLesson,
        models.User
    ).join(
        models.CourseLesson, models.LessonAssignment.lesson_id == models.CourseLesson.id
    ).join(
        models.User, models.LessonAssignment.user_id == models.User.id
    ).where(
        models.LessonAssignment.assigned_by == current_user.id
    )
    
    if status:
        query = query.where(models.LessonAssignment.status == status)
    
    if student_id:
        query = query.where(models.LessonAssignment.user_id == student_id)
    
    query = query.order_by(models.LessonAssignment.assigned_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    rows = result.all()
    
    assignments = []
    for assignment, lesson, student in rows:
        assignments.append(_serialize_assignment(assignment, lesson, student))
    
    return assignments

@router.post("/assignments")
async def create_assignment(
    payload: schemas.LessonAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Создание нового назначения"""
    assignment = models.LessonAssignment(
        user_id=payload.user_id,
        lesson_id=payload.lesson_id,
        assigned_by=current_user.id,
        due_date=payload.due_date,
        note=payload.note,
    )

    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)
    return assignment

@router.get("/activities/recent")
async def get_recent_activities(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Последние активности преподавателя"""
    activities = await _get_recent_activities(current_user.id, db, limit)
    return activities

@router.get("/students/{student_id}")
async def get_student_details(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Детали студента"""
    
    # Проверяем, что преподаватель назначал задания этому студенту
    has_access_result = await db.execute(
        select(func.count(models.LessonAssignment.id))
        .where(
            models.LessonAssignment.assigned_by == current_user.id,
            models.LessonAssignment.user_id == student_id
        )
    )
    has_access = has_access_result.scalar() or 0 > 0
    
    if not has_access:
        raise HTTPException(status_code=403, detail="Нет доступа к этому студенту")
    
    # Получаем данные студента
    student_result = await db.execute(
        select(models.User).where(models.User.id == student_id)
    )
    student = student_result.scalar_one_or_none()
    
    if not student:
        raise HTTPException(status_code=404, detail="Студент не найден")
    
    # Назначения для этого студента
    assignments_result = await db.execute(
        select(models.LessonAssignment, models.CourseLesson)
        .join(models.CourseLesson, models.LessonAssignment.lesson_id == models.CourseLesson.id)
        .where(
            models.LessonAssignment.user_id == student_id,
            models.LessonAssignment.assigned_by == current_user.id
        )
        .order_by(models.LessonAssignment.assigned_at.desc())
    )
    
    assignments = []
    for assignment, lesson in assignments_result.all():
        assignments.append(_serialize_assignment(assignment, lesson))
    
    return {
        "student": _serialize_student_for_teacher(student, len(assignments)),
        "assignments": assignments
    }


@router.get("/submissions/{assignment_id}")
async def get_submissions(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Получение сабмишенов по заданию"""
    result = await db.execute(
        select(models.LessonSubmission)
        .where(models.LessonSubmission.assignment_id == assignment_id)
    )
    return result.scalars().all()

# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============
async def _get_recent_activities(teacher_id: str, db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """Получить последние активности преподавателя"""
    activities = []
    
    # Последние назначения
    assignments_result = await db.execute(
        select(models.LessonAssignment, models.User, models.CourseLesson)
        .join(models.User, models.LessonAssignment.user_id == models.User.id)
        .join(models.CourseLesson, models.LessonAssignment.lesson_id == models.CourseLesson.id)
        .where(models.LessonAssignment.assigned_by == teacher_id)
        .order_by(models.LessonAssignment.assigned_at.desc())
        .limit(5)
    )
    
    for assignment, student, lesson in assignments_result.all():
        activities.append({
            "id": f"assignment_{assignment.id}",
            "type": "assignment",
            "message": f"Назначен урок '{lesson.title}' студенту {student.surname} {student.name}",
            "date": assignment.assigned_at.isoformat() if assignment.assigned_at else None,
            "icon": "fa-tasks",
            "color": "text-blue-600",
        })
    
    # Последние сданные работы
    week_ago = datetime.now() - timedelta(days=7)
    submissions_result = await db.execute(
        select(models.LessonSubmission, models.LessonAssignment, models.User)
        .join(models.LessonAssignment, models.LessonSubmission.assignment_id == models.LessonAssignment.id)
        .join(models.User, models.LessonSubmission.user_id == models.User.id)
        .where(
            models.LessonAssignment.assigned_by == teacher_id,
            models.LessonSubmission.created_at >= week_ago
        )
        .order_by(models.LessonSubmission.created_at.desc())
        .limit(5)
    )
    
    for submission, assignment, student in submissions_result.all():
        activities.append({
            "id": f"submission_{submission.id}",
            "type": "submission",
            "message": f"Студент {student.surname} {student.name} сдал задание",
            "date": submission.created_at.isoformat() if submission.created_at else None,
            "icon": "fa-file-upload",
            "color": "text-green-600",
        })
    
    # Сортируем по дате и ограничиваем
    activities.sort(key=lambda x: x["date"] or "", reverse=True)
    return activities[:limit]

# app/routers/teachers/teacher_panel.py - ДОБАВИТЬ ЭТИ ЭНДПОИНТЫ

@router.get("/assigned-courses")
async def get_assigned_courses(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Получить курсы, на которые назначен преподаватель"""
    # Находим назначения преподавателя на курсы
    assignments_result = await db.execute(
        select(models.TeacherCourseAssignment)
        .where(models.TeacherCourseAssignment.teacher_id == current_user.id)
        .where(models.TeacherCourseAssignment.status == "active")
    )
    assignments = assignments_result.scalars().all()
    
    courses_data = []
    for assignment in assignments:
        course_result = await db.execute(
            select(models.Course).where(models.Course.id == assignment.course_id)
        )
        course = course_result.scalar_one_or_none()
        
        if course:
            # Считаем студентов на курсе
            student_count_result = await db.execute(
                select(func.count(models.UserCourseProgress.id))
                .where(models.UserCourseProgress.course_id == course.id)
            )
            student_count = student_count_result.scalar() or 0
            
            # Считаем модули курса
            module_count_result = await db.execute(
                select(func.count(models.CourseModule.id))
                .where(models.CourseModule.course_id == course.id)
            )
            module_count = module_count_result.scalar() or 0
            
            courses_data.append({
                "id": str(course.id),
                "name": course.name,
                "description": course.description or "",
                "category": course.category or "",
                "category_name": course.category_name or "",
                "category_color": course.category_color or "#1A535C",
                "student_count": student_count,
                "module_count": module_count,
                "duration": course.duration or "",
                "created_at": course.created_at.isoformat() if course.created_at else None,
            })
    
    return courses_data

@router.get("/modules")
async def get_teacher_modules(
    course_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Получить модули курсов преподавателя"""
    # Сначала получаем курсы преподавателя
    assignments_result = await db.execute(
        select(models.TeacherCourseAssignment.course_id)
        .where(models.TeacherCourseAssignment.teacher_id == current_user.id)
        .where(models.TeacherCourseAssignment.status == "active")
    )
    course_ids = [row[0] for row in assignments_result.all()]
    
    if not course_ids:
        return []
    
    # Если указан конкретный курс, проверяем, что он принадлежит преподавателю
    if course_id:
        if UUID(course_id) not in course_ids:
            raise HTTPException(status_code=403, detail="Нет доступа к этому курсу")
        course_ids = [UUID(course_id)]
    
    # Получаем модули
    query = select(
        models.CourseModule,
        models.Course.name.label("course_name")
    ).join(
        models.Course, models.CourseModule.course_id == models.Course.id
    ).where(
        models.CourseModule.course_id.in_(course_ids)
    ).order_by(models.CourseModule.course_id, models.CourseModule.order)
    
    result = await db.execute(query)
    rows = result.all()
    
    modules = []
    for module, course_name in rows:
        # Считаем уроки в модуле
        lesson_count_result = await db.execute(
            select(func.count(models.CourseLesson.id))
            .where(models.CourseLesson.module_id == module.id)
        )
        lesson_count = lesson_count_result.scalar() or 0
        
        modules.append({
            "id": str(module.id),
            "course_id": str(module.course_id),
            "course_name": course_name,
            "title": module.title,
            "description": module.description or "",
            "order": module.order,
            "recommended_time": module.recommended_time or "",
            "lesson_count": lesson_count,
        })
    
    return modules

@router.post("/modules", status_code=201)
async def create_module(
    payload: schemas.ModuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Создать модуль в курсе преподавателя"""
    # Проверяем, что преподаватель имеет доступ к курсу
    assignment_result = await db.execute(
        select(models.TeacherCourseAssignment)
        .where(
            models.TeacherCourseAssignment.teacher_id == current_user.id,
            models.TeacherCourseAssignment.course_id == UUID(payload.course_id),
            models.TeacherCourseAssignment.status == "active"
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=403, detail="Нет доступа к этому курсу")
    
    # Проверяем существование курса
    course_result = await db.execute(
        select(models.Course).where(models.Course.id == UUID(payload.course_id))
    )
    course = course_result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(status_code=404, detail="Курс не найден")
    
    # Создаем модуль
    module = models.CourseModule(
        course_id=UUID(payload.course_id),
        title=payload.title,
        order=payload.order,
        description=payload.description,
        recommended_time=payload.recommended_time
    )
    
    db.add(module)
    await db.commit()
    await db.refresh(module)
    
    return {
        "id": str(module.id),
        "course_id": str(module.course_id),
        "title": module.title,
        "description": module.description,
        "order": module.order,
        "recommended_time": module.recommended_time
    }

@router.get("/lessons")
async def get_teacher_lessons(
    course_id: Optional[str] = Query(None),
    module_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Получить уроки преподавателя"""
    # Получаем курсы преподавателя
    assignments_result = await db.execute(
        select(models.TeacherCourseAssignment.course_id)
        .where(models.TeacherCourseAssignment.teacher_id == current_user.id)
        .where(models.TeacherCourseAssignment.status == "active")
    )
    teacher_course_ids = [row[0] for row in assignments_result.all()]
    
    if not teacher_course_ids:
        return []
    
    # Построение запроса С ПРЕДВАРИТЕЛЬНОЙ ЗАГРУЗКОЙ
    query = select(
        models.CourseLesson
    ).options(
        selectinload(models.CourseLesson.module).selectinload(models.CourseModule.course)
    ).join(
        models.CourseModule, models.CourseLesson.module_id == models.CourseModule.id
    ).join(
        models.Course, models.CourseModule.course_id == models.Course.id
    ).where(
        models.CourseModule.course_id.in_(teacher_course_ids)
    )
    
    # Фильтры
    if course_id:
        query = query.where(models.CourseModule.course_id == UUID(course_id))
    
    if module_id:
        query = query.where(models.CourseLesson.module_id == UUID(module_id))
    
    query = query.order_by(models.CourseLesson.module_id, models.CourseLesson.order)
    
    result = await db.execute(query)
    lessons = result.scalars().all()
    
    # Теперь можно безопасно обращаться к связанным данным
    serialized_lessons = []
    for lesson in lessons:
        serialized_lessons.append({
            "id": str(lesson.id),
            "module_id": str(lesson.module_id),
            "module_title": lesson.module.title if lesson.module else "",
            "course_id": str(lesson.module.course_id) if lesson.module else "",
            "course_name": lesson.module.course.name if lesson.module and lesson.module.course else "",
            "title": lesson.title,
            "description": lesson.description or "",
            "order": lesson.order,
            "pptx_url": lesson.pptx_url,
            "homework_url": lesson.homework_url,
        })
    
    return serialized_lessons

@router.get("/course-students")
async def get_course_students(
    course_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Получить студентов на курсах преподавателя"""
    # Получаем курсы преподавателя
    assignments_result = await db.execute(
        select(models.TeacherCourseAssignment.course_id)
        .where(models.TeacherCourseAssignment.teacher_id == current_user.id)
        .where(models.TeacherCourseAssignment.status == "active")
    )
    teacher_course_ids = [row[0] for row in assignments_result.all()]
    
    if not teacher_course_ids:
        return []
    
    # Если указан курс, проверяем доступ
    if course_id:
        course_uuid = UUID(course_id)
        if course_uuid not in teacher_course_ids:
            raise HTTPException(status_code=403, detail="Нет доступа к этому курсу")
        teacher_course_ids = [course_uuid]
    
    # Получаем студентов на курсах преподавателя
    query = select(
        models.User,
        models.UserCourseProgress.course_id,
        models.UserCourseProgress.progress_percent
    ).join(
        models.UserCourseProgress, models.User.id == models.UserCourseProgress.user_id
    ).where(
        models.UserCourseProgress.course_id.in_(teacher_course_ids),
        models.User.type == "apprentice"
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    students = []
    for user, progress_course_id, progress_percent in rows:
        # Получаем название курса
        course_result = await db.execute(
            select(models.Course.name)
            .where(models.Course.id == progress_course_id)
        )
        course_name = course_result.scalar_one_or_none() or ""
        
        students.append({
            "id": str(user.id),
            "email": user.email,
            "name": user.name or "",
            "surname": user.surname or "",
            "patronymic": user.patronymic or "",
            "phone": user.phone or "",
            "group_code": user.group_code or "",
            "status": user.status or "active",
            "course_id": str(progress_course_id),
            "course_name": course_name,
            "progress_percent": progress_percent or 0,
        })
    
    return students


# В teacher_panel.py добавьте или измените следующие эндпоинты:

# ============ УРОКИ ============

@router.post("/lessons")
async def create_lesson(
    module_id: str = Form(...),
    order: int = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    pptx_file: UploadFile = File(None),
    homework_file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Создать урок в модуле"""
    try:
        module_uuid = UUID(module_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID модуля")
    
    # Получаем модуль
    module_result = await db.execute(
        select(models.CourseModule).where(models.CourseModule.id == module_uuid)
    )
    module = module_result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(status_code=404, detail="Модуль не найден")
    
    # Проверяем доступ преподавателя к курсу
    assignment_result = await db.execute(
        select(models.TeacherCourseAssignment).where(
            models.TeacherCourseAssignment.teacher_id == current_user.id,
            models.TeacherCourseAssignment.course_id == module.course_id,
            models.TeacherCourseAssignment.status == "active"
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=403, detail="Нет доступа к этому курсу")
    
    # Проверяем, нет ли уже урока с таким порядком в этом модуле
    existing_lesson_result = await db.execute(
        select(models.CourseLesson).where(
            models.CourseLesson.module_id == module_uuid,
            models.CourseLesson.order == order
        )
    )
    existing_lesson = existing_lesson_result.scalar_one_or_none()
    
    if existing_lesson:
        raise HTTPException(
            status_code=400, 
            detail="Урок с таким порядковым номером уже существует в этом модуле"
        )
    
    try:
        # Асинхронно сохраняем файлы
        pptx_url = None
        homework_url = None
        
        if pptx_file:
            pptx_url = await save_file(pptx_file)
        
        if homework_file:
            homework_url = await save_file(homework_file)
        
        # Создаем урок
        lesson = models.CourseLesson(
            module_id=module_uuid,
            order=order,
            title=title,
            description=description,
            pptx_url=pptx_url,
            homework_url=homework_url,
        )
        
        db.add(lesson)
        await db.commit()
        await db.refresh(lesson)
        
        return {
            "id": str(lesson.id),
            "module_id": str(lesson.module_id),
            "title": lesson.title,
            "description": lesson.description,
            "order": lesson.order,
            "pptx_url": lesson.pptx_url,
            "homework_url": lesson.homework_url,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании урока: {str(e)}")

@router.get("/lessons/{lesson_id}")
async def get_lesson(
    lesson_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Получить информацию об уроке"""
    try:
        lesson_uuid = UUID(lesson_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID урока")
    
    # Получаем урок
    lesson_result = await db.execute(
        select(
            models.CourseLesson,
            models.CourseModule,
            models.Course
        )
        .join(models.CourseModule, models.CourseLesson.module_id == models.CourseModule.id)
        .join(models.Course, models.CourseModule.course_id == models.Course.id)
        .where(models.CourseLesson.id == lesson_uuid)
    )
    
    row = lesson_result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Урок не найден")
    
    lesson, module, course = row
    
    # Проверяем доступ преподавателя к курсу
    assignment_result = await db.execute(
        select(models.TeacherCourseAssignment).where(
            models.TeacherCourseAssignment.teacher_id == current_user.id,
            models.TeacherCourseAssignment.course_id == course.id,
            models.TeacherCourseAssignment.status == "active"
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=403, detail="Нет доступа к этому уроку")
    
    return {
        "id": str(lesson.id),
        "module_id": str(lesson.module_id),
        "course_id": str(course.id),
        "title": lesson.title,
        "description": lesson.description,
        "order": lesson.order,
        "pptx_url": lesson.pptx_url,
        "homework_url": lesson.homework_url,
        "course_name": course.name,
        "module_title": module.title
    }

@router.put("/lessons/{lesson_id}")
async def update_lesson(
    lesson_id: str,
    order: int = Form(None),
    title: str = Form(None),
    description: str = Form(None),
    pptx_file: UploadFile = File(None),
    homework_file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Обновить урок"""
    try:
        lesson_uuid = UUID(lesson_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат ID урока")
    
    # Получаем урок
    lesson_result = await db.execute(
        select(
            models.CourseLesson,
            models.CourseModule,
            models.Course
        )
        .join(models.CourseModule, models.CourseLesson.module_id == models.CourseModule.id)
        .join(models.Course, models.CourseModule.course_id == models.Course.id)
        .where(models.CourseLesson.id == lesson_uuid)
    )
    
    row = lesson_result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Урок не найден")
    
    lesson, module, course = row
    
    # Проверяем доступ преподавателя к курсу
    assignment_result = await db.execute(
        select(models.TeacherCourseAssignment).where(
            models.TeacherCourseAssignment.teacher_id == current_user.id,
            models.TeacherCourseAssignment.course_id == course.id,
            models.TeacherCourseAssignment.status == "active"
        )
    )
    assignment = assignment_result.scalar_one_or_none()
    
    if not assignment:
        raise HTTPException(status_code=403, detail="Нет доступа к этому уроку")
    
    try:
        # Обновляем поля
        if title is not None:
            lesson.title = title
        if order is not None:
            # Проверяем, нет ли другого урока с таким порядком в этом модуле
            if order != lesson.order:
                existing_lesson_result = await db.execute(
                    select(models.CourseLesson).where(
                        models.CourseLesson.module_id == module.id,
                        models.CourseLesson.order == order,
                        models.CourseLesson.id != lesson.id
                    )
                )
                existing_lesson = existing_lesson_result.scalar_one_or_none()
                
                if existing_lesson:
                    raise HTTPException(
                        status_code=400, 
                        detail="Урок с таким порядковым номером уже существует в этом модуле"
                    )
                lesson.order = order
        if description is not None:
            lesson.description = description
        
        # Асинхронно сохраняем файлы
        if pptx_file:
            lesson.pptx_url = await save_file(pptx_file)
        if homework_file:
            lesson.homework_url = await save_file(homework_file)
        
        await db.commit()
        await db.refresh(lesson)
        
        return {
            "id": str(lesson.id),
            "module_id": str(lesson.module_id),
            "title": lesson.title,
            "description": lesson.description,
            "order": lesson.order,
            "pptx_url": lesson.pptx_url,
            "homework_url": lesson.homework_url
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении урока: {str(e)}")
    
@router.get("/download/{filename:path}")
async def download_file(
    filename: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(require_role("teacher"))
):
    """Скачать файл из папки uploads"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    # Проверяем, существует ли файл
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    # Определяем MIME-тип файла
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "application/octet-stream"
    
    # Возвращаем файл с правильными заголовками
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=mime_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )