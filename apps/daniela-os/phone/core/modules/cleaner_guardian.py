import glob
import os
import time

RAM_DIR = "/data/data/com.termux/files/usr/tmp/daniela_ram"


def purge_temp_files():
    if not os.path.exists(RAM_DIR):
        return "Directorio temporal limpio."

    time.time()
    count = 0
    freed = 0

    for ext in ["*.m4a", "*.wav", "*.mp3", "*.jpg", "*.png"]:
        for f in glob.glob(os.path.join(RAM_DIR, ext)):
            try:
                freed += os.path.getsize(f)
                os.remove(f)
                count += 1
            except Exception:
                pass

    freed_mb = freed / (1024 * 1024)
    return f"Purga temporal completada. Se eliminaron {count} archivos liberando {freed_mb:.2f} MB."


if __name__ == "__main__":
    print(purge_temp_files())
