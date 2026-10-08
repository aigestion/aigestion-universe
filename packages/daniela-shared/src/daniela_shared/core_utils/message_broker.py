"""
Inter-Agent Message Broker
==========================
JSON-based communication protocol so agents can talk to each other.

AGENT_CORREO can ask AGENT_DOCUMENTOS to draft a response.
AGENT_VIGIA can alert OPERATOR to take corrective action.
Daniela can broadcast tasks to the whole squad.

Features:
- In-memory queue + SQLite persistence
- Message priorities: URGENT (interrupts), NORMAL (queues)
- Patterns: request-response, fire-and-forget, broadcast
- Auto-logging to knowledge graph (when available)
- Thread-safe for concurrent agents

Usage:
    from message_broker import broker

    # Send a message
    broker.send("AGENT_CORREO", "AGENT_DOCUMENTOS",
               "draft_response",
               {"client": "ACME Corp", "topic": "invoice delay"})

    # Receive messages (blocking or non-blocking)
    msgs = broker.receive("AGENT_DOCUMENTOS")
    for msg in msgs:
        print(msg)
        broker.ack(msg["id"])
"""

import json
import os
import sqlite3
import threading
import time
import uuid
from datetime import datetime

# Raiz del repo: fuente unica en paths.py (BROKER_DB/LOG_DIR viven en data/core/).
# Fallback por fichero si paths.py no esta importable (p. ej. core/ suelto en sys.path).
try:
    from paths import BROKER_DB as _BROKER_DB
    from paths import LOG_DIR as _LOG_DIR
    BROKER_DB = os.fspath(_BROKER_DB)
    LOG_DIR = os.fspath(_LOG_DIR)
except ImportError:  # pragma: no cover
    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BROKER_DB = os.path.join(_REPO_ROOT, "data", "core", "agent_messages.db")
    LOG_DIR = os.path.join(_REPO_ROOT, "data", "core", "agent_activity")

# Ensure dirs exist
os.makedirs(os.path.dirname(BROKER_DB), exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Message types
MSG_TYPES = {
    "request": "Request another agent to do something",
    "response": "Reply to a request",
    "broadcast": "Message to all agents",
    "alert": "Urgent notification",
    "status": "Status update",
    "handoff": "Hand off a task to another agent",
    "collaborate": "Ask for collaborative help",
}

# Priorities
PRIORITY_URGENT = 0   # Interrupts current task
PRIORITY_HIGH = 1     # Processed before normal
PRIORITY_NORMAL = 2   # Standard queue
PRIORITY_LOW = 3      # Background


class AgentMessage:
    """A single message between agents."""

    def __init__(self, sender: str, recipient: str, msg_type: str,
                 payload: dict, priority: int = PRIORITY_NORMAL,
                 reply_to: str = None):
        self.id = str(uuid.uuid4())[:12]
        self.sender = sender
        self.recipient = recipient
        self.msg_type = msg_type
        self.payload = payload
        self.priority = priority
        self.reply_to = reply_to
        self.timestamp = datetime.now().isoformat()
        self.status = "pending"  # pending, delivered, acked, failed
        self.delivered_at = None
        self.acked_at = None

    def to_dict(self) -> dict:

        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "msg_type": self.msg_type,
            "payload": self.payload,
            "priority": self.priority,
            "reply_to": self.reply_to,
            "timestamp": self.timestamp,
            "status": self.status,
            "delivered_at": self.delivered_at,
            "acked_at": self.acked_at,
        }

    @classmethod
    def from_dict(cls, data: dict):

        msg = cls(
            sender=data["sender"],
            recipient=data["recipient"],
            msg_type=data["msg_type"],
            payload=data.get("payload", {}),
            priority=data.get("priority", PRIORITY_NORMAL),
            reply_to=data.get("reply_to"),
        )
        msg.id = data["id"]
        msg.timestamp = data["timestamp"]
        msg.status = data.get("status", "pending")
        msg.delivered_at = data.get("delivered_at")
        msg.acked_at = data.get("acked_at")
        return msg


class MessageBroker:
    """Thread-safe message broker for inter-agent communication."""

    def __init__(self, db_path: str = BROKER_DB):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()
        # In-memory subscriber callbacks (for real-time notifications)
        self._subscribers: dict[str, list] = {}
        # In-memory pending messages per agent
        self._queues: dict[str, list[AgentMessage]] = {}

    def _init_db(self):
        """Initialize SQLite database for message persistence."""
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    msg_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    priority INTEGER DEFAULT 2,
                    reply_to TEXT,
                    timestamp TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    delivered_at TEXT,
                    acked_at TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_recipient_status
                ON messages (recipient, status, priority)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON messages (timestamp DESC)
            """)
            conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def send(self, sender: str, recipient: str, msg_type: str,
             payload: dict, priority: int = PRIORITY_NORMAL,
             reply_to: str = None) -> str:
        """
        Send a message from one agent to another.

        Args:
            sender: Agent name sending the message
            recipient: Agent name receiving (or 'ALL' for broadcast)
            msg_type: Type of message (request, response, alert, etc.)
            payload: Message content dict
            priority: Message priority (0=urgent, 2=normal, 3=low)
            reply_to: Message ID this is replying to

        Returns:
            Message ID
        """
        msg = AgentMessage(sender, recipient, msg_type, payload, priority, reply_to)

        with self._lock:
            # Persist to SQLite
            with self._get_conn() as conn:
                conn.execute("""
                    INSERT INTO messages (id, sender, recipient, msg_type, payload,
                                         priority, reply_to, timestamp, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (msg.id, msg.sender, msg.recipient, msg.msg_type,
                      json.dumps(msg.payload), msg.priority, msg.reply_to,
                      msg.timestamp, msg.status))
                conn.commit()

            # Add to in-memory queue
            if recipient == "ALL":
                # Broadcast: add to all known agent queues
                for agent_name in self._queues:
                    self._queues[agent_name].append(msg)
                    self._queues[agent_name].sort(key=lambda m: m.priority)
            else:
                if recipient not in self._queues:
                    self._queues[recipient] = []
                self._queues[recipient].append(msg)
                self._queues[recipient].sort(key=lambda m: m.priority)

            # Notify subscribers
            if recipient in self._subscribers:
                for callback in self._subscribers[recipient]:
                    try:
                        callback(msg)
                    except Exception:
                        pass

        return msg.id

    def receive(self, agent_name: str, block: bool = False,
                timeout: float = 0) -> list[dict]:
        """
        Receive pending messages for an agent.

        Args:
            agent_name: Agent to get messages for
            block: If True, wait for messages
            timeout: Max seconds to block (0 = indefinite)

        Returns:
            List of message dicts
        """
        if agent_name not in self._queues:
            self._queues[agent_name] = []

        if block:
            start = time.time()
            while not self._queues[agent_name]:
                if timeout > 0 and (time.time() - start) > timeout:
                    break
                time.sleep(0.1)

        with self._lock:
            messages = []
            while self._queues[agent_name]:
                msg = self._queues[agent_name].pop(0)
                msg.status = "delivered"
                msg.delivered_at = datetime.now().isoformat()

                # Update in DB
                with self._get_conn() as conn:
                    conn.execute("""
                        UPDATE messages SET status='delivered', delivered_at=?
                        WHERE id=?
                    """, (msg.delivered_at, msg.id))
                    conn.commit()

                messages.append(msg.to_dict())

        return messages

    def ack(self, msg_id: str, result: dict = None):
        """Acknowledge a message was processed."""
        with self._lock:
            with self._get_conn() as conn:
                acked_at = datetime.now().isoformat()
                conn.execute("""
                    UPDATE messages SET status='acked', acked_at=?
                    WHERE id=?
                """, (acked_at, msg_id))

                if result:
                    # Store result in payload
                    row = conn.execute(
                        "SELECT payload FROM messages WHERE id=?", (msg_id,)
                    ).fetchone()
                    if row:
                        payload = json.loads(row["payload"])
                        payload["_result"] = result
                        conn.execute("""
                            UPDATE messages SET payload=?
                            WHERE id=?
                        """, (json.dumps(payload), msg_id))
                conn.commit()

    def subscribe(self, agent_name: str, callback):
        """Register a callback for real-time message notifications."""
        if agent_name not in self._subscribers:
            self._subscribers[agent_name] = []
        self._subscribers[agent_name].append(callback)

    def get_history(self, agent_name: str = None, limit: int = 50) -> list[dict]:
        """Get message history from database."""
        with self._get_conn() as conn:
            if agent_name:
                rows = conn.execute("""
                    SELECT * FROM messages
                    WHERE sender=? OR recipient=? OR recipient='ALL'
                    ORDER BY timestamp DESC LIMIT ?
                """, (agent_name, agent_name, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM messages
                    ORDER BY timestamp DESC LIMIT ?
                """, (limit,)).fetchall()

        return [dict(row) for row in rows]

    def get_pending_count(self, agent_name: str = None) -> int:
        """Get count of pending messages."""
        with self._get_conn() as conn:
            if agent_name:
                row = conn.execute("""
                    SELECT COUNT(*) as count FROM messages
                    WHERE recipient=? AND status='pending'
                """, (agent_name,)).fetchone()
            else:
                row = conn.execute("""
                    SELECT COUNT(*) as count FROM messages
                    WHERE status='pending'
                """).fetchone()
        return row["count"]

    def get_stats(self) -> dict:
        """Get broker statistics."""
        with self._get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()["c"]
            pending = conn.execute(
                "SELECT COUNT(*) as c FROM messages WHERE status='pending'"
            ).fetchone()["c"]
            delivered = conn.execute(
                "SELECT COUNT(*) as c FROM messages WHERE status='delivered'"
            ).fetchone()["c"]
            acked = conn.execute(
                "SELECT COUNT(*) as c FROM messages WHERE status='acked'"
            ).fetchone()["c"]
            urgent = conn.execute(
                "SELECT COUNT(*) as c FROM messages WHERE priority=0"
            ).fetchone()["c"]

            # Messages by agent
            by_agent = conn.execute("""
                SELECT sender, COUNT(*) as c
                FROM messages
                GROUP BY sender
                ORDER BY c DESC
            """).fetchall()

        return {
            "total_messages": total,
            "pending": pending,
            "delivered": delivered,
            "acked": acked,
            "urgent": urgent,
            "by_sender": {row["sender"]: row["c"] for row in by_agent},
            "active_queues": list(self._queues.keys()),
            "queue_sizes": {k: len(v) for k, v in self._queues.items()},
        }


class ActivityLogger:
    """Logs agent activity to JSON for storyboard generation."""

    def __init__(self, log_dir: str = LOG_DIR):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    def log(self, agent_name: str, action: str, details: dict):
        """Log an agent action."""
        entry = {
            "agent": agent_name,
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }

        log_file = os.path.join(self.log_dir, f"{agent_name}_activity.jsonl")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_recent(self, agent_name: str, limit: int = 10) -> list[dict]:
        """Get recent activity for an agent."""
        log_file = os.path.join(self.log_dir, f"{agent_name}_activity.jsonl")
        if not os.path.exists(log_file):
            return []

        entries = []
        with open(log_file, encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                if line.strip():
                    entries.append(json.loads(line))
        return entries

    def get_all_recent(self, limit: int = 50) -> dict[str, list[dict]]:
        """Get recent activity for all agents."""
        result = {}
        for fname in os.listdir(self.log_dir):
            if fname.endswith("_activity.jsonl"):
                agent = fname.replace("_activity.jsonl", "")
                result[agent] = self.get_recent(agent, limit)
        return result


# Singleton instances
broker = MessageBroker()
activity = ActivityLogger()


def demo():
    """Demo the message broker."""
    print("=" * 60)
    print("INTER-AGENT MESSAGE BROKER - DEMO")
    print("=" * 60)
    print()

    # Clear old messages
    with broker._get_conn() as conn:
        conn.execute("DELETE FROM messages")
        conn.commit()

    print("[1] Sending messages between agents...")
    print()

    # AGENT_VIGIA detects anomaly, alerts OPERATOR
    msg_id = broker.send(
        "AGENT_VIGIA", "OPERATOR", "alert",
        {"anomaly": "CPU spike 95%", "server": "localhost:5050",
         "action": "investigate"},
        priority=PRIORITY_URGENT
    )
    print(f"  VIGIA -> OPERATOR: alert (CPU spike) [urgent] id={msg_id}")

    # AGENT_CORREO asks AGENT_DOCUMENTOS to draft response
    msg_id = broker.send(
        "AGENT_CORREO", "AGENT_DOCUMENTOS", "request",
        {"task": "draft_email_response", "client": "ACME Corp",
         "topic": "invoice delay", "tone": "professional"},
        priority=PRIORITY_NORMAL
    )
    print(f"  CORREO -> DOCUMENTOS: request (draft response) [normal] id={msg_id}")

    # Daniela broadcasts to all
    msg_id = broker.send(
        "DANIELA", "ALL", "broadcast",
        {"task": "daily_briefing", "time": "09:00",
         "topics": ["pending emails", "calendar conflicts", "content calendar"]},
        priority=PRIORITY_HIGH
    )
    print(f"  DANIELA -> ALL: broadcast (daily briefing) [high] id={msg_id}")

    # AGENT_DOCUMENTOS responds to CORREO
    msg_id = broker.send(
        "AGENT_DOCUMENTOS", "AGENT_CORREO", "response",
        {"status": "drafted", "preview": "Estimado cliente de ACME Corp...",
         "word_count": 145},
        priority=PRIORITY_NORMAL,
        reply_to=msg_id
    )
    print(f"  DOCUMENTOS -> CORREO: response (draft ready) [normal] id={msg_id}")

    print()
    print("[2] OPERATOR receiving messages...")
    msgs = broker.receive("OPERATOR")
    for m in msgs:
        print(f"  [{m['msg_type'].upper()}] from {m['sender']}: {m['payload']}")
        broker.ack(m["id"])
    print(f"  Acked {len(msgs)} messages")

    print()
    print("[3] DOCUMENTOS receiving messages...")
    msgs = broker.receive("AGENT_DOCUMENTOS")
    for m in msgs:
        print(f"  [{m['msg_type'].upper()}] from {m['sender']}: {m['payload']}")
        broker.ack(m["id"])
    print(f"  Acked {len(msgs)} messages")

    print()
    print("[4] Broker statistics:")
    stats = broker.get_stats()
    print(f"  Total messages: {stats['total_messages']}")
    print(f"  Pending: {stats['pending']}")
    print(f"  Acked: {stats['acked']}")
    print(f"  By sender: {stats['by_sender']}")

    print()
    print("[5] Activity logging demo:")
    activity.log("AGENT_CORREO", "classify_email",
                 {"from": "cliente@acme.com", "subject": "Factura atrasada",
                  "classification": "urgent", "priority": 9})
    activity.log("AGENT_CORREO", "auto_respond",
                 {"drafted_by": "AGENT_DOCUMENTOS", "sent": True})
    recent = activity.get_recent("AGENT_CORREO", 5)
    print(f"  Logged {len(recent)} activities for AGENT_CORREO")
    for r in recent:
        print(f"  - {r['action']}: {r['details']}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    demo()


# =============================================================================
# Event Bus Compatibility Layer (from shared.events)
# =============================================================================

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger("aig.events")

@dataclass
class Event:
    """Standard event structure."""
    type: str
    payload: dict[str, Any]
    source: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    correlation_id: str | None = None

    def to_json(self) -> str:
        return json.dumps(asdict(self))

class InMemoryEventBus:
    """In-memory event bus for local development/testing."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._subscriptions: dict[str, list[Callable]] = defaultdict(list)
        self._connected = True

    @property
    def is_connected(self) -> bool:
        return self._connected

    def publish_sync(self, subject: str, event: Event) -> bool:
        """Publish event synchronously."""
        full_subject = f"{self.service_name}.{subject}"
        for handler in self._subscriptions.get(full_subject, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler error for {full_subject}: {e}")
        return True

    def subscribe_sync(self, subject: str, handler: Callable[[Event], Any]) -> bool:
        """Subscribe synchronously."""
        full_subject = f"{self.service_name}.{subject}"
        self._subscriptions[full_subject].append(handler)
        return True

# Global in-memory event bus
_in_memory_bus: InMemoryEventBus | None = None

def get_in_memory_bus(service_name: str) -> InMemoryEventBus:
    """Get or create global in-memory event bus."""
    global _in_memory_bus
    if _in_memory_bus is None:
        _in_memory_bus = InMemoryEventBus(service_name)
    return _in_memory_bus
