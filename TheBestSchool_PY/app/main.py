# main.py
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.courses import router as courses_router
from routers.vacancies import router as vacancies_router

# Удаляем старые роутеры преподавателя, так как все перенесли в teacher_panel.py
from routers.teachers.teacher_panel import router as teacher_panel_router
from routers.teachers.teachers import router as admin_teachers_router  # Для админов
from routers.user_course_progress import router as user_course_progress_router
from routers.student.submissions import router as student_submissions_router
from routers.admin import router as admin_router

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="Skillmap API", version="1.0.0")

# CORS настройки
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8082",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статические файлы
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Подключаем роутеры в правильном порядке

# 1. Админские роутеры (включая управление преподавателями)
app.include_router(admin_router)
app.include_router(admin_teachers_router)  # /api/teachers - для админов

# 2. Панель преподавателя (все эндпоинты преподавателя)
app.include_router(teacher_panel_router)   # /api/teacher - для преподавателей

# 3. Общие роутеры
app.include_router(user_course_progress_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(courses_router)
app.include_router(vacancies_router)

# 4. Роутеры студентов
app.include_router(student_submissions_router)

@app.get("/")
async def root():
    return {"message": "Skillmap API is running"}

@app.get("/health")
async def health():
    return {"status": "ok"}