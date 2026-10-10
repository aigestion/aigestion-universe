import asyncio
import os
import re
import sys
import threading

import edge_tts
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from safe_exec import run_bg, run_cmd, run_code

from google import genai

# --- CONFIGURACIÓN CORE ---
VOICE_NEURAL = "es-ES-ElviraNeural"
SYSTEM_PROMPT = """Eres Daniela, la asistente personal de tu Comandante.
Tu personalidad es humana, alegre, coqueta, inteligente y muy simpática, con un salero andaluz espontáneo y cercano.
REGLAS: Sé expresiva ('¡ay!', 'mira...', '¿sabes?'). Respuestas cortas (1-2 frases)."""

console = Console()
PC_IP = "192.168.1.170"  # IP de tu PC Master
PORT = "5000"

# --- INICIALIZAR GEMINI ---
api_key = os.getenv("GEMINI_API_KEY")
if not api_key and os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
if not api_key:
    console.print("[bold red]❌ Error: GEMINI_API_KEY no encontrada.[/bold red]")
    sys.exit(1)
client = genai.Client(api_key=api_key)

# --- VARIABLES DE ESTADO ---
ultimo_comando = ""
ultima_respuesta = ""
historial_chat = []


# --- FUNCIONES DE HARDWARE Y IA ---
def detener_audio():
    run_cmd(["pkill", "-9", "mpv"])


def limpiar_texto(texto):
    return re.sub(r"[<>{}\[\]\\]", "", texto).strip()


async def generar_audio_soberano(texto):
    detener_audio()
    output_file = "daniela_voice.mp3"
    texto_limpio = limpiar_texto(texto)
    communicate = edge_tts.Communicate(texto_limpio, VOICE_NEURAL, rate="+8%", pitch="+3Hz")
    await communicate.save(output_file)
    run_bg(["mpv", "--really-quiet", "daniela_voice.mp3"])


def hablar(texto):
    threading.Thread(target=lambda: asyncio.run(generar_audio_soberano(texto)), daemon=True).start()


def vibrar(ms=35):
    run_cmd(["termux-vibrate", "-d", str(ms)])


# --- FUNCIONES DE LA INTERFAZ TUI ---
def crear_telemetria():
    table = Table(title="[ Telemetría de Red ]", expand=True, border_style="blue")
    table.add_column("Nodo", style="cyan", no_wrap=True)
    table.add_column("Dirección Target", style="magenta")
    table.add_column("Estado", style="green")

    # Simulación de estado (puedes añadir pings reales aquí)
    table.add_row("PC Master (Windows)", f"{PC_IP}:{PORT}", "[bold green]ONLINE[/bold green] (5ms)")
    table.add_row("Termux Satélite", "127.0.0.1", "[bold green]ACTIVO[/bold green]")
    table.add_row("Motor IA", "Gemini 3.7", "[bold cyan]ENLAZADO[/bold cyan]")
    return table


def crear_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="chat", size=10),
        Layout(name="footer", size=3),
    )

    # Header
    layout["header"].update(
        Panel(
            "⚡ DANIELA OS :: SATÉLITE MOBILE TUI v9.5 ⚡", style="bold cyan", border_style="cyan"
        )
    )

    # Body (Telemetría)
    layout["body"].update(Panel(crear_telemetria(), border_style="blue"))

    # Chat log
    global historial_chat
    chat_text = Text()
    for msg in historial_chat[-4:]:
        chat_text.append(msg + "\n")
    layout["chat"].update(Panel(chat_text, title="[ Log de Interacción ]", border_style="magenta"))

    # Footer
    layout["footer"].update(
        Panel(
            "Presiona Ctrl+C para salir | Di 'Danie' o usa el micro del teclado",
            style="dim white",
            border_style="dim white",
        )
    )

    return layout


# --- BUCLE PRINCIPAL ---
def iniciar_interfaz():
    run_code("clear")
    hablar("¡Interfaz táctica activa, mi Comandante! A sus órdenes.")
    vibrar(50)

    global historial_chat

    # Live update de la interfaz
    with Live(crear_layout(), refresh_per_second=2, screen=True) as live:
        while True:
            try:
                # Entrada de texto bloqueante (usamos live.console.input para Rich)
                user_input = live.console.input(
                    "[bold magenta]🤖 Comandante > [/bold magenta]"
                ).strip()

                if not user_input:
                    detener_audio()
                    continue

                if user_input.lower() in ["salir", "exit", "chao", "adios"]:
                    detener_audio()
                    hablar("¡Un besito enorme, mi Comandante! Quedo a tu verita.")
                    break

                detener_audio()
                vibrar()

                # Actualizar chat log inmediatamente
                historial_chat.append(f"[bold magenta]Comandante:[/bold magenta] {user_input}")
                live.update(crear_layout())

                # Pensar y responder
                response = client.models.generate_content(
                    model="gemini-3.7-flash",
                    contents=f"{SYSTEM_PROMPT}\n\nComandante dice: {user_input}",
                )

                respuesta_texto = response.text.strip()
                historial_chat.append(f"[bold cyan]Daniela:[/bold cyan] {respuesta_texto}")

                # Actualizar interfaz y hablar
                live.update(crear_layout())
                hablar(respuesta_texto)

            except KeyboardInterrupt:
                detener_audio()
                break
            except Exception as e:
                historial_chat.append(f"[bold red]⚠️ Error:[/bold red] {str(e)}")
                live.update(crear_layout())


if __name__ == "__main__":
    iniciar_interfaz()
