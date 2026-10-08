import os
import time

import requests
import uvicorn
from daniela_rag import MobileRAG
from daniela_vision import capture_photo
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Daniela OS - Hybrid Router Edge RAG + Vision", version="3.5")

DANIELA_IP = os.getenv("DANIELA_IP", "100.98.235.124")
CORE_URL = f"http://{DANIELA_IP}:8000/api/chat"
rag_engine = MobileRAG()


class ChatRequest(BaseModel):
    prompt: str


def check_tailscale_core(timeout=1.5) -> bool:
    try:
        r = requests.get(f"http://{DANIELA_IP}:8000/api/system/status", timeout=timeout)
        return r.status_code == 200
    except Exception:
        return False


def handle_vision_command(query: str) -> str:
    q = query.lower()
    if any(k in q for k in ["foto", "camara", "mira", "que ves", "captura", "imagen"]):
        path, size_kb = capture_photo()
        if path and size_kb > 0:
            return f"[Visión Edge Pixel 8]: Foto capturada con éxito en RAM ({size_kb:.1f} KB). Guardada en {path}."
        else:
            return "[Visión Edge Pixel 8]: Error al acceder a la cámara o permisos denegados."
    return None


@app.post("/api/hybrid/chat")
def hybrid_chat(req: ChatRequest):
    start_time = time.time()
    prompt = req.prompt.strip()

    # 1. Comandos de Visión Edge Local
    vision_resp = handle_vision_command(prompt)
    if vision_resp:
        return {
            "source": "Edge Vision (Pixel 8)",
            "response": vision_resp,
            "latency_ms": round((time.time() - start_time) * 1000, 1),
        }

    # 2. Intentar comunicación con el Mini PC por Tailscale
    if check_tailscale_core(timeout=1.5):
        try:
            res = requests.post(CORE_URL, json={"prompt": prompt}, timeout=8.0)
            if res.status_code == 200:
                data = res.json()
                return {
                    "source": "Core (Mini PC)",
                    "response": data.get("response", "Sin respuesta."),
                    "latency_ms": round((time.time() - start_time) * 1000, 1),
                }
        except Exception:
            pass

    # 3. Fallback Local RAG SQLite
    rag_hits = rag_engine.search(prompt, top_k=1)
    if rag_hits:
        hit = rag_hits[0]
        local_response = f"[{hit['title']}]: {hit['content']}"
    else:
        local_response = f"Procesado en local (Pixel 8 Edge): Entendido '{prompt}'."

    return {
        "source": "Edge RAG (Pixel 8)",
        "response": local_response,
        "latency_ms": round((time.time() - start_time) * 1000, 1),
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
