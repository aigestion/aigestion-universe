import time

import requests
from rich.console import Console
from rich.panel import Panel
from safe_exec import run_cmd, run_code

console = Console()
PC_IP = "192.168.1.170"
PORT = "5000"

# Personalidad de Daniela fuera de casa
DANIELA_PERSONALIDAD = """Eres Daniela, una asistente de IA increíblemente simpática, cálida, eficiente y leal a tu Comandante.
Tus respuestas deben ser naturales, fluidas, conversacionales y breves (máximo 2 o 3 frases).
Hablas con un toque sutil de complicidad y entusiasmo profesional. Evita listas largas salvo que te lo pida."""


def comprobar_red_local():
    try:
        res = requests.get(f"http://{PC_IP}:{PORT}/", timeout=1.5)
        return res.status_code == 200
    except Exception:
        return False


def hablar_termux(texto):
    # Llama al motor TTS nativo de Android en Termux si está instalado (termux-tts-speak)
    texto_limpio = texto.replace("'", "").replace('"', "")
    run_cmd(["termux-tts-speak", texto_limpio])


def bucle_satelite():
    run_code("clear")
    console.print(
        Panel("⚡ DANIELA OS :: MÓDULO SATÉLITE DUAL (Móvil / Nube) ⚡", style="bold cyan")
    )

    while True:
        es_local = comprobar_red_local()

        if es_local:
            console.print(
                "🟢 [MODO PROXIMIDAD]: PC Master detectada en la Wi-Fi local. Enlace activo.",
                style="bold green",
            )
        else:
            console.print(
                "🌐 [MODO SATÉLITE REMOTO]: PC fuera de alcance. Conectado directamente a la Nube.",
                style="bold yellow",
            )
            console.print(
                "🎙️ Daniela lista con voz y personalidad remota activa.", style="italic magenta"
            )

        time.sleep(10)


if __name__ == "__main__":
    bucle_satelite()
