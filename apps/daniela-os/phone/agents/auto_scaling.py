"""Auto-Escalado de Recursos.

Ajusta la frecuencia de agentes según recursos disponibles.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import psutil

from .base import Agent


class AutoScalingAgent(Agent):
    """Agente de auto-escalado."""

    def __init__(self, config: dict | None = None):
        super().__init__("auto_scaling", config)
        self.scaling_file = Path(__file__).parent / "scaling.json"
        self.scaling = self._load_scaling()

    def _load_scaling(self) -> dict:
        if self.scaling_file.exists():
            return json.loads(self.scaling_file.read_text())
        return {"rules": [], "last_check": None}

    def _save_scaling(self):
        self.scaling_file.write_text(json.dumps(self.scaling, indent=2))

    def get_resources(self) -> dict[str, Any]:
        """Obtiene recursos del sistema."""
        battery = None
        try:
            bat = psutil.sensors_battery()
            if bat:
                battery = bat.percent
        except (PermissionError, OSError):
            pass
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "battery_percent": battery,
        }

    def should_scale(self, resources: dict) -> bool:
        """Determina si se debe escalar."""
        if resources["cpu_percent"] > 80:
            return True
        if resources["memory_percent"] > 85:
            return True
        if resources.get("battery_percent") and resources["battery_percent"] < 20:
            return True
        return False

    def run(self) -> dict[str, Any]:
        """Ejecuta un ciclo de auto-escalado."""
        self.start()
        try:
            resources = self.get_resources()
            should_scale = self.should_scale(resources)

            self.scaling["last_check"] = datetime.now().isoformat()
            self.scaling["resources"] = resources
            self.scaling["should_scale"] = should_scale
            self._save_scaling()

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = (
                f"CPU: {resources['cpu_percent']}%, RAM: {resources['memory_percent']}%"
            )
            self.save_metrics()
            return {"resources": resources, "should_scale": should_scale}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            return {"error": str(e)}
        finally:
            self.stop()
