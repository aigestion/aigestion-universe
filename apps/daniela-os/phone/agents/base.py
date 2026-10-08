"""Clase base para todos los agentes y subagentes."""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Agent(ABC):
    """Clase base para agentes autónomos."""

    def __init__(self, name: str, config: dict | None = None):
        self.name = name
        self.config = config or {}
        self.status = "idle"
        self.last_run = None
        self.subagents: list[Agent] = []
        self.metrics = {
            "runs": 0,
            "success": 0,
            "errors": 0,
            "last_output": None,
        }
        self.log_dir = Path(__file__).parent / "logs"
        self.log_dir.mkdir(exist_ok=True)

    def add_subagent(self, subagent: "Agent"):
        """Agrega un subagente."""
        self.subagents.append(subagent)
        self.log(f"Subagente agregado: {subagent.name}")

    def run_subagents(self) -> list[dict[str, Any]]:
        """Ejecuta todos los subagentes."""
        results = []
        for subagent in self.subagents:
            try:
                result = subagent.run()
                results.append({"name": subagent.name, "result": result})
            except Exception as e:
                results.append({"name": subagent.name, "error": str(e)})
        return results

    @abstractmethod
    def run(self) -> dict[str, Any]:
        """Ejecuta el agente."""

    def start(self):
        """Inicia el agente."""
        self.status = "running"
        self.last_run = datetime.now().isoformat()
        logger.info(f"[{self.name}] Iniciando...")

    def stop(self):
        """Detiene el agente."""
        self.status = "idle"
        logger.info(f"[{self.name}] Detenido")

    def log(self, message: str, level: str = "info"):
        """Registra un mensaje."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{self.name}] [{level.upper()}] {message}"
        print(log_entry)
        log_file = self.log_dir / f"{self.name}.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry + "\n")

    def save_metrics(self):
        """Guarda métricas del agente."""
        metrics_file = self.log_dir / f"{self.name}_metrics.json"
        with open(metrics_file, "w", encoding="utf-8") as f:
            json.dump(self.metrics, f, indent=2)

    def report_to_brain(self, resultado: dict[str, Any], prioridad: str = "normal"):
        """Reporta el resultado del agente al cerebro de Daniela.

        Jerarquía: sub-agente → agente → Daniela.
        Si este agente tiene sub-agentes, sus reportes ya llegaron aquí
        vía `run_subagents()`. Este método sube el resultado agregado.

        `resultado` debe incluir al menos:
          - `success` (bool)
          - `output` (dict o str, opcional)
          - `error` (str, opcional)
        """
        try:
            from .brain import get_brain

            brain = get_brain()
            brain.report(
                agente=self.name,
                resultado=resultado,
                prioridad=prioridad,
            )
            self.log(f"Reporte enviado a Daniela: {resultado.get('output', '')[:80]}")
        except Exception as e:
            self.log(f"No pude reportar a Daniela: {e}", level="warn")

    def health_check(self) -> dict[str, Any]:
        """Verifica el estado del agente."""
        return {
            "name": self.name,
            "status": self.status,
            "last_run": self.last_run,
            "metrics": self.metrics,
            "subagents": [s.name for s in self.subagents],
        }
