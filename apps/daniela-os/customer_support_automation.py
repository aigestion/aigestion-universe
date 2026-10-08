"""
Customer Support Automation
============================
Chatbot multicanal con RAG + escalamiento humano inteligente.

Quick Win #8: Expande telegram_bot.py y webhook_server.py.
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [SUPPORT] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class SupportTicket:
    """Ticket de soporte."""

    ticket_id: str
    user_id: str
    channel: str  # telegram, web, email, whatsapp
    message: str
    category: str
    priority: int
    status: str  # open, bot_handled, escalated, resolved
    created_at: str
    resolved_at: str | None


class CustomerSupportAutomation:
    """Sistema automatizado de soporte al cliente."""

    def __init__(self):
        self.kb_file = "support_knowledge_base.json"
        self.tickets_file = "support_tickets.json"
        self.knowledge_base = self._cargar_kb()
        self.tickets = self._cargar_tickets()

    def _cargar_kb(self) -> dict:
        """Carga base de conocimiento."""
        if os.path.exists(self.kb_file):
            with open(self.kb_file, encoding="utf-8") as f:
                return json.load(f)
        return self._kb_default()

    def _kb_default(self) -> dict:
        """Base de conocimiento por defecto."""
        return {
            "faq": [
                {
                    "question": "como instalar",
                    "answer": "Para instalar AIGestion: 1) Descarga desde GitHub, 2) Ejecuta setup.py, 3) Configura .env con tus credenciales.",
                    "category": "instalacion",
                    "keywords": ["instalar", "setup", "configurar", "empezar"],
                },
                {
                    "question": "no funciona",
                    "answer": "Verifica: 1) Python 3.10+, 2) Dependencias instaladas (pip install -r requirements.txt), 3) Archivo .env configurado.",
                    "category": "troubleshooting",
                    "keywords": ["error", "falla", "no funciona", "problema", "bug"],
                },
                {
                    "question": "precio",
                    "answer": "AIGestion tiene version gratuita (basica) y Pro ($29/mes). Enterprise disponible bajo consulta.",
                    "category": "ventas",
                    "keywords": ["precio", "costo", "cuanto cuesta", "plan", "suscripcion"],
                },
                {
                    "question": "api key",
                    "answer": "Obtienes API key en Google AI Studio (para Gemini) o OpenAI dashboard. Guardala en el archivo .env.",
                    "category": "configuracion",
                    "keywords": ["api", "key", "token", "credenciales", "gemini"],
                },
                {
                    "question": "como usar daniela",
                    "answer": "Daniela responde a comandos de voz y texto. Prueba: 'Hola Daniela, que tengo hoy?' o 'Daniela, resume mis emails'.",
                    "category": "uso",
                    "keywords": ["usar", "comando", "voz", "daniela", "ayuda"],
                },
            ],
            "troubleshooting": {
                "error_500": "Error interno del servidor. Reinicia el servicio y verifica logs.",
                "timeout": "Tiempo de espera agotado. Verifica conexion a internet y estado de APIs externas.",
                "no_audio": "Problema de audio. Verifica permisos de microfono y configuracion de edge-tts.",
            },
        }

    def _cargar_tickets(self) -> list[dict]:
        """Carga tickets existentes."""
        if os.path.exists(self.tickets_file):
            with open(self.tickets_file, encoding="utf-8") as f:
                return json.load(f)
        return []

    def buscar_respuesta_kb(self, query: str) -> dict | None:
        """
        Busca respuesta en base de conocimiento.

        Args:
            query: Pregunta del usuario

        Returns:
            Mejor match o None
        """
        query_lower = query.lower()
        best_match = None
        best_score = 0

        for faq in self.knowledge_base.get("faq", []):
            score = 0
            keywords = faq.get("keywords", [])

            for kw in keywords:
                if kw in query_lower:
                    score += 1

            # Bonus por palabras en pregunta exacta
            if any(word in faq["question"] for word in query_lower.split()):
                score += 0.5

            if score > best_score:
                best_score = score
                best_match = faq

        return best_match if best_score >= 1 else None

    def clasificar_ticket(self, message: str, channel: str) -> tuple[str, int]:
        """
        Clasifica ticket por categoria y prioridad.

        Returns:
            (categoria, prioridad)
        """
        msg_lower = message.lower()

        # Categorias
        categories = {
            "urgent": ["urgente", "critico", "down", "caido", "no puedo acceder"],
            "billing": ["factura", "pago", "cobro", "precio", "suscripcion"],
            "technical": ["error", "bug", "falla", "no funciona", "problema tecnico"],
            "feature": ["sugerencia", "feature", "mejora", "quiero", "falta"],
            "general": ["como", "ayuda", "pregunta", "info"],
        }

        detected_category = "general"
        for cat, keywords in categories.items():
            if any(kw in msg_lower for kw in keywords):
                detected_category = cat
                break

        # Prioridad
        priority = 30  # Base
        if detected_category == "urgent":
            priority = 95
        elif detected_category == "billing":
            priority = 60
        elif detected_category == "technical":
            priority = 70
        elif detected_category == "feature":
            priority = 40

        # Ajuste por palabras de urgencia
        if any(w in msg_lower for w in ["ahora", "inmediato", "emergencia"]):
            priority += 20

        return detected_category, min(priority, 100)

    def procesar_mensaje(self, user_id: str, message: str, channel: str = "web") -> dict:
        """
        Procesa mensaje de usuario y determina accion.

        Returns:
            Dict con respuesta, accion y estado
        """
        ticket_id = f"TKT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id[:6]}"
        categoria, prioridad = self.clasificar_ticket(message, channel)

        # 1. Buscar en KB
        kb_answer = self.buscar_respuesta_kb(message)

        if kb_answer and prioridad < 80:
            # Bot puede manejarlo
            ticket = SupportTicket(
                ticket_id=ticket_id,
                user_id=user_id,
                channel=channel,
                message=message,
                category=categoria,
                priority=prioridad,
                status="bot_handled",
                created_at=datetime.now().isoformat(),
                resolved_at=datetime.now().isoformat(),
            )
            self._guardar_ticket(ticket)

            return {
                "ticket_id": ticket_id,
                "status": "resolved_by_bot",
                "response": kb_answer["answer"],
                "category": categoria,
                "escalate": False,
            }

        # 2. Escalamiento humano
        ticket = SupportTicket(
            ticket_id=ticket_id,
            user_id=user_id,
            channel=channel,
            message=message,
            category=categoria,
            priority=prioridad,
            status="escalated",
            created_at=datetime.now().isoformat(),
            resolved_at=None,
        )
        self._guardar_ticket(ticket)

        return {
            "ticket_id": ticket_id,
            "status": "escalated",
            "response": self._mensaje_escalamiento(categoria, prioridad),
            "category": categoria,
            "priority": prioridad,
            "escalate": True,
        }

    def _mensaje_escalamiento(self, categoria: str, prioridad: int) -> str:
        """Genera mensaje de escalamiento."""
        if prioridad >= 80:
            return (
                "⚠️ Tu solicitud ha sido marcada como URGENTE. "
                "Un agente humano te contactara en los proximos 15 minutos."
            )
        elif categoria == "technical":
            return (
                "He registrado tu problema tecnico. Nuestro equipo de soporte "
                "te respondera en menos de 2 horas. Ticket: referencia."
            )
        else:
            return (
                "Gracias por contactarnos. Te responderemos en menos de 24 horas. "
                "Tu numero de ticket es: referencia"
            )

    def _guardar_ticket(self, ticket: SupportTicket):
        """Guarda ticket en base de datos."""
        self.tickets.append(
            {
                "ticket_id": ticket.ticket_id,
                "user_id": ticket.user_id,
                "channel": ticket.channel,
                "message": ticket.message,
                "category": ticket.category,
                "priority": ticket.priority,
                "status": ticket.status,
                "created_at": ticket.created_at,
                "resolved_at": ticket.resolved_at,
            }
        )

        with open(self.tickets_file, "w", encoding="utf-8") as f:
            json.dump(self.tickets, f, indent=2, ensure_ascii=False)

    def obtener_metricas(self) -> dict:
        """Obtiene metricas de soporte."""
        total = len(self.tickets)
        if total == 0:
            return {"mensaje": "Sin tickets registrados"}

        bot_resolved = sum(1 for t in self.tickets if t["status"] == "bot_handled")
        escalated = sum(1 for t in self.tickets if t["status"] == "escalated")
        resolved = sum(1 for t in self.tickets if t["resolved_at"])

        avg_resolution_time = 0
        resolved_tickets = [t for t in self.tickets if t["resolved_at"]]
        if resolved_tickets:
            times = []
            for t in resolved_tickets:
                created = datetime.fromisoformat(t["created_at"])
                resolved = datetime.fromisoformat(t["resolved_at"])
                times.append((resolved - created).total_seconds() / 3600)
            avg_resolution_time = sum(times) / len(times)

        return {
            "total_tickets": total,
            "bot_resolution_rate": round(bot_resolved / total * 100, 1),
            "escalation_rate": round(escalated / total * 100, 1),
            "avg_resolution_hours": round(avg_resolution_time, 1),
            "tickets_by_category": self._tickets_por_categoria(),
            "satisfaction_estimate": "Buena" if bot_resolved / total > 0.6 else "Mejorable",
        }

    def _tickets_por_categoria(self) -> dict:
        """Agrupa tickets por categoria."""
        categorias = {}
        for t in self.tickets:
            cat = t["category"]
            categorias[cat] = categorias.get(cat, 0) + 1
        return categorias

    def demo(self):
        """Demostracion del soporte automatizado."""
        print("=" * 60)
        print("CUSTOMER SUPPORT AUTOMATION - DEMO")
        print("=" * 60)
        print()

        print("[1] Base de Conocimiento:")
        print(f"  FAQs disponibles: {len(self.knowledge_base['faq'])}")
        for faq in self.knowledge_base["faq"]:
            print(f"  - [{faq['category']}] {faq['question']}")
        print()

        print("[2] Procesando consultas de ejemplo:")
        consultas = [
            ("user_001", "Como instalo AIGestion?", "telegram"),
            ("user_002", "Tengo un error critico en produccion!", "web"),
            ("user_003", "Cuanto cuesta el plan Pro?", "email"),
            ("user_004", "Mi servidor no responde desde ayer", "web"),
            ("user_005", "Como uso los comandos de voz?", "telegram"),
        ]

        for user_id, msg, channel in consultas:
            resultado = self.procesar_mensaje(user_id, msg, channel)
            print(f"\n  Usuario: {user_id} | Canal: {channel}")
            print(f"  Pregunta: {msg}")
            print(f"  Estado: {resultado['status']}")
            print(f"  Respuesta: {resultado['response'][:80]}...")
            if resultado["escalate"]:
                print(f"  ⚠️ Escalado - Prioridad: {resultado.get('priority', 'N/A')}")
        print()

        print("[3] Metricas de Soporte:")
        metricas = self.obtener_metricas()
        print(f"  Total tickets: {metricas['total_tickets']}")
        print(f"  Resueltos por bot: {metricas['bot_resolution_rate']}%")
        print(f"  Escalados: {metricas['escalation_rate']}%")
        print(f"  Tiempo medio resolucion: {metricas['avg_resolution_hours']}h")
        print(f"  Satisfaccion estimada: {metricas['satisfaction_estimate']}")
        print()

        print("=" * 60)


if __name__ == "__main__":
    support = CustomerSupportAutomation()
    support.demo()
