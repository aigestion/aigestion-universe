#!/usr/bin/env python3
"""
aig Module Adapters - Conectores Quick Win
=================================================
Adapta cada modulo Quick Win al protocolo unificado de DanielaCore.

Cada adapter:
- Importa el modulo real
- Expone un handler uniforme: handler(action, **params)
- Traduce entre el API nativo del modulo y el estandar del core
- Maneja errores gracefulmente

Autor: aig Team
"""

from __future__ import annotations

import importlib.util
import json
import sys
import traceback
from pathlib import Path
from typing import Any

# Directorio de este modulo (core/ desde Fase 2) y raiz del repo.
MODULES_DIR = Path(__file__).parent
_REPO_ROOT = MODULES_DIR.parent.parent

# Directorios donde viven los modulos, en orden de prioridad (Fase 2:
# los dominios empaquetados conviven con shims en raiz durante 1-2 sprints).
MODULE_SEARCH_PATHS = [
    _REPO_ROOT,
    _REPO_ROOT / "aig" / "agents",
    _REPO_ROOT / "aig" / "content",
]


def load_module(name: str):
    """Carga un modulo Python desde archivo sin necesidad de __init__.py."""
    file_path = next(
        (base / f"{name}.py" for base in MODULE_SEARCH_PATHS if (base / f"{name}.py").exists()),
        None,
    )
    if file_path is None:
        return None
    spec = importlib.util.spec_from_file_location(name, file_path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return None
    return mod


# ═══════════════════════════════════════════════════════════════
# Adapter Base
# ═══════════════════════════════════════════════════════════════

class ModuleAdapter:
    """Clase base para adapters de modulos."""

    module_name: str = ""
    actions: dict[str, str] = {}  # action_name -> descripcion

    def __init__(self):
        self._mod = None
        self._loaded = False

    def _ensure_loaded(self) -> bool:
        if self._loaded:
            return self._mod is not None
        self._mod = load_module(self.module_name)
        self._loaded = True
        return self._mod is not None

    def handler(self, action: str = "default", **params: Any) -> dict[str, Any]:

        if not self._ensure_loaded():
            return {
                "status": "error",
                "error": f"No se pudo cargar {self.module_name}.py",
            }
        method = getattr(self, f"do_{action}", self.do_default)
        try:
            return method(**params)
        except Exception as e:
            return {
                "status": "error",
                "action": action,
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

    def do_default(self, **params: Any) -> dict[str, Any]:

        return {
            "status": "ok",
            "message": f"Modulo {self.module_name} cargado. Acciones: {list(self.actions.keys())}",
        }

    def do_health_check(self, **params: Any) -> dict[str, Any]:

        ok = self._ensure_loaded()
        return {
            "status": "healthy" if ok else "unhealthy",
            "module": self.module_name,
            "loaded": ok,
        }


# ═══════════════════════════════════════════════════════════════
# Adapters Especificos
# ═══════════════════════════════════════════════════════════════

class ProactiveAdapter(ModuleAdapter):
    module_name = "daniela_proactive_engine_v2"
    actions = {
        "analyze_calendar": "Analiza eventos del calendario y genera alertas",
        "daily_briefing": "Genera briefing diario",
        "detect_patterns": "Detecta patrones en datos historicos",
    }

    def do_analyze_calendar(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        if hasattr(mod, "ProactiveEngine"):
            engine = mod.ProactiveEngine()
            if hasattr(engine, "analyze_upcoming_events"):
                events = params.get("events", [])
                result = engine.analyze_upcoming_events(events)
                return {"status": "ok", "alerts": result}
        return {"status": "stub", "message": "Proactive engine disponible pero no inicializado con datos"}

    def do_daily_briefing(self, **params: Any) -> dict[str, Any]:

        return {"status": "ok", "briefing": "Daniela Proactive esta lista para analizar tu calendario."}


class EmailAdapter(ModuleAdapter):
    module_name = "email_zero_inbox"
    actions = {
        "classify": "Clasifica un email",
        "auto_reply": "Genera respuesta automatica",
        "batch_process": "Procesa lote de emails",
    }

    def do_default(self, **params: Any) -> dict[str, Any]:
        # El chat llega sin accion: la query se clasifica como si fuera
        # el cuerpo de un email pegado (sender "chat", queda registrado).
        query = params.get("query", "")
        if query:
            from datetime import datetime

            return self.do_classify(email={
                "id": f"chat-{int(datetime.now().timestamp())}",
                "subject": query[:80], "sender": "chat",
                "body": query, "date": datetime.now().isoformat(),
            })
        return super().do_default(**params)

    def do_classify(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        email = params.get("email")
        if email and hasattr(mod, "classify_email"):
            result = mod.classify_email(email)
            return {"status": "ok", "classification": result}
        return {"status": "stub", "message": "Proporciona un email para clasificar"}

    def do_auto_reply(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        email = params.get("email")
        tone = params.get("tone", "formal")
        if email and hasattr(mod, "generate_reply"):
            reply = mod.generate_reply(email, tone)
            return {"status": "ok", "reply": reply}
        return {"status": "stub", "message": "Proporciona un email para generar respuesta"}


class InvoiceAdapter(ModuleAdapter):
    module_name = "smart_invoice_auditor"
    actions = {
        "audit": "Audita una factura",
        "check_duplicates": "Verifica duplicados",
        "detect_fraud": "Detecta anomalias y fraude",
    }

    def do_default(self, **params: Any) -> dict[str, Any]:
        # El chat llega sin accion: si trae dict factura, audita de verdad.
        invoice = params.get("invoice")
        if isinstance(invoice, dict):
            return self.do_audit(invoice=invoice)
        return super().do_default(**params)

    def do_audit(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        if hasattr(mod, "SmartInvoiceAuditor"):
            auditor = mod.SmartInvoiceAuditor()
            invoice_data = params.get("invoice")
            if invoice_data:
                result = auditor.audit(invoice_data)
                return {"status": "ok", "audit": result}
        return {"status": "stub", "message": "Proporciona datos de factura para auditar"}


class MeetingAdapter(ModuleAdapter):
    module_name = "meeting_intelligence"
    actions = {
        "analyze": "Analiza transcripcion de reunion",
        "extract_actions": "Extrae action items",
        "summarize": "Genera resumen ejecutivo",
    }

    def do_default(self, **params: Any) -> dict[str, Any]:
        # El chat llega sin accion: transcripcion pegada o dict se analiza.
        transcript = params.get("transcript", "") or params.get("query", "")
        if transcript:
            return self.do_analyze(transcript=transcript)
        return super().do_default(**params)

    def do_analyze(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        transcript = params.get("transcript", "")
        if transcript and hasattr(mod, "MeetingIntelligence"):
            try:
                intel = mod.MeetingIntelligence()
                return {
                    "status": "ok",
                    "participants": intel.extraer_participantes(transcript),
                    "actions": intel.extraer_action_items(transcript),
                    "decisions": intel.extraer_decisiones(transcript),
                    "summary": intel.generar_resumen(transcript, params.get("titulo", "Reunion")),
                }
            except Exception as e:
                return {"status": "error", "error": str(e)[:300]}
        return {"status": "stub", "message": "Proporciona una transcripcion para analizar"}

    def do_expediente(self, **params: Any) -> dict[str, Any]:

        transcript = params.get("transcript", "") or params.get("query", "")
        if not transcript:
            return {"status": "stub", "message": "Proporciona una transcripcion"}
        try:
            from agents.agent_expediente import procesar

            return {"status": "ok", "expediente": procesar(
                transcript, titulo=params.get("titulo", "Reunion"))}
        except Exception as e:
            return {"status": "error", "error": str(e)[:300]}


class SentimentAdapter(ModuleAdapter):
    module_name = "sentiment_dashboard"
    actions = {
        "analyze": "Analiza sentimiento de texto",
        "batch": "Analiza lote de textos",
        "dashboard": "Genera resumen de dashboard",
    }

    def do_analyze(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        text = params.get("text", "")
        if text and hasattr(mod, "SentimentAnalyzer"):
            analyzer = mod.SentimentAnalyzer()
            result = analyzer.analyze(text)
            return {"status": "ok", "analysis": result}
        return {"status": "stub", "message": "Proporciona un texto para analizar"}


class SocialAdapter(ModuleAdapter):
    module_name = "social_media_command_center"
    actions = {
        "generate_post": "Genera post para red social",
        "schedule": "Programa publicacion",
        "campaign": "Genera campana completa",
    }

    def do_generate_post(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        topic = params.get("topic", "")
        platform = params.get("platform", "twitter")
        if hasattr(mod, "SocialMediaCommandCenter"):
            center = mod.SocialMediaCommandCenter()
            if hasattr(center, "generate_post"):
                post = center.generate_post(topic, platform)
                return {"status": "ok", "post": post, "platform": platform}
        return {"status": "stub", "message": f"Social media center listo para generar contenido sobre '{topic}'"}


class SupportAdapter(ModuleAdapter):
    module_name = "customer_support_automation"
    actions = {
        "match_faq": "Busca respuesta en FAQ",
        "classify_ticket": "Clasifica ticket de soporte",
        "should_escalate": "Determina si escalar a humano",
    }

    def do_match_faq(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        query = params.get("query", "")
        if query and hasattr(mod, "find_best_faq_match"):
            match = mod.find_best_faq_match(query)
            return {"status": "ok", "match": match}
        return {"status": "stub", "message": "Proporciona una consulta para buscar en FAQ"}

class CodeGenAdapter(ModuleAdapter):
    module_name = "code_generation_agent"
    actions = {
        "generate": "Genera codigo desde descripcion",
        "test": "Genera tests para codigo",
        "document": "Genera documentacion",
    }

    def do_default(self, **params: Any) -> dict[str, Any]:
        # El chat del core llega sin accion: una query de codigo ES un generate.
        query = params.get("query", "")
        if query:
            return self.do_generate(description=query, language=params.get("language", "python"))
        return super().do_default(**params)

    def do_generate(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        description = params.get("description", "")
        language = params.get("language", "python")
        if description and hasattr(mod, "CodeGenerationAgent"):
            agent = mod.CodeGenerationAgent()
            code = agent.generate(description, language)
            return {"status": "ok", "code": code, "language": language}
        return {"status": "stub", "message": f"CodeGen listo para generar {language} desde: {description[:50]}..."}


class ContentAdapter(ModuleAdapter):
    module_name = "content_factory_ai"
    actions = {
        "generate": "Genera contenido para plataforma",
        "campaign": "Genera campana multi-plataforma",
        "email_sequence": "Genera secuencia de emails",
    }

    def do_generate(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        topic = params.get("topic", "")
        platform = params.get("platform", "blog")
        if topic and hasattr(mod, "ContentFactoryAI"):
            factory = mod.ContentFactoryAI()
            result = factory.generate(topic=topic, platform=platform, save=False)
            return {"status": "ok", "content": result}
        return {"status": "stub", "message": f"Content Factory listo para generar {platform} sobre '{topic}'"}

    def do_campaign(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        topic = params.get("topic", "")
        if topic and hasattr(mod, "ContentFactoryAI"):
            factory = mod.ContentFactoryAI()
            results = factory.generate_campaign(topic=topic)
            return {"status": "ok", "campaign": results}
        return {"status": "stub", "message": f"Content Factory listo para campana sobre '{topic}'"}


class SwarmAdapter(ModuleAdapter):
    module_name = "swarm_intelligence"
    actions = {
        "dispatch": "Despacha tarea a swarm",
        "status": "Estado del swarm",
        "results": "Resultados del swarm",
    }

    def do_default(self, **params: Any) -> dict[str, Any]:
        # El chat del core llega sin accion: una query de swarm ES un dispatch.
        query = params.get("query", "") or params.get("task", "")
        if query:
            return self.do_dispatch(task=query, agents=params.get("agents", ["content", "code"]))
        return super().do_default(**params)

    def do_dispatch(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        task = params.get("task", "")
        agents = params.get("agents", ["content", "code"])
        if task and hasattr(mod, "SwarmCoordinator"):
            coordinator = mod.SwarmCoordinator()
            result = coordinator.dispatch(task, agents)
            return {"status": "ok", "dispatch": result}
        return {"status": "stub", "message": f"Swarm listo para coordinar: {task[:50]}..."}

    def do_status(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        if mod and hasattr(mod, "SwarmIntelligence"):
            try:
                return {"status": "ok", "swarm": mod.SwarmIntelligence().obtener_estado_swarm()}
            except Exception as e:
                return {"status": "error", "error": str(e)[:200]}
        return {"status": "error", "error": "swarm no disponible"}

    def do_results(self, **params: Any) -> dict[str, Any]:

        try:
            from agents.agent_scoreboard import Scoreboard

            return {"status": "ok", "swarm": Scoreboard().swarm_stats()}
        except Exception as e:
            return {"status": "error", "error": str(e)[:200]}


class CadAdapter(ModuleAdapter):
    module_name = "agent_cad_studio"
    actions = {
        "disenar": "Disena pieza parametrica desde texto",
        "validar": "Valida .scad existente",
        "estado": "Disenos + toolchain",
    }

    def do_default(self, **params: Any) -> dict[str, Any]:
        # El chat llega sin accion: describir una pieza ES un disenar.
        query = params.get("query", "")
        if query:
            return self.do_disenar(descripcion=query)
        return super().do_default(**params)

    def do_disenar(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        descripcion = params.get("descripcion", "") or params.get("query", "")
        if descripcion and hasattr(mod, "disenar"):
            try:
                return {"status": "ok",
                        "diseno": mod.disenar(descripcion)}
            except Exception as e:
                return {"status": "error", "error": str(e)[:300]}
        return {"status": "stub", "message": "Describe la pieza a disenar"}

    def do_estado(self, **params: Any) -> dict[str, Any]:

        mod = self._mod
        if mod and hasattr(mod, "estado"):
            try:
                return {"status": "ok", "cad": mod.estado()}
            except Exception as e:
                return {"status": "error", "error": str(e)[:200]}
        return {"status": "error", "error": "cad no disponible"}


# ═══════════════════════════════════════════════════════════════
# Factory de Adapters
# ═══════════════════════════════════════════════════════════════

ADAPTER_MAP = {
    "daniela_proactive": ProactiveAdapter,
    "email_zero_inbox": EmailAdapter,
    "smart_invoice": InvoiceAdapter,
    "meeting_intel": MeetingAdapter,
    "sentiment_dashboard": SentimentAdapter,
    "social_media": SocialAdapter,
    "customer_support": SupportAdapter,
    "code_gen": CodeGenAdapter,
    "content_factory": ContentAdapter,
    "swarm_intel": SwarmAdapter,
    "cad_studio": CadAdapter,
}


def get_adapter(module_name: str) -> ModuleAdapter | None:
    """Obtiene la instancia de adapter para un modulo."""
    adapter_cls = ADAPTER_MAP.get(module_name)
    if adapter_cls:
        return adapter_cls()
    return None


def list_adapters() -> dict[str, type[ModuleAdapter]]:
    """Lista todos los adapters disponibles."""
    return dict(ADAPTER_MAP)


# ═══════════════════════════════════════════════════════════════
# CLI de Prueba
# ═══════════════════════════════════════════════════════════════

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="aig Module Adapters")
    parser.add_argument("module", choices=list(ADAPTER_MAP.keys()), help="Modulo a probar")
    parser.add_argument("--action", "-a", default="health_check", help="Accion a ejecutar")
    parser.add_argument("--params", "-p", default="{}", help="JSON de parametros")

    args = parser.parse_args()

    adapter = get_adapter(args.module)
    if not adapter:
        print(f"Adapter no encontrado para {args.module}")
        return 1

    params = json.loads(args.params)
    result = adapter.handler(action=args.action, **params)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

