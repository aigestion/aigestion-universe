import subprocess
import re

def run(context):
    cmd = context.lower()
    
    try:
        # Inspección directa de la tabla ARP local mediante 'ip neighbor'
        res = subprocess.run(['ip', 'neighbor'], capture_output=True, text=True, timeout=5)
        output = res.stdout.strip()
        
        if not output:
            return "📡 [NET AUDIT]: No se detectaron vecinos activos en la subred local o no hay conexión WiFi."

        devices = []
        lines = output.split('\n')
        
        for line in lines:
            # Filtrar entradas activas (REACHABLE, STALE, DELAY)
            parts = line.split()
            if len(parts) >= 5 and ("REACHABLE" in line or "STALE" in line or "DELAY" in line):
                ip = parts[0]
                dev = parts[2]
                mac = parts[4] if len(parts) > 4 else "Desconocida"
                state = parts[-1]
                devices.append(f"• IP: `{ip}` | MAC: `{mac}` | Dev: `{dev}` ({state})")

        if not devices:
            return "📡 [NET AUDIT]: Red inspeccionada. No se encontraron dispositivos activos adicionales."

        count = len(devices)
        header = f"🛡️ [NET AUDIT]: Auditoría finalizada. **{count}** dispositivo(s) detectado(s) en la subred:\n\n"
        return header + "\n".join(devices)

    except Exception as e:
        return f"❌ [NET AUDIT]: Error durante la auditoría de red: {str(e)}"
