import subprocess


def audit_network():
    try:
        cmd = ["nmap", "-sn", "192.168.1.0/24"]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        devices = [line.replace("Nmap scan report for ", "").strip() for line in output.split('\n') if "Nmap scan report for" in line]
        return f"🛡️ [NETSEC AUDIT]: {len(devices)} dispositivos detectados en la red local."
    except Exception as e:
        return f"⚠️ [NETSEC ERROR]: {e}"
