import os

import requests


def check_ollama_status(host="http://127.0.0.1:11434"):
    """Verifica si Ollama está corriendo localmente de forma opcional."""
    try:
        res = requests.get(f"{host}/api/tags", timeout=1.5)
        return res.status_code == 200
    except Exception:
        return False

def get_preferred_llm_provider():
    """
    Retorna el proveedor de IA prioritario.
    1. OpenRouter (Si existe OPENROUTER_API_KEY)
    2. Ollama (Solo si el servicio local responde)
    3. Fallback en la nube / Modo pasivo
    """
    if os.getenv("OPENROUTER_API_KEY"):
        return "openrouter"
    elif check_ollama_status():
        return "ollama_local"
    else:
        return "cloud_fallback"
