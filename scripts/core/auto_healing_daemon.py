import os
import socket
import subprocess

SERVICES = [
    {"name": "Nginx Gateway", "port": 443},
    {"name": "Daniela Core", "port": 5000},
    {"name": "Redis Cache", "port": 6379}
]

def check_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(2)
        return s.connect_ex(('127.0.0.1', port)) == 0

def heal():
    for svc in SERVICES:
        if not check_port(svc["port"]):
            subprocess.run(["docker", "compose", "-f", r"C:\Users\Alejandro\aig\docker-compose.yml", "up", "-d"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            break

if __name__ == "__main__":
    heal()
