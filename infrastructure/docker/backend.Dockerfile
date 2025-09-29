# Use a small Python image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/home/app/.local/bin:$PATH"

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc ca-certificates && \
    pip install --no-cache-dir -r /app/requirements.txt && \
    apt-get purge -y --auto-remove build-essential gcc && \
    rm -rf /var/lib/apt/lists/*


COPY backend /app/backend

WORKDIR /app/backend

RUN addgroup --system app && adduser --system --ingroup app app && chown -R app:app /app

USER app

EXPOSE 8000

# Healthcheck uses python builtin urllib to avoid adding curl
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request, sys; \
try: r=urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=3); \
sys.exit(0 if r.getcode()==200 else 1); \
except Exception: sys.exit(1)"

# Production command (uvicorn serving main:app)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--app-dir", "/app/backend"]
