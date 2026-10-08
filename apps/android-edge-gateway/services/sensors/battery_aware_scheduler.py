#!/usr/bin/env python3
"""
Battery-Aware Scheduler (PA-14)
================================
Daniela ajusta su comportamiento segun la bateria del Pixel.

  - Full mode (>50%): TTS, streaming, RAG, analisis continuo
  - Normal mode (20-50%): polling cada 30s, TTS solo alerts
  - Save mode (<20%): solo notificaciones criticas, sin TTS, sin streaming

Se ejecuta en background thread y notifica cuando hay cambios de modo.

Cost: $0 — solo lectura de bateria via Termux o Pixel Bridge
"""

import json
import subprocess
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = PROJECT_ROOT / "data" / "battery_scheduler"
STATE_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE = STATE_DIR / "battery_state.json"
HISTORY_FILE = STATE_DIR / "battery_history.jsonl"


@dataclass
class BatteryMode:
    """Modo de comportamiento basado en bateria."""

    name: str  # "full", "normal", "save"
    min_pct: int
    max_pct: int
    poll_interval: int  # seconds
    tts_enabled: bool
    streaming_enabled: bool
    gps_frequency: str  # "continuous", "on_demand", "disabled"
    sensor_polling: str  # "realtime", "periodic", "disabled"
    description: str


MODES = {
    "full": BatteryMode(
        name="full",
        min_pct=50,
        max_pct=100,
        poll_interval=30,
        tts_enabled=True,
        streaming_enabled=True,
        gps_frequency="continuous",
        sensor_polling="realtime",
        description="Full power — all features active",
    ),
    "normal": BatteryMode(
        name="normal",
        min_pct=20,
        max_pct=49,
        poll_interval=60,
        tts_enabled=True,  # only for alerts
        streaming_enabled=False,
        gps_frequency="on_demand",
        sensor_polling="periodic",
        description="Normal — reduced polling, alerts only TTS",
    ),
    "save": BatteryMode(
        name="save",
        min_pct=0,
        max_pct=19,
        poll_interval=300,  # 5 min
        tts_enabled=False,
        streaming_enabled=False,
        gps_frequency="disabled",
        sensor_polling="disabled",
        description="Battery save — critical notifications only",
    ),
}


class BatteryAwareScheduler:
    """Scheduler que ajusta comportamiento segun bateria."""

    def __init__(self):
        self._current_mode: str = "full"
        self._battery_pct: int = 100
        self._battery_charging: bool = False
        self._last_check: float = 0
        self._callbacks: list = []
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._load_state()

    def _load_state(self):
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                self._battery_pct = data.get("battery_pct", 100)
                self._current_mode = data.get("mode", "full")
                self._battery_charging = data.get("charging", False)
            except (json.JSONDecodeError, KeyError):
                pass

    def _save_state(self):
        data = {
            "mode": self._current_mode,
            "battery_pct": self._battery_pct,
            "charging": self._battery_charging,
            "updated_at": datetime.now().isoformat(),
        }
        STATE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def _log_history(self, event: str, details: dict = None):
        """Log de eventos de bateria a JSONL."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "battery_pct": self._battery_pct,
            "mode": self._current_mode,
            "charging": self._battery_charging,
            "details": details or {},
        }
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def get_battery(self) -> dict:
        """Lee el estado de la bateria."""
        # Intentar via dual_mode (detecta Pixel vs PC)
        try:
            from dual_mode_switch import dual_mode

            if dual_mode.is_pixel():
                # En Pixel: termux-battery-status directo
                result = subprocess.run(
                    ["termux-battery-status"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    return {
                        "percentage": data.get("percentage", 100),
                        "charging": data.get("status", "") == "CHARGING",
                        "temperature": data.get("temperature", 0),
                    }
            else:
                # En PC: pedir al Pixel via bridge
                from bridges.pixel.pixel_bridge_hub import pixel_bridge

                status = pixel_bridge.get_battery()
                if status.get("ok"):
                    data = status.get("data", {})
                    return {
                        "percentage": data.get("percentage", 100),
                        "charging": data.get("status", "") == "CHARGING",
                        "temperature": data.get("temperature", 0),
                    }
        except Exception:
            pass

        # Fallback: estado cached
        return {
            "percentage": self._battery_pct,
            "charging": self._battery_charging,
        }

    def determine_mode(self, pct: int, charging: bool) -> str:
        """Determina el modo basado en bateria y carga."""
        if charging and pct > 20:
            # Si esta cargando y tiene >20%, modo full
            return "full"
        elif pct >= 50:
            return "full"
        elif pct >= 20:
            return "normal"
        else:
            return "save"

    def check(self) -> dict:
        """Lee bateria y actualiza modo si es necesario."""
        battery = self.get_battery()
        pct = battery.get("percentage", 100)
        charging = battery.get("charging", False)

        old_mode = self._current_mode
        new_mode = self.determine_mode(pct, charging)

        self._battery_pct = pct
        self._battery_charging = charging
        self._last_check = time.time()

        mode_changed = old_mode != new_mode
        if mode_changed:
            self._current_mode = new_mode
            self._log_history(
                "mode_change",
                {
                    "old_mode": old_mode,
                    "new_mode": new_mode,
                },
            )
            # Notificar callbacks
            for callback in self._callbacks:
                try:
                    callback(old_mode, new_mode, pct)
                except Exception:
                    pass
        else:
            self._log_history("check", {"mode": new_mode})

        self._save_state()

        return {
            "battery_pct": pct,
            "charging": charging,
            "mode": new_mode,
            "mode_changed": mode_changed,
            "old_mode": old_mode if mode_changed else None,
        }

    def on_mode_change(self, callback: Callable):
        """Registra un callback que se llama cuando cambia el modo."""
        self._callbacks.append(callback)

    def get_current_mode(self) -> BatteryMode:
        """Retorna el BatteryMode activo."""
        return MODES.get(self._current_mode, MODES["full"])

    def get_poll_interval(self) -> int:
        """Retorna el intervalo de polling actual."""
        return self.get_current_mode().poll_interval

    def should_tts(self) -> bool:
        """True si TTS esta permitido."""
        return self.get_current_mode().tts_enabled

    def should_stream(self) -> bool:
        """True si streaming esta permitido."""
        return self.get_current_mode().streaming_enabled

    def get_status(self) -> dict:
        """Estado completo del scheduler."""
        mode = self.get_current_mode()
        return {
            "battery_pct": self._battery_pct,
            "charging": self._battery_charging,
            "mode": self._current_mode,
            "mode_config": asdict(mode),
            "last_check": (
                datetime.fromtimestamp(self._last_check).isoformat() if self._last_check else None
            ),
            "poll_interval": mode.poll_interval,
            "tts_enabled": mode.tts_enabled,
            "streaming_enabled": mode.streaming_enabled,
            "gps_frequency": mode.gps_frequency,
            "sensor_polling": mode.sensor_polling,
        }

    def start_background(self):
        """Inicia el scheduler en background thread."""
        if self._running:
            return

        def _loop():
            self._running = True
            while self._running:
                try:
                    self.check()
                except Exception:
                    pass
                interval = self.get_poll_interval()
                time.sleep(interval)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop_background(self):
        """Detiene el scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)


# Singleton
battery_scheduler = BatteryAwareScheduler()


# ============================================================================
# CLI
# ============================================================================

if __name__ == "__main__":
    import sys

    print("=" * 50)
    print("  BATTERY-AWARE SCHEDULER (PA-14)")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("  Usage: python battery_aware_scheduler.py status|check|start|stop|history")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "status":
        status = battery_scheduler.get_status()
        print(f"  Battery: {status['battery_pct']}%")
        print(f"  Charging: {status['charging']}")
        print(f"  Mode: {status['mode']}")
        print(f"  Poll interval: {status['poll_interval']}s")
        print(f"  TTS: {status['tts_enabled']}")
        print(f"  Streaming: {status['streaming_enabled']}")
        print(f"  GPS: {status['gps_frequency']}")
        print(f"  Sensors: {status['sensor_polling']}")

    elif cmd == "check":
        result = battery_scheduler.check()
        print(f"  Battery: {result['battery_pct']}%")
        print(f"  Mode: {result['mode']}")
        if result["mode_changed"]:
            print(f"  MODE CHANGED: {result['old_mode']} -> {result['mode']}")
        else:
            print("  No mode change")

    elif cmd == "start":
        battery_scheduler.start_background()
        print("  Background scheduler started")
        print(f"  Poll interval: {battery_scheduler.get_poll_interval()}s")
        print("  Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            battery_scheduler.stop_background()
            print("\n  Stopped")

    elif cmd == "stop":
        battery_scheduler.stop_background()
        print("  Stopped")

    elif cmd == "history":
        if HISTORY_FILE.exists():
            lines = HISTORY_FILE.read_text(encoding="utf-8").strip().split("\n")
            for line in lines[-20:]:  # ultimos 20
                entry = json.loads(line)
                ts = entry["timestamp"][:19]
                event = entry["event"]
                pct = entry["battery_pct"]
                mode = entry["mode"]
                print(f"  [{ts}] {event}: {pct}% ({mode})")
        else:
            print("  No history yet")

    else:
        print(f"  Unknown command: {cmd}")