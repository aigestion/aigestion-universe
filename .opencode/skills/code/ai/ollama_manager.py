import json
import logging
import subprocess

from skills import node_manager


def list_local_models():
    """Consulta modelos en local o en el nodo remoto 'server-ai'."""
    try:
        cmd = ["curl", "-s", "--max-time", "2", "http://localhost:11434/api/tags"]
        output = subprocess.check_output(cmd, text=True)
        data = json.loads(output)
        models = [m['name'] for m in data.get('models', [])]
        return f"🧠 [OLLAMA LOCAL]: Modelos disponibles: {', '.join(models)}"
    except Exception:
        logging.info("Ollama local no disponible, consultando nodo remoto 'server-ai'...")
        return node_manager.exec_remote_cmd("server-ai", "curl -s http://localhost:11434/api/tags")

def query_local_model(model, prompt):
    """Ejecuta consulta localmente con fallback automático al servidor remoto via SSH."""
    try:
        cmd = ["curl", "-s", "--max-time", "3", "http://localhost:11434/api/generate", "-d",
               json.dumps({"model": model, "prompt": prompt, "stream": False})]
        output = subprocess.check_output(cmd, text=True)
        data = json.loads(output)
        return f"🤖 [LOCAL LLM]: {data.get('response', 'No hubo respuesta.')}"
    except Exception:
        logging.info("Ollama local no disponible, delegando a nodo remoto 'server-ai'...")
        payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).replace('"', '\\"')
        remote_cmd = f'curl -s http://localhost:11434/api/generate -d "{payload}"'
        return node_manager.exec_remote_cmd("server-ai", remote_cmd)
