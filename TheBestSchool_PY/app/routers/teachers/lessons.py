from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os, uuid, shutil

import models
from dependencies import get_db
from auth import get_current_user

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

router = APIRouter(
    prefix="/api/teacher/lessons",
    tags=["teacher-lessons"]
)

@router.post("/courses/{course_id}/modules/{module_id}", status_code=201)
async def create_lesson(
    course_id: str,
    module_id: str,
    order: int = Form(...),
    title: str = Form(...),
    description: str = Form(None),
    pptx_file: UploadFile = File(None),
    homework_file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.type != "teacher":
        raise HTTPException(status_code=403)

    module = await db.scalar(
        select(models.CourseModule)
        .where(models.CourseModule.id == module_id)
    )
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    def save_file(f: UploadFile):
        ext = os.path.splitext(f.filename)[1]
        name = f"{uuid.uuid4()}{ext}"
        path = os.path.join(UPLOAD_DIR, name)
        with open(path, "wb") as out:
            shutil.copyfileobj(f.file, out)
        return f"/uploads/{name}"

    lesson = models.CourseLesson(
        module_id=module_id,
        order=order,
        title=title,
        description=description,
        pptx_url=save_file(pptx_file) if pptx_file else None,
        homework_url=save_file(homework_file) if homework_file else None,
    )

    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)

    return lesson
