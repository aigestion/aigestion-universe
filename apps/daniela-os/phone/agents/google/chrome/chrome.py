"""Chrome: Controla Chrome con DevTools Protocol (gratis)."""

from typing import Any

import requests

from ..base import GoogleAgent


class ChromeAgent(GoogleAgent):
    """Agente para Chrome DevTools Protocol."""

    def __init__(self, config: dict | None = None):
        super().__init__("chrome", config)
        self.debug_port = config.get("debug_port", 9222) if config else 9222

    def list_tabs(self) -> dict[str, Any]:
        """Lista pestañas abiertas."""
        try:
            resp = requests.get(f"http://localhost:{self.debug_port}/json", timeout=5)
            resp.raise_for_status()
            return {"tabs": resp.json()}
        except Exception as e:
            return {"error": str(e)}

    def new_tab(self, url: str) -> dict[str, Any]:
        """Abre una nueva pestaña."""
        try:
            resp = requests.get(f"http://localhost:{self.debug_port}/json/new?{url}", timeout=5)
            resp.raise_for_status()
            return {"tab": resp.json()}
        except Exception as e:
            return {"error": str(e)}

    def run(self) -> dict[str, Any]:
        """Ejecuta verificación de estado."""
        self.start()
        try:
            tabs = self.list_tabs()
            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.save_metrics()
            return {"tabs": tabs}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            return {"error": str(e)}
        finally:
            self.stop()
