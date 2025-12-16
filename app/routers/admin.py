# app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.params import Body, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime
import uuid

from database import get_db
from auth import require_role
import models

router = APIRouter(prefix="/api/admin", tags=["admin"])

# --- Helpers -----------------------------------------------------------------
async def _get_user_or_404(db: AsyncSession, user_id: str):
    user = await db.scalar(select(models.User).where(models.User.id == user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

async def _get_course_by_name(db: AsyncSession, name: str):
    return await db.scalar(select(models.Course).where(models.Course.name == name))

# --- Endpoints ---------------------------------------------------------------

@router.get("/users", response_model=List[dict])
async def list_users(
    skip: int = Query(0),
    limit: int = Query(100),
    user_type: Optional[str] = Query(None, description="Filter by user type"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role("admin"))
):
    """
    List users. Optional filters: user_type (admin/teacher/apprentice/moderator), active (true/false).
    Returns basic info for each user.
    """
    q = select(models.User).offset(skip).limit(limit)
    result = await db.execute(q)
    users = result.scalars().all()

    out = []
    for u in users:
        if user_type and u.type != user_type:
            continue
        if active is not None and bool(u.active) != bool(active):
            continue
        out.append({
            "id": u.id,
            "email": u.email,
            "surname": u.surname,
            "name": u.name,
            "patronymic": u.patronymic,
            "type": u.type,
            "active": bool(u.active),
            "reg_date": u.reg_date.isoformat() if getattr(u, "reg_date", None) else None,
        })
    return out

@router.get("/users/{user_id}", response_model=dict)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db), _=Depends(require_role("admin"))):
    user = await _get_user_or_404(db, user_id)
    return {
        "id": user.id,
        "email": user.email,
        "surname": user.surname,
        "name": user.name,
        "patronymic": user.patronymic,
        "type": user.type,
        "active": bool(user.active),
        "reg_date": user.reg_date.isoformat() if getattr(user, "reg_date", None) else None,
    }

@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: str,
    payload: dict = Body(...),  # {"new_role": "teacher"}
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role("admin"))
):
    """
    Change user's role. payload: { "new_role": "teacher" | "admin" | "apprentice" | "moderator" }
    """
    new_role = payload.get("new_role")
    if not new_role or new_role not in ("admin", "teacher", "apprentice", "moderator"):
        raise HTTPException(status_code=400, detail="Invalid new_role")

    # prevent changing own role (optional)
    # current_user = await require_role("admin") ... (we don't use here)
    user = await _get_user_or_404(db, user_id)

    if user.type == new_role:
        return {"message": "Role unchanged", "user_id": user.id, "role": user.type}

    # If promoting to teacher, ensure teacher-specific fields exist (defaults)
    if new_role == "teacher":
        user.hire_date = user.hire_date or datetime.now().strftime("%d.%m.%Y")
        user.department = user.department or "General"
        user.title = user.title or "Teacher"
        user.teacher_hours_per_week = user.teacher_hours_per_week or 20

    user.type = new_role
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"message": "Role updated", "user_id": user.id, "new_role": user.type}

@router.put("/users/{user_id}/status")
async def change_user_status(
    user_id: str,
    payload: dict = Body(...),  # {"active": true|false}
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role("admin"))
):
    """
    Activate or deactivate user. payload: {"active": true|false}
    """
    active = payload.get("active")
    if active is None:
        raise HTTPException(status_code=400, detail="active field required")

    user = await _get_user_or_404(db, user_id)

    user.active = bool(active)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {"message": "User status updated", "user_id": user.id, "active": user.active}

@router.post("/users/{user_id}/enroll")
async def enroll_user_on_course(
    user_id: str,
    payload: dict = Body(...),  # { "course_name": "Name" }
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role("admin"))
):
    """
    Enroll user to a course by name. If course with that name doesn't exist -> create it.
    Returns progress id.
    """
    course_name = (payload.get("course_name") or "").strip()
    if not course_name:
        raise HTTPException(status_code=400, detail="course_name required")

    user = await _get_user_or_404(db, user_id)

    # find course by exact name
    course = await _get_course_by_name(db, course_name)
    if not course:
        # create minimal course
        course = models.Course(
            name=course_name,
            description=f"Auto-created course {course_name}",
            category="it",
            category_name="IT",
            category_color="#1A535C"
        )
        db.add(course)
        await db.commit()
        await db.refresh(course)

    # check existing enrollment
    existing = await db.scalar(
        select(models.UserCourseProgress).where(
            models.UserCourseProgress.user_id == user.id,
            models.UserCourseProgress.course_id == course.id
        )
    )
    if existing:
        return {"message": "User already enrolled", "course_id": str(course.id), "progress_id": existing.id}

    prog = models.UserCourseProgress(
        user_id=user.id,
        course_id=course.id,
        current_module_id=None,
        completed_lessons=[],
        progress_percent=0.0
    )
    db.add(prog)
    await db.commit()
    await db.refresh(prog)

    return {"message": "Enrolled", "course_id": str(course.id), "progress_id": prog.id}

@router.get("/courses", response_model=List[dict])
async def list_courses(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role("admin"))
):
    result = await db.execute(select(models.Course).order_by(models.Course.created_at.desc()))
    courses = result.scalars().all()
    out = []
    for c in courses:
        out.append({
            "id": str(c.id),
            "name": c.name,
            "category": c.category_name,
            "created_at": c.created_at.isoformat() if c.created_at else None
        })
    return out

@router.post("/courses", status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: dict = Body(...),  # {"name": "...", "description": "..."}
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role("admin"))
):
    name = (payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    # check duplicate
    found = await db.scalar(select(models.Course).where(models.Course.name == name))
    if found:
        raise HTTPException(status_code=400, detail="Course with this name already exists")

    c = models.Course(
        name=name,
        description=payload.get("description") or f"Course {name}",
        category=payload.get("category") or "it",
        category_name=payload.get("category_name") or "IT",
        category_color=payload.get("category_color") or "#1A535C"
    )
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return {"id": str(c.id), "name": c.name}
