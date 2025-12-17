#!/usr/bin/env python3
# create_tables.py
import asyncio
import sys
from sqlalchemy import text
from database import engine
import models

async def create_tables():
    try:
        print("🔧 Creating database tables...")
        
        # Импортируем метаданные моделей
        from models import Base
        
        async with engine.begin() as conn:
            # Создаем все таблицы
            await conn.run_sync(Base.metadata.create_all)
            
            # Проверяем наличие столбца phone в таблице users
            # Используем text() для SQL запросов
            query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='phone'
            """)
            
            result = await conn.execute(query)
            column_exists = result.fetchone() is not None
            
            if not column_exists:
                print("➕ Adding 'phone' column to 'users' table...")
                # Добавляем столбец phone
                alter_query = text("""
                    ALTER TABLE users 
                    ADD COLUMN phone VARCHAR(11),
                    ADD CONSTRAINT users_phone_unique UNIQUE (phone)
                """)
                await conn.execute(alter_query)
                print("✅ 'phone' column added successfully!")
            else:
                print("ℹ️ 'phone' column already exists.")
        
        print("✅ Tables created/updated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating/updating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(create_tables())
    sys.exit(0 if success else 1)