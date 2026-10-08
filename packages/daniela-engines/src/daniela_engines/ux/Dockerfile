FROM python:3.11-slim

WORKDIR /app

COPY engine/ux_engine/ ./ux_engine/

COPY engine/ux_engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 9830

CMD ["python", "-m", "ux_engine.server"]
