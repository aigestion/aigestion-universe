"""
Epic PC - One-Click Launcher
Starts all 40 systems as background processes
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

EPIC_ROOT = Path(__file__).parent

AIG_ROOT = Path(__file__).parent.parent
OMNIPRESENTE_SCRIPT = AIG_ROOT / "gev" / "daniela-os" / "server.py"

SYSTEMS = [
    {
        "name": "Daniela Omnipresente",
        "port": 9200,
        "script": str(OMNIPRESENTE_SCRIPT),
        "external": True,
    },
    {"name": "Voice AI Desktop", "port": 5010, "script": "voice-daemon/voice_daemon.py"},
    {"name": "Neural Wallpaper", "port": 5011, "script": "neural-wallpaper/neural_wallpaper.py"},
    {"name": "3D File Galaxy", "port": 5012, "script": "file-galaxy/file_galaxy.py"},
    {
        "name": "Notification Brain",
        "port": 5013,
        "script": "notification-brain/notification_brain.py",
    },
    {"name": "System Hologram", "port": 5014, "script": "health-hologram/health_hologram.py"},
    {"name": "Code Copilot", "port": 5015, "script": "code-copilot/code_copilot.py"},
    {"name": "Cross-Device Telepathy", "port": 5016, "script": "cross-device/cross_device.py"},
    {"name": "Predictive Launcher", "port": 5017, "script": "app-launcher/app_launcher.py"},
    {"name": "AR Desktop", "port": 5018, "script": "ar-overlay/ar_overlay.py"},
    {"name": "Living Organism", "port": 5019, "script": "living-organism/living_organism.py"},
    {"name": "Web Launcher", "port": 5020, "script": "web/server.py"},
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
    {
        "name": "Theme Time Machine",
        "port": 5034,
        "script": "theme-time-machine/theme_time_machine.py",
    },
    {"name": "Desktop Pets 2.0", "port": 5035, "script": "desktop-pets/desktop_pets.py"},
    {"name": "Code Rain Matrix", "port": 5036, "script": "code-rain/code_rain.py"},
    {"name": "Pixel Art Dashboard", "port": 5037, "script": "pixel-dashboard/pixel_dashboard.py"},
    {"name": "Holographic Calendar", "port": 5038, "script": "holo-calendar/holo_calendar.py"},
    {
        "name": "Sound Visualizer Pro",
        "port": 5039,
        "script": "sound-visualizer/sound_visualizer.py",
    },
    {"name": "Night Mode Orchestrator", "port": 5040, "script": "night-mode/night_mode.py"},
    {
        "name": "Smart Clipboard History",
        "port": 5041,
        "script": "clipboard-history/clipboard_history.py",
    },
    {
        "name": "Auto-Screenshot Context",
        "port": 5042,
        "script": "auto-screenshot/auto_screenshot.py",
    },
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


def print_banner():
    print("""
============================================================
            EPIC PC EXPERIENCE LAUNCHER
============================================================
  62 Epic PC systems + 50 Daniela Omnipresente
  Web UI: http://localhost:5020
  Omnipresente: http://localhost:9200

  Usage: python launch.py [start|stop|status]
============================================================
""")


def start_all():
    print("Starting all systems...\n")
    procs = []
    for sys_info in SYSTEMS:
        if sys_info.get("external"):
            script_path = Path(sys_info["script"])
        else:
            script_path = EPIC_ROOT / sys_info["script"]
        if not script_path.exists():
            print(f"  [WARN] {sys_info['name']}: script not found ({sys_info['script']})")
            continue
        try:
            proc = subprocess.Popen(
                [sys.executable, str(script_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            )
            procs.append({"name": sys_info["name"], "port": sys_info["port"], "pid": proc.pid})
            print(f"  [OK] {sys_info['name']:<30} Port: {sys_info['port']}  PID: {proc.pid}")
        except Exception as e:
            print(f"  [FAIL] {sys_info['name']}: {e}")
    pid_file = EPIC_ROOT / "pids.json"
    with open(pid_file, "w") as f:
        json.dump(procs, f, indent=2)
    print(f"\n{len(procs)} systems started")
    print("Web UI: http://localhost:5020\n")
    time.sleep(1)
    import webbrowser

    webbrowser.open("http://localhost:5020")


def stop_all():
    print("Stopping all systems...\n")
    pid_file = EPIC_ROOT / "pids.json"
    if pid_file.exists():
        with open(pid_file) as f:
            procs = json.load(f)
        for p in procs:
            try:
                os.kill(p["pid"], 9)
                print(f"  [STOP] {p['name']} (PID: {p['pid']})")
            except Exception:
                pass
        pid_file.unlink()
    print("\nAll systems stopped")


def status():
    print("\nSystem Status:\n")
    for sys_info in SYSTEMS:
        try:
            import urllib.request

            urllib.request.urlopen(f"http://localhost:{sys_info['port']}/", timeout=2)
            stat = "[RUNNING]"
        except Exception:
            stat = "[STOPPED]"
        print(f"  {stat}  {sys_info['name']:<30} :{sys_info['port']}")


if __name__ == "__main__":
    print_banner()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "start"
    if cmd == "start":
        start_all()
    elif cmd == "stop":
        stop_all()
    elif cmd == "status":
        status()
    else:
        print("Usage: python launch.py [start|stop|status]")
