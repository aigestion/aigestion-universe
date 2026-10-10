FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    flask==3.0.* \
    flask-cors==4.0.* \
    gunicorn==22.* \
    redis==5.0.* \
    psutil==5.9.* \
    requests==2.31.*

# Build context is the REPO ROOT.
COPY packages/daniela-backend/src/daniela_backend/perf-opt/ ./

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME=perf
ENV PORT=9998

EXPOSE 9998

CMD ["gunicorn", "--bind", "0.0.0.0:9998", "--workers", "2", "--threads", "4", "--timeout", "120", "server:app"]
