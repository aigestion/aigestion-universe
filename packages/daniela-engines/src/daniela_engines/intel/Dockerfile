FROM python:3.11-slim

WORKDIR /app

COPY engine/intel_engine/ ./intel_engine/

COPY engine/intel_engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 9850

CMD ["python", "-m", "intel_engine.server"]
