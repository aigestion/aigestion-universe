FROM python:3.11-slim

WORKDIR /app

# aig-shared es dependencia comun: cross_engine/server.py importa
# `shared.auth.middleware`. Sin esto el contenedor arranca y muere con
# `ModuleNotFoundError: No module named 'shared'`.
# El contexto de build es la RAIZ del repo, de ahi el prefijo `aig-shared/`.
COPY shared/ ./shared/
RUN pip install --no-cache-dir ./shared

COPY engine/cross_engine/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY engine/cross_engine/ ./cross_engine/

EXPOSE 9900 8080

CMD ["python", "-m", "cross_engine.server"]
