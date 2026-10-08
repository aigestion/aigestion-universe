#!/bin/bash
echo "🚀 Levantando servicios del Monorepo AIGESTION..."

# 1. Matar procesos previos
pkill -9 -f nexus_dashboard.py
pkill -9 -f sentinel.py

# 2. Arrancar Nexus Command Center V5 Pro
nohup python3 ~/aig-monorepo/apps/nexus-command-center/nexus_dashboard.py > ~/aig-monorepo/nexus.log 2>&1 &
echo "  [✓] Nexus Dashboard levantado en puerto 8000/8080."

# 3. Arrancar Sentinel Guardián (Auto-recovery & Auto-rollback)
nohup python3 ~/aig-monorepo/pixela8/app/agents/sentinel.py > ~/aig-monorepo/sentinel.log 2>&1 &
echo "  [✓] Sentinel Agent iniciado."

# 4. Arrancar TaskWorker en segundo plano
nohup python3 -c 'from core.task_worker import TaskWorker; TaskWorker().start_worker_loop(2.0)' > ~/aig-monorepo/task_worker.log 2>&1 &
echo "  [✓] TaskWorker iniciado."

sleep 2
echo -e "\n🟢 Procesos activos:"
pgrep -fl python3
