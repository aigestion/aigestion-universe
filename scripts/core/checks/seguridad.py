import json
import subprocess

from safe_exec import run_code


def detectar_bolsillo():
    """Usa el sensor de proximidad para saber si el móvil está tapado."""
    print("🌑 Comprobando sensor de proximidad...")
    try:
        proc = subprocess.Popen(["termux-sensor", "-s", "proximity", "-n", "1"],
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        out, _ = proc.communicate(timeout=3)
        data = json.loads(out)
        for key in data:
            if "values" in data[key]:
                distancia = data[key]["values"][0]
                if distancia < 2.0:
                    return True # Está en el bolsillo / tapado
                return False
    except Exception:
        pass
    return False

def autorizacion_biometrica():
    """Lanza el escáner facial/huella del Pixel."""
    print("👁️ Solicitando reconocimiento facial/biométrico...")
    try:
        raw = subprocess.check_output(["termux-fingerprint"], stderr=subprocess.DEVNULL).decode('utf-8')
        data = json.loads(raw)
        return data.get("auth_result") == "AUTH_RESULT_SUCCESS"
    except Exception:
        return False

# SECUENCIA ÉPICA DE PRUEBA
run_code("clear")
print("=== PROTOCOLO DE SEGURIDAD DANIELA ===\n")

en_bolsillo = detectar_bolsillo()

if en_bolsillo:
    print("👖 ESTADO: Teléfono en el bolsillo (o boca abajo).")
    print("🤫 Daniela: 'Comandante, estamos a oscuras. No pediré reconocimiento facial. Modo Stealth activo.'")
else:
    print("📱 ESTADO: Teléfono al descubierto.")
    print("🗣️ Daniela: 'Entorno despejado. Solicitando escaneo facial para continuar...'")

    if autorizacion_biometrica():
        print("✅ ACCESO CONCEDIDO: ¡Hola, Alejandro! Identidad confirmada.")
    else:
        print("❌ ACCESO DENEGADO: Intruso detectado o lectura cancelada.")
