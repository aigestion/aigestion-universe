FROM python:3.11-slim

WORKDIR /app

# Runtime deps for the Hermes service (Flask app + registry/event bus).
# No `aig-base`: that image belongs to the legacy repo and is not in this one.
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    flask==3.0.* \
    flask-cors==4.0.* \
    flask-socketio==5.3.* \
    gunicorn==22.* \
    redis==5.0.* \
    psutil==5.9.* \
    requests==2.31.* \
    httpx==0.28.* \
    aiohttp==3.9.* \
    casbin==1.43.*

# Hermes service tree (server.py + advanced/integration/memory/personality/skills).
COPY apps/hermes-ide/hermes/ ./

# server.py imports `core.auth.casbin_auth`, `core.message_broker` and
# `core.service_registry`. In this repo those live in daniela-shared's
# `core_utils/`; they are copied as a flat `core/` package and `/app/core` is
# added to PYTHONPATH so the legacy flat imports inside them
# (`from paths import ...` in message_broker) keep resolving.
COPY packages/daniela-shared/src/daniela_shared/core_utils/ ./core/

ENV PYTHONPATH=/app:/app/core
ENV PYTHONUNBUFFERED=1
ENV SERVICE_NAME=hermes
ENV PORT=9300

EXPOSE 9300

CMD ["gunicorn", "--bind", "0.0.0.0:9300", "--workers", "2", "--threads", "4", "--timeout", "120", "server:app"]
