# database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
import os

# URL базы данных
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/skillmap")

# Создаем движок
engine = create_async_engine(DATABASE_URL, echo=True)

# Создаем фабрику сессий
AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Базовый класс для моделей
Base = declarative_base()

# Зависимость для получения сессии базы данных
async def get_db():
    """Получение сессии базы данных"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()