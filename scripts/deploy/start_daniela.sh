#!/bin/bash

echo "=================================================="
echo "⚡ INICIANDO AUTOMATIZACIÓN DE DANIELA OS // B2B ⚡"
echo "=================================================="

# 1. Detener procesos previos
echo "[1/4] Limpiando procesos antiguos..."
pkill -9 -f "python3" 2>/dev/null
pkill -9 -f "cloudflared" 2>/dev/null
sleep 1

# 2. Ejecutar test suite de base de datos
echo "[2/4] Validando tablas SQLite y motor de logs..."
python3 test_daniela.py
if [ $? -ne 0 ]; then
    echo "❌ Error en las pruebas unitarias. Abortando."
    exit 1
fi

# 3. Arrancar servidor backend en segundo plano
echo "[3/4] Arrancando servidor Python en puerto 8082..."
nohup python3 server.py > server.log 2>&1 &
sleep 2

# 4. Iniciar túnel seguro Cloudflare
echo "[4/4] Levantando túnel público HTTPS en Cloudflare..."
echo "=================================================="
echo "👉 Abre el navegador en: http://127.0.0.1:8082/index.html"
echo "=================================================="

cloudflared tunnel --url http://localhost:8082
