# main.py - исправленная версия с правильной аутентификацией
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from jose import jwt, JWTError

from database import get_db
from models import User
from auth import SECRET_KEY, ALGORITHM, create_access_token, verify_password, get_password_hash

app = FastAPI(title="Skillmap API", version="1.0.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели для запросов
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    phone: str
    surname: str
    name: str
    patronymic: Optional[str] = None

class LoginRequest(BaseModel):
    username: EmailStr
    password: str

# Регистрация
@app.post("/api/v1/auth/register")
async def register_user(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    # Проверяем длину пароля
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Пароль должен содержать минимум 8 символов")
    
    # Проверяем телефон (11 цифр)
    phone_digits = ''.join(filter(str.isdigit, request.phone))
    if len(phone_digits) != 11:
        raise HTTPException(status_code=400, detail="Номер телефона должен содержать 11 цифр")
    
    # Проверяем, существует ли пользователь с таким email
    result = await db.execute(select(User).where(User.email == request.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    
    # Проверяем телефон
    result = await db.execute(select(User).where(User.phone == phone_digits))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Пользователь с таким телефоном уже существует")
    
    # Создаем пользователя
    user = User(
        email=request.email,
        password=get_password_hash(request.password),
        surname=request.surname,
        name=request.name,
        patronymic=request.patronymic,
        phone=phone_digits,
        type="apprentice",
        status="active",
        track_id="default",
        group_code="A1",
        hours_per_week=0,
        progress_percent=0,
        credits_earned=0,
        enrollment_date="",
        expected_graduation=""
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Создаем токен
    access_token = create_access_token({"sub": str(user.id)})
    
    return {
        "ok": True,
        "user_id": user.id,
        "access": access_token
    }

# Вход
@app.post("/api/v1/auth/login")
async def login_user(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    # Находим пользователя по email
    result = await db.execute(select(User).where(User.email == request.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.password):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    
    # Создаем токен
    access_token = create_access_token({"sub": str(user.id)})
    
    return {"access": access_token, "token_type": "bearer"}

# Получение данных текущего пользователя
@app.get("/api/v1/users/me")
async def get_current_user_me(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Неавторизованный доступ")
    
    token = authorization[7:]  # Убираем "Bearer "
    
    try:
        # Декодируем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Неверный токен")
        
        # Находим пользователя по ID
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        return {
            "id": user.id,
            "email": user.email,
            "surname": user.surname,
            "name": user.name,
            "patronymic": user.patronymic,
            "phone": user.phone,
            "active": user.active,
            "type": user.type,
            "reg_date": user.reg_date.isoformat() if user.reg_date else None,
            "up_date": user.up_date,
            "status": user.status,
            "track_id": user.track_id,
            "group_code": user.group_code,
            "progress_percent": user.progress_percent,
            "credits_earned": user.credits_earned,
            "hours_per_week": user.hours_per_week,
            "enrollment_date": user.enrollment_date,
            "expected_graduation": user.expected_graduation,
        }
        
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Неверный токен: {str(e)}")

# Тестовый маршрут
@app.get("/")
async def root():
    return {"message": "Skillmap API is running"}

# Проверка здоровья
@app.get("/health")
async def health_check():
    return {"status": "healthy"}