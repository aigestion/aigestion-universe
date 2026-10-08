import json
import logging
import os

MEMORY_FILE = "memory.json"


def process_memory(action_type, text):
    try:
        data = {}
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    data = {}

        if action_type == "save":
            key_val = text.replace("recuerda", "").replace("guarda", "").strip()
            if ":" in key_val:
                k, v = key_val.split(":", 1)
                data[k.strip()] = v.strip()
            else:
                data[f"mem_{len(data) + 1}"] = key_val

            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"Memoria guardada: {key_val}")
            return f"🧠 Dato almacenado en memoria persistente: '{key_val}'"
        else:
            if not data:
                return "🧠 La memoria está vacía."
            items = [f"{k}: {v}" for k, v in data.items()]
            return "🧠 Memorias registradas:\n" + "\n".join(items[:5])
    except Exception as e:
        logging.error(f"Error en Skill de Memoria: {str(e)}")
        return f"Error en la gestión de memoria: {e}"
