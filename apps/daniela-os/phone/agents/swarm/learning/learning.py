"""Learning: Agente que aprende de cada interacción."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ...base import Agent


class LearningAgent(Agent):
    """Agente que aprende de cada interacción."""

    def __init__(self, config: dict | None = None):
        super().__init__("learning", config)
        self.knowledge_file = Path(__file__).parent / "knowledge.json"
        self.knowledge = self._load_knowledge()

    def _load_knowledge(self) -> dict:
        if self.knowledge_file.exists():
            return json.loads(self.knowledge_file.read_text())
        return {"patterns": [], "insights": [], "last_learning": None}

    def _save_knowledge(self):
        self.knowledge_file.write_text(json.dumps(self.knowledge, indent=2))

    def learn_from_interaction(self, interaction: dict) -> dict[str, Any]:
        """Aprende de una interacción."""
        insight = {
            "interaction": interaction,
            "pattern": interaction.get("pattern", ""),
            "outcome": interaction.get("outcome", ""),
            "learned": datetime.now().isoformat(),
        }
        self.knowledge["insights"].append(insight)
        self.knowledge["last_learning"] = datetime.now().isoformat()
        self._save_knowledge()
        return insight

    def run(self) -> dict[str, Any]:
        """Ejecuta un ciclo de aprendizaje."""
        self.start()
        try:
            interactions = self.config.get("interactions", [])
            insights = []
            for interaction in interactions:
                insight = self.learn_from_interaction(interaction)
                insights.append(insight)

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(insights)} insights"
            self.save_metrics()
            self.log(f"Insights generados: {len(insights)}")
            return {"insights": insights}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            self.log(f"Error: {e}", "error")
            return {"error": str(e)}
        finally:
            self.stop()
