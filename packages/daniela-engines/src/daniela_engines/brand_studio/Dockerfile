FROM python:3.11-slim

WORKDIR /app

COPY shared/ ./shared/
RUN pip install --no-cache-dir ./shared

COPY engine/brand_studio/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# ffmpeg: el endpoint /api/brand/render lo exige (503 honesto sin el).
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY engine/brand_studio/ ./brand_studio/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 9920

CMD ["python", "-m", "brand_studio.server"]
