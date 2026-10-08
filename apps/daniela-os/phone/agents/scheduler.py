"""Scheduler: Ejecuta agentes 24/7 con intervalos configurables."""

import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Agent
from .builder.builder import BuilderAgent
from .caller.caller import CallerAgent
from .guardian.guardian import GuardianAgent
from .researcher.researcher import ResearcherAgent
from .scout.scout import ScoutAgent
from .social.social import SocialAgent
from .studio.studio import StudioAgent
from .web.web import WebAgent


class Scheduler:
    """Programador de agentes 24/7."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.agents: dict[str, Agent] = {}
        self.running = False
        self.threads: list[threading.Thread] = []
        self.log_file = Path(__file__).parent / "scheduler.log"

    def register_agent(self, name: str, agent: Agent, interval: int):
        """Registra un agente con su intervalo de ejecución."""
        self.agents[name] = {"agent": agent, "interval": interval}
        self.log(f"Agente registrado: {name} (cada {interval}s)")

    def _run_agent_loop(self, name: str, agent: Agent, interval: int):
        """Ejecuta un agente en un loop infinito."""
        while self.running:
            try:
                self.log(f"Ejecutando {name}...")
                result = agent.run()
                self.log(f"{name} completado: {result}")
            except Exception as e:
                self.log(f"Error en {name}: {e}")
            time.sleep(interval)

    def start(self):
        """Inicia todos los agentes."""
        self.running = True
        self.log("Scheduler iniciado - Ejercito 24/7 activo")

        for name, config in self.agents.items():
            thread = threading.Thread(
                target=self._run_agent_loop,
                args=(name, config["agent"], config["interval"]),
                daemon=True,
            )
            thread.start()
            self.threads.append(thread)

    def stop(self):
        """Detiene todos los agentes."""
        self.running = False
        for _name, config in self.agents.items():
            config["agent"].stop()
        self.log("Scheduler detenido")

    def log(self, message: str):
        """Registra un mensaje."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    def get_status(self) -> dict[str, Any]:
        """Obtiene el estado de todos los agentes."""
        return {
            "running": self.running,
            "agents": {
                name: config["agent"].health_check() for name, config in self.agents.items()
            },
        }


def create_default_scheduler() -> Scheduler:
    """Crea un scheduler con la configuración por defecto."""
    scheduler = Scheduler()

    # Registrar agentes con intervalos (en segundos)
    scheduler.register_agent("scout", ScoutAgent(), interval=3600)  # 1h
    scheduler.register_agent("studio", StudioAgent(), interval=7200)  # 2h
    scheduler.register_agent("social", SocialAgent(), interval=10800)  # 3h
    scheduler.register_agent("web", WebAgent(), interval=1800)  # 30min
    scheduler.register_agent("caller", CallerAgent(), interval=14400)  # 4h
    scheduler.register_agent("researcher", ResearcherAgent(), interval=21600)  # 6h
    scheduler.register_agent("guardian", GuardianAgent(), interval=21600)  # 6h
    scheduler.register_agent("builder", BuilderAgent(), interval=86400)  # 24h

    return scheduler


if __name__ == "__main__":
    scheduler = create_default_scheduler()
    try:
        scheduler.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
