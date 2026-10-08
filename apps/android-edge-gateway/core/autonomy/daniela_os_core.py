#!/usr/bin/env python3
"""
aig Core - Orquestador Principal v1.0.0
================================================
Unifica los 10 Quick Wins en una plataforma cohesiva con:
- Registro modular de capacidades
- Enrutamiento inteligente de intents
- Pipeline de procesamiento estandarizado
- Configuracion centralizada
- CLI unificada

Autor: aig Team
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Protocol, runtime_checkable

# ═══════════════════════════════════════════════════════════════
# Modelos de Datos
# ═══════════════════════════════════════════════════════════════

@dataclass
class ModuleInfo:
    """Metadatos de un modulo registrado."""
    name: str
    description: str
    intents: list[str]
    handler: Callable[..., Any]
    dependencies: list[str] = field(default_factory=list)
    enabled: bool = True
    version: str = "1.0.0"


@dataclass
class PipelineStep:
    """Un paso en un pipeline de procesamiento."""
    module: str
    action: str
    params: dict[str, Any] = field(default_factory=dict)
    condition: str | None = None  # expresion simple para conditional execution


@dataclass
class PipelineResult:
    """Resultado de ejecutar un pipeline."""
    success: bool
    outputs: list[dict[str, Any]]
    errors: list[str]
    duration_ms: float
    trace: list[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════
# Protocolos
# ═══════════════════════════════════════════════════════════════

@runtime_checkable
class QuickWinModule(Protocol):
    """Protocolo que deben cumplir los modulos Quick Win."""

    def execute(self, intent: str, params: dict[str, Any]) -> dict[str, Any]:

        ...

    def health_check(self) -> dict[str, Any]:

        ...


# ═══════════════════════════════════════════════════════════════
# Registro de Modulos
# ═══════════════════════════════════════════════════════════════

class ModuleRegistry:
    """Registro central de modulos aig."""

    def __init__(self):
        self._modules: dict[str, ModuleInfo] = {}
        self._intent_map: dict[str, list[str]] = {}  # intent -> [module_names]

    def register(self, info: ModuleInfo) -> None:
        """Registra un nuevo modulo."""
        self._modules[info.name] = info
        for intent in info.intents:
            self._intent_map.setdefault(intent, []).append(info.name)
        print(f"  [REGISTRY] Modulo registrado: {info.name}")

    def get(self, name: str) -> ModuleInfo | None:

        return self._modules.get(name)

    def list_all(self) -> list[ModuleInfo]:

        return list(self._modules.values())

    def list_enabled(self) -> list[ModuleInfo]:

        return [m for m in self._modules.values() if m.enabled]

    def find_by_intent(self, intent: str) -> list[ModuleInfo]:

        names = self._intent_map.get(intent, [])
        return [self._modules[n] for n in names if n in self._modules and self._modules[n].enabled]

    def search_intents(self, query: str) -> list[tuple[str, ModuleInfo]]:
        """Busca intents que contengan la query."""
        results = []
        q = query.lower()
        for intent, names in self._intent_map.items():
            if q in intent.lower():
                for n in names:
                    mod = self._modules.get(n)
                    if mod and mod.enabled:
                        results.append((intent, mod))
        return results


# ═══════════════════════════════════════════════════════════════
# Enrutador de Intents
# ═══════════════════════════════════════════════════════════════

class IntentRouter:
    """Enruta peticiones al modulo adecuado basado en intent detection."""

    KEYWORD_MAP = {
        # Productividad
        "calendario": "proactive",
        "reunion": "meeting",
        "agenda": "proactive",
        "deadline": "proactive",
        "alerta": "proactive",
        # Email
        "email": "email",
        "inbox": "email",
        "correo": "email",
        "gmail": "email",
        # Facturas
        "factura": "invoice",
        "invoice": "invoice",
        "gasto": "invoice",
        "receipt": "invoice",
        # Sentimiento
        "sentimiento": "sentiment",
        "sentiment": "sentiment",
        "analisis": "sentiment",
        "emocion": "sentiment",
        # Redes Sociales
        "social": "social",
        "twitter": "social",
        "linkedin": "social",
        "instagram": "social",
        "post": "social",
        "redes": "social",
        # Soporte
        "soporte": "support",
        "support": "support",
        "ticket": "support",
        "faq": "support",
        "ayuda": "support",
        # Codigo
        "codigo": "code",
        "code": "code",
        "programar": "code",
        "script": "code",
        "funcion": "code",
        # Contenido
        "contenido": "content",
        "content": "content",
        "blog": "content",
        "newsletter": "content",
        "articulo": "content",
        "copy": "content",
        # Swarm / Multi-agente
        "swarm": "swarm",
        "agente": "swarm",
        "multi": "swarm",
        "coordinar": "swarm",
        "equipo": "swarm",
        # CAD / 3D (Open CADStudio)
        "cad": "cad",
        "stl": "cad",
        "disena": "cad",
        "diseña": "cad",
        "pieza": "cad",
        "imprimir": "cad",
        "impresion": "cad",
        "openscad": "cad",
        "freecad": "cad",
        "3d": "cad",
    }

    INTENT_TO_MODULE = {
        "proactive": "daniela_proactive",
        "email": "email_zero_inbox",
        "invoice": "smart_invoice",
        "meeting": "meeting_intel",
        "sentiment": "sentiment_dashboard",
        "social": "social_media",
        "support": "customer_support",
        "code": "code_gen",
        "content": "content_factory",
        "swarm": "swarm_intel",
        "cad": "cad_studio",
    }

    def __init__(self, registry: ModuleRegistry):
        self.registry = registry

    def detect(self, query: str) -> list[tuple[str, float]]:
        """
        Detecta intents en una query natural.
        Retorna lista de (intent, score) ordenada por score.
        """
        query_lower = query.lower()
        scores: dict[str, float] = {}

        for keyword, intent in self.KEYWORD_MAP.items():
            if keyword in query_lower:
                scores[intent] = scores.get(intent, 0) + 1.0

        # Normalizar
        if scores:
            max_score = max(scores.values())
            scores = {k: v / max_score for k, v in scores.items()}

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def route(self, query: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Enruta una query al modulo mas apropiado y ejecuta.
        Retorna resultado estructurado.
        """
        intents = self.detect(query)
        if not intents:
            return {
                "success": False,
                "error": "No se pudo detectar intent. Intenta ser mas especifico.",
                "suggestions": [
                    "Usa palabras como: email, factura, reunion, codigo, contenido, redes",
                ],
            }

        top_intent, score = intents[0]
        module_name = self.INTENT_TO_MODULE.get(top_intent)

        if not module_name:
            return {
                "success": False,
                "error": f"Intent '{top_intent}' no tiene modulo asignado.",
            }

        module_info = self.registry.get(module_name)
        if not module_info or not module_info.enabled:
            return {
                "success": False,
                "error": f"Modulo '{module_name}' no disponible o deshabilitado.",
            }

        # Ejecutar handler
        merged_params = {"query": query, "intent": top_intent, **(params or {})}
        try:
            result = module_info.handler(**merged_params)
            return {
                "success": True,
                "intent": top_intent,
                "confidence": score,
                "module": module_name,
                "result": result,
            }
        except Exception as e:
            return {
                "success": False,
                "intent": top_intent,
                "module": module_name,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }


# ═══════════════════════════════════════════════════════════════
# Pipeline Runner
# ═══════════════════════════════════════════════════════════════

class PipelineRunner:
    """Ejecuta pipelines secuenciales de modulos."""

    def __init__(self, registry: ModuleRegistry):
        self.registry = registry

    def run(self, steps: list[PipelineStep]) -> PipelineResult:

        import time

        start = time.perf_counter()
        outputs: list[dict[str, Any]] = []
        errors: list[str] = []
        trace: list[str] = []

        context: dict[str, Any] = {}  # shared context entre pasos

        for i, step in enumerate(steps):
            trace.append(f"Step {i+1}: {step.module}.{step.action}")

            # Evaluar condicion
            if step.condition and not self._eval_condition(step.condition, context):
                trace.append("  -> Condicion falsa, saltando")
                continue

            mod_info = self.registry.get(step.module)
            if not mod_info:
                err = f"Modulo '{step.module}' no encontrado"
                errors.append(err)
                trace.append(f"  -> ERROR: {err}")
                continue

            try:
                params = {**step.params, "_context": context, "_step": i}
                result = mod_info.handler(action=step.action, **params)
                outputs.append({"step": i, "module": step.module, "result": result})
                context[f"step_{i}_output"] = result
                trace.append("  -> OK")
            except Exception as e:
                err = f"[{step.module}] {e}"
                errors.append(err)
                trace.append(f"  -> ERROR: {err}")

        duration = (time.perf_counter() - start) * 1000
        return PipelineResult(
            success=len(errors) == 0,
            outputs=outputs,
            errors=errors,
            duration_ms=duration,
            trace=trace,
        )

    def _eval_condition(self, condition: str, context: dict[str, Any]) -> bool:
        """Evalua una condicion simple contra el contexto."""
        # Ejemplo: "step_0_output.status == 'success'"
        try:
            parts = condition.split("==")
            if len(parts) == 2:
                key = parts[0].strip().replace("step_", "")
                expected = parts[1].strip().strip("'\"")
                val = context.get(f"step_{key}")
                return str(val) == expected
            return True
        except Exception:
            return True


# ═══════════════════════════════════════════════════════════════
# aig Core
# ═══════════════════════════════════════════════════════════════

# Raiz del repo: este modulo vive en mobile-app/core/autonomy/, asi que la
# raiz queda 3 niveles arriba (parents[3]); parents[2] es mobile-app/ y
# dejaba el config colgado fuera del repo.
_REPO_ROOT = Path(__file__).resolve().parents[3]


class DanielaCore:
    """
    Orquestador principal de aig.
    Punto de entrada unificado para todos los modulos Quick Win.
    """

    VERSION = "1.0.0"
    CONFIG_PATH = _REPO_ROOT / "config.json"

    def __init__(self):
        self.registry = ModuleRegistry()
        self.router = IntentRouter(self.registry)
        self.pipeline = PipelineRunner(self.registry)
        self.config: dict[str, Any] = {}
        self._load_config()
        self._bootstrap_modules()

    # ── Configuracion ───────────────────────────────────────────

    def _load_config(self) -> None:
        if self.CONFIG_PATH.exists():
            self.config = json.loads(self.CONFIG_PATH.read_text(encoding="utf-8"))
        else:
            self.config = self._default_config()
            self._save_config()

    def _save_config(self) -> None:
        self.CONFIG_PATH.write_text(json.dumps(self.config, indent=2, ensure_ascii=False))

    def _default_config(self) -> dict[str, Any]:
        return {
            "version": self.VERSION,
            "modules": {
                "daniela_proactive": {"enabled": True, "priority": 1},
                "email_zero_inbox": {"enabled": True, "priority": 2},
                "smart_invoice": {"enabled": True, "priority": 3},
                "meeting_intel": {"enabled": True, "priority": 4},
                "sentiment_dashboard": {"enabled": True, "priority": 5},
                "social_media": {"enabled": True, "priority": 6},
                "customer_support": {"enabled": True, "priority": 7},
                "code_gen": {"enabled": True, "priority": 8},
                "content_factory": {"enabled": True, "priority": 9},
                "swarm_intel": {"enabled": True, "priority": 10},
                "cad_studio": {"enabled": True, "priority": 11},
            },
            "features": {
                "auto_route": True,
                "pipeline_fallback": True,
                "health_checks": True,
            },
        }

    # ── Bootstrap ───────────────────────────────────────────────

    def _bootstrap_modules(self) -> None:
        """Registra todos los modulos Quick Win disponibles via adapters."""
        print("[CORE] Inicializando modulos aig...")

        # Intentar cargar adapters reales
        adapters = self._load_adapters()

        module_definitions = [
            {
                "name": "daniela_proactive",
                "description": "Motor proactivo: anticipa necesidades desde calendario y tareas",
                "intents": ["proactive", "calendario", "agenda", "deadline", "alerta"],
                "dependencies": [],
            },
            {
                "name": "email_zero_inbox",
                "description": "Clasificacion inteligente de emails con respuestas automaticas",
                "intents": ["email", "inbox", "correo", "gmail"],
                "dependencies": [],
            },
            {
                "name": "smart_invoice",
                "description": "Auditoria de facturas con OCR, duplicados y deteccion de fraude",
                "intents": ["invoice", "factura", "gasto", "receipt"],
                "dependencies": [],
            },
            {
                "name": "meeting_intel",
                "description": "Inteligencia de reuniones: transcripcion, action items, decisiones",
                "intents": ["meeting", "reunion", "transcripcion"],
                "dependencies": [],
            },
            {
                "name": "sentiment_dashboard",
                "description": "Analisis de sentimiento en espanol con priorizacion",
                "intents": ["sentiment", "sentimiento", "analisis", "emocion"],
                "dependencies": [],
            },
            {
                "name": "social_media",
                "description": "Centro de comando para redes sociales multi-plataforma",
                "intents": ["social", "twitter", "linkedin", "instagram", "post", "redes"],
                "dependencies": [],
            },
            {
                "name": "customer_support",
                "description": "Automatizacion de soporte con FAQ matching y escalamiento",
                "intents": ["support", "soporte", "ticket", "faq", "ayuda"],
                "dependencies": [],
            },
            {
                "name": "code_gen",
                "description": "Generacion de codigo desde lenguaje natural",
                "intents": ["code", "codigo", "programar", "script", "funcion"],
                "dependencies": [],
            },
            {
                "name": "content_factory",
                "description": "Fabrica de contenido multi-plataforma (blog, newsletter, ads)",
                "intents": ["content", "contenido", "blog", "newsletter", "articulo", "copy"],
                "dependencies": [],
            },
            {
                "name": "swarm_intel",
                "description": "Coordinador multi-agente para tareas complejas",
                "intents": ["swarm", "agente", "multi", "coordinar", "equipo"],
                "dependencies": [],
            },
            {
                "name": "cad_studio",
                "description": "Diseno CAD parametrico Text-to-OpenSCAD + BOM",
                "intents": ["cad", "stl", "pieza", "imprimir", "openscad"],
                "dependencies": [],
            },
        ]

        for defn in module_definitions:
            enabled = self.config.get("modules", {}).get(defn["name"], {}).get("enabled", True)
            adapter = adapters.get(defn["name"])
            handler = adapter.handler if adapter else self._stub_handler(defn["name"])
            info = ModuleInfo(
                name=defn["name"],
                description=defn["description"],
                intents=defn["intents"],
                handler=handler,
                dependencies=defn["dependencies"],
                enabled=enabled,
            )
            self.registry.register(info)

        print(f"[CORE] {len(self.registry.list_enabled())} modulos activos.")

    def _load_adapters(self) -> dict[str, Any]:
        """Carga adapters desde adapters.py si existe."""
        adapters = {}
        adapters_path = Path(__file__).parent / "adapters.py"
        if not adapters_path.exists():
            return adapters
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("adapters", adapters_path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules["adapters"] = mod
                spec.loader.exec_module(mod)
                if hasattr(mod, "ADAPTER_MAP"):
                    for name, cls in mod.ADAPTER_MAP.items():
                        adapters[name] = cls()
                    print(f"  [ADAPTERS] {len(adapters)} adapters cargados.")
        except Exception as e:
            print(f"  [ADAPTERS] Error cargando adapters: {e}")
        return adapters

    def _stub_handler(self, module_name: str) -> Callable[..., Any]:
        """Crea un handler stub cuando no hay adapter disponible."""
        def handler(**kwargs: Any) -> dict[str, Any]:

            return {
                "status": "stub",
                "message": f"Modulo {module_name} en modo stub. Adapter no disponible.",
                "module": module_name,
            }
        return handler

    # ── API Publica ─────────────────────────────────────────────

    def ask(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """
        Punto de entrada principal. Procesa una consulta natural
        y la enruta al modulo adecuado.
        """
        return self.router.route(query, kwargs)

    def run_pipeline(self, steps: list[PipelineStep]) -> PipelineResult:
        """Ejecuta un pipeline de modulos secuencial."""
        return self.pipeline.run(steps)

    def health(self) -> dict[str, Any]:
        """Health check de todos los modulos."""
        results = {}
        for mod in self.registry.list_enabled():
            try:
                result = mod.handler(action="health_check")
                results[mod.name] = {"status": "ok", "result": result}
            except Exception as e:
                results[mod.name] = {"status": "error", "error": str(e)}

        return {
            "core_version": self.VERSION,
            "timestamp": datetime.now().isoformat(),
            "modules_total": len(self.registry.list_all()),
            "modules_enabled": len(self.registry.list_enabled()),
            "modules": results,
        }

    def status(self) -> dict[str, Any]:
        """Estado general del sistema."""
        return {
            "version": self.VERSION,
            "modules": [
                {
                    "name": m.name,
                    "enabled": m.enabled,
                    "description": m.description,
                    "intents": m.intents[:3],
                }
                for m in self.registry.list_all()
            ],
            "config_path": str(self.CONFIG_PATH),
        }


# ═══════════════════════════════════════════════════════════════
# CLI Unificada
# ═══════════════════════════════════════════════════════════════

def create_core() -> DanielaCore:
    return DanielaCore()


def main() -> int:
    parser = argparse.ArgumentParser(description="aig Core - Orquestador Principal")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # ask
    ask_parser = subparsers.add_parser("ask", help="Consulta natural al sistema")
    ask_parser.add_argument("query", help="Tu consulta")
    ask_parser.add_argument("--module", help="Forzar modulo especifico")

    # pipeline
    pipe_parser = subparsers.add_parser("pipeline", help="Ejecutar pipeline JSON")
    pipe_parser.add_argument("--file", "-f", help="Archivo JSON con pasos")
    pipe_parser.add_argument("--steps", "-s", help="JSON inline de pasos")

    # health
    subparsers.add_parser("health", help="Health check de modulos")

    # status
    subparsers.add_parser("status", help="Estado del sistema")

    # module
    mod_parser = subparsers.add_parser("module", help="Operaciones de modulo")
    mod_parser.add_argument("action", choices=["list", "enable", "disable"])
    mod_parser.add_argument("name", nargs="?", help="Nombre del modulo")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    core = create_core()

    if args.command == "ask":
        result = core.ask(args.query)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "pipeline":
        steps_data: list[dict[str, Any]] = []
        if args.file:
            steps_data = json.loads(Path(args.file).read_text(encoding="utf-8"))
        elif args.steps:
            steps_data = json.loads(args.steps)
        else:
            print("Error: Especifica --file o --steps")
            return 1

        steps = [PipelineStep(**s) for s in steps_data]
        result = core.run_pipeline(steps)
        print(json.dumps({
            "success": result.success,
            "duration_ms": result.duration_ms,
            "outputs": result.outputs,
            "errors": result.errors,
            "trace": result.trace,
        }, indent=2, ensure_ascii=False))

    elif args.command == "health":
        result = core.health()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "status":
        result = core.status()
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "module":
        if args.action == "list":
            for m in core.registry.list_all():
                status = "ON" if m.enabled else "OFF"
                print(f"[{status}] {m.name:20} - {m.description}")
        elif args.action in ("enable", "disable") and args.name:
            if args.name in [m.name for m in core.registry.list_all()]:
                core.config.setdefault("modules", {}).setdefault(args.name, {})["enabled"] = (args.action == "enable")
                core._save_config()
                print(f"Modulo '{args.name}' {args.action}d.")
            else:
                print(f"Modulo '{args.name}' no encontrado.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
