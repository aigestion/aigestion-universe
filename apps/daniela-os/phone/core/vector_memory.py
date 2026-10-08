import datetime
import json
import os

MEMORY_FILE = os.path.expanduser("~/core/memoria_daniela.json")


def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"context": [], "system_notes": []}


def save_memory(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def remember_fact(note, category="general"):
    mem = load_memory()
    entry = {"timestamp": datetime.datetime.now().isoformat(), "category": category, "note": note}
    mem["system_notes"].append(entry)
    save_memory(mem)
    print(f"🧠 Memoria guardada: [{category}] {note}")


def search_memory(query):
    mem = load_memory()
    words = query.lower().split()
    results = []
    for item in mem["system_notes"]:
        note_lower = item["note"].lower()
        if any(w in note_lower for w in words):
            results.append(item["note"])
    return results


if __name__ == "__main__":
    # Inicialización con datos de contexto de Daniela OS
    remember_fact("Google Drive se mantiene al 0% mediante purgas automáticas.", "nube")
    remember_fact(
        "Las cuentas administradas son noemisanalex@gmail.com y admin@aigestion.net.", "cuentas"
    )
    remember_fact("El monorepo principal reside en ~/apps/AIGESTION-MONOREPO.", "infraestructura")
    print("\n🔍 Prueba de búsqueda en memoria:")
    print(search_memory("cuentas"))
