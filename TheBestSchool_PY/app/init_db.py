# init_db.py
from database import engine, SessionLocal
import models
from sqlalchemy.sql import text

def create_tables():
    """Создает все таблицы в базе данных"""
    print("Создание таблиц в базе данных...")
    models.Base.metadata.create_all(bind=engine)
    print("Таблицы успешно созданы!")

def check_tables_exist():
    """Проверяет существование таблиц"""
    session = SessionLocal()
    try:
        # Проверяем существование таблицы курсов
        result = session.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'courses')"))
        courses_exists = result.scalar()
        
        if not courses_exists:
            print("Таблицы не найдены. Создаем...")
            create_tables()
        else:
            print("Таблицы уже существуют.")
            
        return courses_exists
    finally:
        session.close()

if __name__ == "__main__":
    check_tables_exist()