from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/dev", tags=["dev"])

@router.get("/info", response_class=HTMLResponse)
async def dev_info():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dev Info - Fitness API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            h1 { color: #333; }
            .endpoint { background: #f4f4f4; padding: 10px; margin: 10px 0; }
            code { background: #eee; padding: 2px 5px; }
        </style>
    </head>
    <body>
        <h1>Fitness API Development Info</h1>
        <p>Backend порт: 8082</p>
        <p>База данных: PostgreSQL</p>
        <p>Документация API: <a href="/docs">Swagger UI</a></p>
        <p>Альтернативная документация: <a href="/redoc">ReDoc</a></p>
        
        <h2>Тестовые пользователи:</h2>
        <ul>
            <li><strong>Admin:</strong> admin / admin123</li>
            <li><strong>Teacher:</strong> teacher / teacher123</li>
            <li><strong>Student:</strong> student / student123</li>
            <li><strong>Moderator:</strong> moderator / moderator123</li>
        </ul>
        
        <h2>Основные эндпоинты:</h2>
        <div class="endpoint"><code>POST /login</code> - Авторизация</div>
        <div class="endpoint"><code>GET /user</code> - Текущий пользователь</div>
        <div class="endpoint"><code>POST /admin</code> - Создать администратора</div>
        <div class="endpoint"><code>POST /apprentice</code> - Создать ученика</div>
        <div class="endpoint"><code>POST /trainer</code> - Создать преподавателя</div>
        <div class="endpoint"><code>POST /training/{trainerId}/{apprenticeId}</code> - Создать тренировку</div>
    </body>
    </html>
    """

@router.get("/links")
async def dev_links():
    return {
        "links": [
            {"url": "/dev/info", "description": "HTML-страница с информацией"},
            {"url": "/docs", "description": "Swagger UI документация"},
            {"url": "/redoc", "description": "ReDoc документация"},
            {"url": "/health", "description": "Health check endpoint"},
            {"url": "/", "description": "Корневой endpoint"}
        ]
    }