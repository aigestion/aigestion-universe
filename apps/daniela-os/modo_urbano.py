import time

from copiloto_voz import ejecutar_copiloto
from monitor_recursos import inspeccionar_recursos
from safe_exec import run_code
from wake_word import esperar_palabra_clave

if __name__ == "__main__":
    print("🌆 [MODO URBANO] Daniela OS en guardia. Di 'Daniela' o presiona ENTER para activar...")
    run_code("termux-tts-speak 'Modo urbano activado. En guardia Comandante.'")

    while True:
        inspeccionar_recursos()
        if esperar_palabra_clave():
            ejecutar_copiloto()
        time.sleep(2)
