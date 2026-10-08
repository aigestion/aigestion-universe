"""EpicBrain: Memoria persistente, aprendizaje por refuerzo, emociones."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ...base import Agent


class InitiativeBrainAgent(Agent):
    """Agente de cerebro épico con memoria y emociones."""

    def __init__(self, config: dict | None = None):
        super().__init__("initiative_brain", config)
        self.brain_dir = Path(__file__).parent / "data"
        self.brain_dir.mkdir(exist_ok=True)
        self.memory_file = self.brain_dir / "memory.json"
        self.emotions_file = self.brain_dir / "emotions.json"
        self.memory = self._load(self.memory_file, {"facts": [], "patterns": [], "decisions": []})
        self.emotions = self._load(self.emotions_file, {"current": "neutral", "history": []})

    def _load(self, path: Path, default: dict) -> dict:
        if path.exists():
            return json.loads(path.read_text())
        return default

    def _save(self, path: Path, data: dict):
        path.write_text(json.dumps(data, indent=2))

    def remember(self, fact: str, importance: float = 0.5):
        """Recuerda un hecho con importancia."""
        self.memory["facts"].append(
            {
                "fact": fact,
                "importance": importance,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._save(self.memory_file, self.memory)

    def learn_pattern(self, pattern: str, outcome: str):
        """Aprende un patrón y su resultado."""
        self.memory["patterns"].append(
            {
                "pattern": pattern,
                "outcome": outcome,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._save(self.memory_file, self.memory)

    def decide(self, context: str, options: list[str]) -> dict[str, Any]:
        """Toma una decisión basada en patrones aprendidos."""
        # Buscar patrones similares
        similar = [p for p in self.memory["patterns"] if context.lower() in p["pattern"].lower()]
        chosen = similar[0]["outcome"] if similar else options[0]

        decision = {
            "context": context,
            "options": options,
            "chosen": chosen,
            "confidence": len(similar) / max(len(self.memory["patterns"]), 1),
            "timestamp": datetime.now().isoformat(),
        }
        self.memory["decisions"].append(decision)
        self._save(self.memory_file, self.memory)
        return decision

    def set_emotion(self, emotion: str, intensity: float = 0.5):
        """Establece el estado emocional."""
        self.emotions["current"] = emotion
        self.emotions["history"].append(
            {
                "emotion": emotion,
                "intensity": intensity,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._save(self.emotions_file, self.emotions)

    def predict_need(self, context: str) -> dict[str, Any]:
        """Predice necesidades basándose en patrones."""
        predictions = []
        for pattern in self.memory["patterns"]:
            if context.lower() in pattern["pattern"].lower():
                predictions.append(
                    {
                        "need": pattern["outcome"],
                        "confidence": 0.7,
                    }
                )
        return {"predictions": predictions, "context": context}

    def run(self) -> dict[str, Any]:
        """Ejecuta un ciclo de cerebro."""
        self.start()
        try:
            # Aprender de la interacción
            interactions = self.config.get("interactions", [])
            for interaction in interactions:
                self.learn_pattern(interaction["pattern"], interaction["outcome"])

            # Tomar decisiones
            decisions = self.config.get("decisions", [])
            results = []
            for d in decisions:
                result = self.decide(d["context"], d["options"])
                results.append(result)

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(results)} decisiones"
            self.save_metrics()
            return {"decisions": results, "emotion": self.emotions["current"]}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            return {"error": str(e)}
        finally:
            self.stop()
