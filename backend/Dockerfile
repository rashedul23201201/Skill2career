# Base image with Python 3.12 slim
FROM python:3.12-slim

# Prevent Python from writing .pyc files to disc & stdout/stderr buffering
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed for compiling C extensions if necessary
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and Alembic migrations
COPY . .

# Expose backend port
EXPOSE 8000

# Default command: run migrations then start server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
