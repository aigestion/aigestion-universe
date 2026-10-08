import json, os

VAULT_FILE = "/data/data/com.termux/files/home/daniela-os/memory_vault.json"

def save_memory(data):
    vault = load_vault()
    vault.append(data)
    with open(VAULT_FILE, 'w') as f:
        json.dump(vault, f)

def load_vault():
    if not os.path.exists(VAULT_FILE): return []
    with open(VAULT_FILE, 'r') as f:
        try: return json.load(f)
        except: return []

def run(context):
    if "guarda" in context.lower():
        save_memory(context.replace("guarda", "").strip())
        return "💾 [MEMORY]: Dato archivado en la Bóveda."
    elif "memoria" in context.lower() or "recuerda" in context.lower():
        vault = load_vault()
        if not vault: return "🗄️ [MEMORY]: Bóveda vacía."
        return f"🗄️ [MEMORY]: He encontrado {len(vault)} registros. Últimos: " + "; ".join(vault[-3:])
    return "❌ [MEMORY]: Comando no reconocido. Usa 'guarda <dato>' o 'recuerda'."
