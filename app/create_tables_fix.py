# create_tables_fixed.py
#!/usr/bin/env python3
import asyncio
import sys
from database import engine
from models import Base

async def create_tables():
    try:
        print("🔧 Creating database tables...")
        async with engine.begin() as conn:
            # Сбрасываем все таблицы (ОСТОРОЖНО: удалит все данные!)
            # await conn.run_sync(Base.metadata.drop_all)
            
            # Создаем все таблицы
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Tables created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(create_tables())
    sys.exit(0 if success else 1)