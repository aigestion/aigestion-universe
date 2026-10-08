"""API endpoints for Android app."""
from .termux_api_gateway import app as termux_app

__all__ = ["termux_app"]