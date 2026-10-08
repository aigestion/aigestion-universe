"""
Email Zero Inbox AI
===================
Clasifica emails, genera respuestas automaticas y mantiene inbox limpio.

Quick Win #3: Integra con gmail_service.py existente.
"""

import json
import logging
import os
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format="%(asctime)s [EMAIL] %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class EmailClassification:
    """Clasificacion de un email."""

    email_id: str
    subject: str
    sender: str
    category: str  # urgent, important, delegable, newsletter, spam
    priority: int  # 0-100
    suggested_action: str
    draft_reply: str | None


class EmailZeroInbox:
    """Sistema de gestion inteligente de emails."""

    def __init__(self):
        self.rules_file = "email_rules.json"
        self.history_file = "email_history.json"
        self.cargar_reglas()

    def cargar_reglas(self):
        """Carga reglas de clasificacion personalizadas."""
        if os.path.exists(self.rules_file):
            with open(self.rules_file, encoding="utf-8") as f:
                self.rules = json.load(f)
        else:
            self.rules = self._reglas_default()
            self.guardar_reglas()

    def _reglas_default(self) -> dict:
        """Reglas de clasificacion por defecto."""
        return {
            "senders_urgent": ["jefe", "ceo", "director", "cliente", "urgente"],
            "senders_important": ["contable", "abogado", "proveedor", "socio"],
            "subjects_urgent": ["urgente", "critico", "deadline", "vence", "inmediato"],
            "subjects_newsletter": ["newsletter", "boletin", "oferta", "promo", "unsubscribe"],
            "domains_delegable": ["marketing", "rrhh", "soporte", "admin"],
            "keywords_spam": ["ganaste", "premio", "loteria", "herencia", "principe"],
        }

    def guardar_reglas(self):
        """Guarda reglas actualizadas."""
        with open(self.rules_file, "w", encoding="utf-8") as f:
            json.dump(self.rules, f, indent=2, ensure_ascii=False)

    def clasificar_email(self, email: dict) -> EmailClassification:
        """
        Clasifica un email segun reglas + contenido.

        Args:
            email: Dict con 'id', 'subject', 'sender', 'body', 'date'
        """
        subject = email.get("subject", "").lower()
        sender = email.get("sender", "").lower()
        body = email.get("body", "").lower()
        email_id = email.get("id", "unknown")

        # 1. Detectar SPAM primero
        if self._es_spam(subject, body, sender):
            return EmailClassification(
                email_id=email_id,
                subject=email["subject"],
                sender=email["sender"],
                category="spam",
                priority=0,
                suggested_action="Eliminar automaticamente",
                draft_reply=None,
            )

        # 2. Detectar newsletters
        if self._es_newsletter(subject, sender):
            return EmailClassification(
                email_id=email_id,
                subject=email["subject"],
                sender=email["sender"],
                category="newsletter",
                priority=5,
                suggested_action="Archivar en carpeta Newsletters",
                draft_reply=None,
            )

        # 3. Detectar urgente
        if self._es_urgente(subject, sender, body):
            return EmailClassification(
                email_id=email_id,
                subject=email["subject"],
                sender=email["sender"],
                category="urgent",
                priority=95,
                suggested_action="Responder inmediatamente",
                draft_reply=self._generar_borrador(email, "urgente"),
            )

        # 4. Detectar importante
        if self._es_importante(subject, sender, body):
            return EmailClassification(
                email_id=email_id,
                subject=email["subject"],
                sender=email["sender"],
                category="important",
                priority=70,
                suggested_action="Responder hoy",
                draft_reply=self._generar_borrador(email, "importante"),
            )

        # 5. Detectar delegable
        if self._es_delegable(subject, sender):
            return EmailClassification(
                email_id=email_id,
                subject=email["subject"],
                sender=email["sender"],
                category="delegable",
                priority=40,
                suggested_action="Delegar a equipo correspondiente",
                draft_reply=self._generar_borrador(email, "delegar"),
            )

        # Default: informativo
        return EmailClassification(
            email_id=email_id,
            subject=email["subject"],
            sender=email["sender"],
            category="info",
            priority=20,
            suggested_action="Revisar cuando sea conveniente",
            draft_reply=None,
        )

    def _es_spam(self, subject: str, body: str, sender: str) -> bool:
        """Detecta emails de spam."""
        spam_keywords = self.rules.get("keywords_spam", [])
        text = f"{subject} {body}"
        return any(kw in text for kw in spam_keywords)

    def _es_newsletter(self, subject: str, sender: str) -> bool:
        """Detecta newsletters."""
        newsletter_keywords = self.rules.get("subjects_newsletter", [])
        return any(kw in subject for kw in newsletter_keywords) or "noreply" in sender

    def _es_urgente(self, subject: str, sender: str, body: str) -> bool:
        """Detecta emails urgentes."""
        urgent_senders = self.rules.get("senders_urgent", [])
        urgent_subjects = self.rules.get("subjects_urgent", [])

        sender_match = any(s in sender for s in urgent_senders)
        subject_match = any(k in subject for k in urgent_subjects)
        body_urgent = any(k in body for k in ["urgente", "critico", "inmediato", "ahora"])

        return sender_match or subject_match or body_urgent

    def _es_importante(self, subject: str, sender: str, body: str) -> bool:
        """Detecta emails importantes."""
        important_senders = self.rules.get("senders_important", [])
        return any(s in sender for s in important_senders) or "factura" in subject

    def _es_delegable(self, subject: str, sender: str) -> bool:
        """Detecta emails delegables."""
        delegable_domains = self.rules.get("domains_delegable", [])
        return any(d in sender for d in delegable_domains)

    def _generar_borrador(self, email: dict, tipo: str) -> str | None:
        """Genera borrador de respuesta segun tipo."""
        sender = email.get("sender", "").split("@")[0]
        email.get("subject", "")

        templates = {
            "urgente": (
                f"Hola {sender.title()},\n\n"
                "He recibido tu mensaje y estoy trabajando en ello. "
                "Te dare una respuesta detallada lo antes posible.\n\n"
                "Gracias por tu paciencia.\n\n"
                "Saludos,\nDaniela"
            ),
            "importante": (
                f"Hola {sender.title()},\n\n"
                "Gracias por tu mensaje. Lo revisare y te respondere "
                "durante el dia de hoy.\n\n"
                "Saludos,\nDaniela"
            ),
            "delegar": (
                f"Hola {sender.title()},\n\n"
                "He recibido tu solicitud y la he derivado al equipo "
                "correspondiente. Te contactaran pronto.\n\n"
                "Saludos,\nDaniela"
            ),
        }

        return templates.get(tipo)

    def procesar_inbox(self, emails: list[dict]) -> dict:
        """
        Procesa inbox completo y genera acciones.

        Returns:
            Dict con clasificaciones y estadisticas
        """
        clasificaciones = []
        acciones = {
            "responder_ahora": [],
            "responder_hoy": [],
            "delegar": [],
            "archivar": [],
            "eliminar": [],
        }

        for email in emails:
            clasif = self.clasificar_email(email)
            clasificaciones.append(clasif)

            # Agrupar por accion
            if clasif.category == "urgent":
                acciones["responder_ahora"].append(clasif)
            elif clasif.category == "important":
                acciones["responder_hoy"].append(clasif)
            elif clasif.category == "delegable":
                acciones["delegar"].append(clasif)
            elif clasif.category == "newsletter":
                acciones["archivar"].append(clasif)
            elif clasif.category == "spam":
                acciones["eliminar"].append(clasif)

        return {
            "total": len(emails),
            "clasificaciones": clasificaciones,
            "acciones": acciones,
            "resumen": self._generar_resumen(acciones),
        }

    def _generar_resumen(self, acciones: dict) -> str:
        """Genera resumen ejecutivo del inbox."""
        urgentes = len(acciones["responder_ahora"])
        importantes = len(acciones["responder_hoy"])
        delegables = len(acciones["delegar"])
        archivar = len(acciones["archivar"])
        eliminar = len(acciones["eliminar"])

        resumen = f"""Resumen del Inbox:
- {urgentes} emails URGENTES (responder ahora)
- {importantes} emails IMPORTANTES (responder hoy)
- {delegables} emails DELEGABLES
- {archivar} newsletters/archivar
- {eliminar} spam/eliminar
"""

        if urgentes > 0:
            resumen += f"\n⚠️ ATENCION: {urgentes} emails requieren respuesta inmediata!"

        return resumen

    def demo(self):
        """Demostracion del Email Zero Inbox."""
        print("=" * 60)
        print("EMAIL ZERO INBOX AI - DEMO")
        print("=" * 60)
        print()

        emails_demo = [
            {
                "id": "1",
                "subject": "URGENTE: Problema critico en produccion",
                "sender": "jefe@empresa.com",
                "body": "Necesitamos solucion inmediata. Esto es critico.",
                "date": "2026-09-05",
            },
            {
                "id": "2",
                "subject": "Newsletter Septiembre - Ofertas especiales",
                "sender": "noreply@marketing.com",
                "body": "Nuestras mejores ofertas del mes...",
                "date": "2026-09-05",
            },
            {
                "id": "3",
                "subject": "Factura #12345 - Pago pendiente",
                "sender": "contable@empresa.com",
                "body": "La factura vence el proximo martes.",
                "date": "2026-09-05",
            },
            {
                "id": "4",
                "subject": "Ganaste un premio de $1,000,000!",
                "sender": "spam@loteria.com",
                "body": "Has sido seleccionado para un premio increible!",
                "date": "2026-09-05",
            },
            {
                "id": "5",
                "subject": "Solicitud de vacaciones - Maria",
                "sender": "rrhh@empresa.com",
                "body": "Maria solicita vacaciones del 10-20 de septiembre.",
                "date": "2026-09-05",
            },
        ]

        resultado = self.procesar_inbox(emails_demo)

        print("Emails procesados:", resultado["total"])
        print()

        for c in resultado["clasificaciones"]:
            print(f"  [{c.category.upper()}] {c.subject}")
            print(f"    De: {c.sender}")
            print(f"    Prioridad: {c.priority}/100")
            print(f"    Accion: {c.suggested_action}")
            if c.draft_reply:
                print(f"    Borrador: {c.draft_reply[:50]}...")
            print()

        print(resultado["resumen"])
        print("=" * 60)


if __name__ == "__main__":
    inbox = EmailZeroInbox()
    inbox.demo()
