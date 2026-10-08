import os
import shutil

BASE_DIR = os.path.expanduser("~/daniela-os")

def run(context):
    removed_files = 0
    freed_bytes = 0

    # 1. Archivos temporales específicos a eliminar
    temp_files = [
        os.path.join(BASE_DIR, "vision_snap.jpg"),
        os.path.join(BASE_DIR, "audio_snap.wav")
    ]

    for fpath in temp_files:
        if os.path.exists(fpath):
            try:
                freed_bytes += os.path.getsize(fpath)
                os.remove(fpath)
                removed_files += 1
            except Exception:
                pass

    # 2. Limpieza de carpetas __pycache__ y archivos .pyc / .tmp
    for root, dirs, files in os.walk(BASE_DIR):
        for d in dirs:
            if d == "__pycache__":
                cache_dir = os.path.join(root, d)
                try:
                    for c_root, _, c_files in os.walk(cache_dir):
                        for cf in c_files:
                            freed_bytes += os.path.getsize(os.path.join(c_root, cf))
                    shutil.rmtree(cache_dir)
                    removed_files += 1
                except Exception:
                    pass

        for f in files:
            if f.endswith(".pyc") or f.endswith(".tmp") or f.endswith(".log.bak"):
                file_path = os.path.join(root, f)
                try:
                    freed_bytes += os.path.getsize(file_path)
                    os.remove(file_path)
                    removed_files += 1
                except Exception:
                    pass

    freed_kb = freed_bytes / 1024
    return f"🧹 [CLEANER]: Limpieza finalizada. **{removed_files}** elemento(s) purgados ({freed_kb:.1f} KB liberados)."
