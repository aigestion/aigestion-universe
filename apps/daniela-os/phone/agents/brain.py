"""Cerebro Central Unificado de Daniela.

Todos los agentes consultan y aportan a este cerebro compartido.
Jerarquía de reporte: sub-agentes → agentes → Daniela (brain).
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class DanielaBrain:
    """Cerebro central con memoria compartida."""

    def __init__(self, brain_dir: str | None = None):
        self.brain_dir = Path(brain_dir or Path(__file__).parent / "brain")
        self.brain_dir.mkdir(exist_ok=True)
        self.memory_file = self.brain_dir / "memory.json"
        self.knowledge_file = self.brain_dir / "knowledge.json"
        self.decisions_file = self.brain_dir / "decisions.json"
        self.reports_file = self.brain_dir / "reports.json"
        self.memory = self._load(self.memory_file, {"facts": [], "patterns": []})
        self.knowledge = self._load(self.knowledge_file, {"insights": [], "learnings": []})
        self.decisions = self._load(self.decisions_file, {"decisions": [], "outcomes": []})
        self.reports = self._load(self.reports_file, {"reports": [], "pendientes": []})

    def _load(self, path: Path, default: dict) -> dict:
        if path.exists():
            return json.loads(path.read_text())
        return default

    def _save(self, path: Path, data: dict):
        path.write_text(json.dumps(data, indent=2))

    def remember(self, fact: str, source: str = "unknown"):
        """Añade un hecho a la memoria."""
        self.memory["facts"].append(
            {
                "fact": fact,
                "source": source,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._save(self.memory_file, self.memory)

    def learn(self, insight: str, pattern: str = ""):
        """Añade un insight al conocimiento."""
        self.knowledge["insights"].append(
            {
                "insight": insight,
                "pattern": pattern,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._save(self.knowledge_file, self.knowledge)

    def decide(self, decision: str, context: str, options: list[str]):
        """Registra una decisión."""
        self.decisions["decisions"].append(
            {
                "decision": decision,
                "context": context,
                "options": options,
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._save(self.decisions_file, self.decisions)

    def recall(self, query: str) -> list[dict]:
        """Recuerda hechos relacionados."""
        return [f for f in self.memory["facts"] if query.lower() in f["fact"].lower()]

    def report(
        self,
        agente: str,
        resultado: dict[str, Any],
        padre: str | None = None,
        prioridad: str = "normal",
    ) -> dict[str, Any]:
        """Registra un reporte jerárquico: sub-agente → agente → Daniela.

        Si `padre` se da, el reporte viene de un sub-agente y se agrupa
        bajo el agente padre. Daniela lo ve en `pendientes` hasta que el
        usuario decide (junto a Daniela) cómo actuar.

        Devuelve el registro creado (con `id` y `ts`).
        """
        ts = datetime.now().isoformat()
        reporte = {
            "id": f"{agente}-{int(datetime.now().timestamp())}",
            "agente": agente,
            "padre": padre,
            "prioridad": prioridad,
            "resultado": resultado,
            "estado": "pendiente",
            "ts": ts,
        }
        self.reports["reports"].append(reporte)
        if prioridad in ("alta", "critica"):
            self.reports["pendientes"].append(reporte["id"])
        self._save(self.reports_file, self.reports)

        if resultado.get("error"):
            self.remember(
                f"[{agente}] ERROR: {resultado['error'][:200]}",
                source=f"report:{agente}",
            )
        elif resultado.get("success"):
            self.learn(
                f"[{agente}] completó: {str(resultado.get('output', ''))[:200]}",
                pattern="reporte",
            )
        return reporte

    def marcar_decidido(self, reporte_id: str, decision: str):
        """Marca un reporte como decidido (Daniela + usuario acuerdan)."""
        for r in self.reports["reports"]:
            if r["id"] == reporte_id:
                r["estado"] = "decidido"
                r["decision"] = decision
                r["ts_decision"] = datetime.now().isoformat()
                break
        self.reports["pendientes"] = [x for x in self.reports["pendientes"] if x != reporte_id]
        self._save(self.reports_file, self.reports)

    def reportes_pendientes(self, prioridad: str | None = None) -> list[dict]:
        """Lista de reportes aún sin decisión de Daniela + usuario."""
        ids = set(self.reports["pendientes"])
        out = [r for r in self.reports["reports"] if r["id"] in ids]
        if prioridad:
            out = [r for r in out if r.get("prioridad") == prioridad]
        return out

    def get_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas del cerebro."""
        return {
            "facts": len(self.memory["facts"]),
            "insights": len(self.knowledge["insights"]),
            "decisions": len(self.decisions["decisions"]),
            "reportes": len(self.reports["reports"]),
            "pendientes": len(self.reports["pendientes"]),
            "last_update": datetime.now().isoformat(),
        }


# Instancia global del cerebro
_brain: DanielaBrain | None = None


def get_brain() -> DanielaBrain:
    """Obtiene la instancia global del cerebro."""
    global _brain
    if _brain is None:
        _brain = DanielaBrain()
    return _brain
