"""
Event triggers (Ideas 21-30).
Webhooks, file watchers, DB triggers, HTTP polling, email triggers,
cron triggers, message queues, manual triggers, composite triggers, debounce/throttle.
"""

import hashlib
import hmac
import json
import logging
import sqlite3
import threading
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    WEBHOOK = "webhook"
    FILE_SYSTEM = "file_system"
    DATABASE = "database"
    HTTP_POLL = "http_poll"
    EMAIL = "email"
    SCHEDULE = "schedule"
    MESSAGE_QUEUE = "message_queue"
    MANUAL = "manual"
    COMPOSITE = "composite"


class TriggerStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"


@dataclass
class Trigger:
    trigger_id: str
    name: str
    trigger_type: TriggerType
    config: dict[str, Any] = field(default_factory=dict)
    status: TriggerStatus = TriggerStatus.ACTIVE
    action_type: str | None = None
    action_params: dict[str, Any] = field(default_factory=dict)
    debounce_ms: int = 0
    throttle_ms: int = 0
    created_at: float = field(default_factory=time.time)
    last_fired: float | None = None
    fire_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["trigger_type"] = self.trigger_type.value
        d["status"] = self.status.value
        return d


class DebounceThrottle:
    """Idea 30: Debounce/throttle for triggers."""

    def __init__(self):
        self._last_fired: dict[str, float] = {}
        self._pending: dict[str, threading.Timer] = {}
        self._lock = threading.Lock()

    def debounce(self, trigger_id: str, delay_ms: int, callback: Callable):
        with self._lock:
            if trigger_id in self._pending:
                self._pending[trigger_id].cancel()
            timer = threading.Timer(delay_ms / 1000.0, callback)
            self._pending[trigger_id] = timer
            timer.start()

    def throttle(self, trigger_id: str, interval_ms: int) -> bool:
        with self._lock:
            now = time.time() * 1000
            last = self._last_fired.get(trigger_id, 0)
            if now - last >= interval_ms:
                self._last_fired[trigger_id] = now
                return True
            return False


class WebhookReceiver:
    """Idea 21: Webhook receiver (generic HTTP triggers)."""

    def __init__(self):
        self.endpoints: dict[str, dict[str, Any]] = {}

    def register(self, path: str, trigger_id: str,
                 secret: str | None = None, headers: dict | None = None):
        self.endpoints[path] = {
            "trigger_id": trigger_id,
            "secret": secret,
            "expected_headers": headers or {},
        }

    def unregister(self, path: str):
        self.endpoints.pop(path, None)

    def verify_signature(self, path: str, payload: bytes, signature: str) -> bool:
        endpoint = self.endpoints.get(path)
        if not endpoint or not endpoint["secret"]:
            return True
        expected = hashlib.sha256(
            endpoint["secret"].encode() + payload
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def handle_request(self, path: str, method: str, body: bytes,
                       headers: dict[str, str]) -> str | None:
        endpoint = self.endpoints.get(path)
        if not endpoint:
            return None
        if method != "POST":
            return None
        sig = headers.get("X-Hub-Signature-256", "")
        if endpoint["secret"] and not self.verify_signature(path, body, sig):
            return None
        return endpoint["trigger_id"]


class FileSystemWatcher:
    """Idea 22: File system watcher (new/modified/deleted)."""

    def __init__(self):
        self.watchers: dict[str, dict[str, Any]] = {}
        self._snapshots: dict[str, dict[str, float]] = {}
        self._running = False
        self._thread: threading.Thread | None = None

    def add_watch(self, trigger_id: str, path: str, events: list[str] | None = None):
        self.watchers[trigger_id] = {
            "path": path,
            "events": events or ["created", "modified", "deleted"],
        }
        self._take_snapshot(trigger_id)

    def remove_watch(self, trigger_id: str):
        self.watchers.pop(trigger_id, None)
        self._snapshots.pop(trigger_id, None)

    def _take_snapshot(self, trigger_id: str):
        watcher = self.watchers.get(trigger_id)
        if not watcher:
            return
        path = Path(watcher["path"])
        snapshot = {}
        if path.exists():
            if path.is_file():
                snapshot[str(path)] = path.stat().st_mtime
            elif path.is_dir():
                for f in path.rglob("*"):
                    if f.is_file():
                        snapshot[str(f)] = f.stat().st_mtime
        self._snapshots[trigger_id] = snapshot

    def check_changes(self) -> list[dict[str, Any]]:
        changes = []
        for trigger_id, watcher in self.watchers.items():
            old_snapshot = self._snapshots.get(trigger_id, {})
            current_snapshot = {}
            path = Path(watcher["path"])
            if path.exists():
                if path.is_file():
                    current_snapshot[str(path)] = path.stat().st_mtime
                elif path.is_dir():
                    for f in path.rglob("*"):
                        if f.is_file():
                            current_snapshot[str(f)] = f.stat().st_mtime

            for fpath in current_snapshot:
                if fpath not in old_snapshot and "created" in watcher["events"]:
                    changes.append({"trigger_id": trigger_id, "event": "created",
                                    "path": fpath})
                elif fpath in old_snapshot and current_snapshot[fpath] != old_snapshot[fpath]:
                    if "modified" in watcher["events"]:
                        changes.append({"trigger_id": trigger_id, "event": "modified",
                                        "path": fpath})

            for fpath in old_snapshot:
                if fpath not in current_snapshot and "deleted" in watcher["events"]:
                    changes.append({"trigger_id": trigger_id, "event": "deleted",
                                    "path": fpath})

            self._snapshots[trigger_id] = current_snapshot
        return changes


class DatabaseChangeTrigger:
    """Idea 23: Database change trigger (polling-based)."""

    def __init__(self, db_path: str = "trigger_watches.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS watches (
                trigger_id TEXT PRIMARY KEY, query TEXT, last_hash TEXT,
                poll_interval INTEGER DEFAULT 60)""")

    def register(self, trigger_id: str, query: str, poll_interval: int = 60):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT OR REPLACE INTO watches VALUES (?, ?, NULL, ?)",
                         (trigger_id, query, poll_interval))

    def unregister(self, trigger_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM watches WHERE trigger_id = ?", (trigger_id,))

    def check_changes(self, data_db_path: str) -> list[dict[str, Any]]:
        changes = []
        with sqlite3.connect(self.db_path) as conn:
            watches = conn.execute("SELECT * FROM watches").fetchall()
        for trigger_id, query, last_hash, _ in watches:
            try:
                with sqlite3.connect(data_db_path) as data_conn:
                    rows = data_conn.execute(query).fetchall()
                current_hash = hashlib.md5(
                    json.dumps(rows, default=str).encode()
                ).hexdigest()
                if last_hash and current_hash != last_hash:
                    changes.append({"trigger_id": trigger_id, "event": "data_changed",
                                    "rows": len(rows)})
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("UPDATE watches SET last_hash = ? WHERE trigger_id = ?",
                                 (current_hash, trigger_id))
            except Exception as e:
                logger.error(f"DB trigger {trigger_id} error: {e}")
        return changes


class HttpPollTrigger:
    """Idea 24: HTTP endpoint trigger (poll URL for changes)."""

    def __init__(self):
        self.endpoints: dict[str, dict[str, Any]] = {}
        self._last_etags: dict[str, str] = {}

    def register(self, trigger_id: str, url: str, method: str = "GET",
                 headers: dict | None = None, poll_interval: int = 60):
        self.endpoints[trigger_id] = {
            "url": url, "method": method,
            "headers": headers or {}, "poll_interval": poll_interval,
        }

    def unregister(self, trigger_id: str):
        self.endpoints.pop(trigger_id, None)
        self._last_etags.pop(trigger_id, None)

    def check(self, trigger_id: str, fetch_func: Callable | None = None) -> dict | None:
        endpoint = self.endpoints.get(trigger_id)
        if not endpoint:
            return None
        try:
            import urllib.request
            req = urllib.request.Request(
                endpoint["url"], method=endpoint["method"],
                headers=endpoint["headers"],
            )
            if trigger_id in self._last_etags:
                req.add_header("If-None-Match", self._last_etags[trigger_id])
            with urllib.request.urlopen(req, timeout=10) as resp:
                etag = resp.headers.get("ETag")
                if etag:
                    self._last_etags[trigger_id] = etag
                if resp.status == 200:
                    return {"trigger_id": trigger_id, "event": "changed",
                            "status": resp.status}
                return None
        except Exception as e:
            logger.error(f"HTTP poll {trigger_id} error: {e}")
            return None


class EmailTrigger:
    """Idea 25: Email trigger (IMAP monitoring)."""

    def __init__(self):
        self.mailboxes: dict[str, dict[str, Any]] = {}
        self._last_uids: dict[str, int] = {}

    def register(self, trigger_id: str, host: str, port: int, username: str,
                 password: str, folder: str = "INBOX",
                 subject_filter: str | None = None):
        self.mailboxes[trigger_id] = {
            "host": host, "port": port, "username": username,
            "password": password, "folder": folder,
            "subject_filter": subject_filter,
        }

    def unregister(self, trigger_id: str):
        self.mailboxes.pop(trigger_id, None)

    def check(self, trigger_id: str) -> list[dict[str, Any]]:
        mailbox = self.mailboxes.get(trigger_id)
        if not mailbox:
            return []
        try:
            import imaplib
            conn = imaplib.IMAP4_SSL(mailbox["host"], mailbox["port"])
            conn.login(mailbox["username"], mailbox["password"])
            conn.select(mailbox["folder"])
            last_uid = self._last_uids.get(trigger_id, 0)
            _, data = conn.search(None, f"UID {last_uid + 1}:*")
            messages = []
            for num in data[0].split():
                _, msg_data = conn.fetch(num, "(UID BODY[HEADER.FIELDS (SUBJECT)])")
                uid = int(msg_data[0][0].decode().split("UID")[1].split()[0])
                body = msg_data[0][1].decode(errors="ignore")
                subject = ""
                for line in body.split("\n"):
                    if line.lower().startswith("subject:"):
                        subject = line.split(":", 1)[1].strip()
                if uid > last_uid:
                    if (not mailbox["subject_filter"] or
                            mailbox["subject_filter"].lower() in subject.lower()):
                        messages.append({"trigger_id": trigger_id, "event": "new_email",
                                         "subject": subject, "uid": uid})
                    self._last_uids[trigger_id] = max(self._last_uids.get(trigger_id, 0), uid)
            conn.logout()
            return messages
        except Exception as e:
            logger.error(f"Email trigger {trigger_id} error: {e}")
            return []


class MessageQueueTrigger:
    """Idea 27: Message queue trigger (simple pub/sub)."""

    def __init__(self):
        self.subscriptions: dict[str, dict[str, Any]] = {}
        self._queues: dict[str, list[dict]] = {}
        self._lock = threading.Lock()

    def subscribe(self, trigger_id: str, channel: str, pattern: str | None = None):
        self.subscriptions[trigger_id] = {"channel": channel, "pattern": pattern}
        self._queues.setdefault(channel, [])

    def unsubscribe(self, trigger_id: str):
        # 2026-09-23: la unica linea del `if` era `queue = ...` sin usar
        # (F841); sin ella el `if` quedaba vacio. El pop ya hace el trabajo.
        self.subscriptions.pop(trigger_id, None)

    def publish(self, channel: str, message: dict[str, Any]):
        with self._lock:
            self._queues.setdefault(channel, []).append({
                "message": message, "timestamp": time.time(),
            })

    def consume(self, trigger_id: str) -> dict | None:
        sub = self.subscriptions.get(trigger_id)
        if not sub:
            return None
        with self._lock:
            queue = self._queues.get(sub["channel"], [])
            if queue:
                return queue.pop(0)
        return None


class CompositeTrigger:
    """Idea 29: Composite trigger (AND/OR logic)."""

    def __init__(self):
        self.composites: dict[str, dict[str, Any]] = {}
        self._fire_counts: dict[str, int] = {}
        self._lock = threading.Lock()

    def register(self, trigger_id: str, child_trigger_ids: list[str],
                 logic: str = "AND"):
        self.composites[trigger_id] = {
            "children": child_trigger_ids, "logic": logic.upper(),
        }
        self._fire_counts[trigger_id] = 0

    def unregister(self, trigger_id: str):
        self.composites.pop(trigger_id, None)
        self._fire_counts.pop(trigger_id, None)

    def child_fired(self, child_id: str) -> list[str]:
        fired_triggers = []
        with self._lock:
            for tid, comp in self.composites.items():
                if child_id in comp["children"]:
                    self._fire_counts[tid] = self._fire_counts.get(tid, 0) + 1
                    if comp["logic"] == "OR":
                        fired_triggers.append(tid)
                        self._fire_counts[tid] = 0
                    elif comp["logic"] == "AND":
                        if self._fire_counts[tid] >= len(comp["children"]):
                            fired_triggers.append(tid)
                            self._fire_counts[tid] = 0
        return fired_triggers

    def reset(self, trigger_id: str):
        self._fire_counts[trigger_id] = 0


class TriggerManager:
    """Trigger manager (Ideas 21-30)."""

    def __init__(self):
        self.triggers: dict[str, Trigger] = {}
        self.webhook = WebhookReceiver()
        self.file_watcher = FileSystemWatcher()
        self.db_trigger = DatabaseChangeTrigger()
        self.http_poll = HttpPollTrigger()
        self.email_trigger = EmailTrigger()
        self.message_queue = MessageQueueTrigger()
        self.composite = CompositeTrigger()
        self.debounce_throttle = DebounceThrottle()
        self._action_handlers: dict[str, Callable] = {}
        self._fire_log: list[dict[str, Any]] = []

    def register_action(self, action_type: str, handler: Callable):
        self._action_handlers[action_type] = handler

    def add_trigger(self, name: str, trigger_type: str, config: dict | None = None,
                    action_type: str | None = None,
                    action_params: dict | None = None,
                    debounce_ms: int = 0, throttle_ms: int = 0) -> Trigger:
        trigger = Trigger(
            trigger_id=str(uuid.uuid4()), name=name,
            trigger_type=TriggerType(trigger_type),
            config=config or {}, action_type=action_type,
            action_params=action_params or {},
            debounce_ms=debounce_ms, throttle_ms=throttle_ms,
        )
        self.triggers[trigger.trigger_id] = trigger

        if trigger_type == "webhook" and config:
            self.webhook.register(
                config.get("path", f"/trigger/{trigger.trigger_id}"),
                trigger.trigger_id, config.get("secret"),
            )
        elif trigger_type == "file_system" and config:
            self.file_watcher.add_watch(
                trigger.trigger_id, config.get("path", "."),
                config.get("events"),
            )
        elif trigger_type == "message_queue" and config:
            self.message_queue.subscribe(
                trigger.trigger_id, config.get("channel", "default"),
            )
        elif trigger_type == "composite" and config:
            self.composite.register(
                trigger.trigger_id,
                config.get("child_ids", []),
                config.get("logic", "AND"),
            )

        return trigger

    def remove_trigger(self, trigger_id: str) -> bool:
        trigger = self.triggers.pop(trigger_id, None)
        if trigger:
            if trigger.trigger_type == TriggerType.WEBHOOK:
                self.webhook.unregister(f"/trigger/{trigger_id}")
            elif trigger.trigger_type == TriggerType.FILE_SYSTEM:
                self.file_watcher.remove_watch(trigger_id)
            elif trigger.trigger_type == TriggerType.MESSAGE_QUEUE:
                self.message_queue.unsubscribe(trigger_id)
            elif trigger.trigger_type == TriggerType.COMPOSITE:
                self.composite.unregister(trigger_id)
            return True
        return False

    def pause_trigger(self, trigger_id: str) -> bool:
        trigger = self.triggers.get(trigger_id)
        if trigger:
            trigger.status = TriggerStatus.PAUSED
            return True
        return False

    def resume_trigger(self, trigger_id: str) -> bool:
        trigger = self.triggers.get(trigger_id)
        if trigger and trigger.status == TriggerStatus.PAUSED:
            trigger.status = TriggerStatus.ACTIVE
            return True
        return False

    def list_triggers(self, status: str | None = None,
                      trigger_type: str | None = None) -> list[dict]:
        triggers = list(self.triggers.values())
        if status:
            triggers = [t for t in triggers if t.status.value == status]
        if trigger_type:
            triggers = [t for t in triggers if t.trigger_type.value == trigger_type]
        return [t.to_dict() for t in triggers]

    def fire_trigger(self, trigger_id: str, payload: dict | None = None) -> dict[str, Any]:
        trigger = self.triggers.get(trigger_id)
        if not trigger:
            return {"error": "Trigger not found"}
        if trigger.status != TriggerStatus.ACTIVE:
            return {"error": "Trigger not active"}

        if trigger.throttle_ms > 0:
            if not self.debounce_throttle.throttle(trigger_id, trigger.throttle_ms):
                return {"status": "throttled"}

        now = time.time()
        trigger.last_fired = now
        trigger.fire_count += 1

        result = {
            "trigger_id": trigger_id,
            "fired_at": now,
            "payload": payload,
        }

        if trigger.action_type:
            handler = self._action_handlers.get(trigger.action_type)
            if handler:
                try:
                    action_result = handler({**trigger.action_params, **(payload or {})})
                    result["action_result"] = str(action_result)
                except Exception as e:
                    result["action_error"] = str(e)

        self._fire_log.append(result)
        return result

    def poll_all(self) -> list[dict[str, Any]]:
        events = []
        for tid, trigger in self.triggers.items():
            if trigger.status != TriggerStatus.ACTIVE:
                continue
            if trigger.trigger_type == TriggerType.FILE_SYSTEM:
                for change in self.file_watcher.check_changes():
                    if change["trigger_id"] == tid:
                        self.fire_trigger(tid, change)
                        events.append(change)
        return events

    def get_fire_log(self, trigger_id: str | None = None,
                     limit: int = 100) -> list[dict]:
        log = self._fire_log
        if trigger_id:
            log = [e for e in log if e.get("trigger_id") == trigger_id]
        return log[-limit:]
