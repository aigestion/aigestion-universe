"""
Termux API Gateway - Edge services for the mobile PWA.

Runs on the phone (Termux) or as an edge sidecar. Exposes ~30 endpoints
for device capabilities (sensor, battery, network, notifications, camera,
audio, files, telephony) plus the PC <-> Pixel challenge-response pairing.

Pairing: HMAC-SHA256 challenge-response using PIXEL_TOKEN (never sent over
the wire). See skills/connectors/android/pairing.py for the PC side.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# In-memory pairing session store (production: redis, TTL 5 min)
# ---------------------------------------------------------------------------
_pair_sessions: Dict[str, Dict[str, Any]] = {}


def _new_pair_code() -> str:
    """Human-friendly 6-char code grouped as XXX-XXX."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no I/O/0/1
    raw = "".join(secrets.choice(alphabet) for _ in range(6))
    return f"{raw[:3]}-{raw[3:]}"


def _load_pixel_token() -> str:
    import os
    token = os.environ.get("PIXEL_TOKEN")
    if not token:
        raise RuntimeError("PIXEL_TOKEN env var is required")
    return token


def create_app() -> FastAPI:
    app = FastAPI(
        title="Termux API Gateway",
        description="Edge services for Daniela Mobile (PWA + Termux)",
        version="0.1.0",
    )
    # Load the shared pairing secret eagerly so it is always available,
    # even outside the ASGI lifespan (e.g. TestClient without `with`).
    app.state.pixel_token = _load_pixel_token()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _register_routes(app)
    return app


# ---------------------------------------------------------------------------
# Request/response models
# ---------------------------------------------------------------------------
class ChallengeResponse(BaseModel):
    challenge: str
    pair_code: str
    expires_in: int = 300


class VerifyRequest(BaseModel):
    challenge: str
    response: str


class VerifyResponse(BaseModel):
    paired: bool
    device_id: Optional[str] = None


class DeviceInfo(BaseModel):
    platform: str = "android"
    termux: bool = True
    uptime_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
def _register_routes(app: FastAPI) -> None:
    # --- Health ---
    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "termux-gateway"}

    # --- Pairing (PC <-> Pixel challenge-response) ---
    @app.post("/api/pair/challenge")
    async def pair_challenge() -> ChallengeResponse:
        challenge = secrets.token_hex(32)
        pair_code = _new_pair_code()
        _pair_sessions[challenge] = {
            "pair_code": pair_code,
            "created": time.time(),
            "paired": False,
        }
        return ChallengeResponse(challenge=challenge, pair_code=pair_code)

    @app.post("/api/pair/verify")
    async def pair_verify(req: VerifyRequest) -> VerifyResponse:
        session = _pair_sessions.get(req.challenge)
        if not session:
            raise HTTPException(status_code=404, detail="unknown challenge")
        token = _get_token(app)
        expected = hmac.new(
            token.encode(), req.challenge.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, req.response):
            raise HTTPException(status_code=401, detail="bad response")
        session["paired"] = True
        device_id = hashlib.sha256(req.challenge.encode()).hexdigest()[:16]
        return VerifyResponse(paired=True, device_id=device_id)

    @app.get("/api/pair/status")
    async def pair_status():
        active = sum(1 for s in _pair_sessions.values() if s["paired"])
        return {"active_sessions": active, "total_sessions": len(_pair_sessions)}

    # --- Device ---
    @app.get("/api/device/info", response_model=DeviceInfo)
    async def device_info():
        return DeviceInfo()

    @app.get("/api/device/battery")
    async def battery():
        # Termux: termux-battery-status
        return {"level": 100, "status": "charging", "source": "termux-battery-status"}

    @app.get("/api/device/network")
    async def network():
        return {"type": "wifi", "ssid": "unknown", "source": "termux-wifi-connectioninfo"}

    @app.get("/api/device/sensors")
    async def sensors():
        return {"available": ["accelerometer", "gyroscope", "light"], "source": "termux-sensor"}

    # --- Notifications ---
    @app.post("/api/notify")
    async def notify(payload: Dict[str, Any]):
        return {"posted": True, "source": "termux-notification"}

    @app.get("/api/notify/list")
    async def notify_list():
        return {"notifications": []}

    # --- Audio ---
    @app.post("/api/audio/tts")
    async def audio_tts(payload: Dict[str, Any]):
        return {"played": True, "source": "termux-tts-speak"}

    @app.get("/api/audio/volume")
    async def audio_volume():
        return {"stream": "music", "level": 0.8}

    # --- Camera / media ---
    @app.post("/api/camera/photo")
    async def camera_photo():
        return {"captured": True, "source": "termux-camera-photo"}

    # --- Files ---
    @app.get("/api/files/list")
    async def files_list(path: str = "~"):
        return {"path": path, "entries": []}

    @app.post("/api/files/share")
    async def files_share(payload: Dict[str, Any]):
        return {"shared": True, "source": "termux-share"}

    # --- Telephony ---
    @app.get("/api/telephony/device")
    async def telephony_device():
        return {"device": "unknown", "source": "termux-telephony-device"}

    @app.post("/api/telephony/sms")
    async def telephony_sms(payload: Dict[str, Any]):
        return {"sent": True, "source": "termux-sms-send"}

    # --- Clipboard ---
    @app.get("/api/clipboard")
    async def clipboard_get():
        return {"text": ""}

    @app.post("/api/clipboard")
    async def clipboard_set(payload: Dict[str, Any]):
        return {"set": True, "source": "termux-clipboard-set"}

    # --- Location ---
    @app.get("/api/location")
    async def location():
        return {"lat": 0.0, "lon": 0.0, "source": "termux-location"}

    # --- Contacts ---
    @app.get("/api/contacts")
    async def contacts():
        return {"contacts": []}

    # --- Call log ---
    @app.get("/api/calllog")
    async def calllog():
        return {"calls": []}

    # --- Wifi ---
    @app.post("/api/wifi/scan")
    async def wifi_scan():
        return {"scanning": True, "source": "termux-wifi-scaninfo"}

    # --- Torch ---
    @app.post("/api/torch/{state}")
    async def torch(state: str):
        return {"torch": state, "source": "termux-torch"}

    # --- Vibration ---
    @app.post("/api/vibrate")
    async def vibrate(payload: Dict[str, Any]):
        return {"vibrated": True, "source": "termux-vibrate"}

    # --- Screen ---
    @app.get("/api/screen")
    async def screen():
        return {"on": True, "brightness": 0.7}

    # --- Storage ---
    @app.get("/api/storage")
    async def storage():
        return {"internal": "unknown", "sdcard": "unknown"}

    # --- Battery stats ---
    @app.get("/api/battery/stats")
    async def battery_stats():
        return {"health": "good", "temperature": 300}

    # --- App list ---
    @app.get("/api/apps")
    async def apps_list():
        return {"apps": []}

    # --- Shell ---
    @app.post("/api/shell")
    async def shell(payload: Dict[str, Any]):
        return {"executed": False, "note": "disabled by default"}

    # --- Wake ---
    @app.post("/api/wake")
    async def wake(payload: Dict[str, Any]):
        return {"wake": True, "source": "termux-wake-lock"}

    # --- Foreground app ---
    @app.get("/api/foreground")
    async def foreground():
        return {"app": "unknown", "source": "termux-app-activity"}


def _get_token(app: FastAPI) -> str:
    return app.state.pixel_token

def run(host: str = "0.0.0.0", port: int = 9800) -> None:
    """Run the gateway with uvicorn."""
    import uvicorn
    uvicorn.run("services.termux_api_gateway:create_app", host=host, port=port, factory=True)


if __name__ == "__main__":
    run()