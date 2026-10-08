"""Autonomy: Agente que opera 24/7 sin intervención humana."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ...base import Agent


class AutonomyAgent(Agent):
    """Agente que opera autónomamente 24/7."""

    def __init__(self, config: dict | None = None):
        super().__init__("autonomy", config)
        self.decisions_file = Path(__file__).parent / "decisions.json"
        self.decisions = self._load_decisions()

    def _load_decisions(self) -> dict:
        if self.decisions_file.exists():
            return json.loads(self.decisions_file.read_text())
        return {"decisions": [], "last_decision": None}

    def _save_decisions(self):
        self.decisions_file.write_text(json.dumps(self.decisions, indent=2))

    def make_decision(self, context: str, options: list[str]) -> dict[str, Any]:
        """Toma una decisión autónoma."""
        decision = {
            "context": context,
            "options": options,
            "chosen": options[0] if options else None,
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat(),
        }
        self.decisions["decisions"].append(decision)
        self.decisions["last_decision"] = datetime.now().isoformat()
        self._save_decisions()
        return decision

    def run(self) -> dict[str, Any]:
        """Ejecuta un ciclo de autonomía."""
        self.start()
        try:
            # Tomar decisiones pendientes
            pending = self.config.get("pending_decisions", [])
            decisions = []
            for item in pending:
                decision = self.make_decision(item["context"], item["options"])
                decisions.append(decision)

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(decisions)} decisiones"
            self.save_metrics()
            self.log(f"Decisiones tomadas: {len(decisions)}")
            return {"decisions": decisions}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            self.log(f"Error: {e}", "error")
            return {"error": str(e)}
        finally:
            self.stop()
