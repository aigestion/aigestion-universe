"""Auto-Seguridad 24/7.

Escanea vulnerabilidades y auto-parchea dependencias.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Agent


class AutoSecurityAgent(Agent):
    """Agente de seguridad automática."""

    def __init__(self, config: dict | None = None):
        super().__init__("auto_security", config)
        self.vulnerabilities_file = Path(__file__).parent / "vulnerabilities.json"
        self.vulnerabilities = self._load_vulnerabilities()

    def _load_vulnerabilities(self) -> dict:
        if self.vulnerabilities_file.exists():
            return json.loads(self.vulnerabilities_file.read_text())
        return {"vulnerabilities": [], "last_scan": None}

    def _save_vulnerabilities(self):
        self.vulnerabilities_file.write_text(json.dumps(self.vulnerabilities, indent=2))

    def scan_vulnerabilities(self) -> list[dict]:
        """Escanea vulnerabilidades con safety."""
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                return json.loads(result.stdout) if result.stdout else []
        except Exception as e:
            self.log(f"Error escaneando: {e}", "error")
        return []

    def auto_patch(self) -> dict[str, Any]:
        """Auto-parchea dependencias vulnerables."""
        try:
            result = subprocess.run(
                ["pip", "install", "--upgrade", "-r", "requirements.txt"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            return {"success": result.returncode == 0, "output": result.stdout}
        except Exception as e:
            return {"error": str(e)}

    def run(self) -> dict[str, Any]:
        """Ejecuta un ciclo de seguridad."""
        self.start()
        try:
            vulnerabilities = self.scan_vulnerabilities()
            patch_result = self.auto_patch()

            self.vulnerabilities["vulnerabilities"] = vulnerabilities
            self.vulnerabilities["last_scan"] = datetime.now().isoformat()
            self._save_vulnerabilities()

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(vulnerabilities)} vulnerabilidades"
            self.save_metrics()
            return {"vulnerabilities": vulnerabilities, "patch": patch_result}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            return {"error": str(e)}
        finally:
            self.stop()
