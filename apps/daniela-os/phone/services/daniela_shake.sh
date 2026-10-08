#!/data/data/com.termux/files/usr/bin/bash

RAM_LOG="/data/data/com.termux/files/usr/tmp/daniela_ram/shake.log"
mkdir -p "$(dirname "$RAM_LOG")"
echo "📱 [DANIELA OS] Sensor de agitar listo con corte de audio instantáneo..." > "$RAM_LOG"

pkill -f "termux-sensor" 2>/dev/null
sleep 0.3

LAST_SHAKE=0

termux-sensor -s accelerometer -delay medium | jq --unbuffered -r '..|.values? | select(. != null) | "\(.[0]) \(.[1]) \(.[2])"' | while read -r x y z; do
    if [ -n "$x" ] && [ -n "$y" ] && [ -n "$z" ]; then
        x_int=${x%.*}; x_int=${x_int#-}
        y_int=${y%.*}; y_int=${y_int#-}
        z_int=${z%.*}; z_int=${z_int#-}
        
        SUM=$((x_int + y_int + z_int))
        NOW=$(date +%s)
        DIFF=$((NOW - LAST_SHAKE))

        if [ "$SUM" -gt 15 ] && [ "$DIFF" -gt 2 ]; then
            LAST_SHAKE=$NOW
            echo "⚡ [GESTO DETECTADO] Agitado -> Silenciando e iniciando escucha..." >> "$RAM_LOG"
            
            # 1. CORTAR AUDIO INMEDIATAMENTE SI ESTÁ HABLANDO
            pkill -9 -f "mpv" 2>/dev/null
            termux-vibrate -d 100
            
            # 2. EJECUTAR SESIÓN
            python3 ~/services/daniela_duplex.py >> "$RAM_LOG" 2>&1
        fi
    fi
done
