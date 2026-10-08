import random
import time
from datetime import datetime

import requests

BASE_URL = "http://192.168.1.133:5059/api/swarm/dispatch"

SWARM_TASKS = {
    "orchestrator": [
        "Sincronizar tabla de nodos y balancear carga",
        "Validar reglas de gobernanza de la version v6.4",
        "Auditar latencia entre backend Termux y clientes PC",
    ],
    "rag_analyst": [
        "Indexar nuevos documentos en memory_rag.db",
        "Auditoria semantica de coherencia en reporte_daniela.pdf",
        "Ejecutar busqueda vectorial sobre grafos de contexto",
    ],
    "vault_keeper": [
        "Verificar integridad de tablas en daniela_vault.db",
        "Optimizar indices SQLite y limpiar registros temporales",
        "Generar copia de respaldo de la base de datos de memoria",
    ],
    "canary_guard": [
        "Ejecutar analisis dinamico de aislamiento en entorno de pruebas",
        "Escanear procesos activos en busca de desviaciones de seguridad",
        "Verificar contencion de ejecucion en la camara de cristal",
    ],
}

print("=================================================================")
print("🚀 [Daniela-OS Swarm] Iniciando despachador continuo")
print(f"🎯 Target: {BASE_URL}")
print("⏱️  Intervalo: 3 segundos (Presiona CTRL+C para detener)")
print("=================================================================")

agents = list(SWARM_TASKS.keys())
cycle = 1

while True:
    agent = random.choice(agents)
    task = random.choice(SWARM_TASKS[agent])
    payload = {"agent_id": agent, "task": f"[{cycle:04d}] {task}"}
    now = datetime.now().strftime("%H:%M:%S")
    try:
        res = requests.post(BASE_URL, json=payload, timeout=5)
        if res.status_code == 200:
            data = res.json()
            print(f"[{now}] 🟢 [{data.get('agent', agent).upper()}]: {data.get('execution', 'OK')}")
        else:
            print(f"[{now}] 🔴 Error HTTP {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[{now}] ⚠️ Error de conexion: {e}")
    cycle += 1
    time.sleep(3)
