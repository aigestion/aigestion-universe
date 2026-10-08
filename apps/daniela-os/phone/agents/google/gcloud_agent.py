"""Agente Google Cloud: usa gcloud CLI para controlar servicios de Google."""

import os
import subprocess
from pathlib import Path
from typing import Any

from .base import GoogleAgent


class GCloudAgent(GoogleAgent):
    """Agente que usa gcloud CLI para controlar Google Cloud."""

    def __init__(self, config: dict | None = None):
        super().__init__("gcloud", config)
        self.gcloud_path = self._find_gcloud()

    def _find_gcloud(self) -> str | None:
        """Busca el binario de gcloud."""
        paths = [
            "/tmp/opencode/google-cloud-sdk/bin/gcloud",
            "/usr/bin/gcloud",
            "/usr/local/bin/gcloud",
            os.path.expanduser("~/google-cloud-sdk/bin/gcloud"),
        ]
        for path in paths:
            if Path(path).exists():
                return path
        return None

    def _run_gcloud(self, args: list[str]) -> dict[str, Any]:
        """Ejecuta un comando gcloud."""
        if not self.gcloud_path:
            return {"error": "gcloud no encontrado"}
        try:
            cmd = [self.gcloud_path] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except Exception as e:
            return {"error": str(e)}

    def auth_status(self) -> dict[str, Any]:
        """Verifica el estado de autenticación."""
        return self._run_gcloud(["auth", "list"])

    def set_project(self, project_id: str) -> dict[str, Any]:
        """Establece el proyecto activo."""
        return self._run_gcloud(["config", "set", "project", project_id])

    def list_projects(self) -> dict[str, Any]:
        """Lista proyectos disponibles."""
        return self._run_gcloud(["projects", "list", "--format=json"])

    def list_services(self) -> dict[str, Any]:
        """Lista servicios de Google Cloud."""
        return self._run_gcloud(["services", "list", "--available", "--format=json"])

    def enable_service(self, service: str) -> dict[str, Any]:
        """Habilita un servicio."""
        return self._run_gcloud(["services", "enable", service])

    def run(self) -> dict[str, Any]:
        """Ejecuta verificación de estado."""
        self.start()
        try:
            auth = self.auth_status()
            projects = self.list_projects()
            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.save_metrics()
            return {"auth": auth, "projects": projects}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            return {"error": str(e)}
        finally:
            self.stop()
