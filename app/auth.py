# auth.py
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

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