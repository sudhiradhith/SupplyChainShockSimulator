# Multi-stage optimized Dockerfile for Supply Chain Shock Simulator
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=10000

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt requirements-dashboard.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements-dashboard.txt

# Copy application source code
COPY . .

# Expose Render standard port (10000) and local dev port (8501)
EXPOSE 10000 8501

# Default command launches Streamlit Dashboard
CMD ["sh", "-c", "streamlit run app/main.py --server.port=${PORT:-10000} --server.address=0.0.0.0"]
