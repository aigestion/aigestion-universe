"""EpicAgents: Ejército de agentes con subagentes dinámicos."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ...base import Agent


class InitiativeAgentsAgent(Agent):
    """Agente que gestiona el ejército de agentes."""

    def __init__(self, config: dict | None = None):
        super().__init__("initiative_agents", config)
        self.army_file = Path(__file__).parent / "army.json"
        self.army = self._load_army()

    def _load_army(self) -> dict:
        if self.army_file.exists():
            return json.loads(self.army_file.read_text())
        return {"agents": [], "subagents": [], "missions": []}

    def _save_army(self):
        self.army_file.write_text(json.dumps(self.army, indent=2))

    def create_agent(self, name: str, role: str, capabilities: list[str]) -> dict[str, Any]:
        """Crea un agente nuevo."""
        agent = {
            "name": name,
            "role": role,
            "capabilities": capabilities,
            "status": "active",
            "created": datetime.now().isoformat(),
        }
        self.army["agents"].append(agent)
        self._save_army()
        return agent

    def create_subagent(self, parent: str, task: str) -> dict[str, Any]:
        """Crea un subagente dinámico."""
        subagent = {
            "parent": parent,
            "task": task,
            "status": "active",
            "created": datetime.now().isoformat(),
        }
        self.army["subagents"].append(subagent)
        self._save_army()
        return subagent

    def assign_mission(self, agent_name: str, mission: str, reward: int = 100) -> dict[str, Any]:
        """Asigna una misión a un agente."""
        mission_obj = {
            "agent": agent_name,
            "mission": mission,
            "reward": reward,
            "status": "active",
            "created": datetime.now().isoformat(),
        }
        self.army["missions"].append(mission_obj)
        self._save_army()
        return mission_obj

    def get_army_status(self) -> dict[str, Any]:
        """Obtiene el estado del ejército."""
        return {
            "total_agents": len(self.army["agents"]),
            "total_subagents": len(self.army["subagents"]),
            "active_missions": len([m for m in self.army["missions"] if m["status"] == "active"]),
        }

    def run(self) -> dict[str, Any]:
        """Ejecuta un ciclo del ejército."""
        self.start()
        try:
            # Crear agentes pendientes
            pending = self.config.get("pending_agents", [])
            created = []
            for agent in pending:
                created.append(
                    self.create_agent(
                        agent["name"],
                        agent["role"],
                        agent.get("capabilities", []),
                    )
                )

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(created)} agentes creados"
            self.save_metrics()
            return {"created": created, "status": self.get_army_status()}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            return {"error": str(e)}
        finally:
            self.stop()
