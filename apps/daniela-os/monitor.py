import os
import time

LOG_FILE = "daniela_system.log"

print("📡 MONITOR DE LOGS DE DANIELA OS ACTIVO")
print("---------------------------------------")

if not os.path.exists(LOG_FILE):
    open(LOG_FILE, "w").close()

with open(LOG_FILE) as f:
    f.seek(0, os.SEEK_END)
    while True:
        line = f.readline()
        if not line:
            time.sleep(0.5)
            continue
        if "ERROR" in line or "WARNING" in line:
            print(f"🚨 \033[91m{line.strip()}\033[0m")
        else:
            print(f"ℹ️ \033[92m{line.strip()}\033[0m")
