FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || true

COPY multi-region/ ./multi-region/

EXPOSE 8080

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
RUN chown -R appuser:appgroup /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "from multi_region.config import get_all_regions; print('ok')"

CMD ["python", "-m", "multi-region.server"]
