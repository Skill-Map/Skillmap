FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt || true
COPY backend /app/backend
WORKDIR /app/backend
CMD ["python","-c","print('Backend placeholder. Replace with uvicorn app.main:app')"]
