from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uvicorn
from contextlib import asynccontextmanager

from database import engine, get_db, create_uuid_extension
import models
from routers import (
    users, admins, apprentices, teachers,
    moderators, training, schedule, dev, admin_panel
)
from auth import get_current_user
import crud

@asynccontextmanager
async def lifespan(app: FastAPI):
    # При запуске: создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield
    # При остановке
    await engine.dispose()

app = FastAPI(
    title="Fitness API",
    description="Бэкенд для системы управления тренировками",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(users.router)
app.include_router(admins.router)
app.include_router(apprentices.router)
app.include_router(teachers.router)
app.include_router(moderators.router)
app.include_router(training.router)
app.include_router(schedule.router)
app.include_router(dev.router)
app.include_router(admin_panel.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Fitness API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8082,
        reload=True
    )