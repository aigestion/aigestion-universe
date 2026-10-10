import socket
import subprocess
import time

# Kill existing
for port in [9400, 9500, 9600, 9700, 9800, 9999, 9998, 9997]:
    subprocess.run(f'taskkill /F /FI "PORT {port}" 2>nul', shell=True, capture_output=True)

procs = [
    ('Optimization', 'python server.py', r'C:\Users\Alejandro\aig\aig-optimization', 9400),
    ('Frontend V1', 'python server.py', r'C:\Users\Alejandro\aig\frontend-optimization', 9500),
    ('Frontend V2', 'python server.py', r'C:\Users\Alejandro\aig\frontend-opt2', 9600),
    ('Infra', 'python server.py', r'C:\Users\Alejandro\aig\infra-opt', 9700),
    ('Agent/Mobile', 'python server.py', r'C:\Users\Alejandro\aig\agents\api', 9800),
    ('Security', 'python server.py', r'C:\Users\Alejandro\aig\sec-opt', 9999),
    ('Perf/Quality', 'python server.py', r'C:\Users\Alejandro\aig\perf-opt', 9998),
    ('Dashboard', 'python daniela-os/unified-dashboard/server.py', r'C:\Users\Alejandro\aig', 9997),
]

for name, cmd, cwd, _port in procs:
    p = subprocess.Popen(cmd, shell=True, cwd=cwd, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f'Started {name} (PID {p.pid}) in {cwd}')
    time.sleep(1.5)

time.sleep(4)
print()
for port in [9400, 9500, 9600, 9700, 9800, 9999, 9998, 9997]:
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect(('127.0.0.1', port))
        s.close()
        print('[OK] Port ' + str(port))
    except Exception:
        print('[OFF] Port ' + str(port))
