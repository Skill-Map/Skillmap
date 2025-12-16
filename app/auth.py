# auth.py
from datetime import datetime, timedelta
from typing import Optional, Annotated
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
# Конфигурация JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Контекст для хэширования паролей
pwd_context = CryptContext(
    schemes=["argon2"],  # Argon2 вместо bcrypt
    argon2__time_cost=2,  # Время вычисления (больше = медленнее, но безопаснее)
    argon2__memory_cost=102400,  # Память в КБ
    argon2__parallelism=8,  # Параллелизм
    argon2__hash_len=32,  # Длина хэша
    argon2__salt_len=16,  # Длина соли
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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(lambda: None)  # Заглушка, замените на вашу функцию get_db
):
    """Получить текущего пользователя из токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Здесь должна быть функция для получения пользователя из БД
    # Пока используем заглушку
    from models import User
    return User(
        id=1,
        email=email,
        type="admin",  # По умолчанию админ для разработки
        active=True
    )

def require_role(required_role: str):
    """Зависимость для проверки роли пользователя"""
    async def role_checker(current_user = Depends(get_current_user)):
        if current_user.type != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Требуется роль: {required_role}"
            )
        return current_user
    return role_checker

# Альтернативная функция для проверки нескольких ролей
def require_roles(required_roles: list):
    """Зависимость для проверки нескольких ролей"""
    async def roles_checker(current_user = Depends(get_current_user)):
        if current_user.type not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Требуется одна из ролей: {required_roles}"
            )
        return current_user
    return roles_checker