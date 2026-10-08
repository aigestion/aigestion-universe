FROM python:3.11-slim

WORKDIR /app

COPY engine/secure_engine/ ./secure_engine/

COPY engine/secure_engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 9880

CMD ["python", "-m", "secure_engine.server"]
