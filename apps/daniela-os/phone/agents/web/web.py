"""Web: Monitorea y controla la presencia web."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from ..base import Agent


class WebAgent(Agent):
    """Agente que monitorea y controla la web."""

    def __init__(self, config: dict | None = None):
        super().__init__("web", config)
        self.sites_file = Path(__file__).parent / "sites.json"
        self.sites = self._load_sites()

    def _load_sites(self) -> dict:
        if self.sites_file.exists():
            return json.loads(self.sites_file.read_text())
        return {"sites": [], "last_check": None}

    def _save_sites(self):
        self.sites_file.write_text(json.dumps(self.sites, indent=2))

    def check_site(self, url: str) -> dict[str, Any]:
        """Verifica si un sitio está activo."""
        try:
            resp = requests.get(url, timeout=10)
            return {
                "url": url,
                "status": "up" if resp.status_code == 200 else "down",
                "status_code": resp.status_code,
                "response_time": resp.elapsed.total_seconds(),
                "checked": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "url": url,
                "status": "error",
                "error": str(e),
                "checked": datetime.now().isoformat(),
            }

    def scrape_page(self, url: str) -> dict[str, Any]:
        """Extrae información de una página."""
        try:
            from bs4 import BeautifulSoup

            resp = requests.get(url, timeout=30)
            soup = BeautifulSoup(resp.text, "html.parser")
            return {
                "url": url,
                "title": soup.title.string if soup.title else "",
                "links": [a.get("href") for a in soup.find_all("a", href=True)][:20],
                "scraped": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"url": url, "error": str(e)}

    def run(self) -> dict[str, Any]:
        """Ejecuta el ciclo de monitoreo."""
        self.start()
        try:
            sites = self.config.get("sites", [])
            results = []
            for site in sites:
                result = self.check_site(site)
                results.append(result)

            self.sites["sites"] = results
            self.sites["last_check"] = datetime.now().isoformat()
            self._save_sites()

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(results)} sitios verificados"
            self.save_metrics()
            self.log(f"Sitios verificados: {len(results)}")
            return {"sites": results}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            self.log(f"Error: {e}", "error")
            return {"error": str(e)}
        finally:
            self.stop()
