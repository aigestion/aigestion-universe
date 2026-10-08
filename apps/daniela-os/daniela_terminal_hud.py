import time

import requests
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from safe_exec import run_code

console = Console()
PC_IP = "192.168.1.170"
PORT = "5000"


def crear_interface():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3), Layout(name="body"), Layout(name="footer", size=3)
    )

    # Header
    layout["header"].update(
        Panel("⚡ DANIELA OS :: SATÉLITE MOBILE TUI v9.5 ⚡", style="bold cyan")
    )

    # Probar conexión con la PC Master
    try:
        start_time = time.time()
        requests.get(f"http://{PC_IP}:{PORT}/", timeout=2)
        latency = round((time.time() - start_time) * 1000, 2)
        estado_pc = f"[bold green]ONLINE[/bold green] ({latency} ms)"
    except Exception:
        estado_pc = "[bold red]OFFLINE (Esperando Host)[/bold red]"

    # Cuerpo / Métricas
    table = Table(title="Estado de los Nodos Soberanos", expand=True)
    table.add_column("Nodo", style="cyan", no_wrap=True)
    table.add_column("Dirección Target", style="magenta")
    table.add_column("Estado de Sincronización", style="green")

    table.add_row("PC Master (Windows 11)", f"{PC_IP}:{PORT}", estado_pc)
    table.add_row(
        "Termux Satélite (Android)", "127.0.0.1 (Local)", "[bold green]ACTIVO[/bold green]"
    )
    table.add_row("Motor IA", "Gemini 3.7 Flash", "[bold cyan]ENLAZADO[/bold cyan]")

    layout["body"].update(Panel(table, border_style="blue", title="[ Telemetría de Red ]"))

    # Footer
    layout["footer"].update(
        Panel(
            "Presiona Ctrl+C para salir | Di 'Danie' o envía comandos por la API Flask",
            style="dim white",
        )
    )

    return layout


def iniciar_dashboard():
    run_code("clear")
    with Live(crear_interface(), refresh_per_second=2) as live:
        try:
            while True:
                time.sleep(1)
                live.update(crear_interface())
        except KeyboardInterrupt:
            console.print("\n[bold yellow]👋 Cerrando consola TUI de Daniela OS...[/bold yellow]")


if __name__ == "__main__":
    iniciar_dashboard()
