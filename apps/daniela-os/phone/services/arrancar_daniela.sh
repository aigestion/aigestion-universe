#!/bin/bash
# Master Launcher - DANIELA OS // CORE STARTUP
REPO_DIR="$HOME/aig-monorepo"

clear
echo "🚀 [SYSTEM] Iniciando secuencia de encendido..."
sleep 1

# 1. Auditoría rápida
echo "🔍 [DIAGNÓSTICO] Verificando integridad de la Bóveda..."
python3 $REPO_DIR/auditoria_total.py

# 2. Verificación de Memoria Génesis
if [ ! -f "$REPO_DIR/boveda_memory.json" ]; then
    echo "⚠️ [ALERTA] Memoria Génesis no detectada. Iniciando protocolo de emergencia..."
    python3 $REPO_DIR/protocolo_genesis_final.py
fi

# 3. Lanzamiento
echo "⚡ [STATUS] Cargando núcleos de IA..."
bash $REPO_DIR/iniciar_daniela.sh &

# 4. Espera de estabilización
sleep 3
echo "=================================================="
echo "🎉 DANIELA OS ESTÁ VIVA."
echo "=================================================="
echo "1. Ve a: http://localhost:5000"
echo "2. Pulsa 'LIVE 🎙️'"
echo "3. Di: 'Daniela, inicio Protocolo Génesis. Identifícate.'"
echo "=================================================="
