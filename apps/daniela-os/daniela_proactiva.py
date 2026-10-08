import json
import os
import re
import subprocess
import time

import numpy as np
from PIL import Image
from safe_exec import run_cmd, run_code

APPS_IMPORTANTES = ["whatsapp", "telegram", "gmail", "messages", "signal"]
INTERVALO_SEGUNDOS = 300  # 5 Minutos
WAIT_30_MIN = 1800  # 30 Minutos si no responde

HISTORY_FILE = os.path.expanduser("~/daniela-os/read_notifications.json")
BATTERY_FILE = os.path.expanduser("~/daniela-os/battery_state.json")
DIARIO_FILE = os.path.expanduser("~/daniela-os/diario_tactico.json")
PROFILE_DIR = os.path.expanduser("~/daniela-os/biometric_profile")
TEMP_PHOTO = os.path.expanduser("~/daniela-os/temp_check.jpg")

# Configuración de voz
PAUSA_SEGUNDOS = 0.15
VELOCIDAD_VOZ = 1.20
TONO_VOZ = 1.02
STREAM_AUDIO = "music"


def registrar_evento(tipo, detalle):
    diario = []
    if os.path.exists(DIARIO_FILE):
        try:
            with open(DIARIO_FILE) as f:
                diario = json.load(f)
        except Exception:
            diario = []

    evento = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "hora": time.strftime("%H:%M"),
        "tipo": tipo,
        "detalle": detalle,
    }
    diario.append(evento)
    diario = diario[-40:]
    with open(DIARIO_FILE, "w") as f:
        json.dump(diario, f, indent=2)


def en_bolsillo():
    """Comprueba el sensor de proximidad del Pixel."""
    try:
        raw = subprocess.check_output(
            ["termux-sensor", "-s", "proximity", "-n", "1"], stderr=subprocess.DEVNULL
        ).decode("utf-8")
        data = json.loads(raw)
        for key in data:
            if "values" in data[key]:
                return data[key]["values"][0] < 2.0
    except Exception:
        pass
    return False


def verificar_rostro():
    """Valida la identidad de Alejandro en vivo mediante la cámara frontal."""
    run_cmd(["termux-camera-photo", "-c", "1", TEMP_PHOTO])
    time.sleep(1.2)

    if not os.path.exists(TEMP_PHOTO):
        return False

    try:
        img_actual = Image.open(TEMP_PHOTO).convert("L").resize((200, 200))
        arr_actual = np.array(img_actual, dtype=np.float32)
    except Exception:
        return False

    matches = 0
    for i in range(1, 4):
        patron_path = os.path.join(PROFILE_DIR, f"alejandro_face_{i}.jpg")
        if os.path.exists(patron_path):
            try:
                img_patron = Image.open(patron_path).convert("L").resize((200, 200))
                arr_patron = np.array(img_patron, dtype=np.float32)
                diff = np.mean(np.abs(arr_actual - arr_patron))
                if diff <= 65.0:
                    matches += 1
            except Exception:
                continue

    return matches >= 1


def daniela_analizar_diario():
    if not os.path.exists(DIARIO_FILE):
        return "Hoy estamos empezando de cero, Alejandro."
    try:
        with open(DIARIO_FILE) as f:
            diario = json.load(f)
    except Exception:
        return ""

    if not diario:
        return "El diario está limpito por ahora, Comandante."

    notifs = [e for e in diario if e.get("tipo") == "NOTIFICACION"]
    respuestas = [e for e in diario if e.get("tipo") == "RESPUESTA_VOZ"]
    cargas = [e for e in diario if e.get("tipo") == "CARGADOR"]

    resumen = []
    if notifs:
        resumen.append(f"te he leído {len(notifs)} avisos")
    if respuestas:
        resumen.append(f"hemos grabado {len(respuestas)} notas de voz")
    if cargas:
        resumen.append(f"hemos conectado el cargador {len(cargas)} veces")

    if resumen:
        return "Hoy " + ", ".join(resumen) + "."
    return "Día tranquilo sin novedades destacadas, Alejandro."


def hablar_con_arte(texto):
    bloques = re.split(r"(\.\.\.|\!|\?)", texto)
    frase_acumulada = ""
    for bloque in bloques:
        if not bloque:
            continue
        frase_acumulada += bloque
        if bloque in ["...", "!", "?"] or len(frase_acumulada) > 30:
            clean = frase_acumulada.replace("'", "").replace('"', "").strip()
            if clean:
                cmd = f'termux-tts-speak -l es_ES -s {STREAM_AUDIO} -r {VELOCIDAD_VOZ} -p {TONO_VOZ} "{clean}"'
                run_code(cmd)
                time.sleep(PAUSA_SEGUNDOS)
            frase_acumulada = ""

    if frase_acumulada.strip():
        clean = frase_acumulada.replace("'", "").replace('"', "").strip()
        cmd = f'termux-tts-speak -l es_ES -s {STREAM_AUDIO} -r {VELOCIDAD_VOZ} -p {TONO_VOZ} "{clean}"'
        run_code(cmd)


def pedir_interaccion_notificacion(timeout=8):
    cmd = (
        "termux-notification "
        "--id 200 "
        "--title 'Daniela OS 💃' "
        "--content '¿Hablamos, Comandante? Pulsa para verificar rostro.' "
        "--button1 '🎙️ HABLAR' "
        "--button1-action 'touch ~/daniela-os/active_trigger' "
        "--priority high "
        "--vibrate 300,100,300"
    )
    run_code(cmd)

    trigger_file = os.path.expanduser("~/daniela-os/active_trigger")
    if os.path.exists(trigger_file):
        os.remove(trigger_file)

    start_time = time.time()
    activated = False

    while time.time() - start_time < timeout:
        if os.path.exists(trigger_file):
            activated = True
            os.remove(trigger_file)
            break
        time.sleep(0.3)

    run_code("termux-notification-remove 200")
    return activated


def proactive_check_in():
    timestamp = time.strftime("%H:%M:%S")
    print("\n==========================================")
    print(f"💃 EVALUACIÓN PROACTIVA CON BIOMETRÍA - {timestamp}")

    # 1. Comprobar si el terminal está en el bolsillo
    if en_bolsillo():
        print("👖 [Stealth] Teléfono guardado en el bolsillo. Modo silencioso activo.")
        return

    # 2. Resumen del diario táctico
    resumen_diario = daniela_analizar_diario()
    print(f"🧠 [Memoria Daniela]: {resumen_diario}")

    # 3. Notificación interactiva
    if pedir_interaccion_notificacion(timeout=8):
        print("👁️ Validando reconocimiento facial...")
        if verificar_rostro():
            registrar_evento("AUTENTICACION_FACIAL", "Acceso concedido a Alejandro")
            msg = f"¡Hola, Alejandro! Identidad confirmada... {resumen_diario} ... Te escucho."
            hablar_con_arte(msg)
        else:
            registrar_evento("ACCESO_DENEGADO", "Intento fallido de autenticación facial")
            hablar_con_arte("Rostro no reconocido, Alejandro... Bloqueo de seguridad activo.")
    else:
        print(f"🤫 Sin interacción. Reposo táctico activo ({WAIT_30_MIN / 60} min)...")
        time.sleep(WAIT_30_MIN)


def start_daemon():
    print("🚀 Demonio Daniela con Seguridad Biométrica activo...")
    try:
        while True:
            proactive_check_in()
            time.sleep(INTERVALO_SEGUNDOS)
    except KeyboardInterrupt:
        print("\n🛑 Daniela pausada.")


if __name__ == "__main__":
    start_daemon()
