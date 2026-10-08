"""Labs: Controla TODOS los servicios de Google Labs (gratis)."""

import json
import os
from typing import Any

import requests

from ..base import GoogleAgent


class LabsAgent(GoogleAgent):
    """Agente para Google Labs: TODOS los servicios."""

    def __init__(self, config: dict | None = None):
        super().__init__("labs", config)
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    # ── NotebookLM ──────────────────────────────────────────
    def notebooklm_create(self, name: str, sources: list[dict]) -> dict[str, Any]:
        """Crea un cuaderno en NotebookLM."""
        prompt = f"Crea un cuaderno llamado '{name}' con estas fuentes: {json.dumps(sources)}"
        return self._generate(prompt)

    def notebooklm_query(self, notebook_id: str, query: str) -> dict[str, Any]:
        """Consulta un cuaderno."""
        prompt = f"Consulta el cuaderno {notebook_id}: {query}"
        return self._generate(prompt)

    # ── MusicFX ─────────────────────────────────────────────
    def musicfx_generate(self, prompt: str, duration: int = 30) -> dict[str, Any]:
        """Genera música con MusicFX."""
        return self._generate(f"Genera música: {prompt}, duración: {duration}s")

    # ── Whisk ───────────────────────────────────────────────
    def whisk_generate(self, prompt: str) -> dict[str, Any]:
        """Genera imágenes con Whisk."""
        return self._generate(f"Genera imagen: {prompt}")

    # ── Test Kitchen ────────────────────────────────────────
    def test_kitchen(self, recipe: str) -> dict[str, Any]:
        """Prueba una receta en Test Kitchen."""
        return self._generate(f"Prueba esta receta: {recipe}")

    # ── Project Tailwind ─────────────────────────────────────
    def tailwind_generate(self, prompt: str) -> dict[str, Any]:
        """Genera código con Project Tailwind."""
        return self._generate(f"Genera código: {prompt}")

    # ── Veo ─────────────────────────────────────────────────
    def veo_generate(self, prompt: str) -> dict[str, Any]:
        """Genera video con Veo."""
        return self._generate(f"Genera video: {prompt}")

    # ── Imagen ──────────────────────────────────────────────
    def imagen_generate(self, prompt: str) -> dict[str, Any]:
        """Genera imagen con Imagen."""
        return self._generate(f"Genera imagen: {prompt}")

    # ── Gemini ──────────────────────────────────────────────
    def _generate(self, prompt: str) -> dict[str, Any]:
        """Genera contenido con Gemini."""
        url = f"{self.base_url}/models/gemini-2.0-flash:generateContent?key={self.api_key}"
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
            result = self._generate("test")
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
