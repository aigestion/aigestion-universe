#!/usr/bin/env python3
"""
PA-11: Pixel Screen Mirror + AI Vision - Gemini analiza pantalla
===================================================================
scrcpy muestra la pantalla del Pixel en el PC. Cada N segundos,
un screenshot se envia a Gemini Vision que analiza:
  - Codigos de verificacion (SMS, 2FA, email)
  - Spam / phishing en notificaciones
  - Mensajes importantes (WhatsApp, Telegram)
  - Ofertas relevantes
  - Alertas de seguridad

Daniela te dice: "Alejandro, tienes un SMS de verificacion con codigo 483929"
sin que mires el movil.

Flujo:
  1. ADB screenshot (reutiliza adb_mirror.py)
  2. Enviar imagen a Gemini Vision (free tier)
  3. Extraer info relevante (codigos, alertas, mensajes)
  4. Notificar al PC (FCM bridge) + TTS (voice pipeline)

Rutas en daniela_os.py:
  - GET  /api/pixel/vision/status      (estado)
  - POST /api/pixel/vision/start       (iniciar analisis)
  - POST /api/pixel/vision/stop        (detener)
  - POST /api/pixel/vision/analyze     (analizar screenshot ahora)
  - GET  /api/pixel/vision/findings    (hallazgos detectados)

Coste: $0/mes (Gemini free tier + ADB)
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

import requests

# ── Config ───────────────────────────────────────────────────

# Raiz del repo (este modulo vive en pixel/ desde Fase 2).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE_DIR = os.path.join(PROJECT_ROOT, "data", "screen_vision")
STATE_FILE = os.path.join(STATE_DIR, "vision_state.json")
FINDINGS_FILE = os.path.join(STATE_DIR, "findings.json")

# Analysis
ANALYZE_INTERVAL = 15  # seconds between analyses
MAX_FINDINGS = 100

# Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
GEMINI_MODEL = "gemini-2.0-flash"

# What to look for
ANALYSIS_PROMPT = """Analiza esta captura de pantalla de un telefono Android.

Extrae SOLO informacion relevante en formato JSON:
{
  "tipo": "codigo_verificacion|mensaje_importante|spam|alerta_seguridad|oferta|nada",
  "resumen": "descripcion breve en español",
  "codigo": "el codigo numerico si lo hay, sino vacio",
  "remitente": "quien envia si aplica (banco, WhatsApp, etc)",
  "urgente": true/false,
  "accion_sugerida": "que deberia hacer el usuario"
}

Si no hay nada relevante, responde: {"tipo": "nada", "resumen": "", "codigo": "", "remitente": "", "urgente": false, "accion_sugerida": ""}

Responde SOLO con el JSON, sin markdown ni explicaciones."""


# ── Data classes ─────────────────────────────────────────────


@dataclass
class Finding:
    id: str
    timestamp: float
    tipo: str  # codigo_verificacion, mensaje_importante, spam, etc
    resumen: str
    codigo: str = ""
    remitente: str = ""
    urgente: bool = False
    accion_sugerida: str = ""
    image_path: str = ""
    notified: bool = False


@dataclass
class VisionState:
    running: bool = False
    analyze_count: int = 0
    finding_count: int = 0
    last_analyze: float = 0.0
    last_finding: float = 0.0
    last_tipo: str = ""
    gemini_available: bool = False
    error_count: int = 0
    last_error: str = ""


# ── Screen AI Vision ─────────────────────────────────────────


class ScreenAIVision:
    """Screenshot + Gemini Vision analysis of the Pixel screen."""

    def __init__(self):
        self._state = VisionState()
        self._lock = threading.Lock()
        self._findings: List[Finding] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_image_hash = ""
        self._ensure_dirs()
        self._state.gemini_available = bool(GEMINI_API_KEY)

    def _ensure_dirs(self):
        os.makedirs(STATE_DIR, exist_ok=True)

    # ── Screenshot ────────────────────────────────────────────

    def _screenshot(self) -> Optional[str]:
        """Take a Pixel screenshot via ADB (reuses adb_mirror)."""
        try:
            from bridges.comms.adb_mirror import get_instance as get_adb

            adb = get_adb()
            result = adb.screenshot()
            if result.get("ok"):
                return result.get("path")
        except Exception:
            pass
        return None

    # ── Gemini Vision ────────────────────────────────────────

    def _analyze_with_gemini(self, image_path: str) -> Optional[Dict]:
        """Send screenshot to Gemini Vision for analysis."""
        if not GEMINI_API_KEY:
            return None

        try:
            import base64

            with open(image_path, "rb") as f:
                image_bytes = f.read()

            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            )
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": ANALYSIS_PROMPT},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": base64.b64encode(image_bytes).decode("utf-8"),
                                }
                            },
                        ]
                    }
                ]
            }

            r = requests.post(url, json=payload, timeout=25)
            if r.status_code != 200:
                return None

            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            # Strip markdown fences
            text = text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            text = text.rstrip("`").strip()

            return json.loads(text)
        except Exception:
            return None

    # ── Notify ───────────────────────────────────────────────

    def _notify(self, finding: Finding):
        """Notify user via FCM bridge + TTS."""
        try:
            from bridges.comms.fcm_real_bridge import get_instance as get_bridge

            bridge = get_bridge()
            title = f"Vision: {finding.tipo}"
            if finding.tipo == "codigo_verificacion" and finding.codigo:
                title = f"Codigo de {finding.remitente or 'verificacion'}"
            bridge.send_to_pixel(
                title=title,
                body=finding.resumen[:200],
                ntype="security_alert" if finding.urgente else "info",
            )
            finding.notified = True
        except Exception:
            pass

        # TTS if urgent
        if finding.urgente:
            try:
                from bridges.comms.voice_pipeline import get_instance as get_voice

                msg = finding.resumen or f"Alerta: {finding.tipo}"
                get_voice().speak(msg[:200])
            except Exception:
                pass

    # ── Analysis loop ────────────────────────────────────────

    def _analyze_loop(self):
        while self._running:
            try:
                img_path = self._screenshot()

                if img_path and os.path.exists(img_path):
                    with self._lock:
                        self._state.analyze_count += 1
                        self._state.last_analyze = time.time()

                    # Analyze
                    result = self._analyze_with_gemini(img_path)

                    if result and result.get("tipo") not in ("nada", "", None):
                        finding = Finding(
                            id=f"vis_{int(time.time() * 1000)}",
                            timestamp=time.time(),
                            tipo=result.get("tipo", "nada"),
                            resumen=result.get("resumen", ""),
                            codigo=result.get("codigo", ""),
                            remitente=result.get("remitente", ""),
                            urgente=result.get("urgente", False),
                            accion_sugerida=result.get("accion_sugerida", ""),
                            image_path=img_path,
                        )

                        self._findings.append(finding)
                        if len(self._findings) > MAX_FINDINGS:
                            self._findings = self._findings[-MAX_FINDINGS:]

                        with self._lock:
                            self._state.finding_count += 1
                            self._state.last_finding = time.time()
                            self._state.last_tipo = finding.tipo

                        self._notify(finding)
                        self._save_findings()

            except Exception as e:
                with self._lock:
                    self._state.error_count += 1
                    self._state.last_error = str(e)[:200]

            time.sleep(ANALYZE_INTERVAL)

    def _save_findings(self):
        try:
            with open(FINDINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    [asdict(x) for x in self._findings[-50:]], f, indent=2, ensure_ascii=False
                )
        except OSError:
            pass

    # ── Public API ───────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._state.running = True
        self._thread = threading.Thread(
            target=self._analyze_loop, daemon=True, name="screen-vision"
        )
        self._thread.start()

    def stop(self):
        self._running = False
        self._state.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def analyze_now(self) -> Dict:
        """Take a screenshot and analyze it immediately."""
        img_path = self._screenshot()
        if not img_path:
            return {"ok": False, "error": "Screenshot failed (ADB not connected?)"}

        result = self._analyze_with_gemini(img_path)
        if not result:
            return {"ok": False, "error": "Gemini analysis failed (no API key?)"}

        return {"ok": True, "image": img_path, "analysis": result}

    def get_state(self) -> Dict:
        with self._lock:
            return asdict(self._state)

    def get_findings(self, limit: int = 20, tipo: str = "") -> List[Dict]:
        findings = self._findings
        if tipo:
            findings = [f for f in findings if f.tipo == tipo]
        return [asdict(f) for f in findings[-limit:]]

    def save_state(self):
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.get_state(), f, indent=2, ensure_ascii=False)


# ── Singleton ─────────────────────────────────────────────────

_instance: Optional[ScreenAIVision] = None


def get_instance() -> ScreenAIVision:
    global _instance
    if _instance is None:
        _instance = ScreenAIVision()
    return _instance


# ── Flask route registration ──────────────────────────────────


def register_vision_routes(flask_app):
    """Register screen vision routes in daniela_os.py."""

    @flask_app.route("/api/pixel/vision/status")
    def pixel_vision_status():
        return flask_app.jsonify(get_instance().get_state())

    @flask_app.route("/api/pixel/vision/start", methods=["POST"])
    def pixel_vision_start():
        get_instance().start()
        return flask_app.jsonify({"ok": True, "message": "Screen vision analysis started"})

    @flask_app.route("/api/pixel/vision/stop", methods=["POST"])
    def pixel_vision_stop():
        get_instance().stop()
        return flask_app.jsonify({"ok": True, "message": "Screen vision stopped"})

    @flask_app.route("/api/pixel/vision/analyze", methods=["POST"])
    def pixel_vision_analyze():
        return flask_app.jsonify(get_instance().analyze_now())

    @flask_app.route("/api/pixel/vision/findings")
    def pixel_vision_findings():
        limit = int(flask_app.request.args.get("limit", 20))
        tipo = flask_app.request.args.get("tipo", "")
        findings = get_instance().get_findings(limit, tipo)
        return flask_app.jsonify({"count": len(findings), "findings": findings})

    print(
        "[Screen Vision] Routes registered: /api/pixel/vision/* (status, start, stop, analyze, findings)"
    )


# ── CLI ───────────────────────────────────────────────────────


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python screen_ai_vision.py [status|analyze|findings|start]")
        return

    cmd = sys.argv[1]
    vision = get_instance()

    if cmd == "status":
        print(json.dumps(vision.get_state(), indent=2))
    elif cmd == "analyze":
        print(json.dumps(vision.analyze_now(), indent=2))
    elif cmd == "findings":
        findings = vision.get_findings()
        print(f"Findings: {len(findings)}")
        for f in findings:
            print(f"  [{f['tipo']}] {f['resumen'][:70]}")
    elif cmd == "start":
        vision.start()
        print("Screen vision started. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(15)
                s = vision.get_state()
                print(
                    f"  analyses={s['analyze_count']} findings={s['finding_count']} last={s['last_tipo']}"
                )
        except KeyboardInterrupt:
            vision.stop()
            print("Stopped.")
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()