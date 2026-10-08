"""Gemini: Controla modelos Gemini (gratis)."""

import os
from typing import Any

import requests

from ..base import GoogleAgent


class GeminiAgent(GoogleAgent):
    """Agente para modelos Gemini."""

    def __init__(self, config: dict | None = None):
        super().__init__("gemini", config)
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def generate(self, prompt: str, model: str = "gemini-2.0-flash") -> dict[str, Any]:
        """Genera contenido."""
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def embed(self, text: str) -> dict[str, Any]:
        """Genera embeddings."""
        url = f"{self.base_url}/models/text-embedding-004:embedContent?key={self.api_key}"
        payload = {"model": "models/text-embedding-004", "content": {"parts": [{"text": text}]}}
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
            result = self.generate("test")
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
