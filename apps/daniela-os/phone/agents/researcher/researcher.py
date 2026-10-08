"""Researcher: Investiga temas a fondo y genera reportes."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..base import Agent


class ResearcherAgent(Agent):
    """Agente que investiga temas profundamente."""

    def __init__(self, config: dict | None = None):
        super().__init__("researcher", config)
        self.reports_dir = Path(__file__).parent / "reports"
        self.reports_dir.mkdir(exist_ok=True)

    def search_web(self, query: str) -> list[dict]:
        """Busca en la web."""
        try:
            from duckduckgo_search import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=10))
                return [
                    {"title": r["title"], "link": r["href"], "snippet": r["body"]} for r in results
                ]
        except Exception as e:
            self.log(f"Error buscando: {e}", "error")
            return []

    def research_topic(self, topic: str) -> dict[str, Any]:
        """Investiga un tema y genera un reporte."""
        self.log(f"Investigando: {topic}")
        sources = self.search_web(topic)

        report = {
            "topic": topic,
            "sources": sources,
            "summary": f"Reporte sobre {topic} con {len(sources)} fuentes",
            "created": datetime.now().isoformat(),
        }

        # Guardar reporte
        report_file = self.reports_dir / f"{topic.replace(' ', '_')}.json"
        report_file.write_text(json.dumps(report, indent=2))

        return report

    def run(self) -> dict[str, Any]:
        """Ejecuta el ciclo de investigación."""
        self.start()
        try:
            topics = self.config.get("topics", [])
            reports = []
            for topic in topics:
                report = self.research_topic(topic)
                reports.append(report)

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(reports)} reportes"
            self.save_metrics()
            self.log(f"Reportes generados: {len(reports)}")
            return {"reports": reports}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            self.log(f"Error: {e}", "error")
            return {"error": str(e)}
        finally:
            self.stop()
