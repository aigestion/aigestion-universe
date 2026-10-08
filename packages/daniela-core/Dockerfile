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

# Copy project files (src-layout)
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/

# Install dependencies (editable install from src layout)
RUN uv pip install --system -e . --no-cache

# Expose port
EXPOSE 9200

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:9200/health || exit 1

# Run (entrypoint is daniela_core.api:create_app via pyproject.toml [project.scripts])
CMD ["uvicorn", "daniela_core.api:create_app", "--host", "0.0.0.0", "--port", "9200", "--workers", "2"]