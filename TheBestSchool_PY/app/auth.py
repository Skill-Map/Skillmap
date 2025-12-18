# app/auth.py - ТОЛЬКО функции, без роутеров
from datetime import datetime, timedelta
from typing import Optional, Annotated
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
import models
from uuid import UUID
from jose.exceptions import ExpiredSignatureError

# Конфигурация JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Контекст для хэширования паролей
pwd_context = CryptContext(
    schemes=["argon2"],
    argon2__time_cost=2,
    argon2__memory_cost=102400,
    argon2__parallelism=8,
    argon2__hash_len=32,
    argon2__salt_len=16,
    deprecated="auto"
)

def get_password_hash(password: str) -> str:
    """Хэширование пароля"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Схема для аутентификации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db)
) -> models.User:
    """Получить текущего пользователя из токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.get(models.User, UUID(user_id))
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_user_optional(
    token: Annotated[str, Depends(oauth2_scheme)] = None,
    db: AsyncSession = Depends(get_db)
) -> Optional[models.User]:
    """Получить текущего пользователя или None если не авторизован"""
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except (JWTError, ExpiredSignatureError):
        return None
    
    user = await db.get(models.User, UUID(user_id))
    return user

def require_role(required_role: str):
    """Зависимость для проверки роли пользователя"""
    async def role_checker(current_user: models.User = Depends(get_current_user)):
        if current_user.type != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Требуется роль: {required_role}"
            )
        return current_user
    return role_checker

def require_roles(required_roles: list):
    """Зависимость для проверки нескольких ролей"""
    async def roles_checker(current_user: models.User = Depends(get_current_user)):
        if current_user.type not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Требуется одна из ролей: {', '.join(required_roles)}"
            )
        return current_user
    return roles_checker