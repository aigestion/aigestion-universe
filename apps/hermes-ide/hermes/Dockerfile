FROM aig-base:latest

WORKDIR /app

# 2026-09-22: `hermes-epic/` -> `IA-SERVICES/hermes/` -> `ide/hermes/` (P3/P4). El destino se
# queda en `.` (aplanado a /app) porque el CMD arranca `server:app` y
# `server.py` esta en la raiz de la carpeta.
COPY --chown=appuser:appuser ./ide/hermes/ .

# Copy core module for new integrations
COPY --chown=appuser:appuser ./core/ ./core/

# `server.py:22-24` importa `shared.registry`, `shared.events` y
# `shared.auth.middleware`. `aig-base:latest` trae `shared` ya instalado,
# pero es una copia del 2026-09-18T20:44 —ANTERIOR a
# `shared/shared/auth/middleware.py`, que es de las 22:15 del mismo dia—, y
# su `auth/` solo contiene `__init__.py`. Comprobado con
# `docker run --rm aig-base:latest python -c "import shared.auth, os; ..."`.
# Resultado: el contenedor arrancaba y moria en bucle con
#   ModuleNotFoundError: No module named 'shared.auth.middleware'
#
# Se reinstala desde `shared/` (el canonico: su `pyproject.toml` fija
# `include = ["shared*"]`), copiandolo a `./shared/` igual que hace
# `gev/daniela-os/Dockerfile` ("ya viene instalado en aig-base, se reinstala
# para asegurar la ultima version"). Verificado en el contenedor sano: ahi
# `shared.auth.middleware` SI resuelve.
#
# Ojo con la fusion: `/app/shared/` ya existe porque `./ide/hermes/`
# trae su propio `agent_shared/` (renombrado desde `shared/` en P4), que es
# el que resuelve `from agent_shared.config import WEB_PORT` de `server.py`.
# Las dos copias se fusionan en el mismo directorio y no se pisan: `shared/`
# solo aporta el subarbol de paquetes (`auth/`, `config/`, ...), asi que los
# modulos sueltos de Hermes no entran en el wheel.
COPY --chown=appuser:appuser ./shared/ ./shared/

# `aig-base` fija `USER appuser` y appuser NO puede escribir en
# site-packages (comprobado en daniela con un `touch`), asi que `pip install`
# necesita root. Se vuelve a appuser al final: el contenedor no corre como root.
# El `rm -rf` es por si el contexto trae un `shared.egg-info` o un `build/`
# de un build anterior en el host, que harian fallar el wheel.
USER root
RUN rm -rf /app/shared/build /app/shared/shared.egg-info /app/shared/.ruff_cache \
 && pip install --no-cache-dir ./shared
USER appuser

ENV SERVICE_NAME=hermes
ENV PORT=9300

EXPOSE 9300

CMD ["gunicorn", "--bind", "0.0.0.0:9300", "--workers", "2", "--threads", "4", "--timeout", "120", "server:app"]
