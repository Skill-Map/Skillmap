from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

import models, schemas
from dependencies import get_db
from auth import get_current_user

router = APIRouter(
    prefix="/api/teacher/assignments",
    tags=["teacher-assignments"]
)

@router.post("")
async def assign_lesson(
    payload: schemas.LessonAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.type != "teacher":
        raise HTTPException(status_code=403)

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
