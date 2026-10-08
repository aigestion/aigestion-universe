import os
import subprocess

from safe_exec import run_bg, run_code


def escuchar_voz_directa():
    print("\n⚡ [DANIELA OS] Escuchando... Habla ahora.")

    # Tono de activación en altavoz
    run_bg(
        [
            "mpv",
            "--no-video",
            "--ao=opensles",
            "--volume=100",
            os.path.expanduser("~/daniela-os/sonidos/cyber_alarm.wav"),
        ]
    )

    try:
        # Forzar entrada de voz rápida
        raw = (
            subprocess.check_output(["termux-speech-to-text"], stderr=subprocess.DEVNULL, timeout=7)
            .decode("utf-8")
            .strip()
            .lower()
        )
        if raw:
            return raw
    except Exception:
        pass

    return None


def procesar_comando(orden):
    print(f'\n🗣️ Recibido: "{orden}"')

    if "bateria" in orden or "energia" in orden:
        run_code("termux-battery-status")
        run_code("termux-tts-speak 'Mostrando estado de bateria'")
    elif "sos" in orden or "ayuda" in orden or "emergencia" in orden:
        run_code("python ~/daniela-os/panic_sos.py")
    elif "notas" in orden or "mensajes" in orden:
        run_code("python ~/daniela-os/notas_proactivas.py listar")
    elif "hola" in orden or "escuchas" in orden or "daniela" in orden:
        run_code("termux-tts-speak 'Afirmativo Comandante, te escucho alto y claro.'")
        print("🔊 Daniela: Afirmativo Comandante, te escucho alto y claro.")
    else:
        print(f"⚡ Ejecutando acción: {orden}")
        run_code(f"termux-tts-speak 'Procesando {orden}'")


if __name__ == "__main__":
    run_code("termux-tts-speak 'Sistema listo. Presiona enter para hablar.'")
    print("==================================================")
    print("🌆 DANIELA OS - MODO CALLE DE ALTA RESPUESTA")
    print("==================================================")

    while True:
        try:
            print("\n👉 Presiona [ENTER] para hablar | Escribe directamente el comando:")
            entrada = input("Comandante > ").strip().lower()

            # Si presiona ENTER sin texto, activa el micrófono
            if entrada == "":
                orden_voz = escuchar_voz_directa()
                if orden_voz:
                    procesar_comando(orden_voz)
                else:
                    print("⚠️ No se detectó audio claro. Intenta de nuevo o escribe la orden.")
            else:
                # Si escribió texto directamente
                procesar_comando(entrada)

        except KeyboardInterrupt:
            print("\nSaliendo del modo calle...")
            break
