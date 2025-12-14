# main.py
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# роутеры
from routers.auth import router as auth_router
from routers.users import router as users_router
from routers.courses import router as courses_router
from routers.vacancies import router as vacancies_router

app = FastAPI(title="Skillmap API", version="1.0.0")

# --- Оставляем только стандартный CORSMiddleware ---
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:8080",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Подключаем роутеры (все роугеты остаются в своих файлах)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(courses_router)
app.include_router(vacancies_router)

@app.get("/")
async def root():
    return {"message": "Skillmap API is running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8082, reload=True, log_level="debug")
