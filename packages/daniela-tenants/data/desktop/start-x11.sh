#!/data/data/com.termux/files/usr/bin/bash
# Generado por desktop_mode.py (E-23) — 2026-09-10 15:02:48
# Uso: termux-x11 :1 -xstartup "$(pwd)/start-x11.sh"
set -e

export DISPLAY=:1
export PULSE_SERVER=tcp:127.0.0.1:4713
export XDG_RUNTIME_DIR=${TMPDIR:-/data/data/com.termux/files/usr/tmp}

# Ratón y teclado en pantalla para no depender del Bluetooth
matchbox-keyboard &>/dev/null &

# Prevenir el salvapantallas: en un escritorio molesta mas que ayuda
xset s off 2>/dev/null || true
xset -dpms 2>/dev/null || true

# Si hay pantalla externa, ajustamos la resolucion
if command -v xrandr >/dev/null 2>&1; then
  xrandr --output HDMI-1 --mode 1920x1080 2>/dev/null || true
fi

exec startxfce4
