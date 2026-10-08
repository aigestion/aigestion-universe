import glob
import json
import os
import subprocess

from safe_exec import run_bg, run_code


def obtener_telemetria():
    try:
        raw = subprocess.check_output(["termux-battery-status"], stderr=subprocess.DEVNULL).decode(
            "utf-8"
        )
        data = json.loads(raw)
        return {
            "pct": data.get("percentage", 100),
            "estado": data.get("plugged", "UNPLUGGED"),
            "temp": data.get("temperature", 25.0),
        }
    except Exception:
        return {"pct": 100, "estado": "UNPLUGGED", "temp": 25.0}


def autopurga_temporales():
    print("🧹 [MONITOR] Ejecutando purga de temporales...")
    for patron in ["~/daniela-os/*.jpg", "~/daniela-os/sandbox/*.py"]:
        for f in glob.glob(os.path.expanduser(patron)):
            try:
                os.remove(f)
            except OSError:
                pass


def inspeccionar_recursos():
    data = obtener_telemetria()
    pct = data["pct"]
    estado = data["estado"]
    temp = data["temp"]

    print(f"📊 [MONITOR] Batería: {pct}% | Estado: {estado} | Temp: {temp}°C")

    # 1. Alerta Térmica
    if temp > 42.0:
        print("🔥 [ALERTA] Temperatura alta detectada.")
        run_code(
            "termux-tts-speak 'Atención Comandante. Temperatura del núcleo elevada.'"
        )  # 2. Perfiles de Energía
    if pct < 15 and estado == "UNPLUGGED":
        print("⚠️ [PERFIL] Nivel Crítico: Centinela en Modo Supervivencia.")
    elif pct >= 95 and estado != "UNPLUGGED":
        print("⚡ [PERFIL] Carga Completa alcanzada.")
        run_bg(["python", os.path.expanduser("~/daniela-os/gestor_tonos.py"), "LLAMADA_VIP"])

    # 3. Limpieza de mantenimiento
    autopurga_temporales()


if __name__ == "__main__":
    inspeccionar_recursos()
