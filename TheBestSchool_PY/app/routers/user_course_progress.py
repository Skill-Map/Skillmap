# app/routers/user_course_progress.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from dependencies import get_db
from auth import get_current_user
import models

router = APIRouter(prefix="/api/user-course-progress", tags=["user-course-progress"])

@router.get("/me")
async def get_my_progress(db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """
    Возвращаем прогресс текущего пользователя (первую запись).
    Формат ответа:
    { id, user_id, course_id, current_module_id, completed_lessons, progress_percent, started_at, last_accessed }
    """
    res = await db.execute(select(models.UserCourseProgress).where(models.UserCourseProgress.user_id == current_user.id))
    prog = res.scalars().first()
    if not prog:
        raise HTTPException(status_code=404, detail="Progress not found")
    # Преобразуем в JSON-совместимый словарь:
    return {
        "id": str(prog.id),
        "user_id": prog.user_id,
        "course_id": str(prog.course_id),
        "current_module_id": str(prog.current_module_id) if prog.current_module_id else None,
        "completed_lessons": prog.completed_lessons or [],
        "progress_percent": float(prog.progress_percent or 0.0),
        "started_at": prog.started_at.isoformat() if prog.started_at else None,
        "last_accessed": prog.last_accessed.isoformat() if getattr(prog, "last_accessed", None) else None
    }
