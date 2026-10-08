"""Sandbox: Ejecuta pruebas en entorno aislado."""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from ..base import Agent


class SandboxAgent(Agent):
    """Agente que ejecuta pruebas en sandbox."""

    def __init__(self, config: dict | None = None):
        super().__init__("sandbox", config)
        self.sandbox_dir = Path("/tmp/aig_sandbox")
        self.sandbox_dir.mkdir(exist_ok=True)

    def run_test(self, code: str) -> dict[str, Any]:
        """Ejecuta código en sandbox."""
        try:
            # Crear archivo temporal
            test_file = self.sandbox_dir / f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
            test_file.write_text(code)

            # Ejecutar con timeout
            result = subprocess.run(
                ["python3", str(test_file)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.sandbox_dir),
            )

            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": "ok" if result.returncode == 0 else "error",
            }
        except Exception as e:
            return {"error": str(e)}

    def run(self) -> dict[str, Any]:
        """Ejecuta pruebas del sandbox."""
        self.start()
        try:
            tests = self.config.get("tests", [])
            results = []
            for test in tests:
                result = self.run_test(test["code"])
                results.append(result)

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(results)} pruebas"
            self.save_metrics()
            self.log(f"Pruebas ejecutadas: {len(results)}")
            return {"results": results}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            self.log(f"Error: {e}", "error")
            return {"error": str(e)}
        finally:
            self.stop()
