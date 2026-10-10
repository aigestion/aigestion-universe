import json
import socket
import subprocess
import time
import urllib.request

# Kill existing dashboard
subprocess.run('taskkill /F /FI "PORT 9997" 2>nul', shell=True, capture_output=True)
time.sleep(1)

# Start dashboard
proc = subprocess.Popen('python daniela-os/unified-dashboard/server.py', shell=True, cwd=r'C:\Users\Alejandro\aig', creationflags=subprocess.CREATE_NEW_PROCESS_GROUP, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print('Dashboard PID ' + str(proc.pid))
time.sleep(3)

try:
    s = socket.socket()
    s.settimeout(2)
    s.connect(('127.0.0.1', 9997))
    s.close()
    print('[OK] Port 9997 online')
except Exception:
    print('[OFF] Port 9997')

# Wait for poller to run
time.sleep(8)

d = urllib.request.urlopen('http://localhost:9997/api/services', timeout=3).read().decode()
data = json.loads(d)
for svc in data['services']:
    sid = svc['id']
    st = data['status'].get(sid, {})
    mod = st.get('modules', st.get('total_ideas', '-'))
    print('{:30s} ({}): {:10s} modules={}'.format(svc['name'], svc['port'], st.get('status', 'unknown'), mod))
