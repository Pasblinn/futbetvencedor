# 🧠 MOTOR DE PREDIÇÕES REAL - Dockerfile atualizado
FROM python:3.11-slim

# Metadados
LABEL maintainer="Football Analytics Team"
LABEL description="Motor de predições com dados AO VIVO - matemática e análise combinatória"
LABEL version="2.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories for the real prediction engine
RUN mkdir -p \
    models \
    logs \
    cache \
    predictions \
    data/exports

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 🔧 Configurações específicas para motor real
ENV PREDICTION_ENGINE_VERSION=2.0
ENV ENABLE_REAL_TIME_PREDICTIONS=true
ENV CACHE_PREDICTIONS=true
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8000

# Health check mais robusto
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 🚀 Comando principal com reload para desenvolvimento
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]