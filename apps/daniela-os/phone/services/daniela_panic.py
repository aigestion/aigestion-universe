import os
import sqlite3

RAM_DIR = "/data/data/com.termux/files/usr/tmp/daniela_ram"
DB_PATH = os.path.expanduser("~/core/daniela_memory.db")


def execute_panic_protocol():
    print("🚨 [PANIC KEY ACTIVADA] Desinfectando nodo Edge...")

    # 1. Purgar RAMDisk
    if os.path.exists(RAM_DIR):
        for f in os.listdir(RAM_DIR):
            file_path = os.path.join(RAM_DIR, f)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception:
                pass

    # 2. Limpiar eventos recientes de memoria episódica
    if os.path.exists(DB_PATH):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM episodic_events")
                cursor.execute("DELETE FROM episodic_fts")
                conn.commit()
        except Exception:
            pass

    # 3. Respuesta neutra
    return "Modo de mantenimiento activado. Sistema en reposo."


if __name__ == "__main__":
    msg = execute_panic_protocol()
    print(f"🤖 Respuesta de cobertura: '{msg}'")
