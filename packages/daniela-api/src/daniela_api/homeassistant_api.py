"""Shim ADR-001: la implementacion vive en iot_hub.backends.homeassistant.

Se reimporta ``requests`` a proposito: los tests parchean
``api.homeassistant_api.requests.get/request`` y necesitan ese atributo en el
modulo. ``HomeAssistantAPI`` es el mismo objeto de clase, asi que el patch
afecta al backend canonico (modulo requests compartido).
"""

from __future__ import annotations

import requests  # noqa: F401  (targeto de patch en tests/api/)
from iot_hub.backends.homeassistant import HomeAssistantAPI

__all__ = ["HomeAssistantAPI"]
