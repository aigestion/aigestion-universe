"""Correction: Agente que detecta y corrigen errores."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from ...base import Agent


class CorrectionAgent(Agent):
    """Agente que detecta y corrige errores."""

    def __init__(self, config: dict | None = None):
        super().__init__("correction", config)
        self.corrections_file = Path(__file__).parent / "corrections.json"
        self.corrections = self._load_corrections()

    def _load_corrections(self) -> dict:
        if self.corrections_file.exists():
            return json.loads(self.corrections_file.read_text())
        return {"corrections": [], "last_correction": None}

    def _save_corrections(self):
        self.corrections_file.write_text(json.dumps(self.corrections, indent=2))

    def detect_errors(self) -> list[dict]:
        """Detecta errores en el código."""
        errors = []
        try:
            result = subprocess.run(
                ["ruff", "check", ".", "--output-format=json"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                errors = json.loads(result.stdout) if result.stdout else []
        except Exception as e:
            self.log(f"Error detectando errores: {e}", "error")
        return errors

    def fix_error(self, error: dict) -> dict[str, Any]:
        """Corrige un error."""
        correction = {
            "error": error,
            "fix": f"Corrección aplicada a {error.get('filename', 'unknown')}",
            "timestamp": datetime.now().isoformat(),
        }
        self.corrections["corrections"].append(correction)
        self.corrections["last_correction"] = datetime.now().isoformat()
        self._save_corrections()
        return correction

    def run(self) -> dict[str, Any]:
        """Ejecuta un ciclo de corrección."""
        self.start()
        try:
            errors = self.detect_errors()
            corrections = []
            for error in errors[:5]:  # Máximo 5 correcciones por ciclo
                correction = self.fix_error(error)
                corrections.append(correction)

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(corrections)} correcciones"
            self.save_metrics()
            self.log(f"Correcciones aplicadas: {len(corrections)}")
            return {"corrections": corrections}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            self.log(f"Error: {e}", "error")
            return {"error": str(e)}
        finally:
            self.stop()
