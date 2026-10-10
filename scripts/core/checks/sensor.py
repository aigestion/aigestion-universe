import json
import math
import subprocess
import time


def get_acc():
    try:
        raw = subprocess.check_output(["termux-sensor", "-s", "accelerometer", "-n", "1"], stderr=subprocess.DEVNULL).decode('utf-8')
        return json.loads(raw)['values']
    except Exception:
        return [0,0,0]

base = get_acc()
print("Agita ahora. Verás el número 'Delta' subir.")
for _i in range(20):
    curr = get_acc()
    delta = math.sqrt(sum((c - b)**2 for c, b in zip(curr, base)))
    print(f"Delta actual: {delta:.2f}")
    time.sleep(0.5)
