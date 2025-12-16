# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.courses import router as courses_router
from routers.vacancies import router as vacancies_router

from routers.teachers.dashboard import router as teacher_dashboard_router
from routers.teachers.lessons import router as teacher_lessons_router
from routers.teachers.assignments import router as teacher_assignments_router
from routers.teachers.submissions import router as teacher_submissions_router
from routers.user_course_progress import router as user_course_progress_router
from routers.student.submissions import router as student_submissions_router
from routers.admin import router as admin_router

app = FastAPI(title="Skillmap API", version="1.0.0")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8082",
    "http://127.0.0.1:5500",
]

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(admin_router)

app.include_router(user_course_progress_router)
# Public
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(courses_router)
app.include_router(vacancies_router)

# Teacher
app.include_router(teacher_dashboard_router)
app.include_router(teacher_lessons_router)
app.include_router(teacher_assignments_router)
app.include_router(teacher_submissions_router)

# Student
app.include_router(student_submissions_router)

@app.get("/")
async def root():
    return {"message": "Skillmap API is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}
