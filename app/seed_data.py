# seed_data.py
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from datetime import datetime
import json

def seed_courses(db: Session):
    """Заполняет базу данных тестовыми курсами"""
    
    # Проверяем, есть ли уже курсы
    existing_courses = db.query(models.Course).count()
    if existing_courses > 0:
        print(f"В базе уже есть {existing_courses} курсов. Пропускаем заполнение.")
        return
    
    print("Заполняем базу тестовыми данными...")
    
    # Курсы по категориям
    courses_data = [
        # IT курсы
        {
            "name": "Frontend-разработчик (React)",
            "description": "Полный путь от основ HTML/CSS до продвинутого React с TypeScript и современным стэком.",
            "category": "it",
            "category_name": "IT",
            "category_color": "#1A535C",
            "icon": "fab fa-react",
            "duration": "6 месяцев",
            "is_public": True,
            "modules": [
                {
                    "order": 1,
                    "title": "Основы веб-разработки",
                    "description": "Базовые технологии для старта карьеры фронтенд-разработчика",
                    "recommended_time": "3-4 недели",
                    "lessons": [
                        {
                            "order": 1,
                            "title": "HTML5 и семантическая верстка",
                            "description": "Изучение современной HTML разметки, семантических тегов и доступности"
                        },
                        {
                            "order": 2,
                            "title": "CSS3 и адаптивная верстка",
                            "description": "Современный CSS, Flexbox, Grid и создание адаптивных интерфейсов"
                        },
                        {
                            "order": 3,
                            "title": "JavaScript основы",
                            "description": "Фундаментальные концепции JavaScript: переменные, функции, объекты, массивы"
                        },
                        {
                            "order": 4,
                            "title": "DOM манипуляции и события",
                            "description": "Работа с Document Object Model и обработка пользовательских событий"
                        }
                    ]
                },
                {
                    "order": 2,
                    "title": "Продвинутый JavaScript",
                    "description": "Глубокое погружение в современный JavaScript и его особенности",
                    "recommended_time": "4-5 недель",
                    "lessons": [
                        {
                            "order": 1,
                            "title": "Асинхронное программирование",
                            "description": "Promise, async/await, работа с API и обработка асинхронных операций"
                        },
                        {
                            "order": 2,
                            "title": "ES6+ особенности и современный синтаксис",
                            "description": "Стрелочные функции, деструктуризация, модули, spread/rest операторы"
                        },
                        {
                            "order": 3,
                            "title": "Модульность и сборка проектов",
                            "description": "Webpack, импорты/экспорты, настройка среды разработки"
                        },
                        {
                            "order": 4,
                            "title": "Тестирование JavaScript кода",
                            "description": "Unit testing с Jest, интеграционное тестирование, TDD подход"
                        }
                    ]
                },
                {
                    "order": 3,
                    "title": "React и экосистема",
                    "description": "Библиотека для создания современных пользовательских интерфейсов",
                    "recommended_time": "6-8 недель",
                    "lessons": [
                        {
                            "order": 1,
                            "title": "Основы React: компоненты и состояние",
                            "description": "Компонентный подход, props, state, жизненный цикл компонентов"
                        },
                        {
                            "order": 2,
                            "title": "Хуки и контекст",
                            "description": "useState, useEffect, useContext и создание кастомных хуков"
                        },
                        {
                            "order": 3,
                            "title": "Маршрутизация и state-менеджмент",
                            "description": "React Router для SPA, Redux/Toolkit для управления состоянием"
                        },
                        {
                            "order": 4,
                            "title": "TypeScript с React",
                            "description": "Типизированные компоненты, пропсы, хуки и события"
                        },
                        {
                            "order": 5,
                            "title": "Оптимизация и производительность",
                            "description": "Memo, useMemo, useCallback, ленивая загрузка, анализ бандла"
                        }
                    ]
                },
                {
                    "order": 4,
                    "title": "Профессиональный уровень и деплой",
                    "description": "Инструменты и практики для работы в команде и продакшена",
                    "recommended_time": "4-6 недель",
                    "lessons": [
                        {
                            "order": 1,
                            "title": "Тестирование React-приложений",
                            "description": "Jest, React Testing Library, Cypress для e2e тестирования"
                        },
                        {
                            "order": 2,
                            "title": "CI/CD и автоматизация",
                            "description": "GitHub Actions, автоматическое тестирование и деплой"
                        },
                        {
                            "order": 3,
                            "title": "Деплой и мониторинг",
                            "description": "Vercel, Netlify, AWS Amplify, мониторинг производительности"
                        },
                        {
                            "order": 4,
                            "title": "Подготовка к собеседованию",
                            "description": "Типовые задачи, поведенческие вопросы, составление портфолио"
                        }
                    ]
                }
            ]
        },
        {
            "name": "Backend на Python и FastAPI",
            "description": "Создание производительных backend-приложений с использованием Python и FastAPI.",
            "category": "it",
            "category_name": "IT",
            "category_color": "#1A535C",
            "icon": "fab fa-python",
            "duration": "5 месяцев",
            "is_public": True,
            "modules": [
                {
                    "order": 1,
                    "title": "Основы Python для backend",
                    "description": "Синтаксис Python и особенности языка для серверной разработки",
                    "recommended_time": "4 недели",
                    "lessons": [
                        {
                            "order": 1,
                            "title": "Python: основы и особенности",
                            "description": "Синтаксис, структуры данных, функции и объектно-ориентированное программирование"
                        },
                        {
                            "order": 2,
                            "title": "Асинхронное программирование в Python",
                            "description": "Async/await, asyncio, конкурентность и параллелизм"
                        }
                    ]
                },
                {
                    "order": 2,
                    "title": "FastAPI и создание API",
                    "description": "Современный фреймворк для создания быстрых и типизированных API",
                    "recommended_time": "6 недель",
                    "lessons": [
                        {
                            "order": 1,
                            "title": "Введение в FastAPI",
                            "description": "Установка, первое приложение, автоматическая документация OpenAPI"
                        },
                        {
                            "order": 2,
                            "title": "Маршруты, зависимости и валидация",
                            "description": "Создание эндпоинтов, внедрение зависимостей, Pydantic модели"
                        }
                    ]
                }
            ]
        },
        {
            "name": "DevOps: от основ к практике",
            "description": "Освойте инструменты DevOps для автоматизации развертывания и управления инфраструктурой.",
            "category": "it",
            "category_name": "IT",
            "category_color": "#1A535C",
            "icon": "fas fa-server",
            "duration": "7 месяцев",
            "is_public": True,
            "modules": []
        },
        
        # Финансы
        {
            "name": "Финансовый аналитик",
            "description": "Анализ финансовых рынков, оценка инвестиций и управление рисками.",
            "category": "finance",
            "category_name": "Финансы",
            "category_color": "#10B981",
            "icon": "fas fa-chart-line",
            "duration": "4 месяца",
            "is_public": True,
            "modules": [
                {
                    "order": 1,
                    "title": "Основы финансового анализа",
                    "description": "Фундаментальные понятия и инструменты финансового аналитика",
                    "lessons": [
                        {
                            "order": 1,
                            "title": "Финансовая отчетность",
                            "description": "Чтение и анализ балансовых отчетов, отчетов о прибылях и убытках"
                        }
                    ]
                }
            ]
        },
        {
            "name": "Инвестиционный банкир",
            "description": "Структурирование сделок, оценка компаний и работа с клиентами.",
            "category": "finance",
            "category_name": "Финансы",
            "category_color": "#10B981",
            "icon": "fas fa-university",
            "duration": "5 месяцев",
            "is_public": True,
            "modules": []
        },
        
        # Юриспруденция
        {
            "name": "Корпоративный юрист",
            "description": "Правовое сопровождение бизнеса, договорная работа и корпоративное управление.",
            "category": "law",
            "category_name": "Юриспруденция",
            "category_color": "#8B5CF6",
            "icon": "fas fa-gavel",
            "duration": "6 месяцев",
            "is_public": True,
            "modules": [
                {
                    "order": 1,
                    "title": "Основы корпоративного права",
                    "description": "Правовые основы деятельности компаний различных организационно-правовых форм",
                    "lessons": [
                        {
                            "order": 1,
                            "title": "Корпоративное управление",
                            "description": "Права и обязанности акционеров, совета директоров, исполнительных органов"
                        }
                    ]
                }
            ]
        },
        {
            "name": "Юрист по интеллектуальной собственности",
            "description": "Защита авторских прав, товарных знаков и патентов.",
            "category": "law",
            "category_name": "Юриспруденция",
            "category_color": "#8B5CF6",
            "icon": "fas fa-copyright",
            "duration": "4 месяца",
            "is_public": True,
            "modules": []
        },
        
        # Геология
        {
            "name": "Геолог-нефтяник",
            "description": "Поиск и разведка месторождений нефти и газа, анализ геологических данных.",
            "category": "geology",
            "category_name": "Геология",
            "category_color": "#F59E0B",
            "icon": "fas fa-mountain",
            "duration": "8 месяцев",
            "is_public": True,
            "modules": [
                {
                    "order": 1,
                    "title": "Основы геологии нефти и газа",
                    "description": "Формирование, миграция и залегание углеводородов в земной коре",
                    "lessons": [
                        {
                            "order": 1,
                            "title": "Стратиграфия и литология",
                            "description": "Изучение горных пород и их последовательностей для определения нефтегазоносности"
                        }
                    ]
                }
            ]
        },
        
        # Маркетинг
        {
            "name": "Digital-маркетолог",
            "description": "Продвижение брендов в digital-среде, работа с социальными сетями и аналитика.",
            "category": "marketing",
            "category_name": "Маркетинг",
            "category_color": "#EF4444",
            "icon": "fas fa-bullhorn",
            "duration": "3 месяца",
            "is_public": True,
            "modules": [
                {
                    "order": 1,
                    "title": "Основы digital-маркетинга",
                    "description": "Каналы продвижения, метрики эффективности и инструменты аналитики",
                    "lessons": [
                        {
                            "order": 1,
                            "title": "SMM и контент-стратегии",
                            "description": "Продвижение в социальных сетях, создание контент-планов и работа с аудиторией"
                        }
                    ]
                }
            ]
        },
        
        # Менеджмент
        {
            "name": "Проектный менеджер",
            "description": "Управление проектами от инициации до закрытия, работа с командами и стейкхолдерами.",
            "category": "management",
            "category_name": "Менеджмент",
            "category_color": "#0EA5E9",
            "icon": "fas fa-users",
            "duration": "4 месяца",
            "is_public": True,
            "modules": [
                {
                    "order": 1,
                    "title": "Методологии управления проектами",
                    "description": "Agile, Scrum, Waterfall и другие подходы к управлению проектами",
                    "lessons": [
                        {
                            "order": 1,
                            "title": "Основы Scrum",
                            "description": "Роли, артефакты и церемонии в Scrum фреймворке"
                        }
                    ]
                }
            ]
        }
    ]
    
    # Создаем курсы, модули и уроки
    for course_data in courses_data:
        modules_data = course_data.pop('modules', [])
        
        course = models.Course(**course_data)
        db.add(course)
        db.flush()  # Получаем ID курса
        
        # Создаем модули для курса
        for module_data in modules_data:
            lessons_data = module_data.pop('lessons', [])
            
            module = models.CourseModule(course_id=course.id, **module_data)
            db.add(module)
            db.flush()  # Получаем ID модуля
            
            # Создаем уроки для модуля
            for lesson_data in lessons_data:
                lesson = models.CourseLesson(module_id=module.id, **lesson_data)
                db.add(lesson)
    
    # Создаем тестовые вакансии
    vacancies_data = [
        {
            "hh_id": "12345678",
            "title": "Junior Frontend Developer (React)",
            "company": "ООО Яндекс.Технологии",
            "salary": "от 120 000 руб.",
            "experience": "1-3 года",
            "employment": "полная занятость",
            "description": "Разработка пользовательских интерфейсов для внутренних сервисов компании",
            "skills": ["JavaScript", "React", "TypeScript", "HTML", "CSS", "Git"],
            "url": "https://hh.ru/vacancy/12345678"
        },
        {
            "hh_id": "87654321",
            "title": "Python Backend Developer",
            "company": "ОАО СберТех",
            "salary": "от 180 000 руб.",
            "experience": "3-6 лет",
            "employment": "полная занятость",
            "description": "Разработка микросервисной архитектуры для банковских систем",
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes", "Linux"],
            "url": "https://hh.ru/vacancy/87654321"
        },
        {
            "hh_id": "11223344",
            "title": "DevOps Engineer",
            "company": "ООО ВК Технологии",
            "salary": "от 200 000 руб.",
            "experience": "2-4 года",
            "employment": "полная занятость",
            "description": "Настройка и поддержка CI/CD пайплайнов, мониторинг инфраструктуры",
            "skills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Terraform", "Linux"],
            "url": "https://hh.ru/vacancy/11223344"
        }
    ]
    
    vacancies = []
    for vacancy_data in vacancies_data:
        # Преобразуем skills в JSON
        vacancy_data["skills"] = json.dumps(vacancy_data["skills"])
        vacancy = models.Vacancy(**vacancy_data)
        db.add(vacancy)
        vacancies.append(vacancy)
    
    db.flush()
    
    # Связываем курсы с вакансиями
    # Frontend курс с Frontend вакансией
    frontend_course = db.query(models.Course).filter(models.Course.name.ilike("%Frontend%")).first()
    frontend_vacancy = next((v for v in vacancies if "Frontend" in v.title), None)
    
    if frontend_course and frontend_vacancy:
        course_vacancy = models.CourseVacancy(
            course_id=frontend_course.id,
            vacancy_id=frontend_vacancy.id
        )
        db.add(course_vacancy)
    
    # Backend курс с Backend вакансией
    backend_course = db.query(models.Course).filter(models.Course.name.ilike("%Backend%")).first()
    backend_vacancy = next((v for v in vacancies if "Python" in v.title), None)
    
    if backend_course and backend_vacancy:
        course_vacancy = models.CourseVacancy(
            course_id=backend_course.id,
            vacancy_id=backend_vacancy.id
        )
        db.add(course_vacancy)
    
    # DevOps курс с DevOps вакансией
    devops_course = db.query(models.Course).filter(models.Course.name.ilike("%DevOps%")).first()
    devops_vacancy = next((v for v in vacancies if "DevOps" in v.title), None)
    
    if devops_course and devops_vacancy:
        course_vacancy = models.CourseVacancy(
            course_id=devops_course.id,
            vacancy_id=devops_vacancy.id
        )
        db.add(course_vacancy)
    
    # Создаем тестового пользователя если его нет
    user = db.query(models.User).filter(models.User.email == "test@example.com").first()
    if not user:
        user = models.User(
            email="test@example.com",
            surname="Иванов",
            name="Иван",
            password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # пароль: secret
            type="apprentice",
            phone="79991234567",
            status="active",
            track_id="track_001",
            group_code="A-2023",
            hours_per_week=20,
            enrollment_date="01.09.2023",
            expected_graduation="01.09.2024"
        )
        db.add(user)
        db.flush()
    
    # Создаем тестовый прогресс пользователя
    if frontend_course:
        progress = models.UserCourseProgress(
            user_id=user.id,
            course_id=frontend_course.id,
            progress_percent=25.0,
            completed_lessons=json.dumps([])  # пустой список для начала
        )
        db.add(progress)
    
    db.commit()
    print(f"Успешно создано:")
    print(f"- Курсов: {len(courses_data)}")
    print(f"- Вакансий: {len(vacancies)}")
    print(f"- Модулей: {sum(len(course.get('modules', [])) for course in courses_data)}")
    print(f"- Уроков: {sum(len(module.get('lessons', [])) for course in courses_data for module in course.get('modules', []))}")

def main():
    """Основная функция для заполнения данных"""
    db = SessionLocal()
    try:
        seed_courses(db)
        print("\n" + "="*50)
        print("База данных успешно заполнена тестовыми данными!")
        print("="*50)
    except Exception as e:
        db.rollback()
        print(f"\nОшибка при заполнении данных: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()