"""Event bus for inter-service communication (NATS + in-memory fallback)."""

import json
import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

try:
    import nats
    from nats.js import JetStreamContext
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False

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

class EventBus:
    """NATS-based event bus for service communication."""

    def __init__(self, service_name: str, nats_url: str = "nats://localhost:4222"):
        self.service_name = service_name
        self.nats_url = nats_url
        self._conn = None
        self._js: JetStreamContext | None = None
        self._subscriptions: list[Any] = []
        self._connected = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> bool:
        """Connect to NATS server."""
        if not NATS_AVAILABLE:
            logger.warning("NATS not available, using in-memory bus")
            return False
        try:
            self._conn = await nats.connect(self.nats_url)
            self._js = self._conn.jetstream()
            self._connected = True
            return True
        except Exception as e:
            logger.warning(f"NATS connection failed: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from NATS."""
        if self._conn:
            await self._conn.close()
            self._connected = False

    async def publish(self, subject: str, event: Event) -> bool:
        """Publish event to subject."""
        if not self._conn:
            return False
        try:
            await self._conn.publish(f"{self.service_name}.{subject}", event.to_json().encode())
            return True
        except Exception:
            return False

    async def subscribe(self, subject: str, handler: Callable[[Event], Any], durable: str = None) -> bool:
        """Subscribe to subject with handler."""
        if not self._conn:
            return False
        try:
            if durable and self._js:
                sub = await self._js.subscribe(f"{self.service_name}.{subject}", durable=durable, cb=handler)
            else:
                sub = await self._conn.subscribe(f"{self.service_name}.{subject}", cb=handler)
            self._subscriptions.append(sub)
            return True
        except Exception:
            return False

    async def request(self, subject: str, event: Event, timeout: float = 5.0) -> Event | None:
        """Request-response pattern."""
        if not self._conn:
            return None
        try:
            response = await self._conn.request(f"{self.service_name}.{subject}", event.to_json().encode(), timeout=timeout)
            return Event(**json.loads(response.data))
        except Exception:
            return None

# Global event bus
_event_bus: EventBus | None = None

def get_event_bus(service_name: str, nats_url: str = None) -> EventBus:
    """Get or create global event bus."""
    global _event_bus
    if _event_bus is None:
        from shared.config import get_nats_url
        _event_bus = EventBus(service_name, nats_url or get_nats_url())
    return _event_bus
