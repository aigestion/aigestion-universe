FROM python:3.11-slim

WORKDIR /app

# aig-shared is a common dependency (auth middleware, pools, registry).
# Build context is the REPO ROOT, hence the ./shared/ prefix.
COPY aig-shared/ ./shared/
RUN pip install --no-cache-dir ./shared

COPY engine/{{slug}}/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY engine/{{slug}}/ ./{{slug}}/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE {{PORT}}

CMD ["python", "-m", "{{slug}}.server"]
