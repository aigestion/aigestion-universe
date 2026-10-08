"""
aig Auto Engine - Automation & Workflow Platform
50 epic automation ideas in one package.
"""

__version__ = "1.0.0"
__author__ = "aig"

from .actions import ActionLibrary
from .integrations import IntegrationManager
from .scheduler import TaskScheduler
from .triggers import TriggerManager
from .workflow_engine import WorkflowEngine

__all__ = [
    "WorkflowEngine",
    "TaskScheduler",
    "TriggerManager",
    "ActionLibrary",
    "IntegrationManager",
]
