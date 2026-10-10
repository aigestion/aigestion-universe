#!/data/data/com.termux/files/usr/bin/bash
# =============================================================================
#  DanielaOS - Instalador + Auditor para el Pixel
#  Uso:  bash /sdcard/DanielaOS/deploy/install.sh
#  No borra nada. Copia, configura y escribe un informe en /sdcard.
# =============================================================================

SRC="$(cd "$(dirname "$0")" && pwd)"
DST="$HOME/daniela-os"
LOGDIR="/sdcard/DanielaOS/deploy"
LOG="$LOGDIR/INSTALL_LOG.txt"
AUD="$LOGDIR/AUDIT_TERMUX.txt"
GW_PORT=8083     # 8082 ya lo ocupa el server.py antiguo
CORE_PORT=5000

mkdir -p "$DST" "$LOGDIR" "$DST/data" "$DST/templates"
: > "$LOG"; : > "$AUD"

say() { echo "[install] $*"; echo "[$(date +%H:%M:%S)] $*" >> "$LOG"; }

say "=== DANIELAOS DEPLOY $(date) ==="
say "origen : $SRC"
say "destino: $DST"

# ---------------------------------------------------------------------------
# 1. AUDITORIA DEL INTERIOR DE TERMUX (lo que adb no puede ver)
# ---------------------------------------------------------------------------
{
echo "########## AUDITORIA TERMUX - $(date) ##########"
echo
echo "=== 1. HOME de Termux ==="
ls -la "$HOME" 2>&1
echo
echo "=== 2. Tamano de cada carpeta del home ==="
du -sh "$HOME"/* 2>/dev/null | sort -rh 2>/dev/null | head -30
echo
echo "=== 3. apps/ ==="
ls -la "$HOME/apps" 2>&1 | head -40
echo
echo "=== 4. GIT ramas en ~/apps/*  ==="
for d in "$HOME"/apps/*/; do
  if [ -d "$d/.git" ]; then
    echo "--- REPO: $d"
    git -C "$d" branch -a 2>&1 | head -30
    echo "    actual: $(git -C "$d" rev-parse --abbrev-ref HEAD 2>&1)"
    echo "    ultimos commits:"
    git -C "$d" log --oneline -10 2>&1 | head -12
    echo "    cambios sin commit:"
    git -C "$d" status --porcelain 2>&1 | head -30
  fi
done
echo
echo "=== 5. .shortcuts (widgets) ==="
ls -la "$HOME/.shortcuts" 2>&1 | head -20
echo
echo "=== 6. .termux/boot ==="
ls -la "$HOME/.termux/boot" 2>&1 | head -20
echo
echo "=== 7. Python y pip ==="
python3 -V 2>&1
pip list 2>/dev/null | head -40
echo
echo "=== 8. Paquetes Termux ==="
pkg list-installed 2>/dev/null | head -50
echo
echo "=== 9. Procesos ==="
ps -ef 2>/dev/null | grep -iE "python|termux|node" | grep -v grep | head -20
echo
echo "=== 10. Puertos en escucha ==="
cat /proc/net/tcp 2>/dev/null | awk '$4=="0A"{split($2,a,":"); print a[2]}' | sort -u
echo
echo "########## FIN AUDITORIA ##########"
} >> "$AUD" 2>&1
say "auditoria escrita en $AUD"

# ---------------------------------------------------------------------------
# 2. COPIAR MODULOS
# ---------------------------------------------------------------------------
cp -f "$SRC"/*.py "$DST/" 2>>"$LOG"
cp -f "$SRC"/templates/*.html "$DST/templates/" 2>>"$LOG"
say "modulos copiados: $(ls -1 "$DST"/*.py 2>/dev/null | wc -l)"

# ---------------------------------------------------------------------------
# 3. DEPENDENCIAS
# ---------------------------------------------------------------------------
say "instalando dependencias python..."
pip install --quiet flask requests pyserial python-dotenv >>"$LOG" 2>&1
say "flask -> $(python3 -c 'import flask;print(flask.__version__)' 2>&1 | tail -1)"

# ---------------------------------------------------------------------------
# 4. WIDGETS DE TERMUX
# ---------------------------------------------------------------------------
mkdir -p "$HOME/.shortcuts"
W="$HOME/.shortcuts"

cat > "$W/Daniela-Estado" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-toast -g middle "Daniela: consultando estado..."
R=$(curl -s -m 10 http://127.0.0.1:5000/api/pixel/core/status | head -c 400)
termux-dialog -t "DANIELA - ESTADO" -i "${R:-sin respuesta}" >/dev/null 2>&1
EOF

cat > "$W/Daniela-Contexto" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
R=$(curl -s -m 10 http://127.0.0.1:5000/api/pixel/context/current | head -c 400)
termux-dialog -t "DANIELA - CONTEXTO" -i "${R:-sin respuesta}" >/dev/null 2>&1
EOF

cat > "$W/Daniela-SOS" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-vibrate -d 1000
R=$(curl -s -m 10 -X POST http://127.0.0.1:5000/api/pixel/core/panic | head -c 300)
termux-notification -t "DANIELA SOS" -c "Alerta enviada" --priority high
termux-toast -g middle "SOS enviado"
EOF

cat > "$W/Daniela-CajaNegra" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
R=$(curl -s -m 15 -X POST -H "Content-Type: application/json" \
     -d '{"reason":"widget"}' http://127.0.0.1:5000/api/blackbox/trigger | head -c 400)
termux-toast -g middle "Incidente congelado"
termux-notification -t "CAJA NEGRA" -c "$R"
EOF

cat > "$W/Daniela-Dime" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
T=$(termux-dialog -t "DANIELA" -i "Que quieres que diga?" 2>/dev/null)
TXT=$(echo "$T" | python3 -c "import sys,json;print(json.load(sys.stdin).get('text',''))" 2>/dev/null)
[ -n "$TXT" ] && termux-tts-speak "$TXT"
EOF

cat > "$W/Daniela-Sincroniza" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
termux-toast -g middle "Sincronizando con Git Brain..."
R=$(curl -s -m 60 -X POST http://127.0.0.1:5000/api/pixel/git/sync | head -c 300)
termux-notification -t "DANIELA SYNC" -c "$R"
EOF

chmod +x "$W"/Daniela-* 2>>"$LOG"
say "widgets instalados: $(ls -1 "$W"/Daniela-* 2>/dev/null | wc -l)"

# ---------------------------------------------------------------------------
# 5. AUTOARRANQUE (Termux:Boot)
# ---------------------------------------------------------------------------
mkdir -p "$HOME/.termux/boot"
cat > "$HOME/.termux/boot/daniela-os.sh" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
# Arranque automatico de DanielaOS
termux-wake-lock
sleep 15
cd "$DST" || exit 1
PIXEL_GATEWAY_PORT=$GW_PORT nohup python3 "$DST/termux_api_gateway.py" >"$DST/data/gateway.log" 2>&1 &
sleep 3
nohup python3 "$DST/daniela_os.py" --host 0.0.0.0 --port $CORE_PORT >"$DST/data/core.log" 2>&1 &
EOF
chmod +x "$HOME/.termux/boot/daniela-os.sh"
say "autoarranque creado en ~/.termux/boot/daniela-os.sh"

# ---------------------------------------------------------------------------
# 6. ARRANQUE AHORA
# ---------------------------------------------------------------------------
say "arrancando servicios..."
termux-wake-lock 2>/dev/null
cd "$DST" || exit 1

pgrep -f termux_api_gateway.py >/dev/null || \
  PIXEL_GATEWAY_PORT=$GW_PORT nohup python3 "$DST/termux_api_gateway.py" >"$DST/data/gateway.log" 2>&1 &

sleep 3
pgrep -f daniela_os.py >/dev/null || \
  nohup python3 "$DST/daniela_os.py" --host 0.0.0.0 --port $CORE_PORT >"$DST/data/core.log" 2>&1 &

sleep 6
say "--- comprobacion ---"
echo "gateway 8083: $(curl -s -o /dev/null -w '%{http_code}' -m 5 -H 'X-Pixel-Token: daniela-pixel-2026' http://127.0.0.1:8083/api/pixel/health)" >> "$LOG"
echo "core    5000: $(curl -s -o /dev/null -w '%{http_code}' -m 5 http://127.0.0.1:5000/)" >> "$LOG"

say "=== FIN ==="
say "log   : $LOG"
say "aud   : $AUD"
echo
echo "Listo. Ahora anade los widgets de Daniela a la pantalla de inicio"
echo "(mantén pulsada la pantalla > Widgets > Termux:Widget)."
