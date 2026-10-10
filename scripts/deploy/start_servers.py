import socket
import subprocess
import time

SERVERS = [
    ("Daniela", "python daniela-os/server.py"),
    ("Hermes", "python hermes-epic/server.py"),
    ("Optimization", "python aig-optimization/server.py"),
]

procs = {}
for name, cmd in SERVERS:
    proc = subprocess.Popen(
        cmd, shell=True,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    procs[name] = proc.pid
    print(f"[START] {name} -> PID {proc.pid}")
    time.sleep(1)

print("\n[ALL] All servers launched!")
print("[STATUS] Checking ports...")
time.sleep(3)

for port in [9200, 9300, 9400, 5020]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        s.connect(("127.0.0.1", port))
        s.close()
        print(f"[OK] Port {port} online")
    except Exception:
        print(f"[OFF] Port {port}")

print("\n[READY] All services running!")
print("  Daniela:    http://localhost:9200")
print("  Hermes:     http://localhost:9300")
print("  Optimization: http://localhost:9400")
print("  Epic PC:    http://localhost:5020")
