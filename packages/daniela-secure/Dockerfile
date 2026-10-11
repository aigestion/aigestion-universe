FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (binary is at /uv in the uv image)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/
COPY secure_engine/ ./secure_engine/
COPY --from=daniela-core . /daniela-core
COPY --from=daniela-shared . /daniela-shared
COPY --from=daniela-engines . /daniela-engines

# Install dependencies
COPY README.md ./

RUN uv pip install --system -e . --no-cache

# Expose port (will be overridden by docker-compose)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run (secure_engine/ is a namespace package at repo root)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "secure_engine.server:create_app()"]
