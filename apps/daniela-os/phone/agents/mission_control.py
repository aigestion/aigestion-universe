"""Sistema de Misiones.

Los agentes tienen misiones con objetivos y recompensas.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Agent


class MissionControl(Agent):
    """Sistema de misiones para agentes."""

    def __init__(self, config: dict | None = None):
        super().__init__("mission_control", config)
        self.missions_file = Path(__file__).parent / "missions.json"
        self.missions = self._load_missions()

    def _load_missions(self) -> dict:
        if self.missions_file.exists():
            return json.loads(self.missions_file.read_text())
        return {"missions": [], "completed": 0, "active": 0}

    def _save_missions(self):
        self.missions_file.write_text(json.dumps(self.missions, indent=2))

    def create_mission(self, name: str, objective: str, reward: int = 100) -> dict[str, Any]:
        """Crea una misión."""
        mission = {
            "name": name,
            "objective": objective,
            "reward": reward,
            "status": "active",
            "created": datetime.now().isoformat(),
        }
        self.missions["missions"].append(mission)
        self.missions["active"] += 1
        self._save_missions()
        return mission

    def complete_mission(self, name: str) -> dict[str, Any]:
        """Completa una misión."""
        for mission in self.missions["missions"]:
            if mission["name"] == name and mission["status"] == "active":
                mission["status"] = "completed"
                mission["completed"] = datetime.now().isoformat()
                self.missions["completed"] += 1
                self.missions["active"] -= 1
                self._save_missions()
                return mission
        return {"error": "Misión no encontrada"}

    def get_active_missions(self) -> list[dict]:
        """Obtiene misiones activas."""
        return [m for m in self.missions["missions"] if m["status"] == "active"]

    def run(self) -> dict[str, Any]:
        """Ejecuta un ciclo de misiones."""
        self.start()
        try:
            # Crear misiones pendientes
            pending = self.config.get("pending_missions", [])
            created = []
            for mission in pending:
                created.append(
                    self.create_mission(
                        mission["name"],
                        mission["objective"],
                        mission.get("reward", 100),
                    )
                )

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(created)} misiones creadas"
            self.save_metrics()
            return {"created": created, "active": self.get_active_missions()}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            return {"error": str(e)}
        finally:
            self.stop()
