#!/usr/bin/env python3
"""
Скрипт для создания таблиц в базе данных
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
import models

async def create_tables():
    """Создает все таблицы в базе данных"""
    # URL базы данных из переменных окружения
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://bestschool_user:csrnsdrfh@postgres:5432/bestschool_db")
    
    print(f"🔗 Подключение к базе данных...")
    print(f"📡 URL: {DATABASE_URL.replace('csrnsdrfh', '*******')}")
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    try:
        # Создаем все таблицы
        async with engine.begin() as conn:
            print("🗄️ Создание таблиц...")
            await conn.run_sync(models.Base.metadata.create_all)
            print("✅ Таблицы успешно созданы!")
            
        # Закрываем соединение
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Запуск создания таблиц...")
    asyncio.run(create_tables())