"""Conector para MQTT - Mensajería IoT."""

import json
import os
from collections.abc import Callable
from typing import Any

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None


class MQTTConnector:
    """Conector para broker MQTT (Mosquitto)."""

    def __init__(self, host: str | None = None, port: int = 1883, username: str | None = None, password: str | None = None):
        self.host = host or os.getenv("MQTT_HOST", "localhost")
        self.port = port
        self.username = username or os.getenv("MQTT_USER", "")
        self.password = password or os.getenv("MQTT_PASSWORD", "")
        self.client = None
        self.connected = False

    def connect(self) -> bool:
        """Conecta al broker MQTT."""
        if mqtt is None:
            return False
        try:
            self.client = mqtt.Client()
            if self.username:
                self.client.username_pw_set(self.username, self.password)
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()
            self.connected = True
            return True
        except Exception:
            return False

    def disconnect(self):
        """Desconecta del broker."""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False

    def publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False) -> bool:
        """Publica un mensaje en un topic."""
        if not self.connected or not self.client:
            return False
        try:
            if isinstance(payload, (dict, list)):
                payload = json.dumps(payload)
            self.client.publish(topic, payload, qos=qos, retain=retain)
            return True
        except Exception:
            return False

    def subscribe(self, topic: str, callback: Callable[[str, Any], None], qos: int = 0):
        """Suscribe a un topic con callback."""
        if not self.connected or not self.client:
            return False
        try:
            self.client.subscribe(topic, qos)
            self.client.message_callback_add(topic, lambda c, u, m: callback(m.topic, json.loads(m.payload)))
            return True
        except Exception:
            return False
