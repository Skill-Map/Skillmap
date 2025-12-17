# app/vacancies.py - дополненная версия
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import models
from database import get_db

router = APIRouter(prefix="/api/v1/vacancies", tags=["vacancies"])

# Модель для анализа вакансий
class VacancyAnalysisRequest(BaseModel):
    title: str
    links: List[str]
    level: Optional[str] = "junior"

@router.get("/")
async def get_vacancies(
    limit: Optional[int] = 20,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить список вакансий"""
    try:
        query = select(models.Vacancy).order_by(models.Vacancy.id.desc())
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (models.Vacancy.title.ilike(search_term)) |
                (models.Vacancy.company.ilike(search_term))
            )
        
        if limit:
            query = query.limit(limit)
        
        result = await db.execute(query)
        vacancies = result.scalars().all()
        
        return [
            {
                "id": vacancy.id,
                "hh_id": vacancy.hh_id,
                "title": vacancy.title,
                "company": vacancy.company,
                "salary": vacancy.salary,
                "experience": vacancy.experience,
                "employment": vacancy.employment,
                "description": vacancy.description,
                "skills": vacancy.skills,
                "url": vacancy.url,
                "created_at": vacancy.created_at.isoformat() if vacancy.created_at else None
            }
            for vacancy in vacancies
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения вакансий: {str(e)}")

@router.post("/analyze")
async def analyze_vacancies(
    request: VacancyAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """Анализ вакансий и рекомендация курсов"""
    try:
        title = request.title.strip()
        links = request.links
        level = request.level
        
        if not title:
            raise HTTPException(status_code=400, detail="Не указано название вакансии")
        
        if not links:
            raise HTTPException(status_code=400, detail="Не указаны ссылки на вакансии")
        
        # Парсим ID вакансий из ссылок
        vacancy_ids = []
        for link in links:
            if isinstance(link, str) and "hh.ru/vacancy/" in link:
                # Извлекаем ID вакансии из URL
                import re
                match = re.search(r'hh\.ru/vacancy/(\d+)', link)
                if match:
                    vacancy_ids.append(match.group(1))
        
        # Получаем все курсы
        courses_query = select(models.Course).where(models.Course.is_public == True)
        courses_result = await db.execute(courses_query)
        all_courses = courses_result.scalars().all()
        
        # Простой анализ ключевых слов
        keywords = set(word.lower() for word in title.split() if len(word) > 2)
        
        # Добавляем типичные ключевые слова по категориям
        category_keywords = {
            "it": {"frontend", "backend", "react", "python", "javascript", "java", "devops", "data"},
            "finance": {"finance", "analyst", "accounting", "budget", "investment", "bank"},
            "law": {"law", "lawyer", "legal", "corporate", "contract", "justice"},
            "marketing": {"marketing", "digital", "smm", "seo", "content", "advertising"},
            "management": {"management", "project", "manager", "team", "lead", "product"},
            "geology": {"geology", "geologist", "mining", "oil", "gas", "resources"},
            "design": {"design", "designer", "ui", "ux", "interface", "graphic"},
            "medicine": {"medicine", "clinical", "research", "healthcare", "medical"}
        }
        
        # Рекомендуем курсы на основе ключевых слов
        recommended_courses = []
        for course in all_courses:
            score = 0
            reasons = []
            
            # Проверяем совпадение по названию вакансии
            course_name_lower = course.name.lower()
            for keyword in keywords:
                if keyword in course_name_lower:
                    score += 3
                    reasons.append(f"Ключевое слово '{keyword}' в названии курса")
            
            # Проверяем совпадение по описанию
            course_desc_lower = (course.description or "").lower()
            for keyword in keywords:
                if keyword in course_desc_lower:
                    score += 1
                    reasons.append(f"Ключевое слово '{keyword}' в описании курса")
            
            # Проверяем по категорийным ключевым словам
            if course.category in category_keywords:
                category_words = category_keywords[course.category]
                matched_keywords = keywords.intersection(category_words)
                if matched_keywords:
                    score += len(matched_keywords) * 2
                    reasons.append(f"Совпадение по категорийным ключевым словам")
            
            if score > 0:
                recommended_courses.append({
                    "id": course.id,
                    "name": course.name,
                    "description": course.description,
                    "category": course.category,
                    "category_name": course.category_name,
                    "category_color": course.category_color,
                    "duration": course.duration,
                    "score": score,
                    "reasons": reasons[:3]
                })
        
        # Сортируем по убыванию релевантности
        recommended_courses.sort(key=lambda x: x["score"], reverse=True)
        
        return {
            "analysis_id": f"analysis_{int(datetime.now().timestamp())}",
            "vacancy": {
                "title": title,
                "links": links,
                "parsed_ids": vacancy_ids,
                "level": level
            },
            "recommendations": {
                "total_courses_found": len(recommended_courses),
                "top_courses": recommended_courses[:5],
                "suggested_plan": {
                    "duration_estimate": "4-6 месяцев",
                    "weekly_hours": "15-20 часов",
                    "starting_point": recommended_courses[0]["name"] if recommended_courses else "Базовые курсы"
                }
            },
            "analysis_date": datetime.now().isoformat(),
            "next_steps": [
                "Выберите наиболее релевантный курс из рекомендаций",
                "Изучите программу курса",
                "Создайте учебный план с учетом вашего уровня",
                "Начните с первого модуля выбранного курса"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка анализа вакансий: {str(e)}")