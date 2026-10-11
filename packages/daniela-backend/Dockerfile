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
COPY --from=daniela-core . /daniela-core
COPY --from=daniela-engines . /daniela-engines
COPY --from=daniela-shared . /daniela-shared

# Install dependencies
COPY README.md ./

RUN uv pip install --system -e . --no-cache

# Expose port (perf-opt listens on WEB_PORT=9998 from agent_shared.config)
EXPOSE 9998

# Health check
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:9998/health || exit 1

# Run (standalone Flask entrypoint under hyphenated dir; not importable as module)
CMD ["python", "src/daniela_backend/perf-opt/server.py"]
