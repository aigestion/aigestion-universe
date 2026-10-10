#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ENGINES=(
  "epic_pc|5020|epic-pc"
  "daniela|9200|daniela-os"
  "hermes|9300|hermes-epic"
  "optimization|9400|aig-optimization"
  "frontend_v1|9500|frontend-optimization"
  "frontend_v2|9600|frontend-opt2"
  "infra_opt|9700|infra-opt"
  "agent_mobile|9800|agents/api"
  "security|9999|sec-opt"
  "perf|9998|perf-opt"
  "dashboard|9997|daniela-os/unified-dashboard"
  "intel_engine|9850|engine/intel_engine"
  "auto_engine|9860|engine/auto_engine"
  "data_engine|9870|engine/data_engine"
  "secure_engine|9880|engine/secure_engine"
  "devtools_engine|9890|engine/devtools_engine"
  "ecosystem_engine|9840|engine/ecosystem_engine"
  "ux_engine|9830|engine/ux_engine"
  "scale_engine|9820|engine/scale_engine"
)

INFRA_SERVICES=("redis:6379" "gateway:8080" "orchestrator:9900" "nginx:80")
MONITORING_SERVICES=("prometheus:9090" "grafana:3000" "alertmanager:9093" "node-exporter:9100")

print_header() {
  echo -e "\n${CYAN}========================================${NC}"
  echo -e "${CYAN}  aig Production Deployment${NC}"
  echo -e "${CYAN}========================================${NC}\n"
}

print_step() {
  echo -e "\n${YELLOW}>> $1${NC}"
}

print_ok() {
  echo -e "${GREEN}   [OK] $1${NC}"
}

print_err() {
  echo -e "${RED}   [FAIL] $1${NC}"
}

print_header

print_step "1. Checking Docker..."
if ! command -v docker &> /dev/null; then
  print_err "Docker not found"
  exit 1
fi
# E-36 (2026-09-18): en este PC NO existe el plugin `docker compose`
# ("unknown command"), solo el binario suelto `docker-compose`. Antes se
# comprobaba que existiera `docker-compose` pero luego se invocaba
# `docker compose`, asi que este script no podia funcionar aqui.
if docker compose version &> /dev/null; then
  COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
  COMPOSE="docker-compose"
else
  print_err "Docker Compose not found (ni 'docker compose' ni 'docker-compose')"
  exit 1
fi
print_ok "Docker and Compose available: ${COMPOSE}"

print_step "2. Building base image..."
docker build -t aig-base:latest -f config/docker/Dockerfile.base . 2>/dev/null || print_ok "Base image build skipped (no config/docker/Dockerfile.base)"

print_step "3. Building all 19 engine images..."
for entry in "${ENGINES[@]}"; do
  IFS='|' read -r name port dir <<< "$entry"
  echo -ne "   Building ${name}... "
  if docker build -t "aig-${name}:latest" "./${dir}/" 2>/dev/null; then
    echo -e "${GREEN}done${NC}"
  else
    echo -e "${YELLOW}skipped (no Dockerfile)${NC}"
  fi
done

print_step "4. Starting monitoring stack..."
${COMPOSE} -f config/docker/docker-compose.monitoring.yml up -d
print_ok "Monitoring stack started"

print_step "5. Starting production engines..."
${COMPOSE} -f config/docker/docker-compose.prod.yml up -d
print_ok "Production stack started"

print_step "6. Waiting for services to initialize..."
sleep 15

print_step "7. Running health checks..."
echo ""
TOTAL=0
ONLINE=0
OFFLINE=0

for entry in "${ENGINES[@]}"; do
  IFS='|' read -r name port dir <<< "$entry"
  TOTAL=$((TOTAL + 1))
  echo -ne "   ${name} (port ${port}): "
  # E-36: dos bugs medidos aqui.
  #  1) La ruta era /status -> devuelve 404 en TODOS los motores; la buena es
  #     /api/status (200). Resultado: los 19 salian OFFLINE estando sanos.
  #  2) Sin --noproxy, un puerto muerto devuelve 502 (el proxy contesta) en vez
  #     de "conexion rechazada", y oculta la causa real.
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --noproxy '*' --max-time 5 "http://localhost:${port}/api/status" 2>/dev/null || echo "000")
  if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}ONLINE${NC}"
    ONLINE=$((ONLINE + 1))
  else
    echo -e "${RED}OFFLINE (HTTP ${HTTP_CODE})${NC}"
    OFFLINE=$((OFFLINE + 1))
  fi
done

echo -e "\n${CYAN}========================================${NC}"
echo -e "${CYAN}  Deployment Summary${NC}"
echo -e "${CYAN}========================================${NC}"
echo -e "  Total Engines:    ${TOTAL}"
echo -e "  ${GREEN}Online:            ${ONLINE}${NC}"
echo -e "  ${RED}Offline:           ${OFFLINE}${NC}"
echo -e ""
echo -e "  ${CYAN}Service URLs:${NC}"
echo -e "  Nginx:            http://localhost:80"
echo -e "  Gateway:          http://localhost:8080"
echo -e "  Orchestrator:     http://localhost:9900"
echo -e "  Redis:            localhost:6379"
echo -e "  Prometheus:       http://localhost:9090"
echo -e "  Grafana:          http://localhost:3000"
echo -e "  Alertmanager:     http://localhost:9093"
echo -e "  Node Exporter:    http://localhost:9100"
echo -e ""
echo -e "  ${CYAN}Grafana Login: admin / aig-admin-2024${NC}"
echo -e "${CYAN}========================================${NC}\n"
