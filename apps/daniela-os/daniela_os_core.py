#!/usr/bin/env python3
"""DanielaCore - nucleo logico de Daniela OS v2.0.

Cargado por daniela_os.py via importlib (get_core). Expone:
  - VERSION, registry.list_enabled() -> módulos reales del servidor
  - ask(query) -> dict con success/result via Gemini (misma clave que el server)
  - run_pipeline(steps) -> ejecuta pasos secuenciales via ask()
  - PipelineStep(**dict) para core_pipeline()
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any


class ModuleInfo:
    def __init__(self, name: str, description: str, intents: list) -> None:
        self.name = name
        self.description = description
        self.intents = intents


class Registry:
    def __init__(self, modules: list) -> None:
        self._modules = modules

    def list_enabled(self) -> list:
        return list(self._modules)


@dataclass
class PipelineStep:
    tipo: str = "ask"
    parametros: dict = field(default_factory=dict)

    def __init__(self, **kwargs: Any) -> None:
        self.tipo = str(kwargs.get("tipo", kwargs.get("type", "ask")))
        self.parametros = {
            k: v for k, v in kwargs.items() if k not in ("tipo", "type")
        }


_MODULES = [
    ("core", "Consulta directa al core", ["consulta", "pregunta"]),
    ("content", "Generacion de contenido para blog", ["blog", "contenido"]),
    ("swarm", "Coordinacion de enjambre de agentes", ["swarm", "coordinar"]),
    ("code", "Generacion de codigo", ["codigo", "programar"]),
    ("email", "Clasificacion de email", ["email", "clasificar"]),
    ("invoice", "Auditoria de facturas", ["factura", "auditar"]),
    ("sentiment", "Analisis de sentimiento", ["sentimiento", "analizar"]),
    ("social", "Posts para redes sociales", ["social", "post"]),
    ("support", "Soporte automatico", ["soporte", "ayuda"]),
    ("meeting", "Analisis de reuniones", ["reunion", "transcripcion"]),
    ("proactive", "Alertas proactivas de calendario", ["calendario", "alertas"]),
    ("pipeline", "Ejecucion de pipelines JSON", ["pipeline", "pasos"]),
]


class DanielaCore:
    VERSION = "2.0.0"

    def __init__(self) -> None:
        self.registry = Registry(
            [ModuleInfo(n, d, i) for n, d, i in _MODULES]
        )
        self._client = None

    def _gemini(self) -> Any:
        if self._client is None:
            key = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
            if not key:
                return None
            try:
                from google import genai

                self._client = genai.Client(api_key=key)
            except Exception:
                self._client = None
        return self._client

    def ask(self, query: str, **kwargs: Any) -> dict:
        client = self._gemini()
        if client is None:
            return {"status": "offline", "error": "Sin clave Gemini (GEMINI_API_KEY)"}
        try:
            from google.genai import types

            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=str(query),
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Eres el nucleo DanielaCore v2.0 de AIGestion. "
                        "Responde de forma util y concisa."
                    ),
                    temperature=0.65,
                ),
            )
            return {"success": True, "result": {"message": resp.text}}
        except Exception as e:
            return {"status": "error", "error": str(e)[:200]}

    def run_pipeline(self, steps: list) -> Any:
        t0 = time.time()
        outputs: list = []
        errors: list = []
        for s in steps:
            try:
                q = s.parametros.get("query", s.parametros.get("message", ""))
                r = self.ask(q or s.tipo)
                outputs.append(r)
                if not r.get("success"):
                    errors.append(r)
            except Exception as e:
                errors.append({"step": s.tipo, "error": str(e)[:200]})
        ms = int((time.time() - t0) * 1000)

        class _Res:
            pass

        res = _Res()
        res.success = not errors
        res.duration_ms = ms
        res.outputs = outputs
        res.errors = errors
        return res
