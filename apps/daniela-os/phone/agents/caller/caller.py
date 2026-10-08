"""Caller: Realiza llamadas telefónicas automáticamente."""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from ..base import Agent


class CallerAgent(Agent):
    """Agente que realiza llamadas telefónicas."""

    def __init__(self, config: dict | None = None):
        super().__init__("caller", config)
        self.calls_file = Path(__file__).parent / "calls.json"
        self.calls = self._load_calls()

    def _load_calls(self) -> dict:
        if self.calls_file.exists():
            return json.loads(self.calls_file.read_text())
        return {"calls": [], "last_call": None}

    def _save_calls(self):
        self.calls_file.write_text(json.dumps(self.calls, indent=2))

    def make_call(self, phone_number: str, message: str) -> bool:
        """Realiza una llamada usando Twilio o Termux."""
        try:
            # Intentar con Termux primero (gratis)
            cmd = [
                "termux-telephony-call",
                "-n",
                phone_number,
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return True

            # Fallback a Twilio
            from twilio.rest import Client

            client = Client(
                os.getenv("TWILIO_SID"),
                os.getenv("TWILIO_TOKEN"),
            )
            call = client.calls.create(
                to=phone_number,
                from_=os.getenv("TWILIO_PHONE"),
                twiml=f"<Response><Say>{message}</Say></Response>",
            )
            return call.sid is not None
        except Exception as e:
            self.log(f"Error en llamada: {e}", "error")
            return False

    def run(self) -> dict[str, Any]:
        """Ejecuta el ciclo de llamadas."""
        self.start()
        try:
            # Obtener llamadas pendientes
            pending = self.config.get("pending_calls", [])
            made = []
            for call in pending:
                if self.make_call(call["number"], call["message"]):
                    made.append(call)

            self.calls["calls"].extend(made)
            self.calls["last_call"] = datetime.now().isoformat()
            self._save_calls()

            self.metrics["runs"] += 1
            self.metrics["success"] += 1
            self.metrics["last_output"] = f"{len(made)} llamadas"
            self.save_metrics()
            self.log(f"Llamadas realizadas: {len(made)}")
            return {"calls": made}
        except Exception as e:
            self.metrics["errors"] += 1
            self.save_metrics()
            self.log(f"Error: {e}", "error")
            return {"error": str(e)}
        finally:
            self.stop()
