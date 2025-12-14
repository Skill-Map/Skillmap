# routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import crud
from pydantic import BaseModel, EmailStr, Field
from auth import create_access_token
from datetime import timedelta
import os
import schemas
from typing import Optional

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: str = Field(..., min_length=11, max_length=11)  # 11 цифр
    surname: str
    name: str
    patronymic: Optional[str] = None

class LoginRequest(BaseModel):
    username: EmailStr
    password: str

class TokenResponse(BaseModel):
    access: str
    refresh: str | None = None  # можно добавить refresh token позже

@router.post("/register")
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    # Проверяем телефон (только цифры)
    if not payload.phone.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Номер телефона должен содержать только цифры"
        )
    
    # Проверяем длину телефона
    if len(payload.phone) != 11:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Номер телефона должен содержать 11 цифр"
        )
    
    # Создаём ученика с переданными значениями
    try:
        user = await crud.create_user(
            db,
            email=payload.email,
            password=payload.password,
            type=schemas.UserType.APPRENTICE,
            surname=payload.surname,
            name=payload.name,
            patronymic=payload.patronymic,
            phone=payload.phone,  # Передаем телефон
            status="active",
            track_id="default",
            group_code="A1",
            advisor_user_id=None,
            hours_per_week=0,
            enrollment_date="",
            expected_graduation=""
        )

        # Создаём токен для автоматического входа
        access_token = create_access_token({"sub": str(user.id)})
        
        return {
            "ok": True, 
            "user_id": str(user.id),
            "access": access_token  # Возвращаем токен сразу
        }
        
    except Exception as e:
        # Проверяем, если это ошибка уникальности (дубликат email или телефона)
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Пользователь с таким email или телефоном уже существует"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при создании пользователя: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await crud.authenticate_user(db, payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = create_access_token({"sub": str(user.id)})  # Преобразуем UUID в строку
    return {"access": access_token, "refresh": None}