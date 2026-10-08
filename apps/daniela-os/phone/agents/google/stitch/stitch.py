"""Stitch: Genera imágenes con Gemini (gratis)."""

import os
from typing import Any

import requests

from ..base import GoogleAgent


class StitchAgent(GoogleAgent):
    """Agente para Google Stitch (generación de imágenes)."""

    def __init__(self, config: dict | None = None):
        super().__init__("stitch", config)
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")

    def generate_image(self, prompt: str) -> dict[str, Any]:
        """Genera una imagen con Gemini."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent?key={self.api_key}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        }
        try:
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def run(self) -> dict[str, Any]:
        """Ejecuta verificación de estado."""
        self.start()
        try:
            result = self.generate_image("test")
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
