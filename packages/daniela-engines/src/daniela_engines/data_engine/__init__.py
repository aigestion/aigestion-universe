"""Data Engine - 50 Data & Analytics ideas for the aig monorepo."""

__version__ = "1.0.0"
__author__ = "aig Team"

from .analytics import *  # noqa: F403
from .pipeline import *  # noqa: F403
from .reports import *  # noqa: F403
from .storage import *  # noqa: F403
from .visualization import *  # noqa: F403

__all__ = ["__version__"]
