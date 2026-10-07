FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /usr/local/bin/uv /usr/local/bin/uv

# Copy project files (flat layout: modules at root)
COPY pyproject.toml uv.lock* ./
COPY *.py ./
COPY routes/ ./routes/

# Install dependencies
RUN uv pip install --system -e . --no-cache

# Expose port
EXPOSE 9200

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:9200/health || exit 1

# Run (flat layout: top-level api module, cwd /app on sys.path)
CMD ["uvicorn", "api:create_app", "--host", "0.0.0.0", "--port", "9200", "--workers", "2"]
