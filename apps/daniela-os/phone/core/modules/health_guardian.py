import json
import os
import subprocess


def check_system_health():
    report = ["📱 **DIAGNÓSTICO REAL DE SALUD DEL DISPOSITIVO PIXEL**:\n"]

    # 1. Batería mediante Termux API (si está instalado) o fallback en /sys
    try:
        bat_res = subprocess.run(
            ["termux-battery-status"], capture_output=True, text=True, timeout=3.0
        )
        if bat_res.returncode == 0:
            bat = json.loads(bat_res.stdout)
            percentage = bat.get("percentage", "N/A")
            temp = bat.get("temperature", "N/A")
            status = bat.get("status", "N/A")
            health = bat.get("health", "N/A")
            report.append(
                f"• **Batería**: {percentage}% ({status}) | Temp: {temp}°C | Salud: {health}"
            )
        else:
            report.append(
                "• **Batería**: Instala `termux-api` para lecturas de sensores detalladas."
            )
    except Exception as e:
        report.append(f"• **Batería**: No disponible en el shell ({e})")

    # 2. Memoria RAM real (`free -m`)
    try:
        ram_res = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=3.0)
        lines = ram_res.stdout.strip().splitlines()
        if len(lines) >= 2:
            parts = lines[1].split()
            total_ram, used_ram, free_ram = parts[1], parts[2], parts[3]
            report.append(
                f"• **Memoria RAM Real**: Usada {used_ram}MB / Total {total_ram}MB (Libre: {free_ram}MB)"
            )
    except Exception as e:
        report.append(f"• **RAM**: Error al consultar ({e})")

    # 3. Almacenamiento real (`df -h`)
    try:
        df_res = subprocess.run(
            ["df", "-h", os.path.expanduser("~")], capture_output=True, text=True, timeout=3.0
        )
        lines = df_res.stdout.strip().splitlines()
        if len(lines) >= 2:
            parts = lines[1].split()
            size, used, avail = parts[1], parts[2], parts[3]
            report.append(
                f"• **Almacenamiento Termux**: Usado {used} / {size} (Disponible: {avail})"
            )
    except Exception as e:
        report.append(f"• **Almacenamiento**: Error al consultar ({e})")

    # 4. Estado de SQLite ~/apps/aig/data/env.db
    env_db = os.path.expanduser("~/apps/aig/data/env.db")
    if os.path.exists(env_db):
        size_kb = round(os.path.getsize(env_db) / 1024, 2)
        report.append(
            f"• **Base de Datos SQLite (`~/apps/aig/data/env.db`)**: Presente ({size_kb} KB)"
        )
    else:
        report.append(
            "• **Base de Datos SQLite**: ⚠️ No encontrada (`~/apps/aig/data/env.db` falta)."
        )

    return "\n".join(report)


if __name__ == "__main__":
    print(check_system_health())
