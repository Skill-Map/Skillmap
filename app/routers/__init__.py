from .users import router as users_router
from .admins import router as admins_router
from .apprentices import router as apprentices_router
from .teachers import router as teachers_router
from .moderators import router as moderators_router
from .training import router as training_router
from .schedule import router as schedule_router
from .dev import router as dev_router

# Добавляем эндпоинт авторизации в main.py