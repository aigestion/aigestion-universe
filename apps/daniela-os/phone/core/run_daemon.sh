#!/data/data/com.termux/files/usr/bin/bash

echo "🚀 Activando demonio 24/7 de Daniela OS en Pixel..."

while true; do
    # Ejecutar guardianes de limpieza y sincronización
    python3 ~/core/danielas_guardians.py
    
    # Comprobar si es hora del briefing diario (09:00 AM)
    CURRENT_HOUR=$(date +"%H:%M")
    if [ "$CURRENT_HOUR" == "09:00" ]; then
        python3 ~/core/danielas_guardians.py --briefing
    fi
    
    # Esperar 30 minutos (1800 segundos)
    sleep 1800
done
