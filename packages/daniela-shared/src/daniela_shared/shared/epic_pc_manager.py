"""Epic PC Manager — lifecycle + proxy for 62 features.

Absorbs epic-pc's launcher into Daniela as a blueprint.
Manages child processes, proxies requests, and serves the unified web UI.
"""

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

from flask import Blueprint, jsonify, request

EPIC_ROOT = Path(__file__).parent.parent.parent / "epic-pc"
PID_FILE = EPIC_ROOT / "pids.json"

# The 62 features — imported from epic-pc/launch.py
SYSTEMS = [
    {"name": "Voice AI Desktop", "port": 5010, "script": "voice-daemon/voice_daemon.py"},
    {"name": "Neural Wallpaper", "port": 5011, "script": "neural-wallpaper/neural_wallpaper.py"},
    {"name": "3D File Galaxy", "port": 5012, "script": "file-galaxy/file_galaxy.py"},
    {"name": "Notification Brain", "port": 5013, "script": "notification-brain/notification_brain.py"},
    {"name": "System Hologram", "port": 5014, "script": "health-hologram/health_hologram.py"},
    {"name": "Code Copilot", "port": 5015, "script": "code-copilot/code_copilot.py"},
    {"name": "Cross-Device Telepathy", "port": 5016, "script": "cross-device/cross_device.py"},
    {"name": "Predictive Launcher", "port": 5017, "script": "app-launcher/app_launcher.py"},
    {"name": "AR Desktop", "port": 5018, "script": "ar-overlay/ar_overlay.py"},
    {"name": "Living Organism", "port": 5019, "script": "living-organism/living_organism.py"},
    {"name": "AI Memory Palace", "port": 5021, "script": "memory-palace/memory_palace.py"},
    {"name": "Dream Logger", "port": 5022, "script": "dream-logger/dream_logger.py"},
    {"name": "Context Switcher", "port": 5023, "script": "context-switcher/context_switcher.py"},
    {"name": "AI Auto-Organizer", "port": 5024, "script": "auto-organizer/auto_organizer.py"},
    {"name": "Focus Mode", "port": 5025, "script": "focus-mode/focus_mode.py"},
    {"name": "Typing Predictor", "port": 5026, "script": "typing-predictor/typing_predictor.py"},
    {"name": "Meeting Prepper", "port": 5027, "script": "meeting-prepper/meeting_prepper.py"},
    {"name": "Post-Meeting Digest", "port": 5028, "script": "meeting-digest/meeting_digest.py"},
    {"name": "Email Priority Brain", "port": 5029, "script": "email-brain/email_brain.py"},
    {"name": "Knowledge Weaver", "port": 5030, "script": "knowledge-weaver/knowledge_weaver.py"},
    {"name": "Ambient Wallpaper", "port": 5031, "script": "ambient-wallpaper/ambient_wallpaper.py"},
    {"name": "Desktop Zen Garden", "port": 5032, "script": "zen-garden/zen_garden.py"},
    {"name": "Floating Wiki", "port": 5033, "script": "floating-wiki/floating_wiki.py"},
    {"name": "Theme Time Machine", "port": 5034, "script": "theme-time-machine/theme_time_machine.py"},
    {"name": "Desktop Pets 2.0", "port": 5035, "script": "desktop-pets/desktop_pets.py"},
    {"name": "Code Rain Matrix", "port": 5036, "script": "code-rain/code_rain.py"},
    {"name": "Pixel Art Dashboard", "port": 5037, "script": "pixel-dashboard/pixel_dashboard.py"},
    {"name": "Holographic Calendar", "port": 5038, "script": "holo-calendar/holo_calendar.py"},
    {"name": "Sound Visualizer Pro", "port": 5039, "script": "sound-visualizer/sound_visualizer.py"},
    {"name": "Night Mode Orchestrator", "port": 5040, "script": "night-mode/night_mode.py"},
    {"name": "Smart Clipboard History", "port": 5041, "script": "clipboard-history/clipboard_history.py"},
    {"name": "Auto-Screenshot Context", "port": 5042, "script": "auto-screenshot/auto_screenshot.py"},
    {"name": "Batch File Renamer AI", "port": 5043, "script": "file-renamer/file_renamer.py"},
    {"name": "Smart File Watcher", "port": 5044, "script": "file-watcher/file_watcher.py"},
    {"name": "Quick Actions Bar", "port": 5045, "script": "quick-actions/quick_actions.py"},
    {"name": "Desktop Macros AI", "port": 5046, "script": "desktop-macros/desktop_macros.py"},
    {"name": "Clipboard Translator", "port": 5047, "script": "clip-translator/clip_translator.py"},
    {"name": "Smart App Launcher 2.0", "port": 5048, "script": "smart-launcher/smart_launcher.py"},
    {"name": "Focus Timer", "port": 5049, "script": "focus-timer/focus_timer.py"},
    {"name": "Auto-Backup Brain", "port": 5050, "script": "auto-backup/auto_backup.py"},
    {"name": "Game Launcher Hub", "port": 5051, "script": "game-hub/game_hub.py"},
    {"name": "Music Reactive Desktop", "port": 5052, "script": "music-reactive/music_reactive.py"},
    {"name": "Retro Emulator Hub", "port": 5053, "script": "retro-hub/retro_hub.py"},
    {"name": "Desktop DJ", "port": 5054, "script": "desktop-dj/desktop_dj.py"},
    {"name": "Meme Generator", "port": 5055, "script": "meme-generator/meme_generator.py"},
    {"name": "Stream Overlay", "port": 5056, "script": "stream-overlay/stream_overlay.py"},
    {"name": "VR Desktop", "port": 5057, "script": "vr-desktop/vr_desktop.py"},
    {"name": "Keyboard Sound Engine", "port": 5058, "script": "keyboard-sounds/keyboard_sounds.py"},
    {"name": "Desktop Karaoke", "port": 5059, "script": "desktop-karaoke/desktop_karaoke.py"},
    {"name": "Achievement System", "port": 5060, "script": "achievements/achievement_system.py"},
    {"name": "USB Guardian", "port": 5061, "script": "usb-guardian/usb_guardian.py"},
    {"name": "Screen Privacy", "port": 5062, "script": "screen-privacy/screen_privacy.py"},
    {"name": "Password Vault", "port": 5063, "script": "password-vault/password_vault.py"},
    {"name": "Network Sentinel", "port": 5064, "script": "network-sentinel/network_sentinel.py"},
    {"name": "File Integrity", "port": 5065, "script": "file-integrity/file_integrity.py"},
    {"name": "Encrypted Notes", "port": 5066, "script": "encrypted-notes/encrypted_notes.py"},
    {"name": "Parental Controls", "port": 5067, "script": "parental-controls/parental_controls.py"},
    {"name": "Privacy Dashboard", "port": 5068, "script": "privacy-dashboard/privacy_dashboard.py"},
    {"name": "Firewall Monitor", "port": 5069, "script": "firewall-monitor/firewall_monitor.py"},
    {"name": "Threat Dashboard", "port": 5070, "script": "threat-dashboard/threat_dashboard.py"},
    {"name": "Flow Builder", "port": 9090, "script": "flow-builder/flow_builder.py"},
    {"name": "Multi-Modal", "port": 9091, "script": "multi-modal/multi_modal.py"},
]

# Categories for the web UI
CATEGORIES = {
    "Core Systems": list(range(5010, 5020)),
    "Intelligence & Assistants": list(range(5021, 5031)),
    "Visual & Experience": list(range(5031, 5041)),
    "Productivity & Automation": list(range(5041, 5051)),
    "Entertainment & Games": list(range(5051, 5061)),
    "Security & Monitoring": list(range(5061, 5071)),
    "Automation": [9090, 9091],
}


def _check_feature(port):
    """Check if a feature is running via TCP."""
    import socket
    try:
        sock = socket.socket()
        sock.settimeout(0.5)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except Exception:
        return False


def _load_pids():
    """Load tracked PIDs from disk."""
    if PID_FILE.exists():
        try:
            with open(PID_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_pids(procs):
    """Save tracked PIDs to disk."""
    with open(PID_FILE, "w") as f:
        json.dump(procs, f, indent=2)


def create_epic_pc_blueprint():
    """Create the Epic PC management blueprint."""
    bp = Blueprint("epic_pc", __name__, url_prefix="/api/epic")

    @bp.route("/systems")
    def list_systems():
        """List all 62 features with their status."""
        running = {}
        for proc in _load_pids():
            running[proc["port"]] = proc

        systems = []
        for s in SYSTEMS:
            is_running = _check_feature(s["port"])
            systems.append({
                "name": s["name"],
                "port": s["port"],
                "script": s["script"],
                "status": "running" if is_running else "stopped",
                "pid": running.get(s["port"], {}).get("pid"),
            })
        return jsonify({"systems": systems, "total": len(systems)})

    @bp.route("/systems/<int:port>/start", methods=["POST"])
    def start_feature(port):
        """Start a single feature."""
        script_info = next((s for s in SYSTEMS if s["port"] == port), None)
        if not script_info:
            return jsonify({"error": "Feature not found"}), 404

        if _check_feature(port):
            return jsonify({"status": "already_running", "port": port})

        script_path = EPIC_ROOT / script_info["script"]
        if not script_path.exists():
            return jsonify({"error": f"Script not found: {script_info['script']}"}), 404

        try:
            proc = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
            )
            procs = _load_pids()
            procs.append({"name": script_info["name"], "port": port, "pid": proc.pid})
            _save_pids(procs)
            return jsonify({"status": "started", "port": port, "pid": proc.pid})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @bp.route("/systems/<int:port>/stop", methods=["POST"])
    def stop_feature(port):
        """Stop a single feature."""
        procs = _load_pids()
        found = False
        for p in procs:
            if p["port"] == port:
                try:
                    os.kill(p["pid"], 9)
                except Exception:
                    pass
                procs.remove(p)
                found = True
                break
        _save_pids(procs)
        return jsonify({"status": "stopped" if found else "not_tracked", "port": port})

    @bp.route("/systems/start-all", methods=["POST"])
    def start_all():
        """Start all features."""
        started = 0
        for s in SYSTEMS:
            if _check_feature(s["port"]):
                continue
            script_path = EPIC_ROOT / s["script"]
            if not script_path.exists():
                continue
            try:
                proc = subprocess.Popen(
                    [sys.executable, str(script_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
                )
                procs = _load_pids()
                procs.append({"name": s["name"], "port": s["port"], "pid": proc.pid})
                _save_pids(procs)
                started += 1
            except Exception:
                pass
        return jsonify({"status": "started", "count": started})

    @bp.route("/systems/stop-all", methods=["POST"])
    def stop_all():
        """Stop all features."""
        procs = _load_pids()
        stopped = 0
        for p in procs:
            try:
                os.kill(p["pid"], 9)
                stopped += 1
            except Exception:
                pass
        _save_pids([])
        return jsonify({"status": "stopped", "count": stopped})

    @bp.route("/proxy/<int:port>/<path:path>")
    def proxy_feature(port, path):
        """Proxy HTTP request to a feature."""
        url = f"http://localhost:{port}/{path}"
        if request.query_string:
            url += f"?{request.query_string.decode()}"
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'AIG-Daniela/1.0')
            for key, val in request.headers:
                if key.lower() not in ('host', 'user-agent'):
                    req.add_header(key, val)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = resp.read()
                return data, resp.status, {"Content-Type": resp.headers.get("Content-Type", "text/html")}
        except Exception as e:
            return jsonify({"error": str(e)}), 502

    return bp
