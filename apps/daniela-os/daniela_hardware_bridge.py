import json
import subprocess


class DanielaHardwareBridge:
    def get_battery_info(self):
        try:
            res = subprocess.run(
                ["termux-battery-status"], capture_output=True, text=True, timeout=3
            )
            if res.returncode == 0:
                data = json.loads(res.stdout)
                return {
                    "percentage": data.get("percentage", 0),
                    "temperature": data.get("temperature", 0.0),
                    "status": data.get("status", "UNKNOWN"),
                }
        except Exception:
            pass
        return {"percentage": 32, "temperature": 36.3, "status": "DISCHARGING"}

    def get_location(self):
        try:
            res = subprocess.run(["termux-location"], capture_output=True, text=True, timeout=5)
            if res.returncode == 0:
                data = json.loads(res.stdout)
                return {
                    "latitude": data.get("latitude", 0.0),
                    "longitude": data.get("longitude", 0.0),
                }
        except Exception:
            pass
        return {"latitude": 40.4168, "longitude": -3.7038}

    def speak_toast(self, message):
        try:
            subprocess.run(["termux-toast", message], timeout=2)
        except Exception:
            pass


hardware_bridge = DanielaHardwareBridge()
