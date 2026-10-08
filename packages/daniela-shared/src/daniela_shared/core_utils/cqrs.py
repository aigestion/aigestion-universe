"""
CQRS (Command Query Responsibility Segregation) for aig.

Separates write (commands) and read (queries) models for scalability.
"""

import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar

from core.event_bus import Command, Event, NATSEventBus, Query, get_event_bus
from core.event_store import EventStore, get_event_store

TCommand = TypeVar("TCommand", bound="Command")
TQuery = TypeVar("TQuery", bound="Query")
TEvent = TypeVar("TEvent", bound="Event")


class CommandResult:
    """Result of command execution."""
    def __init__(
        self,
        success: bool,
        aggregate_id: str = "",
        version: int = 0,
        events: list = None,
        error: str = None
    ):
        self.success = success
        self.aggregate_id = aggregate_id
        self.version = version
        self.events = events or []
        self.error = error


class QueryResult:
    """Result of query execution."""
    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: str = None
    ):
        self.success = success
        self.data = data
        self.error = error


class CommandHandler(ABC):
    """Base command handler."""

    def __init__(self, event_store: EventStore, event_bus: NATSEventBus):
        self.store = event_store
        self.bus = event_bus

    @abstractmethod
    async def handle(self, command: Command) -> CommandResult:
        pass

    def _validate(self, command: Command) -> str | None:
        """Validate command. Return error message if invalid."""
        return None

    def _save_events(
        self,
        aggregate_id: str,
        aggregate_type: str,
        events: list,
        expected_version: int
    ) -> int:
        """Save events and publish to event bus."""
        stream = f"{aggregate_type}-{aggregate_id}"
        new_version = self.store.append(stream, events, expected_version)

        # Publish to event bus
        for event in events:
            asyncio.create_task(self.bus.publish_event(event))

        return new_version


class QueryHandler(ABC):
    """Base query handler."""

    def __init__(self, event_store: EventStore, read_models: dict[str, Any]):
        self.store = event_store
        self.read_models = read_models

    @abstractmethod
    async def handle(self, query: Query) -> QueryResult:
        pass


# ─── Command Dispatcher ───

class CommandDispatcher:
    """Routes commands to handlers."""

    def __init__(self, event_store: EventStore, event_bus: NATSEventBus):
        self.store = event_store
        self.bus = event_bus
        self._handlers: dict[str, CommandHandler] = {}

    def register(self, command_type: str, handler: CommandHandler) -> None:
        self._handlers[command_type] = handler

    async def dispatch(self, command: Command) -> CommandResult:
        handler = self._handlers.get(command.command_type)
        if not handler:
            return CommandResult(
                success=False,
                error=f"No handler for command: {command.command_type}"
            )

        # Validate
        error = handler._validate(command)
        if error:
            return CommandResult(success=False, error=error)

        # Execute
        return await handler.handle(command)


# ─── Query Dispatcher ───

class QueryDispatcher:
    """Routes queries to handlers."""

    def __init__(self, event_store: EventStore, read_models: dict[str, Any]):
        self.store = event_store
        self.read_models = read_models
        self._handlers: dict[str, QueryHandler] = {}

    def register(self, query_type: str, handler: QueryHandler) -> None:
        self._handlers[query_type] = handler

    async def dispatch(self, query: Query) -> QueryResult:
        handler = self._handlers.get(query.query_type)
        if not handler:
            return QueryResult(
                success=False,
                error=f"No handler for query: {query.query_type}"
            )
        return await handler.handle(query)


# ─── Example: User Aggregate ───

@dataclass
class UserState:
    """User aggregate state."""
    id: str
    email: str
    name: str
    created_at: str
    updated_at: str
    version: int = 0


class RegisterUserCommand(Command):
    """Register new user command."""
    def __init__(self, email: str, name: str, aggregate_id: str = None):
        aid = aggregate_id or str(uuid.uuid4())
        super().__init__(
            command_type="RegisterUser",
            aggregate_id=aid,
            aggregate_type="User",
            payload={"email": email, "name": name}
        )


class UserRegistered(Event):
    """User registered event."""
    def __init__(self, aggregate_id: str, email: str, name: str, version: int):
        super().__init__(
            event_type="UserRegistered",
            aggregate_id=aggregate_id,
            aggregate_type="User",
            payload={"email": email, "name": name},
            version=version
        )


class UserAggregate:
    """User aggregate with event sourcing."""

    def __init__(self, aggregate_id: str):
        self.id = aggregate_id
        self.state = UserState(id=aggregate_id, email="", name="", created_at="", updated_at="")
        self.version = 0
        self._pending_events: list[Event] = []

    def register(self, email: str, name: str) -> None:
        """Register new user."""
        if self.state.email:
            raise ValueError("User already registered")

        event = UserRegistered(
            aggregate_id=self.id,
            email=email,
            name=name,
            version=self.version + 1
        )
        self._apply(event)
        self._pending_events.append(event)

    def _apply(self, event: Event) -> None:
        """Apply event to state."""
        if event.event_type == "UserRegistered":
            self.state.email = event.payload["email"]
            self.state.name = event.payload["name"]
            self.state.created_at = event.timestamp
            self.state.updated_at = event.timestamp
            self.version = event.version

    def get_pending_events(self) -> list[Event]:
        return self._pending_events

    def clear_pending_events(self) -> None:
        self._pending_events = []

    def get_state(self) -> dict[str, Any]:
        return {
            "id": self.state.id,
            "email": self.state.email,
            "name": self.state.name,
            "created_at": self.state.created_at,
            "updated_at": self.state.updated_at,
            "version": self.version
        }


class RegisterUserHandler(CommandHandler):
    """Handler for RegisterUser command."""

    async def handle(self, command: RegisterUserCommand) -> CommandResult:
        # Check if user exists
        existing = self.store.read_aggregate(command.aggregate_id, "User")
        if existing:
            return CommandResult(success=False, error="User already exists")

        # Create aggregate
        aggregate = UserAggregate(command.aggregate_id)
        aggregate.register(command.payload["email"], command.payload["name"])

        # Save events
        events = aggregate.get_pending_events()
        new_version = self._save_events(
            command.aggregate_id, "User", events, 0
        )

        aggregate.clear_pending_events()

        return CommandResult(
            success=True,
            aggregate_id=command.aggregate_id,
            version=new_version,
            events=events
        )


# ─── Query Handlers ───

@dataclass
class GetUserQuery(Query):
    """Get user by ID query."""
    def __init__(self, user_id: str):
        super().__init__(
            query_type="GetUser",
            aggregate_id=user_id,
            aggregate_type="User"
        )


class GetUserHandler(QueryHandler):
    """Handler for GetUser query."""

    async def handle(self, query: GetUserQuery) -> QueryResult:
        # Try read model first
        read_model = self.read_models.get("users")
        if read_model and query.aggregate_id in read_model:
            return QueryResult(success=True, data=read_model[query.aggregate_id])

        # Fallback to event store reconstruction
        events = self.store.read_aggregate(query.aggregate_id, "User")
        if not events:
            return QueryResult(success=False, error="User not found")

        # Reconstruct state
        state = {}
        for event in events:
            state.update(event.payload)

        return QueryResult(success=True, data={"id": query.aggregate_id, **state})


# ─── CQRS Facade ───

class CQRS:
    """
    Main CQRS facade for aig.

    Usage:
        cqrs = CQRS()
        await cqrs.execute(RegisterUserCommand(email="x@y.com", name="John"))
        result = await cqrs.query(GetUserQuery(user_id="..."))
    """

    def __init__(
        self,
        event_store: EventStore | None = None,
        event_bus: NATSEventBus | None = None
    ):
        self.store = event_store or get_event_store()
        self.bus = event_bus or get_event_bus()

        self.commands = CommandDispatcher(self.store, self.bus)
        self.queries = QueryDispatcher(self.store, {})

        # Register default handlers
        self.commands.register("RegisterUser", RegisterUserHandler(self.store, self.bus))
        self.queries.register("GetUser", GetUserHandler(self.store, self.queries.read_models))

    async def execute(self, command: Command) -> CommandResult:
        """Execute a command."""
        return await self.commands.dispatch(command)

    async def query(self, query: Query) -> QueryResult:
        """Execute a query."""
        return await self.queries.dispatch(query)

    def register_command(self, command_type: str, handler: CommandHandler) -> None:
        self.commands.register(command_type, handler)

    def register_query(self, query_type: str, handler: QueryHandler) -> None:
        self.queries.register(query_type, handler)

    def register_read_model(self, name: str, model: dict[str, Any]) -> None:
        self.queries.read_models[name] = model


# ─── Global Instance ───

_global_cqrs: CQRS | None = None


def get_cqrs() -> CQRS:
    """Get or create global CQRS instance."""
    global _global_cqrs
    if _global_cqrs is None:
        _global_cqrs = CQRS()
    return _global_cqrs
