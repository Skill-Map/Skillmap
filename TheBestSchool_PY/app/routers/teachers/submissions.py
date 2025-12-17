from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models, schemas
from dependencies import get_db
from auth import get_current_user

router = APIRouter(
    prefix="/api/teacher/submissions",
    tags=["teacher-submissions"]
)

@router.get("/{assignment_id}")
async def get_submissions(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.type != "teacher":
        raise HTTPException(status_code=403)

    result = await db.execute(
        select(models.LessonSubmission)
        .where(models.LessonSubmission.assignment_id == assignment_id)
    )
    return result.scalars().all()
