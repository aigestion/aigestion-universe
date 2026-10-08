"""Guardian: Protege el sistema y hace backups automáticos."""

import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from ..base import Agent


class GuardianAgent(Agent):
    """Agente que protege y hace backups."""

    def __init__(self, config: dict | None = None):
        super().__init__("guardian", config)
        self.backup_dir = Path(os.path.expanduser("~/backups/aig"))
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup_data(self) -> dict[str, Any]:
        """Hace backup de datos importantes."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"
            backup_path.mkdir(exist_ok=True)

            # Backup de data/
            data_dir = Path(os.path.expanduser("~/apps/aig/data"))
            if data_dir.exists():
                shutil.copytree(data_dir, backup_path / "data")

            # Backup de config/
            config_dir = Path(os.path.expanduser("~/apps/aig/config"))
            if config_dir.exists():
                shutil.copytree(config_dir, backup_path / "config")

            # Backup de phone/agents/logs/
            logs_dir = Path(os.path.expanduser("~/apps/aig/phone/agents/logs"))
            if logs_dir.exists():
                shutil.copytree(logs_dir, backup_path / "logs")

            return {"backup_path": str(backup_path), "status": "ok"}
        except Exception as e:
            self.log(f"Error en backup: {e}", "error")
            return {"error": str(e)}

    def check_security(self) -> dict[str, Any]:
        """Verifica la seguridad del sistema."""
        issues = []

        # Verificar permisos de .env
        env_file = Path(os.path.expanduser("~/apps/aig/.env"))
        if env_file.exists():
            stat = env_file.stat()
            if stat.st_mode & 0o077:
                issues.append(".env tiene permisos demasiado abiertos")

        # Verificar que .env.db no esté en el repo
        env_db = Path(os.path.expanduser("~/apps/aig/data/env.db"))
        if env_db.exists():
            # Verificar que esté en .gitignore
            gitignore = Path(os.path.expanduser("~/apps/aig/.gitignore"))
            if gitignore.exists():
                content = gitignore.read_text()
                if "data/env.db" not in content:
                    issues.append("data/env.db no está en .gitignore")

        return {"issues": issues, "status": "ok" if not issues else "warning"}

    def run(self) -> dict[str, Any]:
        """Ejecuta el ciclo de protección."""
        self.start()
        try:
            backup_result = self.backup_data()
            security_result = self.check_security()

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = "backup + security check"
            self.save_metrics()
            self.log("Backup y verificación de seguridad completados")
            return {"backup": backup_result, "security": security_result}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            self.log(f"Error: {e}", "error")
            return {"error": str(e)}
        finally:
            self.stop()
