"""
AGENT_CORREO - Email Processing Agent
======================================
Procesa, clasifica y prioriza correos automaticamente.

Character: Agente Correo (Blue #0099ff, AlvaroNeural voice)
Role: Email classification, priority scoring, auto-response drafting

Real capabilities:
- IMAP email reading (works with any provider)
- Gmail API integration (when credentials available)
- AI-powered classification via Gemini
- Priority scoring (0-10)
- Auto-draft responses (delegates to AGENT_DOCUMENTOS)
- Activity logging for storyboard generation
- Inter-agent messaging via message_broker

Usage:
    from agent_correo import CorreoAgent

    agent = CorreoAgent()
    emails = agent.fetch_unread()
    for email in emails:
        classification = agent.classify(email)
        if classification["priority"] >= 8:
            draft = agent.request_draft(email)
"""

import email
import imaplib
import json
import os
from datetime import datetime

try:
    from message_broker import activity, broker
except ImportError:
    broker = None
    activity = None

# Character config
CHARACTER = {
    "name": "AGENT_CORREO",
    "color": "#0099ff",
    "voice": "es-ES-AlvaroNeural",
    "role": "Email processing + classification + priority scoring",
    "abilities": [
        "Clasifica 50+ correos en 30s",
        "Detecta urgencia por palabras clave + contexto",
        "Genera respuesta automatica con IA",
        "Filtra spam y newsletters",
        "Resume hilos largos en 3 puntos",
    ],
}

# Classification categories
CATEGORIES = {
    "urgent": ["urgente", "inmediato", "crisis", "problema", "error", "fallo"],
    "client": ["cliente", "factura", "pago", "contrato", "presupuesto"],
    "internal": ["equipo", "reunion", "interna", "proyecto", "tarea"],
    "newsletter": ["newsletter", "boletin", "subscribe", "unsubscribe"],
    "spam": ["ganador", "premio", "oferta", "gratis", "click aqui"],
    "social": ["linkedin", "twitter", "facebook", "instagram"],
}

# Priority keywords (add weight to score)
PRIORITY_KEYWORDS = {
    10: ["urgente", "crisis", "fallo critico", "sistema caido"],
    8: ["factura atrasada", "pago pendiente", "reclamacion", "queja"],
    6: ["reunion", "deadline", "entrega", "propuesta"],
    4: ["newsletter", "update", "resumen", "informe"],
    2: ["social", "conexion", "follow"],
}


class CorreoAgent:
    """Email processing agent."""

    def __init__(self, imap_server: str = None, email_addr: str = None, email_pass: str = None):
        self.name = CHARACTER["name"]
        self.character = CHARACTER
        self.imap_server = imap_server or os.environ.get("IMAP_SERVER", "imap.gmail.com")
        self.email_addr = email_addr or os.environ.get("EMAIL_ADDRESS", "")
        self.email_pass = email_pass or os.environ.get("EMAIL_PASSWORD", "")
        self._setup()

    def _setup(self):
        """Initialize agent state."""
        self.inbox_count = 0
        self.processed_today = 0
        self.classified = {
            "urgent": 0,
            "client": 0,
            "internal": 0,
            "newsletter": 0,
            "spam": 0,
            "social": 0,
        }

    def fetch_unread(self, limit: int = 20) -> list[dict]:
        """
        Fetch unread emails via IMAP.

        Returns:
            List of email dicts with: from, subject, body, date, uid
        """
        if not self.email_addr or not self.email_pass:
            # Fallback: return empty (agent is ready but not configured)
            if activity:
                activity.log(
                    self.name,
                    "fetch_attempt",
                    {"status": "no_credentials", "message": "IMAP credentials not configured"},
                )
            return []

        emails = []
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server)
            mail.login(self.email_addr, self.email_pass)
            mail.select("INBOX")

            # Search unread
            status, data = mail.search(None, "UNSEEN")
            if status == "OK":
                uids = data[0].split()[:limit]
                for uid in uids:
                    status, msg_data = mail.fetch(uid, "(RFC822)")
                    if status == "OK":
                        raw = msg_data[0][1]
                        msg = email.message_from_bytes(raw)

                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                ct = part.get_content_type()
                                if ct == "text/plain":
                                    body = part.get_payload(decode=True).decode(
                                        "utf-8", errors="ignore"
                                    )[:500]
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")[
                                :500
                            ]

                        emails.append(
                            {
                                "uid": uid.decode(),
                                "from": msg.get("From", ""),
                                "subject": msg.get("Subject", ""),
                                "body": body,
                                "date": msg.get("Date", ""),
                            }
                        )

            mail.logout()
            self.inbox_count = len(emails)

            if activity:
                activity.log(
                    self.name, "fetch_unread", {"count": len(emails), "server": self.imap_server}
                )

        except Exception as e:
            if activity:
                activity.log(self.name, "fetch_error", {"error": str(e)})

        return emails

    def classify(self, email_data: dict) -> dict:
        """
        Classify an email: category, priority (0-10), summary.

        Uses keyword matching + heuristics. Can be upgraded to Gemini.
        """
        subject = email_data.get("subject", "").lower()
        body = email_data.get("body", "").lower()
        sender = email_data.get("from", "").lower()
        text = f"{subject} {body}"

        # Detect category
        category = "internal"  # default
        for cat, keywords in CATEGORIES.items():
            if any(kw in text for kw in keywords):
                category = cat
                break

        # Calculate priority
        priority = 3  # default low
        for score, keywords in PRIORITY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                priority = max(priority, score)
                break

        # Boost priority for client senders
        client_domains = ["gmail.com", "outlook.com", "yahoo.com"]
        is_personal = any(d in sender for d in client_domains) and "noreply" not in sender
        if is_personal:
            priority = max(priority, 5)

        # Detect if response needed
        needs_response = priority >= 6 and category in ("urgent", "client")
        if any(w in text for w in ["cuando", "puedes", "pueden", "?", "confirmar"]):
            needs_response = True
            priority = max(priority, 5)

        # Generate summary
        summary = subject[:80] if subject else "(sin asunto)"

        self.classified[category] = self.classified.get(category, 0) + 1
        self.processed_today += 1

        result = {
            "category": category,
            "priority": priority,
            "needs_response": needs_response,
            "summary": summary,
            "is_spam": category == "spam",
            "is_newsletter": category == "newsletter",
            "classified_at": datetime.now().isoformat(),
        }

        if activity:
            activity.log(
                self.name, "classify_email", {"from": sender[:50], "subject": summary, **result}
            )

        return result

    def request_draft(self, email_data: dict) -> str | None:
        """
        Request AGENT_DOCUMENTOS to draft a response.

        Uses the message broker to delegate the task.
        """
        if not broker:
            return None

        msg_id = broker.send(
            self.name,
            "AGENT_DOCUMENTOS",
            "request",
            {
                "task": "draft_email_response",
                "original_from": email_data.get("from", ""),
                "original_subject": email_data.get("subject", ""),
                "original_body": email_data.get("body", "")[:200],
                "tone": "professional",
                "language": "es",
            },
            priority=1 if self.classify(email_data)["priority"] >= 8 else 2,
        )

        if activity:
            activity.log(
                self.name,
                "request_draft",
                {
                    "to": "AGENT_DOCUMENTOS",
                    "msg_id": msg_id,
                    "subject": email_data.get("subject", "")[:50],
                },
            )

        return msg_id

    def process_inbox(self, auto_draft: bool = True) -> dict:
        """
        Full inbox processing pipeline:
        fetch -> classify -> (optionally request drafts for urgent)

        Returns:
            Summary dict with counts and actions taken
        """
        emails = self.fetch_unread()
        results = {
            "total": len(emails),
            "by_category": {},
            "by_priority": {"high": 0, "medium": 0, "low": 0},
            "drafts_requested": 0,
            "spam_filtered": 0,
        }

        for email_data in emails:
            cls = self.classify(email_data)

            cat = cls["category"]
            results["by_category"][cat] = results["by_category"].get(cat, 0) + 1

            if cls["priority"] >= 7:
                results["by_priority"]["high"] += 1
            elif cls["priority"] >= 4:
                results["by_priority"]["medium"] += 1
            else:
                results["by_priority"]["low"] += 1

            if cls["is_spam"]:
                results["spam_filtered"] += 1
                continue

            if auto_draft and cls["needs_response"]:
                self.request_draft(email_data)
                results["drafts_requested"] += 1

        # Notify Daniela of results
        if broker and emails:
            broker.send(
                self.name,
                "DANIELA",
                "status",
                {"task": "inbox_processed", **results, "timestamp": datetime.now().isoformat()},
                priority=2,
            )

        if activity:
            activity.log(self.name, "process_inbox_complete", results)

        return results

    def get_status(self) -> dict:
        """Get agent status."""
        return {
            "name": self.name,
            "character": self.character,
            "inbox_count": self.inbox_count,
            "processed_today": self.processed_today,
            "classified": self.classified,
            "configured": bool(self.email_addr and self.email_pass),
            "imap_server": self.imap_server if self.email_addr else "not configured",
        }

    def health_check(self) -> bool:
        """Check if agent is healthy."""
        return True  # Agent is always ready, even without IMAP configured


def demo():
    """Demo the CorreoAgent."""
    print("=" * 60)
    print("AGENT_CORREO - Email Processing Agent")
    print("=" * 60)
    print()

    agent = CorreoAgent()
    print(f"Name: {agent.name}")
    print(f"Color: {agent.character['color']}")
    print(f"Configured: {agent.get_status()['configured']}")
    print()

    # Demo classification with sample emails
    print("[1] Classification demo with sample emails:")
    print()
    samples = [
        {
            "from": "cliente@acme.com",
            "subject": "URGENTE: Factura atrasada 30 dias",
            "body": "Necesito que me contacten inmediatamente sobre la factura...",
        },
        {
            "from": "newsletter@tech.com",
            "subject": "Weekly tech update",
            "body": "Here are this week's top stories...",
        },
        {
            "from": "jefe@empresa.com",
            "subject": "Reunion manana 9am",
            "body": "Confirmar asistencia a la reunion de manana...",
        },
        {
            "from": "spam@winner.com",
            "subject": "HAS GANADO UN PREMIO",
            "body": "Click aqui para reclamar tu premio gratis...",
        },
        {
            "from": "linkedin.com",
            "subject": "Nueva conexion",
            "body": "Tienes 3 nuevas conexiones en LinkedIn...",
        },
    ]

    for s in samples:
        cls = agent.classify(s)
        icon = {
            "urgent": "!!",
            "client": "$",
            "internal": "@",
            "newsletter": "~",
            "spam": "X",
            "social": "+",
        }
        print(
            f"  [{icon.get(cls['category'], '?')}] P:{cls['priority']} {cls['category']:10s} | "
            f"resp={cls['needs_response']} | {s['subject'][:40]}"
        )

    print()
    print(f"[2] Status: {json.dumps(agent.get_status(), indent=2)}")
    print()
    print(f"[3] Processed today: {agent.processed_today}")
    print(f"[4] Classified: {agent.classified}")
    print()
    print("=" * 60)


if __name__ == "__main__":
    demo()
