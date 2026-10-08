"""Evolución Automática de Código.

Propone refactors y mejoras automáticamente.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Agent


class CodeEvolutionAgent(Agent):
    """Agente de evolución de código."""

    def __init__(self, config: dict | None = None):
        super().__init__("code_evolution", config)
        self.evolutions_file = Path(__file__).parent / "evolutions.json"
        self.evolutions = self._load_evolutions()

    def _load_evolutions(self) -> dict:
        if self.evolutions_file.exists():
            return json.loads(self.evolutions_file.read_text())
        return {"evolutions": [], "last_evolution": None}

    def _save_evolutions(self):
        self.evolutions_file.write_text(json.dumps(self.evolutions, indent=2))

    def analyze_code(self) -> dict[str, Any]:
        """Analiza el código para mejoras."""
        try:
            result = subprocess.run(
                ["ruff", "check", ".", "--statistics"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            return {"issues": result.stdout, "timestamp": datetime.now().isoformat()}
        except Exception as e:
            return {"error": str(e)}

    def propose_evolution(self, analysis: dict) -> dict[str, Any]:
        """Propone una evolución del código."""
        evolution = {
            "analysis": analysis,
            "proposal": "Refactor propuesto basado en análisis",
            "priority": "medium",
            "timestamp": datetime.now().isoformat(),
        }
        self.evolutions["evolutions"].append(evolution)
        self.evolutions["last_evolution"] = datetime.now().isoformat()
        self._save_evolutions()
        return evolution

    def run(self) -> dict[str, Any]:
        """Ejecuta un ciclo de evolución."""
        self.start()
        try:
            analysis = self.analyze_code()
            evolution = self.propose_evolution(analysis)

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = "1 evolución propuesta"
            self.save_metrics()
            return {"evolution": evolution}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            return {"error": str(e)}
        finally:
            self.stop()
