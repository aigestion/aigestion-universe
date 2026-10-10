#!/data/data/com.termux/files/usr/bin/sh
# Watchdog Autónomo para Daniela OS / Hermes Agent
LOG_FILE="daniela_audit.log"

echo "🛡️ [WATCHDOG DANIELA OS] Monitoreo en segundo plano activo..."

while true; do
    if [ -f "$LOG_FILE" ]; then
        if grep -q "Traceback" "$LOG_FILE"; then
            echo "⚠️ [WATCHDOG] Anomaly/Traceback detectado. Invocando Auto-Healing..."
            python3 autofix_engine.py
            # Limpiar el log procesado para evitar loops infinitos
            > "$LOG_FILE"
        fi
    fi
    sleep 3
done
