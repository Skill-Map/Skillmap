from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
from database import get_db, AsyncSessionLocal
import crud
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

load_dotenv()

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await crud.get_user(db, user_id)
    if user is None:
        raise credentials_exception
    return user

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость для получения сессии БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
            
