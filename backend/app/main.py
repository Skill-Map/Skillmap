# placeholder FastAPI app (позже заменить полноценной реализацией)
try:
    from fastapi import FastAPI
    app = FastAPI()
    @app.get("/health")
    def health(): return {"status":"ok"}
except Exception:
    # Чтобы import не падал до установки зависимостей
    pass
