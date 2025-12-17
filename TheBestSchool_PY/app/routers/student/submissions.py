# app/routers/student/submissions.py
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os, uuid, shutil

from database import get_db
from auth import get_current_user
import models

router = APIRouter(prefix="/api/student/submissions", tags=["student-submissions"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXT = {".docx", ".pdf", ".zip"}
MAX_BYTES = 50 * 1024 * 1024

def _save_file(file: UploadFile):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    fname = f"{uuid.uuid4()}{ext}"
    path = os.path.join(UPLOAD_DIR, fname)
    total = 0
    with open(path, "wb") as out:
        while True:
            chunk = file.file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_BYTES:
                out.close()
                os.remove(path)
                raise HTTPException(status_code=400, detail="File too large")
            out.write(chunk)
    return f"/{UPLOAD_DIR}/{fname}"

@router.post("/{progress_id}/lessons/{lesson_id}/submission")
async def submit_lesson_file(progress_id: str, lesson_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Проверим прогресс принадлежит текущему пользователю
    prog = await db.scalar(select(models.UserCourseProgress).where(models.UserCourseProgress.id == progress_id))
    if not prog:
        raise HTTPException(status_code=404, detail="Progress not found")
    if prog.user_id != current_user.id and current_user.type != "admin":
        raise HTTPException(status_code=403, detail="No access")

    # Попытаемся найти существующее назначение
    res = await db.execute(select(models.LessonAssignment).where(models.LessonAssignment.user_id == current_user.id, models.LessonAssignment.lesson_id == lesson_id))
    assignment = res.scalars().first()
    if not assignment:
        assignment = models.LessonAssignment(user_id=current_user.id, lesson_id=lesson_id, assigned_by=current_user.id)
        db.add(assignment)
        await db.commit()
        await db.refresh(assignment)

    file_url = _save_file(file)

    submission = models.LessonSubmission(
        assignment_id=assignment.id,
        user_id=current_user.id,
        file_url=file_url,
        filename=file.filename,
        status="sent"
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    assignment.status = "submitted"
    db.add(assignment)
    await db.commit()

    return {
        "id": str(submission.id),
        "assignment_id": str(submission.assignment_id),
        "file_url": submission.file_url,
        "filename": submission.filename,
        "status": submission.status,
        "created_at": submission.created_at.isoformat() if submission.created_at else None
    }
