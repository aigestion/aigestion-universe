#!/bin/bash
echo "[GUARDIÁN] Iniciando monitorización del servidor DANIELA OS..."

while true; do
    if ! pgrep -f "python3" > /dev/null; then
        echo "[ALERTA] Servidor caído. Reiniciando en puerto 8082..."
        nohup python3 -m http.server 8082 --bind 0.0.0.0 > server.log 2>&1 &
    fi
    sleep 5
done
