# Backend Dockerfile for FastAPI
FROM python:3.11-slim
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# Copy application code
COPY . .

EXPOSE 8000

# Adjust the module path (main:app or app.main:app) as needed for your project
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
