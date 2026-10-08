"""Builder: Construye herramientas y automatizaciones."""

from pathlib import Path
from typing import Any

from ..base import Agent


class BuilderAgent(Agent):
    """Agente que construye herramientas y automatizaciones."""

    def __init__(self, config: dict | None = None):
        super().__init__("builder", config)
        self.tools_dir = Path(__file__).parent / "tools"
        self.tools_dir.mkdir(exist_ok=True)

    def create_script(self, name: str, content: str) -> str:
        """Crea un script nuevo."""
        script_path = self.tools_dir / f"{name}.py"
        script_path.write_text(content)
        return str(script_path)

    def create_cron_job(self, name: str, schedule: str, command: str) -> bool:
        """Crea un cron job."""
        try:
            crontab = f"# AIG {name}\n{schedule} {command}\n"
            cron_file = self.tools_dir / f"cron_{name}.txt"
            cron_file.write_text(crontab)
            return True
        except Exception as e:
            self.log(f"Error creando cron: {e}", "error")
            return False

    def run(self) -> dict[str, Any]:
        """Ejecuta el ciclo de construcción."""
        self.start()
        try:
            # Crear herramientas pendientes
            tools = self.config.get("tools", [])
            created = []
            for tool in tools:
                path = self.create_script(tool["name"], tool["content"])
                created.append(path)

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(created)} herramientas"
            self.save_metrics()
            self.log(f"Herramientas creadas: {len(created)}")
            return {"created": created}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            self.log(f"Error: {e}", "error")
            return {"error": str(e)}
        finally:
            self.stop()
