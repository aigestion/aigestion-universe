"""AI Studio: Controla Gemini API (1500 req/día gratis)."""

import os
from typing import Any

import requests

from ..base import GoogleAgent


class AIStudioAgent(GoogleAgent):
    """Agente para Google AI Studio (Gemini API)."""

    def __init__(self, config: dict | None = None):
        super().__init__("ai_studio", config)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")

    def generate_content(self, prompt: str, model: str = "gemini-2.0-flash") -> dict[str, Any]:
        """Genera contenido con Gemini."""
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048,
            },
        }
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def chat(self, messages: list[dict], model: str = "gemini-2.0-flash") -> dict[str, Any]:
        """Chat con Gemini."""
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        payload = {
            "contents": messages,
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 2048,
            },
        }
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def list_models(self) -> dict[str, Any]:
        """Lista modelos disponibles."""
        url = f"{self.base_url}/models?key={self.api_key}"
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def run(self) -> dict[str, Any]:
        """Ejecuta verificación de estado."""
        self.start()
        try:
            models = self.list_models()
            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.save_metrics()
            return {"models": models}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            return {"error": str(e)}
        finally:
            self.stop()
