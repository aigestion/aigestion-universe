import json
import os
import sys
import time

import numpy as np
from PIL import Image
from safe_exec import run_bg, run_cmd, run_code

NOTAS_FILE = os.path.expanduser("~/daniela-os/notas_pendientes.json")
DIR_ROSTROS = os.path.expanduser("~/daniela-os/rostros")


def cargar_notas():
    if os.path.exists(NOTAS_FILE):
        with open(NOTAS_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}


def guardar_notas(notas):
    with open(NOTAS_FILE, "w", encoding="utf-8") as f:
        json.dump(notas, f, indent=4, ensure_ascii=False)


def crear_nota(destinatario, mensaje):
    notas = cargar_notas()
    dest = destinatario.capitalize()
    if dest not in notas:
        notas[dest] = []
    notas[dest].append({"mensaje": mensaje, "fecha": time.strftime("%Y-%m-%d %H:%M:%S")})
    guardar_notas(notas)
    print(f"✅ Nota guardada para {dest}: '{mensaje}'")


def listar_notas():
    notas = cargar_notas()
    if not notas or all(len(v) == 0 for v in notas.values()):
        print("📭 No hay notas pendientes en el sistema.")
        return
    print("\n📋 NOTAS PENDIENTES EN DANIELA OS:")
    for dest, lista in notas.items():
        if lista:
            print(f"\n👤 [{dest}]")
            for i, n in enumerate(lista, 1):
                print(f'  {i}. "{n["mensaje"]}" ({n["fecha"]})')


def borrar_notas(destinatario=None):
    notas = cargar_notas()
    if destinatario:
        dest = destinatario.capitalize()
        if dest in notas:
            del notas[dest]
            print(f"🗑️ Todas las notas para {dest} han sido eliminadas.")
    else:
        notas = {}
        print("🗑️ Todas las notas pendientes del sistema han sido borradas.")
    guardar_notas(notas)


def verificar_y_leer_notas():
    notas = cargar_notas()
    if not notas:
        return

    ruta_captura = os.path.expanduser("~/daniela-os/captura_nota.jpg")
    run_cmd(["termux-camera-photo", "-c", "1", ruta_captura])

    if not os.path.exists(ruta_captura) or os.path.getsize(ruta_captura) == 0:
        return

    try:
        img = Image.open(ruta_captura).convert("L").resize((100, 100))
        matriz_actual = np.array(img, dtype=np.float32)
        os.remove(ruta_captura)
    except Exception:
        return

    for persona, lista_notas in list(notas.items()):
        if not lista_notas:
            continue

        ruta_ref = os.path.join(DIR_ROSTROS, f"{persona.lower()}.npy")
        if not os.path.exists(ruta_ref):
            continue

        matriz_ref = np.load(ruta_ref)
        mse = np.mean((matriz_actual - matriz_ref) ** 2)

        if mse < 1500:
            print(f"👁️ Rostro confirmado: {persona}")
            run_bg(
                [
                    "mpv",
                    "--no-video",
                    "--ao=opensles",
                    "--volume=100",
                    os.path.expanduser("~/daniela-os/sonidos/cyber_alarm.wav"),
                ]
            )

            for nota in lista_notas:
                texto = f"Mensaje para {persona}: {nota['mensaje']}"
                print(f"📢 Leyendo nota: {texto}")
                run_code(f"termux-tts-speak '{texto}'")
                time.sleep(1)

            notas[persona] = []
            guardar_notas(notas)
            break


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd == "crear" and len(sys.argv) >= 4:
            crear_nota(sys.argv[2], " ".join(sys.argv[3:]))
        elif cmd == "listar":
            listar_notas()
        elif cmd == "borrar":
            dest = sys.argv[2] if len(sys.argv) > 2 else None
            borrar_notas(dest)
    else:
        verificar_y_leer_notas()
