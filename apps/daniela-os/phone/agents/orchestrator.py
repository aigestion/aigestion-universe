"""Orquestador Central de Daniela.

Coordina todos los agentes, subagentes y swarm para ejecución 24/7.
"""

import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Agent
from .builder.builder import BuilderAgent
from .caller.caller import CallerAgent
from .dream.dream import DreamAgent
from .google.ai_studio.ai_studio import AIStudioAgent
from .google.chrome.chrome import ChromeAgent
from .google.colab.colab import ColabAgent
from .google.firebase.firebase import FirebaseAgent
from .google.flow.flow import FlowAgent
from .google.gcloud_agent import GCloudAgent
from .google.gemini.gemini import GeminiAgent
from .google.labs.labs import LabsAgent
from .google.stitch.stitch import StitchAgent
from .guardian.guardian import GuardianAgent
from .researcher.researcher import ResearcherAgent
from .sandbox.sandbox import SandboxAgent
from .scout.scout import ScoutAgent
from .social.social import SocialAgent
from .studio.studio import StudioAgent
from .swarm.autonomy.autonomy import AutonomyAgent
from .swarm.correction.correction import CorrectionAgent
from .swarm.learning.learning import LearningAgent
from .swarm.self_improvement.self_improvement import SelfImprovementAgent
from .web.web import WebAgent

# Frecuencia de cada agente, en segundos. La fuente de verdad es
# `Orchestrator._register_agents()`: si añades un agente ahi, añádelo tambien
# aqui, o `tests/agents/test_orchestrator.py::test_intervalos_cubren_todos_los_agentes`
# falla diciendo exactamente cual se ha quedado sin intervalo.
INTERVALOS: dict[str, int] = {
    "scout": 3600,  # 1h
    "studio": 7200,  # 2h
    "social": 10800,  # 3h
    "web": 1800,  # 30min
    "caller": 14400,  # 4h
    "researcher": 21600,  # 6h
    "guardian": 21600,  # 6h
    "builder": 86400,  # 24h
    "dream": 43200,  # 12h
    "sandbox": 3600,  # 1h
    "ai_studio": 3600,  # 1h
    "firebase": 3600,  # 1h
    "colab": 7200,  # 2h
    "gemini": 1800,  # 30min
    "chrome": 300,  # 5min
    "stitch": 7200,  # 2h
    "flow": 7200,  # 2h
    "labs": 3600,  # 1h
    "gcloud": 3600,  # 1h
    "autonomy": 3600,  # 1h
    "learning": 7200,  # 2h
    "correction": 1800,  # 30min
    "self_improvement": 3600,  # 1h
}


class Orchestrator:
    """Orquestador central de Daniela."""

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.agents: dict[str, Agent] = {}
        self.running = False
        self.threads: list[threading.Thread] = []
        self.log_file = Path(__file__).parent / "orchestrator.log"
        self.results_file = Path(__file__).parent / "orchestrator_results.json"
        self._register_agents()

    def _register_agents(self):
        """Registra todos los agentes."""
        # Agentes principales
        self.agents["scout"] = ScoutAgent()
        self.agents["studio"] = StudioAgent()
        self.agents["social"] = SocialAgent()
        self.agents["web"] = WebAgent()
        self.agents["caller"] = CallerAgent()
        self.agents["researcher"] = ResearcherAgent()
        self.agents["guardian"] = GuardianAgent()
        self.agents["builder"] = BuilderAgent()
        self.agents["dream"] = DreamAgent()
        self.agents["sandbox"] = SandboxAgent()

        # Agentes de Google
        self.agents["ai_studio"] = AIStudioAgent()
        self.agents["firebase"] = FirebaseAgent()
        self.agents["colab"] = ColabAgent()
        self.agents["gemini"] = GeminiAgent()
        self.agents["chrome"] = ChromeAgent()
        self.agents["stitch"] = StitchAgent()
        self.agents["flow"] = FlowAgent()
        self.agents["labs"] = LabsAgent()
        self.agents["gcloud"] = GCloudAgent()

        # Swarm: Autonomía, aprendizaje, corrección, automejora
        self.agents["autonomy"] = AutonomyAgent()
        self.agents["learning"] = LearningAgent()
        self.agents["correction"] = CorrectionAgent()
        self.agents["self_improvement"] = SelfImprovementAgent()

    def _run_agent_loop(self, name: str, agent: Agent, interval: int):
        """Ejecuta un agente en un loop infinito."""
        while self.running:
            try:
                self.log(f"Ejecutando {name}...")
                result = agent.run()
                self.log(f"{name} completado: {result}")
                self._save_result(name, result)
            except Exception as e:
                self.log(f"Error en {name}: {e}")
            time.sleep(interval)

    def start(self):
        """Inicia todos los agentes."""
        self.running = True
        self.log("Orquestador iniciado - Ejercito Daniela 24/7 activo")

        # Intervalos por agente (en segundos). Vive FUERA de `start()` para que
        # los tests puedan comprobar que cubre a TODOS los agentes registrados:
        # antes vivia aqui dentro y un agente nuevo caia en el `3600` por
        # defecto sin que nadie se enterase (ver tests/agents/test_orchestrator).
        for name, agent in self.agents.items():
            interval = INTERVALOS.get(name, 3600)
            thread = threading.Thread(
                target=self._run_agent_loop,
                args=(name, agent, interval),
                daemon=True,
            )
            thread.start()
            self.threads.append(thread)

    def stop(self):
        """Detiene todos los agentes."""
        self.running = False
        for _name, agent in self.agents.items():
            agent.stop()
        self.log("Orquestador detenido")

    def log(self, message: str):
        """Registra un mensaje."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    def _save_result(self, name: str, result: dict):
        """Guarda el resultado de un agente."""
        results = {}
        if self.results_file.exists():
            results = json.loads(self.results_file.read_text())
        results[name] = {
            "timestamp": datetime.now().isoformat(),
            "result": result,
        }
        self.results_file.write_text(json.dumps(results, indent=2))

    def get_status(self) -> dict[str, Any]:
        """Obtiene el estado de todos los agentes."""
        return {
            "running": self.running,
            "total_agents": len(self.agents),
            "agents": {name: agent.health_check() for name, agent in self.agents.items()},
        }

    def run_once(self) -> dict[str, Any]:
        """Ejecuta todos los agentes una vez."""
        self.log("Ejecutando todos los agentes una vez...")
        results = {}
        for name, agent in self.agents.items():
            try:
                result = agent.run()
                results[name] = result
                self.log(f"{name}: OK")
            except Exception as e:
                results[name] = {"error": str(e)}
                self.log(f"{name}: ERROR - {e}")
        self._save_result("orchestration", results)
        return results


def create_orchestrator() -> Orchestrator:
    """Crea el orquestador con todos los agentes."""
    return Orchestrator()


if __name__ == "__main__":
    orch = create_orchestrator()
    try:
        orch.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        orch.stop()
