FROM python:3.11-slim

WORKDIR /app

COPY engine/data_engine/ ./data_engine/

COPY engine/data_engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 9870

CMD ["python", "-m", "data_engine.server"]
