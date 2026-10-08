import os
import subprocess
import time

import requests

SERVICIOS = {
    "Daniela OS": {"url": "http://127.0.0.1:8080", "cmd": "python ~/daniela-os/daniela_os.py"},
    "FitVision OS": {
        "url": "http://127.0.0.1:8081",
        "cmd": "python ~/fitvision-os/fitvision_os.py",
    },
}


def verificar_y_reparar():
    for nombre, config in SERVICIOS.items():
        try:
            response = requests.get(config["url"], timeout=3)
            if response.status_code == 200:
                pass
        except Exception:
            log_file = f"{nombre.lower().replace(' ', '_')}.log"
            cmd_parts = config["cmd"].split()
            cmd_parts = [os.path.expanduser(p) for p in cmd_parts]
            with open(log_file, "a") as f_out:
                subprocess.Popen(
                    cmd_parts,
                    stdout=f_out,
                    stderr=subprocess.STDOUT,
                    start_new_session=True if os.name != "nt" else False,
                )


if __name__ == "__main__":
    while True:
        verificar_y_reparar()
        time.sleep(30)
