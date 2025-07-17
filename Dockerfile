# Multi-stage Docker build for Halifax Bar Sentiment Analysis
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Development stage
FROM base as development

# Install development dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code
COPY . .

# Set ownership
RUN chown -R appuser:appuser /app
USER appuser

# Development command
CMD ["python", "-m", "uvicorn", "src.api.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

# Production stage
FROM base as production

# Install only production dependencies
COPY requirements.txt .
RUN pip install --no-dev -r requirements.txt

# Copy source code
COPY --from=development /app/src ./src
COPY --from=development /app/main.py .

# Set ownership
RUN chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "src.api.main:app"]