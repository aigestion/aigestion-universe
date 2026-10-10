#!/usr/bin/env bash
# =============================================================================
#  deploy_prod.sh — Despliegue REAL de produccion, en el PC.  (E-36)
# =============================================================================
#  Por que existe este script
#  --------------------------
#  MEDIDO el 2026-09-18: el "CD" de GitHub NO puede desplegar aqui.
#    * `gh api .../actions/runners` -> {"total_count": 0}  (no hay runner propio)
#    * no existe ningun secreto de despliegue (ni DEPLOY_HOST ni SSH_KEY)
#    * el PC esta en una red domestica, sin ingreso publico
#  Por eso `deploy-prod` (cd-21.yml) solo podia *decir* que habia desplegado:
#  la orden `docker compose` estaba COMENTADA. Produccion es ESTE PC.
#
#  Este script es el despliegue de verdad: reconstruye y recrea los contenedores
#  y **verifica con un health check que puede fallar**. Si algo esta mal, sale
#  con codigo != 0. Nada de "despliegue completado" sin comprobarlo.
#
#  🔴 MEDIDO: en este PC **NO existe el plugin `docker compose`**
#     (`docker compose` -> "unknown command"), solo el binario suelto
#     `docker-compose` v5.5.1. El script detecta cual hay.
#
#  Uso:
#    ./scripts/deploy/deploy_prod.sh                 # build + up + verificar
#    ./scripts/deploy/deploy_prod.sh --no-build      # solo recrear
#    ./scripts/deploy/deploy_prod.sh --dry-run       # enseña lo que haria, no toca nada
#    ./scripts/deploy/deploy_prod.sh --wait 60       # espera antes de verificar
#    ./scripts/deploy/deploy_prod.sh --services "epic_pc dashboard"
#    ./scripts/deploy/deploy_prod.sh --fail-under 95 # umbral del health gate
#
#  NO hace git pull ni git push: el despliegue no debe tocar el historial.
# =============================================================================

set -euo pipefail

# --- localizacion del repo (independiente del cwd) ---------------------------
# ⚠️ 2026-09-20: este script vive en `scripts/deploy/`, no en `scripts/`.
# Antes `SCRIPT_DIR/..` daba la raiz del repo; ahora da `scripts/`, asi que
# COMPOSE_FILE y HEALTH_GATE no se encontraban. Se sube DOS niveles y ademas
# se resuelven las rutas reales con respaldo, para que siga funcionando si el
# fichero vuelve a moverse.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

# 2026-10-04: los compose viven en config/docker/ (antes config/, y antes ahi
# no habia prefijo). El `else` apunta a la ubicacion pre-refactor (intencional
# como ultimo recurso; tests/core/test_referencias_integridad.py lo excluye).
if [ -f "config/docker/docker-compose.prod.yml" ]; then
  COMPOSE_FILE="config/docker/docker-compose.prod.yml"
else
  COMPOSE_FILE="docker-compose.prod.yml"
fi

# ci_health_gate.py se movio a scripts/core/ en el refactor.
if [ -f "scripts/core/ci_health_gate.py" ]; then
  HEALTH_GATE="scripts/core/ci_health_gate.py"
else
  HEALTH_GATE="scripts/ci_health_gate.py"
fi

# --- validacion de rutas resueltas -------------------------------------------
# Los bloques de arriba tienen un `else` que apunta a la ubicacion ANTIGUA
# (pre-refactor). Si alguna vez se entra por ese `else`, el deploy continuaria
# y fallaria mucho mas tarde con un error confuso. Preferimos fallar aqui y
# decir exactamente que falta.
for _f in "$COMPOSE_FILE" "$HEALTH_GATE"; do
  if [ ! -f "$_f" ]; then
    printf '\nERROR: falta un fichero necesario para el deploy: %s\n' "$_f" >&2
    printf 'El refactor del 2026-09-20 movio estos ficheros:\n' >&2
    printf '  docker-compose.prod.yml -> config/docker/\n' >&2
    printf '  ci_health_gate.py       -> scripts/core/\n' >&2
    printf 'Revisa las rutas de este script.\n\n' >&2
    exit 1
  fi
done
BASE_URL="http://localhost"

# --- opciones ----------------------------------------------------------------
DRY_RUN=0
DO_BUILD=1
WAIT_S=45
SERVICES=""
FAIL_UNDER="100"

usage() {
  sed -n '2,32p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit "${1:-0}"
}

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)     DRY_RUN=1 ;;
    --no-build)    DO_BUILD=0 ;;
    --wait)        WAIT_S="${2:?--wait necesita segundos}"; shift ;;
    --services)    SERVICES="${2:?--services necesita una lista}"; shift ;;
    --fail-under)  FAIL_UNDER="${2:?--fail-under necesita un numero}"; shift ;;
    --core)
      # E-38: stack minimo (daniela_os + redis + nginx + ollama)
      # 2026-10-04: los compose viven en `config/docker/` (antes `config/`).
      # Sin el prefijo, `[ ! -f "$COMPOSE_FILE" ]` abortaba con
      # "no encuentro docker-compose.core.yml" y el flag era inusable.
      COMPOSE_FILE="config/docker/docker-compose.core.yml"
      BASE_URL="http://localhost:5000"
      ;;
    -h|--help)     usage 0 ;;
    *) echo "Opcion desconocida: $1" >&2; usage 1 ;;
  esac
  shift
done

# --- utilidades de salida ----------------------------------------------------
if [ -t 1 ]; then
  C_RED=$'\033[0;31m'; C_GRN=$'\033[0;32m'; C_YEL=$'\033[1;33m'
  C_CYA=$'\033[0;36m'; C_OFF=$'\033[0m'
else
  C_RED=""; C_GRN=""; C_YEL=""; C_CYA=""; C_OFF=""
fi
paso()  { printf '\n%s>> %s%s\n' "${C_YEL}" "$1" "${C_OFF}"; }
ok()    { printf '%s   [OK] %s%s\n' "${C_GRN}" "$1" "${C_OFF}"; }
aviso() { printf '%s   [!]  %s%s\n' "${C_YEL}" "$1" "${C_OFF}"; }
fallo() { printf '%s   [FALLO] %s%s\n' "${C_RED}" "$1" "${C_OFF}"; }

echo "${C_CYA}========================================${C_OFF}"
echo "${C_CYA}  Despliegue de PRODUCCION (local)${C_OFF}"
echo "${C_CYA}  repo: ${REPO_ROOT}${C_OFF}"
echo "${C_CYA}========================================${C_OFF}"
if [ "${DRY_RUN}" -eq 1 ]; then
  aviso "MODO --dry-run: no se va a cambiar nada."
fi

# --- 1. comprobaciones previas ----------------------------------------------
paso "1. Comprobando el entorno"
if ! command -v docker >/dev/null 2>&1; then
  fallo "docker no esta en el PATH."
  exit 2
fi
if ! docker info >/dev/null 2>&1; then
  fallo "el demonio de Docker no responde. Arranca Docker Desktop."
  exit 2
fi
ok "docker disponible"

# 🔴 Aqui esta la trampa: el plugin `docker compose` NO tiene por que existir.
if docker compose version >/dev/null 2>&1; then
  COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE="docker-compose"
else
  fallo "no encuentro ni 'docker compose' ni 'docker-compose'."
  exit 2
fi
ok "compose: ${COMPOSE} ($(${COMPOSE} version 2>&1 | head -1))"

if [ ! -f "${COMPOSE_FILE}" ]; then
  fallo "no encuentro ${COMPOSE_FILE}."
  exit 2
fi
ok "${COMPOSE_FILE} presente"

# --- python del proyecto -----------------------------------------------------
PYTHON_BIN="${PYTHON:-}"
if [ -z "${PYTHON_BIN}" ]; then
  if [ -x ".venv/Scripts/python.exe" ]; then
    PYTHON_BIN=".venv/Scripts/python.exe"     # Windows / Git Bash
  elif [ -x ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"             # Linux / macOS
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  fi
fi
if [ -z "${PYTHON_BIN}" ]; then
  fallo "no encuentro un python utilizable (mira PYTHON=...)."
  exit 2
fi
ok "python: ${PYTHON_BIN}"

# --- 2. que version se despliega --------------------------------------------
paso "2. Version a desplegar"
if command -v git >/dev/null 2>&1 && git rev-parse --git-dir >/dev/null 2>&1; then
  SHA="$(git rev-parse --short HEAD 2>/dev/null || echo '?')"
  RAMA="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
  echo "   commit: ${SHA}  rama: ${RAMA}"
  if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    aviso "el arbol de trabajo tiene cambios sin commitear."
    aviso "lo que despliegues NO sera exactamente el commit ${SHA}."
  else
    ok "arbol limpio"
  fi
else
  aviso "no es un repo git utilizable; no puedo decirte el commit."
fi

# --- 3. validar el compose ---------------------------------------------------
paso "3. Validando ${COMPOSE_FILE}"
if ${COMPOSE} -f "${COMPOSE_FILE}" config >/dev/null 2>&1; then
  N_SERV="$(${COMPOSE} -f "${COMPOSE_FILE}" config --services 2>/dev/null | wc -l | tr -d ' ')"
  ok "compose valido (${N_SERV} servicios definidos)"
else
  fallo "compose INVALIDO. Salida:"
  ${COMPOSE} -f "${COMPOSE_FILE}" config 2>&1 | tail -20 || true
  exit 2
fi

if [ "${DRY_RUN}" -eq 1 ]; then
  paso "DRY-RUN: esto es lo que se ejecutaria"
  if [ "${DO_BUILD}" -eq 1 ]; then
    echo "   ${COMPOSE} -f ${COMPOSE_FILE} build ${SERVICES}"
  fi
  echo "   ${COMPOSE} -f ${COMPOSE_FILE} up -d --remove-orphans ${SERVICES}"
  echo "   (espera ${WAIT_S}s)"
  echo "   ${PYTHON_BIN} ${HEALTH_GATE} --base-url ${BASE_URL} --fail-under ${FAIL_UNDER}"
  echo
  ok "dry-run terminado; no se ha tocado nada."
  exit 0
fi

# --- 4. construir ------------------------------------------------------------
if [ "${DO_BUILD}" -eq 1 ]; then
  paso "4. Construyendo imagenes"
  # shellcheck disable=SC2086
  if ${COMPOSE} -f "${COMPOSE_FILE}" build ${SERVICES}; then
    ok "build terminado"
  else
    fallo "el build ha fallado; no se despliega nada."
    exit 3
  fi
else
  paso "4. Build omitido (--no-build)"
fi

# --- 5. recrear --------------------------------------------------------------
paso "5. Recreando contenedores (up -d --remove-orphans)"
# shellcheck disable=SC2086
if ${COMPOSE} -f "${COMPOSE_FILE}" up -d --remove-orphans ${SERVICES}; then
  ok "contenedores recreados"
else
  fallo "'${COMPOSE} up' ha fallado."
  ${COMPOSE} -f "${COMPOSE_FILE}" ps 2>&1 | tail -20 || true
  exit 3
fi

# --- 6. verificar de verdad --------------------------------------------------
paso "6. Verificando (espera ${WAIT_S}s)"
sleep "${WAIT_S}"

echo "   --- estado de los contenedores ---"
${COMPOSE} -f "${COMPOSE_FILE}" ps 2>&1 | tail -30 || true

paso "7. Health gate (umbral ${FAIL_UNDER}%)"
set +e
PYTHONPATH="${REPO_ROOT}" "${PYTHON_BIN}" "${HEALTH_GATE}" \
  --base-url "${BASE_URL}" --fail-under "${FAIL_UNDER}"
GATE_RC=$?
set -e

echo
echo "${C_CYA}========================================${C_OFF}"
if [ "${GATE_RC}" -eq 0 ]; then
  echo "${C_GRN}  DESPLIEGUE VERIFICADO${C_OFF}"
  echo "${C_CYA}========================================${C_OFF}"
  echo "  commit:  $(git rev-parse --short HEAD 2>/dev/null || echo '?')"
  echo "  umbral:  ${FAIL_UNDER}%"
  echo "  gateway: http://localhost:8080"
  echo "  nginx:   http://localhost:80"
  exit 0
else
  echo "${C_RED}  DESPLIEGUE NO VERIFICADO (health gate = ${GATE_RC})${C_OFF}"
  echo "${C_CYA}========================================${C_OFF}"
  echo "  Los contenedores se recrearon, pero el health gate no llega a"
  echo "  ${FAIL_UNDER}%. Mira arriba que motor esta caido."
  echo
  echo "  Para ver el log de un servicio:"
  echo "    ${COMPOSE} -f ${COMPOSE_FILE} logs --tail=80 <servicio>"
  exit 1
fi
