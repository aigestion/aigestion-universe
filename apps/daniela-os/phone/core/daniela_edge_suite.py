import json
import os
from pathlib import Path

import requests
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Daniela OS - Edge Hybrid Suite")

DANIELA_IP = os.getenv("DANIELA_IP", "127.0.0.1")
MINI_PC_URL = f"http://{DANIELA_IP}:8000"
OFFLINE_BUFFER_FILE = Path.home() / ".daniela_offline_buffer.json"

# Palabras prohibidas que activan la autenticación por huella dactilar (Firewall Cognitivo)
CRITICAL_COMMANDS = ["rm -rf", "drop database", "format", "stop-service", "killswitch", "delete"]


class CommandPayload(BaseModel):
    command: str


def is_pc_online():
    try:
        r = requests.get(f"{MINI_PC_URL}/api/system/status", timeout=1.0)
        return r.status_code == 200
    except Exception:
        return False


# 1. 🛡️ FIREWALL COGNITIVO LOCAL
@app.post("/api/edge/shield")
def cognitive_shield(payload: CommandPayload):
    cmd = payload.command.lower()
    for danger in CRITICAL_COMMANDS:
        if danger in cmd:
            return {
                "status": "BLOCKED",
                "reason": f"Comando crítico detectado: '{danger}'. Requiere aprobación por huella (d-auth).",
                "requires_auth": True,
            }
    return {"status": "ALLOWED", "requires_auth": False}


# 2. 📲 BUFFER OFFLINE-FIRST (P2P SINK)
@app.post("/api/edge/buffer/add")
def add_to_offline_buffer(payload: dict):
    buffer = []
    if OFFLINE_BUFFER_FILE.exists():
        try:
            buffer = json.loads(OFFLINE_BUFFER_FILE.read_text())
        except Exception:
            buffer = []

    buffer.append(payload)
    OFFLINE_BUFFER_FILE.write_text(json.dumps(buffer, indent=2))
    return {"status": "buffered", "total_pending": len(buffer)}


@app.post("/api/edge/buffer/sync")
def sync_offline_buffer():
    if not is_pc_online():
        return {"status": "offline", "message": "Mini PC no disponible para sincronización."}

    if not OFFLINE_BUFFER_FILE.exists():
        return {"status": "clean", "synced_count": 0}

    try:
        buffer = json.loads(OFFLINE_BUFFER_FILE.read_text())
        if not buffer:
            return {"status": "clean", "synced_count": 0}

        r = requests.post(f"{MINI_PC_URL}/api/sync/batch", json=buffer, timeout=5.0)
        if r.status_code == 200:
            OFFLINE_BUFFER_FILE.unlink()
            return {"status": "synced", "synced_count": len(buffer)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8002)
