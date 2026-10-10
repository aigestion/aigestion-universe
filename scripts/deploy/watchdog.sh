#!/data/data/com.termux/files/usr/bin/bash
while true; do
  if ! pgrep -f "python3 server.py" > /dev/null; then
    echo "[$(date)] ⚠️ Watchdog: Servidor Flask caído. Reiniciando Daniela OS..." >> watchdog.log
    cd ~/apps/aig-MONOREPO
    fuser -k 8082/tcp 2>/dev/null || true
    nohup python3 server.py > server.log 2>&1 &
  fi
  sleep 4
done
