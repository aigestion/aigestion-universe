#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# DOCKER AUTO-START SYSTEM - aig MONOREPO
# Arranque automático de contenedores Docker al encender el minipc
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Configuración
DOCKER_COMPOSE_DIR="/mnt/c/Users/Alejandro/_ACTIVE/Development/PROYECTOS/aig-MONOREPO/infra/docker"
ENV_FILE="/mnt/c/Users/Alejandro/_ACTIVE/Development/PROYECTOS/aig-MONOREPO/.env"
LOG_FILE="/var/log/aig-docker-startup.log"
MAX_RETRIES=2
RETRY_DELAY=10
STARTUP_TIMEOUT=120

# Función de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Función para verificar Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log "ERROR: Docker no está instalado"
        return 1
    fi

    if ! docker info &> /dev/null; then
        log "ERROR: Docker daemon no está corriendo"
        return 1
    fi

    log "✓ Docker está disponible y corriendo"
    return 0
}

# Función para verificar si contenedores ya están corriendo
check_containers_running() {
    cd "$DOCKER_COMPOSE_DIR" || exit 1

    local running=$(docker compose --env-file "$ENV_FILE" ps --format "{{.Status}}" | grep -c "running\|healthy" || true)
    local total=$(docker compose --env-file "$ENV_FILE" ps --format "{{.Status}}" | wc -l)

    if [ "$running" -gt 0 ] && [ "$running" -eq "$total" ]; then
        log "✓ Todos los contenedores ya están corriendo ($running/$total)"
        return 0
    elif [ "$running" -gt 0 ]; then
        log "⚠ Algunos contenedores están corriendo ($running/$total), se reiniciarán"
        return 1
    else
        log "⚠ No hay contenedores corriendo"
        return 1
    fi
}

# Función para arrancar contenedores
start_containers() {
    log "Iniciando contenedores Docker..."

    cd "$DOCKER_COMPOSE_DIR" || exit 1

    for i in $(seq 1 $MAX_RETRIES); do
        log "Intento $i de $MAX_RETRIES para arrancar contenedores"

        if docker compose --env-file "$ENV_FILE" up -d; then
            log "✓ Contenedores arrancados exitosamente"
            return 0
        else
            log "⚠ Error al arrancar contenedores (intento $i)"
            if [ $i -lt $MAX_RETRIES ]; then
                log "Esperando $RETRY_DELAY segundos antes de reintentar..."
                sleep $RETRY_DELAY
            fi
        fi
    done

    log "ERROR: No se pudieron arrancar los contenedores después de $MAX_RETRIES intentos"
    return 1
}

# Función para verificar estado de contenedores
check_containers() {
    log "Verificando estado de contenedores..."

    cd "$DOCKER_COMPOSE_DIR" || exit 1

    docker compose --env-file "$ENV_FILE" ps

    local unhealthy=$(docker compose --env-file "$ENV_FILE" ps --format "{{.Status}}" | grep -c "unhealthy\|exited" || true)
    local total=$(docker compose --env-file "$ENV_FILE" ps --format "{{.Status}}" | wc -l)

    log "Contenedores: $total total, $unhealthy unhealthy"

    if [ $unhealthy -gt 0 ]; then
        log "⚠ ADVERTENCIA: $unhealthy contenedores no están saludables"
        return 1
    fi

    log "✓ Todos los contenedores están saludables"
    return 0
}

# Función principal
main() {
    log "════════════════════════════════════════════════════════════════════════════════"
    log "DOCKER AUTO-START SYSTEM - aig MONOREPO"
    log "════════════════════════════════════════════════════════════════════════════════"

    if check_docker; then
        # Verificar si contenedores ya están corriendo
        if check_containers_running; then
            check_containers
            log "════════════════════════════════════════════════════════════════════════════════"
            log "✓ SISTEMA YA ESTÁ INICIADO"
            log "════════════════════════════════════════════════════════════════════════════════"
            exit 0
        fi

        # Si no están corriendo, intentar iniciarlos
        if start_containers; then
            check_containers
            log "════════════════════════════════════════════════════════════════════════════════"
            log "✓ SISTEMA INICIADO EXITOSAMENTE"
            log "════════════════════════════════════════════════════════════════════════════════"
            exit 0
        else
            log "════════════════════════════════════════════════════════════════════════════════"
            log "✗ ERROR: No se pudieron arrancar los contenedores"
            log "════════════════════════════════════════════════════════════════════════════════"
            exit 1
        fi
    else
        log "════════════════════════════════════════════════════════════════════════════════"
        log "✗ ERROR: Docker no está disponible"
        log "════════════════════════════════════════════════════════════════════════════════"
        exit 1
    fi
}

# Ejutar función principal
main
