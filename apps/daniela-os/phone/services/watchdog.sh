#!/data/data/com.termux/files/usr/bin/bash

# ======================================================
#       DANIELA OS - WATCHDOG AUTOMÁTICO (PIXEL 8)
# ======================================================

ROUTER_SCRIPT="$HOME/core/daniela_router.py"
WAKEWORD_SCRIPT="$HOME/services/daniela_wakeword.py"
LOG_FILE="$HOME/logs/watchdog.log"

log_event() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 1. Verificar Router Edge (Puerto 8001)
if ! pgrep -f "daniela_router.py" > /dev/null; then
    log_event "⚠️ Router Edge caído. Reiniciando..."
    (cd "$HOME/core" && python "$ROUTER_SCRIPT" > /dev/null 2>&1 &)
fi

# 2. Verificar Wakeword Daemon
if ! pgrep -f "daniela_wakeword.py" > /dev/null; then
    log_event "⚠️ Wakeword Daemon caído. Reiniciando..."
    (cd "$HOME/services" && python "$WAKEWORD_SCRIPT" > /dev/null 2>&1 &)
fi
