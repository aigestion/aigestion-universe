#!/usr/bin/env bash
# Lanza docker compose con los flags correctos para ESTE repositorio.
#
# Existe porque hay tres trampas que no se ven al leer el compose:
#
#   1. El compose vive en `config/`, y Docker Compose resuelve las rutas
#      relativas —y el `.env` que usa para interpolar— respecto a SU directorio,
#      no respecto al directorio desde el que lo lanzas. Sin `--env-file`, las
#      claves de los proveedores del visor saldrian del `config/.env` viejo
#      (que tiene placeholders como OPENAI_API_KEY=YOUR_VALUE_HERE) en vez del
#      `.env` real de la raiz. Comprobado.
#   2. Por lo mismo, `context: ..` dentro de config/ apunta a la raiz del repo.
#      Si algun dia se "arregla" moviendo el compose, hay que revisar todo.
#   3. El binario puede ser `docker compose` (plugin) o `docker-compose`
#      (suelto); en esta maquina solo funciona el segundo.
#
# Uso:
#   scripts/deploy/compose.sh config                 # ver el stack resuelto
#   scripts/deploy/compose.sh up -d --build          # levantar todo
#   scripts/deploy/compose.sh up -d --build gods-eye daniela
#   scripts/deploy/compose.sh logs -f gods-eye
#   scripts/deploy/compose.sh ps
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE="config/docker/docker-compose.yml"
ENTORNO=".env"

if [ ! -f "$RAIZ/$COMPOSE" ]; then
    echo "no encuentro $RAIZ/$COMPOSE" >&2
    exit 1
fi

# Se trabaja con rutas RELATIVAS y el cwd en la raiz del repositorio a proposito.
# `docker.exe` es un binario de Windows y no entiende los caminos estilo Git Bash:
# pasarle `/c/Users/.../.env` le hace buscar `C:\c\Users\...\.env`. Comprobado.
cd "$RAIZ"

if docker compose version >/dev/null 2>&1; then
    CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    CMD=(docker-compose)
else
    echo "no encuentro docker compose ni docker-compose" >&2
    exit 1
fi

if [ -f "$ENTORNO" ]; then
    exec "${CMD[@]}" --env-file "$ENTORNO" -f "$COMPOSE" "$@"
fi

echo "aviso: no hay $RAIZ/$ENTORNO; las claves de los proveedores iran vacias" >&2
exec "${CMD[@]}" -f "$COMPOSE" "$@"
