FROM python:3.11-slim

WORKDIR /app

COPY engine/ecosystem_engine/ ./ecosystem_engine/

# requirements.txt existe (flask, pyyaml, requests) pero nunca se instalaba:
# protocol.py hace `import yaml` -> ModuleNotFoundError y bootloop.
COPY engine/ecosystem_engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 9840

CMD ["python", "-m", "ecosystem_engine.server"]
