"""
Daniela OS - Background Daemon
Keeps all 50 systems alive with auto-restart
"""

import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

DAEMON_DIR = Path(__file__).parent
DATA_DIR = DAEMON_DIR / "data"
LOGS_DIR = DAEMON_DIR / "logs"
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

PID_FILE = DATA_DIR / "daemon_pids.json"
HEARTBEAT_FILE = DATA_DIR / "daemon_heartbeat.json"

SYSTEMS = [
    {"name": "Daniela Server", "port": None, "script": "server.py"},
    {
        "name": "Cross-Device Sync",
        "port": None,
        "script": None,
        "module": "shared.cross_device_sync",
    },
    {"name": "Voice Activation", "port": None, "script": None, "module": "shared.voice_activation"},
]


class DanielaDaemon:
    def __init__(self):
        self.processes = {}
        self.running = True
        self.restart_count = {}

    def log(self, msg, level="INFO"):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] [{level}] {msg}"
        print(line)
        log_file = LOGS_DIR / f"daemon_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def start_server(self):
        self.log("Starting Daniela Server...")
        try:
            proc = subprocess.Popen(
                [sys.executable, str(DAEMON_DIR / "server.py")],
                stdout=open(LOGS_DIR / "server.log", "w", encoding="utf-8"),
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            )
            self.processes["server"] = proc
            self.log(f"Server started (PID: {proc.pid})")
            return True
        except Exception as e:
            self.log(f"Failed to start server: {e}", "ERROR")
            return False

    def check_health(self):
        health = {}
        for name, proc in self.processes.items():
            if proc is None:
                health[name] = False
                continue
            try:
                if os.name == "nt":
                    import ctypes

                    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, proc.pid)
                    if handle:
                        ctypes.windll.kernel32.CloseHandle(handle)
                        health[name] = True
                    else:
                        health[name] = False
                else:
                    os.kill(proc.pid, 0)
                    health[name] = True
            except Exception:
                health[name] = False
        return health

    def restart_failed(self):
        health = self.check_health()
        for name, alive in health.items():
            if not alive:
                count = self.restart_count.get(name, 0)
                if count < 5:
                    self.log(f"{name} is down, restarting (attempt {count + 1})")
                    if name == "server":
                        self.start_server()
                    self.restart_count[name] = count + 1
                else:
                    self.log(f"{name} failed too many times, giving up", "ERROR")

    def save_heartbeat(self):
        heartbeat = {
            "timestamp": time.time(),
            "uptime": time.time() - self.start_time,
            "processes": {
                name: proc.pid if proc else None for name, proc in self.processes.items()
            },
            "health": self.check_health(),
            "restart_counts": self.restart_count,
        }
        HEARTBEAT_FILE.write_text(json.dumps(heartbeat, indent=2), encoding="utf-8")

    def run(self):
        self.start_time = time.time()
        self.log("=" * 50)
        self.log("DANIELA OMNIPRESENTE DAEMON - Starting")
        self.log("=" * 50)

        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        self.start_server()

        self.log("Daemon running. Press Ctrl+C to stop.")

        while self.running:
            try:
                self.save_heartbeat()
                self.restart_failed()
                time.sleep(30)
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.log(f"Error in main loop: {e}", "ERROR")
                time.sleep(5)

        self.log("Daemon shutting down...")
        for name, proc in self.processes.items():
            if proc:
                try:
                    proc.terminate()
                    self.log(f"Stopped {name}")
                except Exception:
                    pass

    def _handle_signal(self, signum, frame):
        self.log(f"Received signal {signum}, shutting down...")
        self.running = False


def status():
    if HEARTBEAT_FILE.exists():
        data = json.loads(HEARTBEAT_FILE.read_text(encoding="utf-8"))
        print("\nDANIELA OMNIPRESENTE - DAEMON STATUS")
        print("=" * 50)
        print(f"Uptime: {data['uptime'] / 3600:.1f} hours")
        print(
            f"Last heartbeat: {datetime.fromtimestamp(data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}"
        )
        print("\nProcesses:")
        for name, pid in data["processes"].items():
            status = "RUNNING" if data["health"].get(name) else "STOPPED"
            print(f"  [{status}] {name} (PID: {pid})")
        print("\nRestart counts:")
        for name, count in data["restart_counts"].items():
            print(f"  {name}: {count}")
    else:
        print("Daemon has not been started yet")


def stop():
    if PID_FILE.exists():
        data = json.loads(PID_FILE.read_text(encoding="utf-8"))
        for name, info in data.items():
            if info.get("pid"):
                try:
                    os.kill(info["pid"], signal.SIGTERM)
                    print(f"Stopped {name}")
                except Exception:
                    pass
        PID_FILE.unlink()
        print("All processes stopped")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "start"
    if cmd == "start":
        DanielaDaemon().run()
    elif cmd == "status":
        status()
    elif cmd == "stop":
        stop()
    else:
        print("Usage: python daemon.py [start|stop|status]")
