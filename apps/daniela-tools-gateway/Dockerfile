FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /usr/local/bin/uv /usr/local/bin/uv

COPY pyproject.toml uv.lock* ./
COPY services/ ./services/

RUN uv pip install --system . --no-cache

EXPOSE 8083

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -f http://localhost:8083/health || exit 1

CMD ["uvicorn", "services.tools_gateway:create_app", "--host", "0.0.0.0", "--port", "8083", "--factory"]
