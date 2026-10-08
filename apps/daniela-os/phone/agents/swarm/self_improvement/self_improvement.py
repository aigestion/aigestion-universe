"""SelfImprovement: Agente que mejora el código y procesos."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from ...base import Agent


class SelfImprovementAgent(Agent):
    """Agente que mejora el código y procesos."""

    def __init__(self, config: dict | None = None):
        super().__init__("self_improvement", config)
        self.improvements_file = Path(__file__).parent / "improvements.json"
        self.improvements = self._load_improvements()

    def _load_improvements(self) -> dict:
        if self.improvements_file.exists():
            return json.loads(self.improvements_file.read_text())
        return {"improvements": [], "last_improvement": None}

    def _save_improvements(self):
        self.improvements_file.write_text(json.dumps(self.improvements, indent=2))

    def analyze_code(self) -> dict[str, Any]:
        """Analiza el código para mejoras."""
        try:
            result = subprocess.run(
                ["ruff", "check", ".", "--statistics"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            return {
                "issues": result.stdout,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e)}

    def suggest_improvement(self, analysis: dict) -> dict[str, Any]:
        """Sugiere una mejora."""
        improvement = {
            "analysis": analysis,
            "suggestion": "Mejora sugerida basada en análisis",
            "priority": "medium",
            "timestamp": datetime.now().isoformat(),
        }
        self.improvements["improvements"].append(improvement)
        self.improvements["last_improvement"] = datetime.now().isoformat()
        self._save_improvements()
        return improvement

    def run(self) -> dict[str, Any]:
        """Ejecuta un ciclo de automejora."""
        self.start()
        try:
            analysis = self.analyze_code()
            improvement = self.suggest_improvement(analysis)

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = "1 mejora sugerida"
            self.save_metrics()
            self.log("Mejora sugerida")
            return {"improvement": improvement}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            self.log(f"Error: {e}", "error")
            return {"error": str(e)}
        finally:
            self.stop()
