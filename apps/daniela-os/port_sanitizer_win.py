import os
import shutil
import tempfile

import psutil


def sanitize():
    print("🧹 [PORT SANITIZER WIN] Purgando procesos y puertos en Windows...")
    targets = ["windsurf", "antigravity", "language", "node"]

    # Matar procesos
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            pname = proc.info["name"].lower()
            if any(t in pname for t in targets):
                print(f"  └─ Eliminando proceso: {proc.info['name']} (PID: {proc.info['pid']})")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Limpiar temporales
    temp_dir = tempfile.gettempdir()
    for item in os.listdir(temp_dir):
        if any(item.startswith(prefix) for prefix in ["windsurf", "vscode", "antigravity"]):
            full_path = os.path.join(temp_dir, item)
            try:
                if os.path.isdir(full_path):
                    shutil.rmtree(full_path, ignore_errors=True)
                else:
                    os.remove(full_path)
            except Exception:
                pass
    print("✅ Purgado completado en Windows.")


if __name__ == "__main__":
    sanitize()
