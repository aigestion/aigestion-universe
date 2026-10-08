import os
import shutil

from safe_exec import run_cmd


def test_componente(nombre, comando):
    print(f"🔍 Auditando {nombre}...", end=" ")
    if shutil.which(comando):
        print("PASÓ ✅")
        return True
    else:
        print("FALLÓ ❌")
        return False


def auditoria():
    print("=== AUDITORÍA DE DANIELA OS ===")
    test_componente("Motor de Audio (mpv)", "mpv")
    test_componente("Motor de voz (espeak-ng)", "espeak-ng")
    test_componente("API de Termux", "termux-microphone-record")

    print("\n=== PRUEBAS UNITARIAS ===")

    # Test 1: TTS Nativo (Calidad HD)
    print("Test 1: TTS Android Nativo...", end=" ")
    run_cmd(["termux-tts-speak", "Prueba de voz HD"])
    print("INTENTADO (Verifica si escuchas voz humana)")

    # Test 2: Audio Directo
    print("Test 2: Audio Directo...", end=" ")
    run_cmd(["mpv", "--ao=opensles", os.path.expanduser("~/daniela-os/sonidos/cyber_alarm.wav")])
    print("INTENTADO (Verifica si escuchas alarma)")


if __name__ == "__main__":
    auditoria()
