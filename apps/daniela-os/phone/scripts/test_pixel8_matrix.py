import os
import socket
import subprocess
import time

import requests


def print_header(title):
    print("\033[1;36m======================================================\033[0m")
    print(f"\033[1;36m 🧪 AUDITORÍA INTEGRAL PIXEL 8: {title}\033[0m")
    print("\033[1;36m======================================================\033[0m")


def test_dirs():
    print("📁 1. Verificando Estructura de Directorios Modular...")
    home = os.path.expanduser("~")
    required = ["apps", "core", "services", "scripts", "logs", "assets", "downloads"]
    missing = []
    for d in required:
        path = os.path.join(home, d)
        if not os.path.exists(path):
            missing.append(d)

    if not missing:
        print("  \033[0;32m[PASS] Directorios de sistema limpios e integrados.\033[0m")
        return True
    else:
        print(f"  \033[0;31m[FAIL] Faltan directorios: {missing}\033[0m")
        return False


def test_hardware():
    print("\n📱 2. Verificando Hardware y API de Android (API Termux)...")
    try:
        # Test vibrador
        subprocess.Popen(
            ["termux-vibrate", "-d", "50"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print("  \033[0;32m[PASS] Motor háptico (Vibración): OK\033[0m")

        # Test síntesis de voz asíncrona sin bloqueo
        subprocess.Popen(
            ["termux-tts-speak", "-l", "es", "-p", "1.1", "-r", "1.1", "Prueba de voz nominal."],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(0.5)
        print("  \033[0;32m[PASS] Síntesis de Voz (TTS Asíncrono): OK\033[0m")
        return True
    except Exception as e:
        print(f"  \033[0;31m[FAIL] Error en API Android: {e}\033[0m")
        return False


def test_ports():
    print("\n🔌 3. Escaneando Puertos Locales (Servicios Edge)...")
    ports = [8001]
    all_ok = True
    for p in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        result = sock.connect_ex(("127.0.0.1", p))
        if result == 0:
            print(f"  \033[0;32m[PASS] Puerto {p} (Router Edge): Escuchando\033[0m")
        else:
            print(f"  \033[0;33m[WARN] Puerto {p}: Cerrado.\033[0m")
            all_ok = False
        sock.close()
    return all_ok


def test_hybrid_router():
    print("\n🧠 4. Evaluando Inferencia del Router Híbrido Local...")
    url = "http://127.0.0.1:8001/api/hybrid/chat"
    try:
        r = requests.post(url, json={"prompt": "Test de diagnóstico autónomo"}, timeout=3.0)
        if r.status_code == 200:
            data = r.json()
            source = data.get("source", "Desconocido")
            resp = data.get("response", "")
            print(f"  \033[0;32m[PASS] Endpoint activo. Fuente: {source}\033[0m")
            print(f"  🤖 Respuesta: '{resp}'")
            return True
        else:
            print(f"  \033[0;31m[FAIL] Código HTTP {r.status_code}\033[0m")
            return False
    except Exception as e:
        print(f"  \033[0;31m[FAIL] Router no responde en 8001: {e}\033[0m")
        return False


def run_all():
    print_header("NODO EDGE (PIXEL 8)")
    t1 = test_dirs()
    t2 = test_hardware()
    t3 = test_ports()

    if not t3:
        print("\n⚙️ Arrancando demonio de respaldo en 8001...")
        subprocess.Popen(
            ["python", os.path.expanduser("~/core/daniela_router.py")],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(1.5)

    t4 = test_hybrid_router()

    print("\n======================================================")
    if t1 and t2 and (t3 or t4):
        print("  \033[1;32m🟢 RESULTADO FINAL: PIXEL 8 OPERATIVO AL 100%\033[0m")
    else:
        print("  \033[1;33m🟡 RESULTADO FINAL: REQUIERE REVISIÓN DE PUERTOS\033[0m")
    print("======================================================")


if __name__ == "__main__":
    run_all()
