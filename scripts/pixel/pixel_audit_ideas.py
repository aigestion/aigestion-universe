#!/usr/bin/env python3
"""
Pixel Audit & Epic Ideas — Acoplar Todo
========================================
Audita el control del Pixel, mapea todos los modulos moviles,
identifica disconnections, y propone ideas epicas para unificar.

  PA-01: Pixel Bridge Hub — unificar todos los modulos sueltos
  PA-02: ADB Mirror — scrcpy + ADB control remoto
  PA-03: Sensor Stream Live — WebSocket telemetry
  PA-04: Firebase FCM Real Bridge — push notifications bidireccionales
  PA-05: IoT Real Integration — Home Assistant local
  PA-06: Dual-Mode Auto-Switch — deteccion automatica PC/Pixel
  PA-07: Pixel as Security Camera — motion detection + AI vision
  PA-08: Voice Pipeline Unificado — PC + Pixel same code
  PA-09: Termux API Gateway — REST API en el Pixel
  PA-10: Geofence Automation Engine — home/outdoors auto-mode
  PA-11: Pixel Screen Mirror + AI Vision — Gemini analiza pantalla
  PA-12: Clipboard Sync — bidireccional PC <-> Pixel
  PA-13: File Sync Daemon — fotos archivos auto-sync
  PA-14: Battery-Aware Scheduler — modo ahorro/full automatico
  PA-15: Pixel as Second Screen — dashboard en el movil

Cost: $0/month — Python + Termux API (free) + Firebase Spark (free) + scrcpy (open source)

CLI:
  python pixel_audit_ideas.py status           — audit status
  python pixel_audit_ideas.py audit           — full audit
  python pixel_audit_ideas.py ideas           — all epic ideas
  python pixel_audit_ideas.py roadmap          — phased roadmap
  python pixel_audit_ideas.py all              — run everything
  python pixel_audit_ideas.py export           — export JSON
"""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "static" / "brand"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR = PROJECT_ROOT / "data" / "pixel_audit"
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# AUDIT DATA
# ==============================================================================

@dataclass
class ModuleAudit:
    """Audit of a single mobile/Pixel related module."""
    id: str
    file: str
    name: str
    category: str  # device_control, voice, satellite, rag, frontend, iot
    termux_commands: list[str]
    status: str  # production, partial, stub, disconnected
    issues: list[str]
    integration: str  # how it connects (or doesn't) to daniela_os.py


@dataclass
class EpicIdea:
    """An epic idea to connect everything."""
    id: str
    title: str
    category: str  # bridge, control, realtime, iot, sync, ai_vision
    priority: str  # critical, high, medium, low
    effort: str  # S, M, L, XL
    description: str
    tech_stack: list[str]
    free_tier: str
    connects: list[str]  # which modules it connects


@dataclass
class RoadmapPhase:
    """A phase in the implementation roadmap."""
    phase: int
    name: str
    duration_weeks: int
    ideas: list[str]
    description: str


# ==============================================================================
# AUDIT RESULTS
# ==============================================================================

AUDIT_RESULTS = [
    ModuleAudit(
        id="MA-01",
        file="android_control.py",
        name="Android Control",
        category="device_control",
        termux_commands=["termux-location", "termux-torch", "termux-clipboard-get", "termux-camera-photo"],
        status="disconnected",
        issues=[
            "Completamente standalone — daniela_os.py no lo importa ni lo referencia",
            "shell=True en subprocess.run — vulnerable a command injection",
            "Path hardcoded en take_photo() — ~/daniela-os/ no existe en el PC",
        ],
        integration="NINGUNA — script standalone que solo corre en Termux",
    ),
    ModuleAudit(
        id="MA-02",
        file="daniela_hardware_bridge.py",
        name="Daniela Hardware Bridge",
        category="device_control",
        termux_commands=["termux-battery-status", "termux-location", "termux-toast"],
        status="disconnected",
        issues=[
            "Devuelve datos fake cuando falla (percentage=32, lat=40.4168 Madrid)",
            "termux-location sin -p ni -r flags — puede colgar indefinidamente",
            "No hay timeout en algunos calls",
            "daniela_os.py no lo importa",
        ],
        integration="NINGUNA — instancia singleton creada pero nadie la usa",
    ),
    ModuleAudit(
        id="MA-03",
        file="daniela_mobile_daemon.py",
        name="Daniela Mobile Daemon",
        category="device_control",
        termux_commands=["termux-vibrate", "termux-tts-speak", "termux-battery-status", "termux-location"],
        status="disconnected",
        issues=[
            "os.system() en TODAS las llamadas — command injection vulnerable",
            "Coordenadas base hardcoded (Tenerife 28.0309, -16.5945)",
            "No hay loop continuo — corre una vez y termina",
            "check_zone() usa margen fijo 0.0015 — no configurable",
        ],
        integration="NINGUNA — standalone script",
    ),
    ModuleAudit(
        id="MA-04",
        file="caja_negra.py",
        name="Caja Negra (Emergency)",
        category="device_control",
        termux_commands=["termux-vibrate", "termux-location", "termux-tts-speak", "termux-microphone-record"],
        status="partial",
        issues=[
            "os.system() en TODAS las llamadas",
            "Audio file path sin sanitizar",
            "No envia datos a ningun servidor — todo local",
            "No hay cifrado de datos de emergencia",
        ],
        integration="NINGUNA — standalone emergency script",
    ),
    ModuleAudit(
        id="MA-05",
        file="daniela_notification_sentinel.py",
        name="Notification Sentinel",
        category="device_control",
        termux_commands=["termux-notification-list"],
        status="partial",
        issues=[
            "Solo lista notificaciones — no las filtra ni clasifica",
            "Body del proposal es hardcoded ('banca y mensajeria filtradas')",
            "No hay accion real sobre notificaciones (no las dismiss, no responde)",
            "daniela_os.py no lo importa",
        ],
        integration="NINGUNA — standalone, retorna dict pero nadie lo lee",
    ),
    ModuleAudit(
        id="MA-06",
        file="daniela_satellite_ai.py",
        name="Daniela Satellite AI",
        category="voice",
        termux_commands=["termux-vibrate"],
        status="partial",
        issues=[
            "Modelo 'gemini-3.7-flash' no existe — usara error o fallback",
            "edge-tts requiere async — puede colgar si event loop ya corre",
            "os.system('pkill -9 mpv') — matara todos los mpv del sistema",
            "API key leida de .env manualmente — no usa dotenv",
        ],
        integration="NINGUNA — console chat standalone",
    ),
    ModuleAudit(
        id="MA-07",
        file="copiloto_voz.py",
        name="Copiloto de Voz",
        category="voice",
        termux_commands=["termux-speech-to-text", "termux-battery-status"],
        status="partial",
        issues=[
            "os.system(comando) en ejecutar_copiloto() — COMMAND INJECTION CRITICO",
            "rm -f ~/daniela-os/*.jpg en mapear_comando() — destructivo sin confirmacion",
            "Solo 8 comandos hardcoded — no escalable",
            "No hay NLP — keyword matching primitivo",
        ],
        integration="NINGUNA — standalone voice command script",
    ),
    ModuleAudit(
        id="MA-08",
        file="daemon_escucha.py",
        name="Daemon de Escucha (Centinela)",
        category="voice",
        termux_commands=["termux-speech-to-text"],
        status="partial",
        issues=[
            "Loop infinito con sleep(2) — consume bateria continuamente",
            "termux-speech-to-text tiene 4s timeout — window corta",
            "No hay VAD (Voice Activity Detection) — graba silencio",
            "Ejecuta conversar_daniela.py con os.system — sin manejo de errores",
        ],
        integration="NINGUNA — standalone daemon",
    ),
    ModuleAudit(
        id="MA-09",
        file="daniela_dual_sat.py",
        name="Daniela Dual SAT",
        category="satellite",
        termux_commands=["termux-tts-speak"],
        status="partial",
        issues=[
            "PC_IP hardcoded (192.168.1.170) — cambiara con DHCP",
            "PORT hardcoded (5000) — no configurable",
            "Loop con sleep(10) — solo detecta, no actua",
            "os.system() para TTS — injection",
        ],
        integration="NINGUNA — standalone satellite mode detector",
    ),
    ModuleAudit(
        id="MA-10",
        file="activar_servicios.py",
        name="Activar Servicios",
        category="satellite",
        termux_commands=[],
        status="partial",
        issues=[
            "Webhook server hardcoded a 0.0.0.0:8081 — sin auth ni SSL",
            "Path hardcoded /data/data/com.termux/files/home/daniela-os/",
            "Importa plugins.gdrive_reporter que puede no existir",
            "No hay error handling real",
        ],
        integration="PARCIAL — webhook escucha Chrome pero no conecta con daniela_os.py",
    ),
    ModuleAudit(
        id="MA-11",
        file="skills/pixel_nano_rag.py",
        name="Pixel Nano RAG",
        category="rag",
        termux_commands=[],
        status="partial",
        issues=[
            "DB path hardcoded ~/daniela-os/memory_rag.db — no existe en PC",
            "Solo recupera ultimos 5 docs — sin semantic search real",
            "No hay embedding generation — solo texto plano",
            "Modelo 'gemini-3.6-flash' correcto pero sin rate limiting",
        ],
        integration="NINGUNA — standalone RAG query, no conectado al chat principal",
    ),
    ModuleAudit(
        id="MA-12",
        file="test_shake_pixel.py",
        name="Shake Pixel Test",
        category="device_control",
        termux_commands=["termux-sensor"],
        status="production",
        issues=[
            "Umbral 3.5 hardcodeado — no configurable",
            "subprocess.Popen sin timeout — puede colgar si termux-sensor falla",
            "No hay uso real del shake detection — solo retorna True/False",
        ],
        integration="NINGUNA — standalone test script",
    ),
    ModuleAudit(
        id="MA-13",
        file="static/daniela_mobile_sync.js",
        name="Mobile Sync JS",
        category="frontend",
        termux_commands=[],
        status="production",
        issues=[
            "WakeLock API sin error handling real",
            "No hay sync real — solo detecta mobile y aplica CSS class",
            "No hay communication con el Pixel — solo frontend detection",
        ],
        integration="PARCIAL — cargado en el frontend pero no hay bidirectional sync",
    ),
    ModuleAudit(
        id="MA-14",
        file="add_camera_hub.py",
        name="Camera Hub",
        category="frontend",
        termux_commands=[],
        status="partial",
        issues=[
            "Path hardcoded /data/data/com.termux/files/home/daniela-os/index.html",
            "Regex replacement fragil — se rompe si el HTML cambia",
            "No hay captura real — solo input file HTML",
            "OCR y aig Vision son solo labels — no hay logica",
        ],
        integration="PARCIAL — patch script que modifica HTML del Pixel",
    ),
    ModuleAudit(
        id="MA-15",
        file="skills/iot_controller.py",
        name="IoT Controller",
        category="iot",
        termux_commands=[],
        status="stub",
        issues=[
            "SIMULACION PURA — no hay llamada real a ninguna API",
            "No hay Home Assistant, MQTT, ni Tuya integration",
            "Solo keyword matching — sin NLU",
            "logging.info pero no hay logging configurado",
        ],
        integration="NINGUNA — stub que retorna strings, no hace nada real",
    ),
    ModuleAudit(
        id="MA-16",
        file="trusted_devices.json",
        name="Trusted Devices",
        category="device_control",
        termux_commands=[],
        status="partial",
        issues=[
            "2 UUIDs sin metadatos — no se sabe que dispositivos son",
            "No hay validacion ni rotacion de trust",
            "No hay uso real en el codigo — nadie importa este archivo",
        ],
        integration="NINGUNA — archivo JSON standalone",
    ),
    ModuleAudit(
        id="MA-17",
        file="battery_state.json",
        name="Battery State",
        category="device_control",
        termux_commands=[],
        status="partial",
        issues=[
            "Estado estatico — no se actualiza en tiempo real",
            "No hay uso real — nadie lee este archivo",
            "is_charging y low_warn_sent sin logica que los use",
        ],
        integration="NINGUNA — archivo JSON standalone",
    ),
]

# Termux command inventory
TERMUX_INVENTORY = {
    "termux-location": {"files": 3, "use": "GPS coordinates"},
    "termux-torch": {"files": 3, "use": "Flashlight on/off"},
    "termux-clipboard-get": {"files": 1, "use": "Read clipboard"},
    "termux-camera-photo": {"files": 4, "use": "Take photo"},
    "termux-battery-status": {"files": 4, "use": "Battery level and status"},
    "termux-tts-speak": {"files": 4, "use": "Text-to-speech in Spanish"},
    "termux-vibrate": {"files": 4, "use": "Haptic feedback"},
    "termux-microphone-record": {"files": 5, "use": "Audio recording"},
    "termux-speech-to-text": {"files": 2, "use": "Voice recognition"},
    "termux-notification-list": {"files": 1, "use": "Read Android notifications"},
    "termux-toast": {"files": 1, "use": "Show toast message"},
    "termux-sensor": {"files": 1, "use": "Accelerometer/gyroscope"},
}

# Missing Termux commands (available but not used)
TERMUX_AVAILABLE_NOT_USED = [
    "termux-telephony-call",     # Make phone calls
    "termux-sms-send",           # Send SMS
    "termux-sms-list",           # Read SMS messages
    "termux-contact-list",      # Read contacts
    "termux-call-log",           # Read call log
    "termux-media-player",       # Play media files
    "termux-clipboard-set",      # Write to clipboard
    "termux-notification",       # Create notifications
    "termux-fingerprint",        # Fingerprint sensor
    "termux-brightness",         # Screen brightness
    "termux-volume",             # Volume control
    "termux-wifi-connectioninfo", # WiFi info
    "termux-wifi-scaninfo",      # WiFi scan results
    "termux-bluetooth-status",   # Bluetooth status
    "termux-telephony-deviceinfo", # Phone info (IMEI, etc.)
]


# ==============================================================================
# EPIC IDEAS
# ==============================================================================

EPIC_IDEAS = [
    EpicIdea(
        id="PA-01",
        title="Pixel Bridge Hub — unificar todos los modulos en un solo controlador",
        category="bridge",
        priority="critical",
        effort="M",
        description="Crear un PixelBridge central que importe y exponga TODOS los modulos (android_control, hardware_bridge, mobile_daemon, caja_negra, notification_sentinel, copiloto, centinela, satellite_ai, pixel_rag). Registrar endpoints en daniela_os.py: /api/pixel/* para que el PC controle el Pixel via HTTP. El Pixel corre un mini-Flask server en Termux que el PC descubre via mDNS.",
        tech_stack=["Python Flask", "Termux", "mDNS (zeroconf)", "requests"],
        free_tier="Todo open source, $0",
        connects=["MA-01", "MA-02", "MA-03", "MA-04", "MA-05", "MA-06", "MA-07", "MA-08", "MA-09", "MA-11"],
    ),
    EpicIdea(
        id="PA-02",
        title="ADB Mirror — scrcpy + ADB control remoto del Pixel",
        category="control",
        priority="high",
        effort="M",
        description="Instalar scrcpy en el PC y ADB en el Pixel. Daniela puede ver la pantalla del Pixel en una ventana del PC, hacer clicks, escribir texto, instalar apps, tomar screenshots. Todo via ADB over WiFi (sin cable). Ideal para que Daniela controle el Pixel sin tocarlo.",
        tech_stack=["scrcpy (open source)", "ADB", "Python subprocess"],
        free_tier="scrcpy es gratis y open source",
        connects=["MA-01", "MA-12", "MA-14"],
    ),
    EpicIdea(
        id="PA-03",
        title="Sensor Stream Live — WebSocket telemetry en tiempo real",
        category="realtime",
        priority="high",
        effort="L",
        description="Streaming continuo de TODOS los sensores del Pixel al PC via WebSocket: acelerometro, giroscopio, GPS, bateria, temperatura, proximidad, luz, nivel de señal. El PC muestra un dashboard en vivo. Daniela sabe exactamente el estado fisico del telefono en cada momento.",
        tech_stack=["Flask-SocketIO", "termux-sensor", "termux-battery-status", "Chart.js"],
        free_tier="Flask-SocketIO es open source",
        connects=["MA-02", "MA-03", "MA-12", "MA-17"],
    ),
    EpicIdea(
        id="PA-04",
        title="Firebase FCM Real Bridge — push notifications bidireccionales",
        category="realtime",
        priority="high",
        effort="M",
        description="Conectar Firebase Cloud Messaging (gratis, Spark plan) para push notifications reales. El PC envia alertas al Pixel (recordatorios, emergencias, resultados de tareas). El Pixel envia eventos al PC (notificaciones de WhatsApp, SMS, llamadas, bateria baja). Bridge real, no simulado.",
        tech_stack=["Firebase Admin SDK", "FCM", "firebase_admin.messaging", "termux-notification-list"],
        free_tier="Firebase Spark plan: 50K MAU, FCM ilimitado",
        connects=["MA-05", "MA-09", "MA-16"],
    ),
    EpicIdea(
        id="PA-05",
        title="IoT Real Integration — Home Assistant local",
        category="iot",
        priority="high",
        effort="L",
        description="Reemplazar el stub de iot_controller.py con integracion real a Home Assistant local (gratis, corre en Raspberry Pi o PC). Control real de luces (Philips Hue, Tuya), persianas, termostato, smart plugs, TV. Daniela recibe comandos de voz o texto y controla la casa real.",
        tech_stack=["Home Assistant (open source)", "REST API", "MQTT", "Philips Hue API", "Tuya API"],
        free_tier="Home Assistant es gratis y self-hosted",
        connects=["MA-15", "MA-07", "MA-08"],
    ),
    EpicIdea(
        id="PA-06",
        title="Dual-Mode Auto-Switch — deteccion automatica PC/Pixel",
        category="bridge",
        priority="critical",
        effort="S",
        description="Cuando Daniela detecta que se ejecuta en el Pixel (via platform detection o battery_state.json), cambia automaticamente a modo satelite: TTS nativo de Android, haptic feedback, GPS, menos polling. Cuando vuelve al PC, sincroniza todo el estado. Transicion seamless sin codigo separado.",
        tech_stack=["Python platform module", "termux detection", "state sync JSON"],
        free_tier="$0",
        connects=["MA-03", "MA-09", "MA-13", "MA-17"],
    ),
    EpicIdea(
        id="PA-07",
        title="Pixel as Security Camera — motion detection + AI vision",
        category="ai_vision",
        priority="medium",
        effort="M",
        description="Cuando el Pixel esta cargando, usar la camara como camara de seguridad. Deteccion de movimiento por comparacion de frames. Si detecta movimiento, toma foto, la envia a Gemini Vision para clasificar (persona, animal, paquete, intruso) y envia alerta al PC via FCM. Gratis con Gemini free tier.",
        tech_stack=["termux-camera-photo", "OpenCV (pip)", "Gemini Vision API", "FCM"],
        free_tier="Gemini Vision: 15 RPM/1500 RPD free",
        connects=["MA-01", "MA-04", "MA-12"],
    ),
    EpicIdea(
        id="PA-08",
        title="Voice Pipeline Unificado — PC + Pixel same code",
        category="voice",
        priority="high",
        effort="M",
        description="Un solo pipeline de voz que detecta el dispositivo y usa el backend correcto: en PC usa Whisper local (faster-whisper, gratis) o Gemini API; en Pixel usa termux-speech-to-text. Daniela te escucha igual en ambos. Elimina codigo duplicado entre copiloto_voz.py, daemon_escucha.py, y satellite_ai.py.",
        tech_stack=["faster-whisper (PC)", "termux-speech-to-text (Pixel)", "edge-tts (ambos)", "platform detection"],
        free_tier="Whisper local es 100% gratis",
        connects=["MA-06", "MA-07", "MA-08"],
    ),
    EpicIdea(
        id="PA-09",
        title="Termux API Gateway — REST API en el Pixel",
        category="bridge",
        priority="critical",
        effort="M",
        description="Mini servidor Flask en el Pixel (Termux) que expone todos los comandos de Termux como endpoints REST. El PC puede llamar POST /torch, POST /camera, GET /location, GET /battery, POST /vibrate, POST /tts, GET /notifications, POST /sms, etc. Auth con token compartido. Esto unifica TODO.",
        tech_stack=["Flask en Termux", "12 Termux API commands", "token auth", "mDNS discovery"],
        free_tier="$0 — todo corre en el Pixel",
        connects=["MA-01", "MA-02", "MA-03", "MA-04", "MA-05", "MA-12"],
    ),
    EpicIdea(
        id="PA-10",
        title="Geofence Automation Engine — home/outdoors auto-mode",
        category="iot",
        priority="medium",
        effort="M",
        description="Cuando el GPS detecta que llegaste a casa (radio configurable), Daniela activa modo home: luces on, musica, resumen del dia, TTS en español. Cuando sales, activa modo outdoors: GPS tracking, battery saving, security alert, notifications forwarded al PC. Coordenadas configurables via JSON.",
        tech_stack=["termux-location", "geofence math", "Home Assistant API", "FCM"],
        free_tier="$0",
        connects=["MA-03", "MA-05", "MA-15"],
    ),
    EpicIdea(
        id="PA-11",
        title="Pixel Screen Mirror + AI Vision — Gemini analiza pantalla",
        category="ai_vision",
        priority="medium",
        effort="L",
        description="scrcpy muestra la pantalla del Pixel en el PC. Cada N segundos, un screenshot se envia a Gemini Vision que analiza: detecta spam/phishing en notificaciones, ofertas relevantes, texto importante, codigo de verificacion. Daniela te dice 'Alejandro, tienes un SMS de verify con codigo 483929' sin que mires el movil.",
        tech_stack=["scrcpy", "ADB screencap", "Gemini Vision API (gemini-3.6-flash)", "Python"],
        free_tier="Gemini Flash: 15 RPM/1500 RPD free",
        connects=["MA-02", "MA-05", "MA-14"],
    ),
    EpicIdea(
        id="PA-12",
        title="Clipboard Sync — bidireccional PC <-> Pixel",
        category="sync",
        priority="medium",
        effort="S",
        description="Sincronizacion del portapapeles en tiempo real. Copias texto en el PC (Ctrl+C) y aparece en el Pixel automaticamente. Copias en el Pixel y aparece en el PC. Usa WebSocket para push instantaneo. Util para copiar codigos, URLs, contrasenas entre dispositivos.",
        tech_stack=["Flask-SocketIO", "termux-clipboard-get/set", "pyperclip (PC)", "watchdog"],
        free_tier="$0",
        connects=["MA-01", "MA-13"],
    ),
    EpicIdea(
        id="PA-13",
        title="File Sync Daemon — fotos y archivos auto-sync",
        category="sync",
        priority="medium",
        effort="M",
        description="Sincronizacion automatica de archivos entre PC y Pixel. Fotos tomadas en el Pixel aparecen en el PC automaticamente. Screenshots del PC aparecen en el Pixel. Usa rsync over SSH o un simple HTTP file watcher. Organiza por fecha automaticamente.",
        tech_stack=["Python watchdog", "HTTP file upload", "termux-storage", "rsync"],
        free_tier="$0",
        connects=["MA-01", "MA-10", "MA-14"],
    ),
    EpicIdea(
        id="PA-14",
        title="Battery-Aware Scheduler — modo ahorro/full automatico",
        category="bridge",
        priority="high",
        effort="S",
        description="Daniela ajusta su comportamiento segun la bateria del Pixel. >50%: modo full (TTS, streaming, RAG, analisis continuo). 20-50%: modo normal (polling cada 30s, TTS solo alerts). <20%: modo ahorro (solo notificaciones criticas, sin TTS, sin streaming, GPS solo on-demand). Battery state compartido via FCM.",
        tech_stack=["termux-battery-status", "FCM", "configurable thresholds JSON"],
        free_tier="$0",
        connects=["MA-02", "MA-03", "MA-17"],
    ),
    EpicIdea(
        id="PA-15",
        title="Pixel as Second Screen — dashboard en el movil",
        category="bridge",
        priority="low",
        effort="M",
        description="El Pixel funciona como segunda pantalla del PC. Muestra el dashboard de Daniela (health score, agent status, activity feed, metrics). Touch controls para interactuar. Cuando el PC esta ocupado procesando, el Pixel muestra el progreso. Usa el navegador del Pixel apuntando a daniela_os.py.",
        tech_stack=["Flask templates", "responsive CSS", "WakeLock API", "touch events"],
        free_tier="$0",
        connects=["MA-13", "MA-14"],
    ),
]


# ==============================================================================
# ROADMAP
# ==============================================================================

ROADMAP = [
    RoadmapPhase(
        phase=1,
        name="Foundation — Bridge & Discovery",
        duration_weeks=3,
        ideas=["PA-09", "PA-01", "PA-06", "PA-14"],
        description="Construir el Termux API Gateway en el Pixel, el Pixel Bridge Hub en el PC, y el auto-switch dual-mode. Esto conecta todo por primera vez.",
    ),
    RoadmapPhase(
        phase=2,
        name="Real-time — Sensors & Notifications",
        duration_weeks=4,
        ideas=["PA-03", "PA-04", "PA-12"],
        description="Streaming de sensores en vivo, push notifications bidireccionales reales con FCM, y clipboard sync instantaneo.",
    ),
    RoadmapPhase(
        phase=3,
        name="Control — ADB & Voice",
        duration_weeks=4,
        ideas=["PA-02", "PA-08", "PA-13"],
        description="Control remoto del Pixel con scrcpy/ADB, unificacion del pipeline de voz PC+Pixel, y file sync automatico.",
    ),
    RoadmapPhase(
        phase=4,
        name="Intelligence — IoT & Vision",
        duration_weeks=5,
        ideas=["PA-05", "PA-10", "PA-07", "PA-11", "PA-15"],
        description="IoT real con Home Assistant, geofence automation, Pixel como camara de seguridad con AI vision, screen mirror con Gemini, y Pixel como second screen.",
    ),
]


# ==============================================================================
# SECURITY AUDIT
# ==============================================================================

SECURITY_FINDINGS = [
    {"id": "PS-01", "severity": "critical", "file": "copiloto_voz.py", "line": 91, "issue": "os.system(comando) ejecuta cualquier comando generado por mapear_comando() — command injection critico"},
    {"id": "PS-02", "severity": "critical", "file": "copiloto_voz.py", "line": 53, "issue": "rm -f ~/daniela-os/*.jpg — destructivo sin confirmacion"},
    {"id": "PS-03", "severity": "high", "file": "daniela_mobile_daemon.py", "line": 9, "issue": "os.system('termux-vibrate -d 80') — injection si pattern viene de input"},
    {"id": "PS-04", "severity": "high", "file": "daniela_mobile_daemon.py", "line": 20, "issue": "os.system(f\"termux-tts-speak -l es '{clean_text}'\") — injection si text tiene comillas dobles o backticks"},
    {"id": "PS-05", "severity": "high", "file": "daniela_satellite_ai.py", "line": 46, "issue": "os.system(f\"termux-tts-speak '{texto_limpio}'\") — mismo patron de injection"},
    {"id": "PS-06", "severity": "high", "file": "daniela_dual_sat.py", "line": 46, "issue": "os.system(f\"termux-tts-speak '{texto_limpio}' 2>/dev/null\") — mismo patron"},
    {"id": "PS-07", "severity": "high", "file": "caja_negra.py", "line": 42, "issue": "os.system(f\"termux-microphone-record -l 10 -f {audio_file}\") — path injection en filename"},
    {"id": "PS-08", "severity": "high", "file": "android_control.py", "line": 6, "issue": "subprocess.run(..., shell=True) — shell injection en termux-location"},
    {"id": "PS-09", "severity": "medium", "file": "activar_servicios.py", "line": 27, "issue": "HTTPServer en 0.0.0.0:8081 sin auth ni SSL — cualquiera en la WiFi puede enviar datos"},
    {"id": "PS-10", "severity": "medium", "file": "daniela_hardware_bridge.py", "line": 27, "issue": "Retorna datos fake (battery=32%, Madrid coords) cuando falla — datos falsos pueden confundir"},
    {"id": "PS-11", "severity": "medium", "file": "trusted_devices.json", "line": 1, "issue": "2 UUIDs sin metadatos ni validacion — cualquiera podria añadir un UUID"},
    {"id": "PS-12", "severity": "low", "file": "daniela_satellite_ai.py", "line": 41, "issue": "API key leida manualmente de .env — no usa dotenv, fallback fragil"},
]


# ==============================================================================
# CLI
# ==============================================================================

def cli_status():
    print("\n" + "=" * 60)
    print("  PIXEL AUDIT & EPIC IDEAS — STATUS")
    print("=" * 60)

    by_status = {}
    for m in AUDIT_RESULTS:
        by_status.setdefault(m.status, []).append(m)

    by_cat = {}
    for m in AUDIT_RESULTS:
        by_cat.setdefault(m.category, []).append(m)

    print(f"\n  Modules audited: {len(AUDIT_RESULTS)}")
    print(f"  Termux commands in use: {len(TERMUX_INVENTORY)}")
    print(f"  Termux commands available but NOT used: {len(TERMUX_AVAILABLE_NOT_USED)}")
    print(f"  Epic ideas: {len(EPIC_IDEAS)}")
    print(f"  Security findings: {len(SECURITY_FINDINGS)}")
    print(f"  Roadmap phases: {len(ROADMAP)}")

    print("\n  By status:")
    for status, modules in sorted(by_status.items()):
        print(f"    {status}: {len(modules)}")

    print("\n  By category:")
    for cat, modules in sorted(by_cat.items()):
        print(f"    {cat}: {len(modules)}")

    critical = [s for s in SECURITY_FINDINGS if s["severity"] == "critical"]
    high = [s for s in SECURITY_FINDINGS if s["severity"] == "high"]
    print(f"\n  Security: {len(critical)} critical, {len(high)} high, "
          f"{len([s for s in SECURITY_FINDINGS if s['severity'] == 'medium'])} medium, "
          f"{len([s for s in SECURITY_FINDINGS if s['severity'] == 'low'])} low")

    # Key finding: daniela_os.py disconnection
    disconnected = [m for m in AUDIT_RESULTS if m.integration.startswith("NINGUNA")]
    print(f"\n  CRITICAL: {len(disconnected)}/{len(AUDIT_RESULTS)} modules are DISCONNECTED from daniela_os.py")
    print("  CRITICAL: 0 ADB/scrcpy integration — no remote screen control")
    print("  CRITICAL: IoT controller is a STUB — no real home automation")
    print("  CRITICAL: FCM imported but not connected to real device registration")


def cli_audit():
    print("\n" + "=" * 60)
    print("  FULL AUDIT — PIXEL/MOBILE MODULES")
    print("=" * 60)

    for m in AUDIT_RESULTS:
        print(f"\n  [{m.id}] {m.name}")
        print(f"    File: {m.file}")
        print(f"    Category: {m.category}")
        print(f"    Status: {m.status}")
        print(f"    Termux commands: {', '.join(m.termux_commands) if m.termux_commands else 'none'}")
        print(f"    Issues ({len(m.issues)}):")
        for issue in m.issues:
            print(f"      - {issue}")
        print(f"    Integration: {m.integration}")

    print(f"\n  {'=' * 60}")
    print("  TERMUX COMMAND INVENTORY")
    print(f"  {'=' * 60}")
    print(f"\n  In use ({len(TERMUX_INVENTORY)} commands):")
    for cmd, info in sorted(TERMUX_INVENTORY.items()):
        print(f"    {cmd} — {info['files']} files — {info['use']}")

    print(f"\n  Available but NOT used ({len(TERMUX_AVAILABLE_NOT_USED)} commands):")
    for cmd in TERMUX_AVAILABLE_NOT_USED:
        print(f"    {cmd}")

    print(f"\n  {'=' * 60}")
    print("  SECURITY FINDINGS")
    print(f"  {'=' * 60}")
    for s in SECURITY_FINDINGS:
        print(f"  [{s['severity'].upper()}] {s['id']}: {s['file']}:{s['line']}")
        print(f"    {s['issue']}")


def cli_ideas():
    print("\n" + "=" * 60)
    print("  EPIC IDEAS — ACOPLOAR TODO")
    print("=" * 60)

    by_cat = {}
    for idea in EPIC_IDEAS:
        by_cat.setdefault(idea.category, []).append(idea)

    for cat, ideas in sorted(by_cat.items()):
        print(f"\n  --- {cat.upper()} ({len(ideas)} ideas) ---")
        for idea in ideas:
            print(f"\n  [{idea.id}] {idea.title}")
            print(f"    Priority: {idea.priority} | Effort: {idea.effort}")
            print(f"    {idea.description[:150]}...")
            print(f"    Tech: {', '.join(idea.tech_stack)}")
            print(f"    Free: {idea.free_tier}")
            print(f"    Connects: {', '.join(idea.connects)}")


def cli_roadmap():
    print("\n" + "=" * 60)
    print("  ROADMAP — 4 PHASES")
    print("=" * 60)

    total_weeks = sum(p.duration_weeks for p in ROADMAP)
    print(f"\n  Total: {total_weeks} weeks | {len(EPIC_IDEAS)} ideas | $0/month")

    for phase in ROADMAP:
        print(f"\n  Phase {phase.phase}: {phase.name}")
        print(f"    Duration: {phase.duration_weeks} weeks")
        print(f"    Ideas: {', '.join(phase.ideas)}")
        print(f"    {phase.description}")


def cli_all():
    cli_status()
    print()
    cli_audit()
    print()
    cli_ideas()
    print()
    cli_roadmap()


def cli_export():
    data = {
        "export_date": datetime.now().isoformat(),
        "summary": {
            "modules_audited": len(AUDIT_RESULTS),
            "termux_commands_in_use": len(TERMUX_INVENTORY),
            "termux_commands_available_not_used": len(TERMUX_AVAILABLE_NOT_USED),
            "epic_ideas": len(EPIC_IDEAS),
            "security_findings": len(SECURITY_FINDINGS),
            "roadmap_phases": len(ROADMAP),
            "disconnected_modules": len([m for m in AUDIT_RESULTS if m.integration.startswith("NINGUNA")]),
        },
        "audit": [asdict(m) for m in AUDIT_RESULTS],
        "termux_inventory": TERMUX_INVENTORY,
        "termux_available_not_used": TERMUX_AVAILABLE_NOT_USED,
        "epic_ideas": [asdict(i) for i in EPIC_IDEAS],
        "security_findings": SECURITY_FINDINGS,
        "roadmap": [asdict(p) for p in ROADMAP],
    }

    # Save to data dir
    data_path = DATA_DIR / "pixel_audit_full.json"
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    # Save to static/brand for frontend access
    brand_path = OUTPUT_DIR / "pixel_audit_ideas.json"
    with open(brand_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("[Export] Saved to:")
    print(f"  {data_path}")
    print(f"  {brand_path}")


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pixel_audit_ideas.py status|audit|ideas|roadmap|all|export")
        return

    cmd = sys.argv[1]
    if cmd == "status":
        cli_status()
    elif cmd == "audit":
        cli_audit()
    elif cmd == "ideas":
        cli_ideas()
    elif cmd == "roadmap":
        cli_roadmap()
    elif cmd == "all":
        cli_all()
    elif cmd == "export":
        cli_export()
    else:
        print(f"Unknown command: {cmd}")
        print("Available: status|audit|ideas|roadmap|all|export")


if __name__ == "__main__":
    main()
