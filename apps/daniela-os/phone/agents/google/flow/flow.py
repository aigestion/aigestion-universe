"""Flow: Automatiza flujos con Gemini (gratis)."""

import json
import os
from typing import Any

import requests

from ..base import GoogleAgent


class FlowAgent(GoogleAgent):
    """Agente para Google Flow."""

    def __init__(self, config: dict | None = None):
        super().__init__("flow", config)
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")

    def create_flow(self, name: str, steps: list[dict]) -> dict[str, Any]:
        """Crea un flujo automatizado."""
        prompt = f"Crea un flujo llamado '{name}' con estos pasos: {json.dumps(steps)}"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def run(self) -> dict[str, Any]:
        """Ejecuta verificación de estado."""
        self.start()
        try:
            result = self.create_flow("test", [])
            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.save_metrics()
            return {"status": "ok", "test": result}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            return {"error": str(e)}
        finally:
            self.stop()
