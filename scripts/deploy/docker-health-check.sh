#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════════
# DOCKER HEALTH CHECK SYSTEM - aig MONOREPO
# Auto-checkeo de salud de contenedores con alertas automáticas
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Configuración
DOCKER_COMPOSE_DIR="/mnt/c/Users/Alejandro/_ACTIVE/Development/PROYECTOS/aig-MONOREPO/infra/docker"
ENV_FILE="/mnt/c/Users/Alejandro/_ACTIVE/Development/PROYECTOS/aig-MONOREPO/.env"
LOG_FILE="/var/log/aig-health-check.log"
ALERT_LOG="/var/log/aig-health-alerts.log"
HEALTH_CHECK_INTERVAL=600  # 10 minutos (reducido de 5 minutos para ahorrar recursos)
MAX_UNHEALTHY_RESTARTS=2  # Reducido de 3 a 2
# Alertas deshabilitadas por defecto para reducir consumo de recursos
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"
EMAIL_RECIPIENT="${ALERT_EMAIL:-}"
ENABLE_ALERTS=false  # Deshabilitar alertas externas por defecto

# Función de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Función de alerta
alert() {
    local severity=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    echo "[$timestamp] [$severity] $message" | tee -a "$ALERT_LOG"

    # Solo enviar alertas externas si están habilitadas
    if [ "$ENABLE_ALERTS" = true ]; then
        # Alerta por Telegram si está configurado
        if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ]; then
        curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
            -d "chat_id=$TELEGRAM_CHAT_ID" \
            -d "text=[$severity] aig Docker Alert: $message" \
            -d "parse_mode=HTML" > /dev/null 2>&1 || true
    fi

    # Alerta por email si está configurado
    if [ -n "$EMAIL_RECIPIENT" ]; then
        echo "[$severity] aig Docker Alert: $message" | mail -s "aig Docker Health Alert [$severity]" "$EMAIL_RECIPIENT" 2>/dev/null || true
    fi
    fi
}

# Función para verificar salud de contenedores
check_container_health() {
    local container_name=$1
    local status=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "unknown")

    case "$status" in
        healthy)
            log "✓ $container_name: healthy"
            return 0
            ;;
        unhealthy)
            log "✗ $container_name: unhealthy"
            alert "CRITICAL" "Container $container_name is unhealthy"
            return 1
            ;;
        starting)
            log "⏳ $container_name: starting"
            return 0
            ;;
        unknown)
            local running=$(docker inspect --format='{{.State.Running}}' "$container_name" 2>/dev/null || echo "false")
            if [ "$running" = "true" ]; then
                log "✓ $container_name: running (no health check)"
                return 0
            else
                log "✗ $container_name: not running"
                alert "CRITICAL" "Container $container_name is not running"
                return 1
            fi
            ;;
        *)
            log "⚠ $container_name: status=$status"
            return 1
            ;;
    esac
}

# Función para verificar todos los contenedores
check_all_containers() {
    log "════════════════════════════════════════════════════════════════════════════════"
    log "HEALTH CHECK - aig MONOREPO"
    log "════════════════════════════════════════════════════════════════════════════════"

    cd "$DOCKER_COMPOSE_DIR" || exit 1

    local unhealthy_count=0
    local total_count=0

    # Obtener todos los contenedores del proyecto
    local containers=$(docker compose --env-file "$ENV_FILE" ps -q)

    if [ -z "$containers" ]; then
        log "⚠ No hay contenedores corriendo"
        alert "WARNING" "No containers are running"
        return 1
    fi

    for container in $containers; do
        local name=$(docker inspect --format='{{.Name}}' "$container" | sed 's/\///')
        total_count=$((total_count + 1))

        if ! check_container_health "$name"; then
            unhealthy_count=$((unhealthy_count + 1))
        fi
    done

    log "════════════════════════════════════════════════════════════════════════════════"
    log "RESUMEN: $total_count contenedores, $unhealthy_count unhealthy"
    log "════════════════════════════════════════════════════════════════════════════════"

    if [ $unhealthy_count -gt 0 ]; then
        alert "CRITICAL" "Health check failed: $unhealthy_count/$total_count containers unhealthy"
        return 1
    else
        log "✓ Todos los contenedores están saludables"
        return 0
    fi
}

# Función para reiniciar contenedores unhealthy
restart_unhealthy_containers() {
    log "Intentando reiniciar contenedores unhealthy..."

    cd "$DOCKER_COMPOSE_DIR" || exit 1

    local containers=$(docker compose --env-file "$ENV_FILE" ps -q)

    for container in $containers; do
        local name=$(docker inspect --format='{{.Name}}' "$container" | sed 's/\///')
        local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "unknown")

        if [ "$status" = "unhealthy" ]; then
            log "Reiniciando $name..."
            docker compose --env-file "$ENV_FILE" restart "$name"
            sleep 5
        fi
    done
}

# Función para verificar recursos del sistema
check_system_resources() {
    log "Verificando recursos del sistema..."

    # CPU
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    log "CPU Usage: ${cpu_usage}%"

    if (( $(echo "$cpu_usage > 90" | bc -l) )); then
        alert "WARNING" "High CPU usage: ${cpu_usage}%"
    fi

    # Memoria
    local mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    log "Memory Usage: ${mem_usage}%"

    if (( $(echo "$mem_usage > 90" | bc -l) )); then
        alert "WARNING" "High memory usage: ${mem_usage}%"
    fi

    # Disco
    local disk_usage=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
    log "Disk Usage: ${disk_usage}%"

    if [ $disk_usage -gt 90 ]; then
        alert "WARNING" "High disk usage: ${disk_usage}%"
    fi
}

# Función principal
main() {
    log "Iniciando health check..."

    check_system_resources

    if check_all_containers; then
        log "✓ Health check completado exitosamente"
        exit 0
    else
        log "⚠ Health check detectó problemas"

        # Intentar reiniciar contenedores unhealthy
        restart_unhealthy_containers

        # Esperar y verificar nuevamente
        sleep 30
        if check_all_containers; then
            log "✓ Contenedores reiniciados exitosamente"
            alert "INFO" "Unhealthy containers restarted successfully"
            exit 0
        else
            log "✗ No se pudieron recuperar los contenedores"
            alert "CRITICAL" "Failed to recover unhealthy containers after restart"
            exit 1
        fi
    fi
}

# Ejutar función principal
main
