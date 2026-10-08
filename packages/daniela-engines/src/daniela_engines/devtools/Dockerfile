FROM python:3.11-slim

WORKDIR /app

COPY engine/devtools_engine/ ./devtools_engine/

# requirements.txt (flask, psutil, pyyaml): debugger.py los importa.
COPY engine/devtools_engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 9890

CMD ["python", "-m", "devtools_engine.server"]
