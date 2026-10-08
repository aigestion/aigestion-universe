"""Cross-Engine Integration System - Connects all 19 aig engines via central event bus."""

__version__ = "1.0.0"

from .connector import EngineConnector
from .event_bus import CrossEngineEventBus
from .orchestrator import CrossEngineOrchestrator
from .protocols import EVENT_TYPES, get_event_category, validate_event_type

__all__ = [
    "CrossEngineEventBus",
    "CrossEngineOrchestrator",
    "EngineConnector",
    "EVENT_TYPES",
    "validate_event_type",
    "get_event_category",
]
