# Migrated from aig/core/event_bus.py (legacy) — preserved as-is, see MIGRATION_PLAN.md.
"""
NATS Event Bus for aig - Event-driven architecture backbone.

Replaces direct HTTP calls with NATS JetStream for loose coupling.
Supports: publish/subscribe, request/reply, event streams, consumer groups.
"""

import asyncio
import json
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

try:
    import nats
    from nats.aio.client import Client as NATS
    from nats.js import JetStreamContext
    from nats.js.api import RetentionPolicy, StorageType, StreamConfig
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False
    nats = None
    JetStreamContext = None
    NATS = None



class EventType(Enum):
    """Standard event types."""
    COMMAND = "cmd"
    EVENT = "evt"
    QUERY = "qry"
    RESPONSE = "resp"


@dataclass
class Event:
    """Standard event structure with metadata for tracing."""
    event_type: str
    aggregate_id: str
    aggregate_type: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    version: int = 1
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> bytes:
        return json.dumps(asdict(self)).encode()

    @classmethod
    def from_json(cls, data: bytes) -> "Event":
        d = json.loads(data.decode())
        return cls(**d)

    def subject(self, service: str) -> str:
        """Generate NATS subject: evt.{service}.{event_type}.{aggregate_type}"""
        return f"evt.{service}.{self.event_type}.{self.aggregate_type.lower()}"


@dataclass
class Command:
    """Command structure for CQRS."""
    command_type: str
    aggregate_id: str
    aggregate_type: str
    payload: dict[str, Any]
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    metadata: dict[str, Any] = field(default_factory=dict)

    def subject(self, service: str) -> str:
        return f"cmd.{service}.{self.command_type.lower()}"


@dataclass
class Query:
    """Query structure for CQRS."""
    query_type: str
    aggregate_id: str | None = None
    aggregate_type: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")

    def subject(self, service: str) -> str:
        return f"qry.{service}.{self.query_type.lower()}"


class NATSEventBus:
    """
    NATS JetStream event bus for aig.

    Provides:
    - Publish/Subscribe with JetStream persistence
    - Request/Reply for CQRS commands/queries
    - Consumer groups for horizontal scaling
    - Dead letter handling
    """

    def __init__(
        self,
        nats_url: str = "nats://localhost:4222",
        service_name: str = "aig",
        streams: list[dict] | None = None
    ):
        if not NATS_AVAILABLE:
            raise RuntimeError("NATS not available. Install: pip install nats-py")

        self.nats_url = nats_url
        self.service_name = service_name
        self.custom_streams = streams or []

        self.nc: NATS | None = None
        self.js: JetStreamContext | None = None
        self._subscriptions: list[Any] = []
        self._connected = False
        self._reconnect_task: asyncio.Task | None = None

    @property
    def connected(self) -> bool:
        return self._connected and self.nc is not None and not self.nc.is_closed

    async def connect(self) -> None:
        """Connect to NATS and initialize JetStream."""
        if self.connected:
            return

        self.nc = await nats.connect(
            self.nats_url,
            reconnect_time_wait=2,
            max_reconnect_attempts=-1,
            disconnected_cb=self._on_disconnect,
            reconnected_cb=self._on_reconnect,
            error_cb=self._on_error
        )
        self.js = self.nc.jetstream()
        await self._create_streams()
        self._connected = True
        print(f"[EventBus] Connected to NATS at {self.nats_url}")

    def _get_default_streams(self) -> list[dict]:
        """Default stream configuration for aig services."""
        services = [
            "daniela", "hermes", "swarm", "orchestrator", "gateway",
            "infra", "agent", "security", "perf",
            "intel", "auto", "data", "secure", "devtools",
            "ecosystem", "ux", "scale", "chaos", "brand"
        ]

        streams = []
        for svc in services:
            streams.append({
                "name": f"EVT_{svc.upper()}",
                "subjects": [f"evt.{svc}.>", f"cmd.{svc}.>", f"qry.{svc}.>"],
                "retention": RetentionPolicy.LIMITS,
                "max_msgs": 1_000_000,
                "max_bytes": 1024 * 1024 * 1024,  # 1GB
                "storage": StorageType.FILE,
                "max_age": 604800,  # 7 days
                "max_msg_size": 1024 * 1024,  # 1MB
            })

        # System streams
        streams.extend([
            {
                "name": "EVT_SYSTEM",
                "subjects": ["evt.system.>", "cmd.system.>", "qry.system.>"],
                "retention": RetentionPolicy.LIMITS,
                "max_msgs": 100000,
                "max_bytes": 100 * 1024 * 1024,
            },
            {
                "name": "EVT_AUDIT",
                "subjects": ["evt.audit.>"],
                "retention": RetentionPolicy.LIMITS,
                "max_msgs": 1000000,
                "max_bytes": 5 * 1024 * 1024 * 1024,  # 5GB
                "max_age": 2592000,  # 30 days
            },
        ])

        # Add custom streams
        streams.extend(self.custom_streams)
        return streams

    async def _create_streams(self) -> None:
        """Create JetStream streams if they don't exist."""
        for stream_config in self._get_default_streams():
            name = stream_config.pop("name")
            try:
                await self.js.add_stream(name=name, config=StreamConfig(**stream_config))
                print(f"[EventBus] Created stream: {name}")
            except Exception as e:
                if "stream name already in use" not in str(e).lower():
                    print(f"[EventBus] Stream {name}: {e}")

    async def _on_disconnect(self) -> None:
        self._connected = False
        print("[EventBus] Disconnected from NATS")

    async def _on_reconnect(self) -> None:
        self._connected = True
        print("[EventBus] Reconnected to NATS")

    async def _on_error(self, e: Exception) -> None:
        print(f"[EventBus] Error: {e}")

    async def publish(self, subject: str, event: Event,
                     headers: dict[str, str] | None = None) -> str:
        """Publish event to NATS JetStream."""
        if not self.connected:
            await self.connect()

        ack = await self.js.publish(
            subject,
            event.to_json(),
            headers=headers or {}
        )
        return ack.seq

    async def publish_event(self, event: Event) -> str:
        """Publish event with auto-generated subject."""
        subject = event.subject(self.service_name)
        return await self.publish(subject, event)

    async def publish_command(self, command: Command) -> str:
        """Publish command with auto-generated subject."""
        subject = command.subject(self.service_name)
        event = Event(
            event_type="command",
            aggregate_id=command.aggregate_id,
            aggregate_type=command.aggregate_type,
            payload={"command": command.command_type, "data": command.payload},
            metadata={"command_id": command.command_id, **command.metadata}
        )
        return await self.publish(subject, event)

    async def request(self, subject: str, payload: dict[str, Any],
                     timeout: float = 30.0) -> Event | None:
        """Request-reply pattern for CQRS."""
        if not self.connected:
            await self.connect()

        try:
            response = await self.nc.request(subject, json.dumps(payload).encode(), timeout=timeout)
            return Event.from_json(response.data)
        except Exception as e:
            print(f"[EventBus] Request failed: {e}")
            return None

    async def subscribe(
        self,
        subject: str,
        handler: Callable[[Event], Any],
        queue: str | None = None,
        durable: str | None = None,
        deliver_policy: str = "all",
        ack_wait: int = 30,
        max_deliver: int = 3
    ) -> Any:
        """Subscribe to subject with consumer group support."""
        if not self.connected:
            await self.connect()

        sub = await self.js.subscribe(
            subject,
            cb=self._wrap_handler(handler),
            queue=queue,
            durable=durable,
            config={
                "ack_wait": ack_wait,
                "max_deliver": max_deliver,
                "deliver_policy": deliver_policy,
            }
        )
        self._subscriptions.append(sub)
        return sub

    def _wrap_handler(self, handler: Callable) -> Callable:
        async def wrapper(msg):
            try:
                event = Event.from_json(msg.data)
                await handler(event)
                await msg.ack()
            except Exception as e:
                print(f"[EventBus] Handler error: {e}")
                await msg.nak()
        return wrapper

    async def subscribe_commands(
        self,
        command_type: str,
        handler: Callable[[Command], Any],
        queue: str = "cmd_handlers"
    ) -> Any:
        """Subscribe to commands for this service."""
        subject = f"cmd.{self.service_name}.{command_type.lower()}"
        async def wrapped(event: Event):
            cmd = Command(
                command_type=event.event_type,
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                payload=event.payload.get("data", {}),
                metadata=event.metadata
            )
            return await handler(cmd)
        return await self.subscribe(subject, wrapped, queue=queue, durable=f"{queue}_{self.service_name}")

    async def subscribe_events(
        self,
        event_type: str,
        handler: Callable[[Event], Any],
        queue: str = "evt_handlers"
    ) -> Any:
        """Subscribe to events for this service."""
        subject = f"evt.{self.service_name}.{event_type.lower()}"
        return await self.subscribe(subject, handler, queue=queue, durable=f"{queue}_{self.service_name}")

    async def close(self) -> None:
        """Close all subscriptions and connection."""
        for sub in self._subscriptions:
            try:
                await sub.unsubscribe()
            except Exception:
                pass
        if self.nc and not self.nc.is_closed:
            await self.nc.close()
        self._connected = False
        print("[EventBus] Closed")


# Global instance
_global_bus: NATSEventBus | None = None


def get_event_bus(
    nats_url: str = "nats://localhost:4222",
    service_name: str = "aig"
) -> NATSEventBus:
    """Get or create global event bus instance."""
    global _global_bus
    if _global_bus is None:
        _global_bus = NATSEventBus(nats_url=nats_url, service_name=service_name)
    return _global_bus


async def close_event_bus() -> None:
    """Close global event bus."""
    global _global_bus
    if _global_bus:
        await _global_bus.close()
        _global_bus = None
