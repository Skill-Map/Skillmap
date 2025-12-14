# app/middleware.py (создайте новый файл)
import json
from fastapi import Request
from fastapi.responses import JSONResponse

async def fix_json_middleware(request: Request, call_next):
    """
    Middleware для исправления проблем с JSON сериализацией
    """
    try:
        # Попробуем прочитать тело запроса
        body = await request.body()
        
        # Если тело пустое, пропускаем
        if not body:
            return await call_next(request)
            
        # Пытаемся декодировать как JSON
        try:
            json_body = json.loads(body)
            # Если успешно, добавляем в state
            request.state.parsed_json = json_body
        except json.JSONDecodeError:
            # Если не JSON, оставляем как есть
            request.state.parsed_json = None
            
        response = await call_next(request)
        return response
        
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "detail": f"Ошибка обработки запроса: {str(e)}",
                "error_code": -1
            }
        )