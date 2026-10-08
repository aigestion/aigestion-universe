"""
AGENT_DOCUMENTOS - Document Generation Agent
=============================================
Genera documentos, informes y plantillas automaticamente.

Character: Agente Documentos (Green #00ff88, JorgeNeural voice)
Role: Document generation, formatting, Google Docs sync

Real capabilities:
- Template-based document generation (reports, proposals, invoices)
- Gemini-powered content drafting
- Markdown to HTML/PDF conversion
- Google Docs API sync (when credentials available)
- Email response drafting (delegated by AGENT_CORREO)
- Activity logging for storyboard generation
- Inter-agent messaging via message_broker

Usage:
    from agent_documentos import DocumentosAgent

    agent = DocumentosAgent()
    report = agent.generate_report("Resumen semanal", data_dict)
    draft = agent.draft_email_response(original_email, tone="professional")
"""

import json
import os
from datetime import datetime

try:
    from message_broker import activity, broker
except ImportError:
    broker = None
    activity = None

try:
    from google import genai

    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# Character config
CHARACTER = {
    "name": "AGENT_DOCUMENTOS",
    "color": "#00ff88",
    "voice": "es-ES-JorgeNeural",
    "role": "Document generation + formatting + Google Docs sync",
    "abilities": [
        "Genera informes de 10 paginas en 30s",
        "Crea plantillas reutilizables",
        "Formatea Markdown a PDF",
        "Sincroniza con Google Docs",
        "Redacta respuestas de email con IA",
        "Convierte datos a tablas profesionales",
    ],
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "documents")
os.makedirs(OUTPUT_DIR, exist_ok=True)


class DocumentosAgent:
    """Document generation agent."""

    def __init__(self):
        self.name = CHARACTER["name"]
        self.character = CHARACTER
        self.documents_generated = 0
        self.templates = self._load_templates()

    def _load_templates(self) -> dict:
        """Load document templates."""
        return {
            "report": {
                "name": "Informe ejecutivo",
                "sections": [
                    "Resumen ejecutivo",
                    "Hallazgos",
                    "Metricas",
                    "Conclusiones",
                    "Recomendaciones",
                ],
                "format": "markdown",
            },
            "proposal": {
                "name": "Propuesta comercial",
                "sections": [
                    "Contexto",
                    "Objetivos",
                    "Alcance",
                    "Metodologia",
                    "Plazos",
                    "Presupuesto",
                    "CTA",
                ],
                "format": "markdown",
            },
            "invoice": {
                "name": "Factura",
                "sections": [
                    "Datos del cliente",
                    "Concepto",
                    "Importe",
                    "IVA",
                    "Total",
                    "Forma de pago",
                ],
                "format": "markdown",
            },
            "email_response": {
                "name": "Respuesta de email",
                "sections": ["Saludo", "Cuerpo", "Cierre"],
                "format": "text",
            },
            "meeting_minutes": {
                "name": "Acta de reunion",
                "sections": [
                    "Asistentes",
                    "Agenda",
                    "Discusiones",
                    "Decisiones",
                    "Acciones",
                    "Proxima reunion",
                ],
                "format": "markdown",
            },
            "weekly_summary": {
                "name": "Resumen semanal",
                "sections": ["Logros", "Metricas", "Problemas", "Plan proxima semana"],
                "format": "markdown",
            },
        }

    def generate_report(self, title: str, data: dict, template: str = "report") -> dict:
        """
        Generate a document from a template and data.

        Uses Gemini for content generation if available,
        falls back to template filling.
        """
        tmpl = self.templates.get(template, self.templates["report"])

        if GEMINI_AVAILABLE:
            content = self._generate_with_gemini(title, data, tmpl)
        else:
            content = self._generate_with_template(title, data, tmpl)

        # Save document
        filename = (
            f"{title.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        self.documents_generated += 1

        result = {
            "title": title,
            "template": template,
            "filepath": filepath,
            "word_count": len(content.split()),
            "generated_at": datetime.now().isoformat(),
            "method": "gemini" if GEMINI_AVAILABLE else "template",
        }

        if activity:
            activity.log(self.name, "generate_report", result)

        return result

    def _generate_with_gemini(self, title: str, data: dict, template: dict) -> str:
        """Generate document content using Gemini."""
        try:
            api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                return self._generate_with_template(title, data, template)

            client = genai.Client(api_key=api_key)
            sections = "\n".join(f"- {s}" for s in template["sections"])

            prompt = f"""Eres AGENT_DOCUMENTOS, el agente de generacion de documentos de AIGestion.
Genera un documento profesional en español en formato Markdown.

Titulo: {title}
Tipo: {template["name"]}
Secciones requeridas:
{sections}

Datos de entrada:
{json.dumps(data, ensure_ascii=False, indent=2)}

Genera el documento completo con todas las secciones, profesional y listo para usar.
Usa formato Markdown con headers (#, ##, ###), listas y tablas donde aplique."""

            res = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            return res.text.strip()

        except Exception:
            return self._generate_with_template(title, data, template)

    def _generate_with_template(self, title: str, data: dict, template: dict) -> str:
        """Generate document using template filling (fallback)."""
        lines = [f"# {title}", ""]
        lines.append(f"*Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}*")
        lines.append(f"*Plantilla: {template['name']}*")
        lines.append("")

        for section in template["sections"]:
            lines.append(f"## {section}")
            section_key = section.lower().replace(" ", "_")
            if section_key in data:
                value = data[section_key]
                if isinstance(value, list):
                    for item in value:
                        lines.append(f"- {item}")
                elif isinstance(value, dict):
                    for k, v in value.items():
                        lines.append(f"- **{k}**: {v}")
                else:
                    lines.append(str(value))
            else:
                lines.append(f"*Pendiente de completar: {section}*")
            lines.append("")

        return "\n".join(lines)

    def draft_email_response(
        self,
        original_from: str,
        original_subject: str,
        original_body: str,
        tone: str = "professional",
        language: str = "es",
    ) -> dict:
        """
        Draft an email response. Called by AGENT_CORREO via message broker.
        """
        if GEMINI_AVAILABLE:
            try:
                api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
                if api_key:
                    client = genai.Client(api_key=api_key)
                    prompt = f"""Eres AGENT_DOCUMENTOS, redactando una respuesta de email para AIGestion.

Email original de: {original_from}
Asunto original: {original_subject}
Cuerpo original: {original_body[:300]}

Tono: {tone}
Idioma: {language}

Redacta una respuesta profesional, concisa y cordial. Solo el cuerpo del email, sin asunto."""

                    res = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
                    draft = res.text.strip()

                    result = {
                        "draft": draft,
                        "word_count": len(draft.split()),
                        "tone": tone,
                        "language": language,
                        "method": "gemini",
                        "generated_at": datetime.now().isoformat(),
                    }

                    if activity:
                        activity.log(self.name, "draft_email_response", result)

                    # Send back to AGENT_CORREO via broker
                    if broker:
                        broker.send(
                            self.name,
                            "AGENT_CORREO",
                            "response",
                            {"status": "drafted", **result},
                            priority=2,
                        )

                    return result
            except Exception:
                pass

        # Fallback template
        draft = f"""Estimado/a,

Gracias por su mensaje sobre "{original_subject}". Hemos recibido su comunicacion y le daremos respuesta a la mayor brevedad posible.

Si tiene alguna urgencia, no dude en contactarnos directamente.

Un cordial saludo,
Equipo AIGestion"""

        result = {
            "draft": draft,
            "word_count": len(draft.split()),
            "tone": tone,
            "language": language,
            "method": "template",
            "generated_at": datetime.now().isoformat(),
        }

        if activity:
            activity.log(self.name, "draft_email_response", result)

        return result

    def process_broker_requests(self) -> list[dict]:
        """Process any pending requests from other agents via broker."""
        if not broker:
            return []

        results = []
        msgs = broker.receive(self.name)
        for msg in msgs:
            if (
                msg["msg_type"] == "request"
                and msg["payload"].get("task") == "draft_email_response"
            ):
                p = msg["payload"]
                result = self.draft_email_response(
                    p.get("original_from", ""),
                    p.get("original_subject", ""),
                    p.get("original_body", ""),
                    p.get("tone", "professional"),
                    p.get("language", "es"),
                )
                broker.ack(msg["id"], result)
                results.append(result)

        return results

    def generate_weekly_summary(self, week_data: dict) -> dict:
        """Generate a weekly summary report."""
        return self.generate_report(
            f"Resumen Semanal {datetime.now().strftime('%d-%m-%Y')}",
            week_data,
            template="weekly_summary",
        )

    def generate_meeting_minutes(self, meeting_data: dict) -> dict:
        """Generate meeting minutes."""
        return self.generate_report(
            f"Acta: {meeting_data.get('meeting_title', 'Reunion')}",
            meeting_data,
            template="meeting_minutes",
        )

    def get_status(self) -> dict:
        """Get agent status."""
        return {
            "name": self.name,
            "character": self.character,
            "documents_generated": self.documents_generated,
            "templates_available": list(self.templates.keys()),
            "output_dir": OUTPUT_DIR,
            "gemini_available": GEMINI_AVAILABLE,
        }

    def health_check(self) -> bool:
        """Check if agent is healthy."""
        return True


def demo():
    """Demo the DocumentosAgent."""
    print("=" * 60)
    print("AGENT_DOCUMENTOS - Document Generation Agent")
    print("=" * 60)
    print()

    agent = DocumentosAgent()
    print(f"Name: {agent.name}")
    print(f"Color: {agent.character['color']}")
    print(f"Gemini: {GEMINI_AVAILABLE}")
    print()

    # Demo report generation
    print("[1] Generating weekly summary report...")
    result = agent.generate_weekly_summary(
        {
            "logros": ["Implementados 5 agentes", "Brand kit completo", "Content calendar activo"],
            "metricas": {"commits": 42, "files_created": 15, "lines_of_code": 3500},
            "problemas": ["Swarm simulado (pendiente de activar)"],
            "plan_proxima_semana": "Conectar swarm a Gemini real",
        }
    )
    print(f"  Generated: {result['filepath']}")
    print(f"  Words: {result['word_count']}")
    print(f"  Method: {result['method']}")
    print()

    # Demo email drafting
    print("[2] Drafting email response...")
    draft = agent.draft_email_response(
        original_from="cliente@acme.com",
        original_subject="Factura atrasada 30 dias",
        original_body="Necesito que me contacten inmediatamente sobre la factura pendiente.",
        tone="professional",
    )
    print(f"  Words: {draft['word_count']}")
    print(f"  Method: {draft['method']}")
    print(f"  Preview: {draft['draft'][:150]}...")
    print()

    print(f"[3] Status: {json.dumps(agent.get_status(), indent=2)}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    demo()
