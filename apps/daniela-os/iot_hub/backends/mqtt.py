"""Backend MQTT — envuelve connectors.mqtt_connector (paho, import-safe)."""

from __future__ import annotations

import socket
from typing import Any

from iot_hub import config


def _connector():
    """Import tardio: paho-mqtt es opcional (si falta, None)."""
    try:
        from connectors.iot.mqtt_connector import MQTTConnector
    except ImportError:
        return None
    return MQTTConnector(
        host=config.MQTT_HOST,
        port=config.MQTT_PORT,
        username=config.MQTT_USER or None,
        password=config.MQTT_PASSWORD or None,
    )


def _broker_probe(timeout: float = 0.8) -> bool:
    """Sondeo TCP barato al broker (sin paho, sin bloqueos largos)."""
    try:
        with socket.create_connection((config.MQTT_HOST, config.MQTT_PORT), timeout=timeout):
            return True
    except OSError:
        return False


def status() -> dict[str, Any]:
    """Estado del broker: configuracion + alcanzabilidad."""
    return {
        "host": config.MQTT_HOST,
        "port": config.MQTT_PORT,
        "topics": list(config.IOT_MQTT_TOPICS),
        "broker_reachable": _broker_probe(),
    }


def publish(topic: str, payload: Any, qos: int = 0) -> dict[str, Any]:
    """Publica en el broker (conexion corta: connect -> publish -> disconnect)."""
    conn = _connector()
    if conn is None:
        return {"ok": False, "error": "paho-mqtt no instalado"}
    if not conn.connect():
        return {"ok": False, "error": f"Broker {config.MQTT_HOST}:{config.MQTT_PORT} no alcanzable"}
    try:
        ok = conn.publish(topic, payload, qos=qos)
    finally:
        conn.disconnect()
    if ok:
        return {"ok": True, "topic": topic}
    return {"ok": False, "error": f"Fallo al publicar en {topic}"}
