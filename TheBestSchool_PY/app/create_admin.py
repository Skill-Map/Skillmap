#!/usr/bin/env python3
"""
Скрипт для создания администратора через SQLAlchemy
"""

import asyncio
import bcrypt
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# Импортируем модели
from models import Base, User

# Настройки базы данных - УКАЖИТЕ СВОИ!
DATABASE_URL = "postgresql+asyncpg://bestschool_user:csrnsdrfh@localhost:5433/bestschool_db"
# Если у вас другой пароль/хост/база, измените:
# postgresql+asyncpg://username:password@host/database_name

async def create_admin_user():
    """Создает администратора в базе данных"""
    
    print("🚀 Подключение к базе данных...")
    
    # Создаем движок
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    # Создаем фабрику сессий
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            # Проверяем, есть ли уже админ с таким email
            print("🔍 Проверяем существующих пользователей...")
            result = await session.execute(
                select(User).where(User.email == "admin2@skillmap.ru")
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                print(f"❌ Администратор уже существует!")
                print(f"   Email: {existing.email}")
                print(f"   Тип: {existing.type}")
                print(f"   ID: {existing.id}")
                
                # Проверяем, является ли он админом
                if existing.type != "admin":
                    print("⚠️  Пользователь существует, но не админ. Обновляю...")
                    existing.type = "admin"
                    existing.super_permissions = True
                    existing.can_manage_roles = True
                    existing.can_manage_billing = True
                    existing.can_impersonate = True
                    await session.commit()
                    print("✅ Тип пользователя обновлен на 'admin'")
                
                return
            
            # Хешируем пароль
            password = "admin123"
            print(f"🔐 Хеширование пароля: {password}")
            hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            
            # Создаем администратора
            admin = User(
                id=uuid.uuid4(),
                email="admin2@skillmap.ru",
                surname="Админ",
                name="Главный",
                patronymic="",
                password=hashed_password,
                type="admin",
                active=True,
                super_permissions=True,
                can_manage_roles=True,
                can_manage_billing=True,
                can_impersonate=True,
                phone="79998887766"  # Добавляем телефон
            )
            
            session.add(admin)
            await session.commit()
            
            print("\n" + "="*50)
            print("✅ АДМИНИСТРАТОР УСПЕШНО СОЗДАН!")
            print("="*50)
            print(f"📧 Email: admin2@skillmap.ru")
            print(f"🔑 Пароль: admin123")
            print(f"👤 ФИО: Админ Главный")
            print(f"📱 Телефон: 79998887766")
            print(f"🎯 Тип: admin")
            print(f"🆔 ID: {admin.id}")
            print("\n⚠️  ВНИМАНИЕ: Смените пароль после первого входа!")
            print("="*50)
            
        except Exception as e:
            print(f"❌ Ошибка при создании администратора: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    print("Начинаем создание администратора...")
    asyncio.run(create_admin_user())