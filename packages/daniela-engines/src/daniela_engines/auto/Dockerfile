FROM python:3.11-slim

WORKDIR /app

COPY engine/auto_engine/ ./auto_engine/

COPY engine/auto_engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 9860

CMD ["python", "-m", "auto_engine.server"]
