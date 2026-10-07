"""
Daniela Core - Autonomous AI Service Management & Edge Orchestrator
Core package for Daniela OS: brain, memory, orchestrator, voice, persona, life.
"""

from .agents import AgentRegistry
from .api import create_app
from .brain import Brain
from .life import DigitalLife
from .memory import MemoryVault
from .orchestrator import Orchestrator
from .persona import PersonaManager
from .security import SecurityEngine
from .tools import ToolGateway
from .voice import VoiceEngine

__version__ = "0.1.0"
__all__ = [
    "AgentRegistry",
    "Brain",
    "DigitalLife",
    "MemoryVault",
    "Orchestrator",
    "PersonaManager",
    "SecurityEngine",
    "ToolGateway",
    "VoiceEngine",
    "create_app",
]
