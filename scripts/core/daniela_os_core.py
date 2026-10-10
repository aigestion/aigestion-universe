# daniela_os_core.py
"""aig core module.
Provides a minimal framework for modules, a registry, and pipeline execution.
This implementation is deliberately lightweight – it can be expanded later
with real AI models, external services, or persistent storage.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module infrastructure
# ---------------------------------------------------------------------------
class Module:
    """Base class for a pluggable module.

    Sub‑classes should implement ``handler`` which receives an ``action`` name and
    arbitrary ``**params``. ``handler`` must return a JSON‑serialisable result.
    """

    def __init__(self, name: str, description: str = "", intents: list[str] | None = None, enabled: bool = True):
        self.name = name
        self.description = description
        self.intents = intents or []
        self.enabled = enabled

    def handler(self, action: str = "default", **params: Any) -> Any:
        """Default handler – simply echoes its input.
        Real modules should subclass :class:`Module` and override this method.
        """
        logger.debug("Module %s invoked with action %s, params %s", self.name, action, params)
        return {
            "module": self.name,
            "action": action,
            "params": params,
            "message": f"Executed {action} on module {self.name}",
        }

class Registry:
    """Container for all loaded modules.

    The registry is deliberately simple – a dict keyed by module name.
    It offers helper methods used by the API gateway.
    """

    def __init__(self):
        self._modules: dict[str, Module] = {}
        self._load_builtin_modules()

    def _load_builtin_modules(self) -> None:
        """Register a few example modules.
        In a real system these could be discovered via ``importlib`` or a plugin
        directory. For now we ship three trivial modules that illustrate the
        contract expected by the gateway.
        """
        for name in ["audit", "content_factory", "notify"]:
            self.register(Module(name=name, description=f"Demo {name} module"))

    def register(self, module: Module) -> None:
        self._modules[module.name] = module
        logger.info("Registered module %s", module.name)

    def get(self, name: str) -> Module | None:
        return self._modules.get(name)

    def list_all(self) -> list[Module]:
        return list(self._modules.values())

    def list_enabled(self) -> list[Module]:
        return [m for m in self._modules.values() if m.enabled]

# ---------------------------------------------------------------------------
# Pipeline handling
# ---------------------------------------------------------------------------
@dataclass
class PipelineStep:
    """Data holder for a pipeline step.

    Fields match the JSON structure expected by ``/v1/pipeline`` and
    ``/v1/epic-run``.
    """

    module: str
    action: str = "run"
    params: dict[str, Any] | None = None
    condition: Any = None  # Not used in this minimal implementation

    def __post_init__(self):
        if self.params is None:
            self.params = {}

class PipelineResult:
    """Result object returned by ``run_pipeline``.

    The gateway serialises this object directly via ``jsonify``.
    """

    def __init__(self, success: bool, duration_ms: int, outputs: list[Any], errors: list[str], trace: list[str]):
        self.success = success
        self.duration_ms = duration_ms
        self.outputs = outputs
        self.errors = errors
        self.trace = trace

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "duration_ms": self.duration_ms,
            "outputs": self.outputs,
            "errors": self.errors,
            "trace": self.trace,
        }

    def __repr__(self) -> str:
        return json.dumps(self.to_dict())

# ---------------------------------------------------------------------------
# Errores
# ---------------------------------------------------------------------------
class SinProveedorError(RuntimeError):
    """Ningun proveedor de IA respondio a la consulta.

    Se lanza a proposito en lugar de devolver texto simulado. Hasta el
    2026-09-18 ``ask()`` devolvia ``"Respuesta simulada a la consulta: '...'"``:
    un ``dict`` con la forma correcta, asi que ninguna capa superior (rutas,
    chat, gateway) detectaba que detras no habia ninguna IA. Un error visible
    es preferible a una respuesta falsa con aspecto de valida.
    """

    def __init__(self, mensaje: str, intentos: list[dict[str, Any]] | None = None):
        super().__init__(mensaje)
        # Traza de lo que se intento, para diagnosticar sin adivinar.
        self.intentos: list[dict[str, Any]] = intentos or []


# ---------------------------------------------------------------------------
# Core class – singleton used by the gateway
# ---------------------------------------------------------------------------
class DanielaCore:
    """Main entry point for the platform.

    Provides:
    * ``ask`` – consulta real a un modelo, via el enrutador del repo.
    * ``run_pipeline`` – sequential execution of registered modules.
    * ``registry`` – module catalogue.
    """

    VERSION = "0.2.0"

    def __init__(self):
        self.registry = Registry()
        # Enrutador de modelos compartido. Se carga en perezoso: importar
        # `model_router` al vuelo evita una dependencia circular y no paga el
        # coste si nadie pregunta.
        self._router: Any = None
        logger.info("DanielaCore initialised – version %s", self.VERSION)

    # ---------------------------------------------------------------- cerebro
    def _enrutador(self) -> Any:
        """Devuelve el enrutador de modelos unico del repo (singleton).

        Reutiliza ``model_router.EnrutadorModelos`` en vez de mantener aqui una
        segunda lista de proveedores: el repo ya tiene una cadena con
        reintentos, sonda de salud e historial (E-32), y duplicarla es
        exactamente como se acaba teniendo cinco copias del mismo fichero.
        """
        if self._router is None:
            from model_router import get_instance
            self._router = get_instance()
        return self._router

    def ask(self, query: str, **context: Any) -> dict[str, Any]:
        """Pregunta de verdad a un modelo, a traves del enrutador del repo.

        Mantiene la forma de retorno historica (``query`` / ``answer`` /
        ``context``) y anade la traza del proveedor que respondio.

        Lanza :class:`SinProveedorError` si ningun proveedor responde. No
        devuelve nunca texto simulado.
        """
        logger.debug("Core received ask: %s with context %s", query, context)

        if not (query or "").strip():
            raise ValueError("consulta vacia")

        max_tokens = int(context.get("max_tokens", 512) or 512)
        resultado = self._enrutador().responder(str(query), max_tokens=max_tokens)

        if not resultado.get("ok"):
            raise SinProveedorError(
                "ningun proveedor de IA respondio: "
                + str(resultado.get("error", "motivo desconocido")),
                intentos=resultado.get("intentos"),
            )

        return {
            "query": query,
            "answer": resultado.get("texto", ""),
            "context": context,
            # Traza: quien respondio, con que modelo y cuanto tardo.
            "proveedor": resultado.get("proveedor"),
            "modelo": resultado.get("modelo"),
            "latencia_ms": resultado.get("latencia_ms"),
            "intentos": resultado.get("intentos", []),
        }

    def run_pipeline(self, steps: list[PipelineStep]) -> PipelineResult:
        start = time.time()
        outputs: list[Any] = []
        errors: list[str] = []
        trace: list[str] = []

        for idx, step in enumerate(steps, start=1):
            trace.append(f"Step {idx}: module={step.module}, action={step.action}")
            mod = self.registry.get(step.module)
            if not mod:
                err = f"Modulo '{step.module}' no encontrado"
                errors.append(err)
                logger.warning(err)
                continue
            try:
                result = mod.handler(action=step.action, **(step.params or {}))
                outputs.append({"step": idx, "module": step.module, "result": result})
            except Exception as exc:  # pragma: no cover – defensive
                err = f"Error en modulo {step.module}: {exc}"
                errors.append(err)
                logger.exception(err)

        duration_ms = int((time.time() - start) * 1000)
        success = len(errors) == 0
        return PipelineResult(success=success, duration_ms=duration_ms, outputs=outputs, errors=errors, trace=trace)

# Export symbols expected by the gateway
__all__ = ["DanielaCore", "PipelineStep", "PipelineResult", "SinProveedorError"]

