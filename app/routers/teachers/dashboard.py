from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

import models
from dependencies import get_db
from auth import get_current_user

router = APIRouter(
    prefix="/api/teacher/dashboard",
    tags=["teacher-dashboard"]
)

@router.get("")
async def teacher_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.type != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers allowed")

    result = await db.execute(
        select(models.User).where(models.User.advisor_user_id == current_user.id)
    )
    students = result.scalars().all()

    students_data = []
    for s in students:
        q1 = await db.execute(
            select(func.count(models.UserCourseProgress.id))
            .where(models.UserCourseProgress.user_id == s.id)
        )
        q2 = await db.execute(
            select(func.avg(models.UserCourseProgress.progress_percent))
            .where(models.UserCourseProgress.user_id == s.id)
        )

        students_data.append({
            "id": s.id,
            "name": f"{s.name} {s.surname}",
            "email": s.email,
            "course_count": q1.scalar() or 0,
            "avg_progress": float(q2.scalar() or 0),
        })

    return {
        "teacher": {
            "id": current_user.id,
            "name": f"{current_user.name} {current_user.surname}",
            "email": current_user.email,
        },
        "students": students_data,
    }
